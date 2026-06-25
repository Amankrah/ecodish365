import logging
from .data_loader import CNFDataLoader
from .data_processor import CNFDataProcessor
import pandas as pd
from functools import lru_cache
from datetime import datetime
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)

class CNFDataPipeline:
    """
    Main pipeline for Canadian Nutrient File data operations.
    Provides a clean interface for food data exploration and management.
    """
    
    def __init__(self, data_dir: str, *, shared_source=None):
        """Initialise the dish pipeline, optionally borrowing dataframes.

        `shared_source` — when given, should be an object exposing the
        standard `*_df` attributes (e.g. an `api.cnf_data_pipeline.CNFDataPipeline`
        instance). The loader wraps those frames by reference rather than
        re-reading the CSVs from disk, so only one in-memory copy of the
        CNF data exists in the process.
        """
        self.data_loader = CNFDataLoader(data_dir, shared_source=shared_source)
        self.data_processor = CNFDataProcessor(self.data_loader)
        self._initialize_search_index()

    def _initialize_search_index(self):
        """Initialize search index for better performance."""
        try:
            # Create lowercase search index for food descriptions
            self.data_loader.food_name_df['search_index'] = (
                self.data_loader.food_name_df['FoodDescription'].str.lower() + ' ' +
                self.data_loader.food_name_df['FoodDescriptionF'].str.lower().fillna('')
            )
        except Exception as e:
            logger.warning(f"Failed to initialize search index: {e}")

    # =============================================================================
    # Food Management Operations
    # =============================================================================
    
    def add_food(self, food_data: Dict, validate: bool = True) -> int:
        """
        Add a single food item to the database.
        
        Args:
            food_data: Dictionary containing food information
            validate: Whether to validate the input data
            
        Returns:
            int: The FoodID of the newly created food
        """
        try:
            return self.data_processor.add_new_food(food_data, validate)
        except Exception as e:
            logger.error(f"Error adding food: {str(e)}")
            raise

    def add_foods_batch(self, foods_data: List[Dict], validate: bool = True) -> List[int]:
        """
        Add multiple foods in a single batch operation.
        
        Args:
            foods_data: List of food dictionaries
            validate: Whether to validate the input data
            
        Returns:
            List[int]: List of FoodIDs for the newly created foods
        """
        try:
            return self.data_processor.add_foods_batch(foods_data, validate)
        except Exception as e:
            logger.error(f"Error adding foods batch: {str(e)}")
            raise

    def update_food(self, food_id: int, updated_data: Dict) -> Dict:
        """Update an existing food item."""
        try:
            return self.data_processor.update_food(food_id, updated_data)
        except Exception as e:
            logger.error(f"Error updating food {food_id}: {str(e)}")
            raise

    def delete_food(self, food_id: int) -> bool:
        """Delete a food item and all related data."""
        try:
            return self.data_processor.delete_food(food_id)
        except Exception as e:
            logger.error(f"Error deleting food {food_id}: {str(e)}")
            raise

    def get_food_details(self, food_id: int) -> Optional[Dict]:
        """Get comprehensive details for a specific food."""
        try:
            return self.data_processor.get_food_details(food_id)
        except Exception as e:
            logger.error(f"Error fetching food details for {food_id}: {str(e)}")
            raise

    # =============================================================================
    # Search and Exploration Operations
    # =============================================================================

    @lru_cache(maxsize=1024)
    def search_foods(self, query: str, limit: int = 50, offset: int = 0, source: str = 'both') -> Dict:
        """
        Advanced food search with pagination and relevance scoring.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            source: WAFCT-EXTEND / FDC-INGEST — 'both' | 'cnf' | 'wafct' | 'fdc'
                (subset rows before substring match).

        Returns:
            Dict containing search results and metadata
        """
        try:
            if not query or len(query.strip()) < 2:
                return {"results": [], "total": 0, "query": query}

            src = (source or 'both').lower()
            if src not in ('cnf', 'wafct', 'fdc', 'ciqual', 'ciqual', 'both'):
                src = 'both'

            query_lower = query.lower().strip()

            base = self.data_loader.food_name_df
            work_df = base
            if src in ('cnf', 'wafct', 'fdc', 'ciqual') and 'source' in base.columns:
                work_df = base[base['source'] == src]
            elif src in ('cnf', 'wafct', 'fdc', 'ciqual'):
                logger.warning(
                    '`source` column missing on food_name_df; ignoring source=%r', src,
                )

            if work_df.empty:
                return {
                    "results": [],
                    "total": 0,
                    "query": query,
                    "limit": limit,
                    "offset": offset,
                    "has_more": False,
                    **({"source_filter": src} if src in ('cnf', 'wafct', 'fdc', 'ciqual') else {}),
                }

            # Search in food descriptions
            mask = work_df['search_index'].str.contains(
                query_lower, case=False, na=False
            )

            results_df = work_df[mask].copy()
            
            # Add relevance scoring
            results_df['relevance'] = results_df['FoodDescription'].str.lower().apply(
                lambda x: self._calculate_relevance(x, query_lower)
            )
            
            # Sort by relevance and apply pagination
            results_df = results_df.sort_values('relevance', ascending=False)
            total_results = len(results_df)
            
            paginated_results = results_df.iloc[offset:offset + limit]
            
            # Format results
            formatted_results = []
            for _, row in paginated_results.iterrows():
                formatted_results.append({
                    'FoodID': int(row['FoodID']),
                    'FoodCode': str(row['FoodCode']),
                    'FoodDescription': str(row['FoodDescription']),
                    'FoodDescriptionF': str(row.get('FoodDescriptionF', '')),
                    'FoodGroupID': int(row['FoodGroupID']),
                    'relevance': float(row['relevance'])
                })
            
            out = {
                "results": formatted_results,
                "total": total_results,
                "query": query,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_results,
            }
            if src in ('cnf', 'wafct', 'fdc', 'ciqual'):
                out["source_filter"] = src
                out["filtered_count"] = total_results
            return out
            
        except Exception as e:
            logger.error(f"Error searching foods: {str(e)}")
            raise

    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score for search results."""
        if query in text:
            if text.startswith(query):
                return 1.0  # Exact match at start
            elif query in text.split():
                return 0.8  # Word match
            else:
                return 0.6  # Substring match
        return 0.1  # Fuzzy match

    def search_foods_by_nutrient(self, nutrient_id: int, min_value: float = None, 
                                max_value: float = None, limit: int = 50) -> List[Dict]:
        """
        Search foods by nutrient content.
        
        Args:
            nutrient_id: The nutrient ID to search for
            min_value: Minimum nutrient value (optional)
            max_value: Maximum nutrient value (optional)
            limit: Maximum number of results
            
        Returns:
            List of foods matching the nutrient criteria
        """
        try:
            # Get nutrient data
            nutrient_df = self.data_loader.nutrient_amount_df[
                self.data_loader.nutrient_amount_df['NutrientID'] == nutrient_id
            ]
            
            # Apply value filters
            if min_value is not None:
                nutrient_df = nutrient_df[nutrient_df['NutrientValue'] >= min_value]
            if max_value is not None:
                nutrient_df = nutrient_df[nutrient_df['NutrientValue'] <= max_value]
            
            # Sort by nutrient value (descending)
            nutrient_df = nutrient_df.sort_values('NutrientValue', ascending=False)
            
            # Get food details
            food_ids = nutrient_df['FoodID'].head(limit).tolist()
            foods = []
            
            for food_id in food_ids:
                food_details = self.get_food_details(food_id)
                if food_details:
                    # Add the specific nutrient value to the response
                    nutrient_value = nutrient_df[nutrient_df['FoodID'] == food_id]['NutrientValue'].iloc[0]
                    food_details['queried_nutrient_value'] = float(nutrient_value)
                    foods.append(food_details)
            
            return foods
            
        except Exception as e:
            logger.error(f"Error searching foods by nutrient: {str(e)}")
            raise

    def discover_foods(
        self,
        criteria: List[Dict],
        basis: str = 'per_100g',
        food_group_id: Optional[int] = None,
        source: Optional[str] = None,
        ratio: Optional[Dict] = None,
        dv_threshold: Optional[Dict] = None,
        sort: Optional[Dict] = None,
        limit: int = 100,
    ) -> Dict:
        """Multi-criteria nutrient discovery for the research workbench.

        Every food in the catalogue must verifiably satisfy ALL criteria (AND logic);
        a food missing a measurement for a criterion nutrient is excluded, mirroring the
        single-nutrient search (we only return verified matches).

        Args:
            criteria: list of {nutrient_id, min?, max?}. Thresholds are interpreted in
                      the chosen `basis`.
            basis: 'per_100g' (raw CNF values) or 'per_100kcal' (energy-adjusted density;
                   value_per_100kcal = value_per_100g / energy_per_100g * 100).
            food_group_id: optional CNF FoodGroupID scope.
            source: 'cnf' | 'wafct' | None (both).
            ratio: optional {numerator_id, denominator_id}; reported + sortable. Basis-
                   invariant (numerator and denominator scale together).
            dv_threshold: optional {nutrient_id, min_pct?, max_pct?}; %DV is always computed
                   on the per-100 g amount (Health Canada table), independent of `basis`.
            sort: optional {key, direction}; key is a NutrientID (int/str), 'ratio', or
                  'energy'. Default: first criterion (or ratio, or energy), descending.
            limit: max rows (capped at 200).

        Returns dict: {foods: [...], involved_nutrient_ids: [...], basis, count}.
        """
        import numpy as np
        from api.services.cnf_daily_values import get_daily_value

        nl = self.data_loader
        na = nl.nutrient_amount_df
        fn = nl.food_name_df
        limit = max(1, min(int(limit), 200))
        criteria = criteria or []
        ENERGY_ID = 208

        # --- Collect every nutrient id we must read ---
        needed = {ENERGY_ID}
        for c in criteria:
            needed.add(int(c['nutrient_id']))
        if ratio:
            needed.add(int(ratio['numerator_id']))
            needed.add(int(ratio['denominator_id']))
        dv_nid = int(dv_threshold['nutrient_id']) if dv_threshold else None
        if dv_nid is not None:
            needed.add(dv_nid)
            dv_entry = get_daily_value(dv_nid)
            if dv_entry and dv_entry.get('sum_with_nutrient_id') is not None:
                needed.add(int(dv_entry['sum_with_nutrient_id']))
        sort_key = (sort or {}).get('key')
        sort_nid = None
        if isinstance(sort_key, (int, float)) or (isinstance(sort_key, str) and sort_key.isdigit()):
            sort_nid = int(sort_key)
            needed.add(sort_nid)

        # --- Wide per-food nutrient frame (FoodID x NutrientID), values per 100 g ---
        sub = na[na['NutrientID'].isin(needed)][['FoodID', 'NutrientID', 'NutrientValue']]
        if sub.empty:
            return {'foods': [], 'involved_nutrient_ids': sorted(needed), 'basis': basis, 'count': 0}
        wide = sub.pivot_table(index='FoodID', columns='NutrientID',
                               values='NutrientValue', aggfunc='first')
        wide.index = wide.index.astype('int64')

        def col(nid):
            return wide[nid] if nid in wide.columns else pd.Series(np.nan, index=wide.index)

        # Energy-adjusted basis factor (100 / energy_per_100g), NaN where energy <= 0.
        if basis == 'per_100kcal':
            e = col(ENERGY_ID)
            basis_factor = (100.0 / e).where(e > 0)
        else:
            basis_factor = None

        def basis_val(nid):
            v = col(nid)
            return v * basis_factor if basis_factor is not None else v

        # --- AND criteria mask (NaN comparisons -> False -> excluded) ---
        mask = pd.Series(True, index=wide.index)
        for c in criteria:
            val = basis_val(int(c['nutrient_id']))
            if c.get('min') is not None:
                mask &= (val >= float(c['min']))
            if c.get('max') is not None:
                mask &= (val <= float(c['max']))

        # --- %DV threshold (on per-100 g amount; sums trans into saturated for 606) ---
        if dv_nid is not None:
            entry = get_daily_value(dv_nid)
            if entry and entry.get('dv', 0) > 0:
                num = col(dv_nid).copy()
                other_id = entry.get('sum_with_nutrient_id')
                if other_id is not None:
                    num = num.add(col(int(other_id)), fill_value=0)
                pct = num / float(entry['dv']) * 100.0
                if dv_threshold.get('min_pct') is not None:
                    mask &= (pct >= float(dv_threshold['min_pct']))
                if dv_threshold.get('max_pct') is not None:
                    mask &= (pct <= float(dv_threshold['max_pct']))

        # --- ratio (basis-invariant), NaN where denominator <= 0 ---
        ratio_series = None
        if ratio:
            denc = col(int(ratio['denominator_id']))
            ratio_series = (col(int(ratio['numerator_id'])) / denc).where(denc > 0)

        # --- food-group + source scope ---
        allowed = fn
        if food_group_id is not None:
            allowed = allowed[allowed['FoodGroupID'] == int(food_group_id)]
        if source in ('cnf', 'wafct', 'fdc', 'ciqual') and 'source' in allowed.columns:
            allowed = allowed[allowed['source'] == source]
        allowed_ids = set(int(x) for x in allowed['FoodID'].dropna().tolist())
        mask &= wide.index.to_series().isin(allowed_ids)

        # --- choose the ranking series ---
        if sort_nid is not None:
            sort_vals = basis_val(sort_nid)
        elif sort_key == 'ratio' and ratio_series is not None:
            sort_vals = ratio_series
        elif sort_key == 'energy':
            sort_vals = col(ENERGY_ID)
        elif criteria:
            sort_vals = basis_val(int(criteria[0]['nutrient_id']))
        elif ratio_series is not None:
            sort_vals = ratio_series
        else:
            sort_vals = col(ENERGY_ID)
        ascending = (sort or {}).get('direction') == 'asc'

        ordered_index = (sort_vals[mask]
                         .sort_values(ascending=ascending, na_position='last')
                         .head(limit).index.tolist())

        # --- assemble rows (vectorised lookups, no per-food get_food_details) ---
        fg = getattr(nl, 'food_group_df', None)
        group_names = {}
        if fg is not None and 'FoodGroupID' in fg.columns and 'FoodGroupName' in fg.columns:
            group_names = dict(zip(fg['FoodGroupID'], fg['FoodGroupName']))
        fn_idx = fn.set_index('FoodID')
        has_source = 'source' in fn.columns
        involved = sorted(n for n in needed if n != ENERGY_ID)

        foods = []
        for fid in ordered_index:
            try:
                row = fn_idx.loc[fid]
            except KeyError:
                continue
            gid = row.get('FoodGroupID')
            e_val = col(ENERGY_ID).get(fid)
            nutrient_values = {}
            basis_values = {}
            for nid in involved:
                v = col(nid).get(fid)
                if v is not None and pd.notna(v):
                    nutrient_values[nid] = round(float(v), 4)
                if basis_factor is not None:
                    bv = basis_val(nid).get(fid)
                    if bv is not None and pd.notna(bv):
                        basis_values[nid] = round(float(bv), 4)
            rv = ratio_series.get(fid) if ratio_series is not None else None
            sv = sort_vals.get(fid)
            foods.append({
                'FoodID': int(fid),
                'FoodCode': str(row.get('FoodCode', '')),
                'FoodDescription': str(row.get('FoodDescription', '')),
                'FoodGroupID': int(gid) if pd.notna(gid) else None,
                'FoodGroupName': str(group_names.get(gid, 'Unknown')),
                'source': (str(row.get('source')) if has_source and pd.notna(row.get('source')) else 'cnf'),
                'energy_kcal': (round(float(e_val), 2) if e_val is not None and pd.notna(e_val) else None),
                'nutrient_values': {str(k): v for k, v in nutrient_values.items()},
                'basis_values': {str(k): v for k, v in basis_values.items()},
                'ratio_value': (round(float(rv), 4) if rv is not None and pd.notna(rv) else None),
                'sort_value': (round(float(sv), 4) if sv is not None and pd.notna(sv) else None),
            })

        return {
            'foods': foods,
            'involved_nutrient_ids': involved,
            'basis': basis,
            'count': len(foods),
        }

    def get_foods_by_group(
        self,
        food_group_id: int,
        limit: int = 100,
        offset: int = 0,
        q: Optional[str] = None,
        sort: str = 'name',
        sort_dir: str = 'asc',
        food_type: Optional[str] = None,
        thermal: Optional[str] = None,
        preservation: Optional[str] = None,
        source: Optional[str] = None,
        include_summary: bool = False,
    ) -> Dict:
        """List foods in a food group with enrichment, filters, and pagination.

        Enriches each row with source, energy/protein/fibre per 100 g, food_type,
        and two-axis prep-state tags from the offline CNF/WAFCT label files.
        """
        from api.services.cnf_food_type import get_food_type
        from api.services.cnf_prep_state import prep_state_of

        ENERGY_ID, PROTEIN_ID, FIBRE_ID = 208, 203, 291
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        sort = (sort or 'name').lower()
        sort_dir = (sort_dir or 'asc').lower()
        if sort_dir not in ('asc', 'desc'):
            sort_dir = 'asc'

        try:
            fn = self.data_loader.food_name_df
            pool = fn[fn['FoodGroupID'] == int(food_group_id)].copy()
            total_in_group = len(pool)

            if pool.empty:
                empty = {
                    'foods': [],
                    'food_group_id': int(food_group_id),
                    'count': 0,
                    'total_count': 0,
                    'total_in_group': 0,
                    'limit': limit,
                    'offset': offset,
                    'has_more': False,
                }
                if include_summary:
                    empty['summary'] = self._empty_group_summary()
                return empty

            if 'source' not in pool.columns:
                pool['source'] = 'cnf'
            if source in ('cnf', 'wafct', 'fdc', 'ciqual'):
                pool = pool[pool['source'] == source]

            if food_type in ('single', 'mixed'):
                matched_ids = []
                for fid in pool['FoodID'].astype(int):
                    rec = get_food_type(int(fid))
                    if rec and rec.get('food_type') == food_type:
                        matched_ids.append(int(fid))
                pool = pool[pool['FoodID'].astype(int).isin(matched_ids)]

            if thermal:
                matched_ids = []
                for fid in pool['FoodID'].astype(int):
                    ps = prep_state_of(int(fid))
                    t = ps.thermal_state if ps else 'unknown'
                    if t == thermal:
                        matched_ids.append(int(fid))
                pool = pool[pool['FoodID'].astype(int).isin(matched_ids)]

            if preservation:
                matched_ids = []
                for fid in pool['FoodID'].astype(int):
                    ps = prep_state_of(int(fid))
                    p = ps.preservation_state if ps else 'unknown'
                    if p == preservation:
                        matched_ids.append(int(fid))
                pool = pool[pool['FoodID'].astype(int).isin(matched_ids)]

            summary = None
            if include_summary:
                summary = self._compute_group_summary_from_df(pool)

            if q and q.strip():
                needle = q.strip().lower()
                if 'search_index' in pool.columns:
                    pool = pool[pool['search_index'].str.contains(needle, na=False, regex=False)]
                else:
                    pool = pool[
                        pool['FoodDescription'].str.lower().str.contains(needle, na=False, regex=False)
                        | pool['FoodDescriptionF'].fillna('').str.lower().str.contains(needle, na=False, regex=False)
                    ]

            total_count = len(pool)
            if total_count == 0:
                result = {
                    'foods': [],
                    'food_group_id': int(food_group_id),
                    'count': 0,
                    'total_count': 0,
                    'total_in_group': total_in_group,
                    'limit': limit,
                    'offset': offset,
                    'has_more': False,
                }
                if include_summary:
                    result['summary'] = summary or self._empty_group_summary()
                return result

            food_ids = pool['FoodID'].astype(int).tolist()
            na = self.data_loader.nutrient_amount_df
            nut_sub = na[
                na['FoodID'].isin(food_ids) & na['NutrientID'].isin([ENERGY_ID, PROTEIN_ID, FIBRE_ID])
            ][['FoodID', 'NutrientID', 'NutrientValue']]
            nut_map: Dict[int, Dict[int, float]] = {}
            for row in nut_sub.itertuples(index=False):
                fid = int(row.FoodID)
                bucket = nut_map.get(fid)
                if bucket is None:
                    bucket = {}
                    nut_map[fid] = bucket
                bucket[int(row.NutrientID)] = float(row.NutrientValue)

            rows: List[Dict] = []
            for rec in pool.itertuples(index=False):
                fid = int(rec.FoodID)
                nuts = nut_map.get(fid, {})
                ft = get_food_type(fid)
                ps = prep_state_of(fid)
                src = str(getattr(rec, 'source', 'cnf') or 'cnf')
                rows.append({
                    'FoodID': fid,
                    'FoodCode': str(rec.FoodCode),
                    'FoodDescription': str(rec.FoodDescription),
                    'FoodDescriptionF': str(getattr(rec, 'FoodDescriptionF', '') or ''),
                    'source': src,
                    'energy_kcal': nuts.get(ENERGY_ID),
                    'protein_g': nuts.get(PROTEIN_ID),
                    'fibre_g': nuts.get(FIBRE_ID),
                    'food_type': ft.get('food_type') if ft else None,
                    'thermal_state': ps.thermal_state if ps else None,
                    'preservation_state': ps.preservation_state if ps else None,
                })

            reverse = sort_dir == 'desc'
            if sort == 'kcal':
                rows.sort(key=lambda r: (r['energy_kcal'] is None, r['energy_kcal'] or 0), reverse=reverse)
            elif sort == 'food_id':
                rows.sort(key=lambda r: r['FoodID'], reverse=reverse)
            else:
                rows.sort(key=lambda r: (r['FoodDescription'] or '').lower(), reverse=reverse)

            page = rows[offset:offset + limit]
            return {
                'foods': page,
                'food_group_id': int(food_group_id),
                'count': len(page),
                'total_count': total_count,
                'total_in_group': total_in_group,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(page)) < total_count,
                **({'summary': summary} if include_summary else {}),
            }

        except Exception as e:
            logger.error(f"Error getting foods by group: {str(e)}")
            raise

    @staticmethod
    def _empty_group_summary() -> Dict:
        return {
            'total_in_group': 0,
            'cnf_count': 0,
            'wafct_count': 0,
            'food_type': {'single': 0, 'mixed': 0, 'unknown': 0},
            'thermal_state': {},
            'preservation_state': {},
            'prep_both_known_pct': 0.0,
            'cnf_count': 0,
            'wafct_count': 0,
            'fdc_count': 0,
            'ciqual_count': 0,
        }

    @staticmethod
    def _compute_group_summary_from_df(pool) -> Dict:
        """Aggregate source, food-type, and prep-state counts for a food frame."""
        from api.services.cnf_food_type import get_food_type
        from api.services.cnf_prep_state import prep_state_of

        cnf_count = wafct_count = fdc_count = ciqual_count = 0
        ft_single = ft_mixed = ft_unknown = 0
        thermal_counts: Dict[str, int] = {}
        preservation_counts: Dict[str, int] = {}
        both_known = 0

        for rec in pool.itertuples(index=False):
            fid = int(rec.FoodID)
            src = str(getattr(rec, 'source', 'cnf') or 'cnf')
            if src == 'wafct':
                wafct_count += 1
            elif src == 'fdc':
                fdc_count += 1
            elif src == 'ciqual':
                ciqual_count += 1
            else:
                cnf_count += 1

            ft = get_food_type(fid)
            if ft is None:
                ft_unknown += 1
            elif ft.get('food_type') == 'mixed':
                ft_mixed += 1
            else:
                ft_single += 1

            ps = prep_state_of(fid)
            if ps:
                t = ps.thermal_state or 'unknown'
                p = ps.preservation_state or 'unknown'
            else:
                t = p = 'unknown'
            thermal_counts[t] = thermal_counts.get(t, 0) + 1
            preservation_counts[p] = preservation_counts.get(p, 0) + 1
            if t != 'unknown' and p != 'unknown':
                both_known += 1

        total = len(pool)
        return {
            'total_in_group': total,
            'cnf_count': cnf_count,
            'wafct_count': wafct_count,
            'fdc_count': fdc_count,
            'ciqual_count': ciqual_count,
            'food_type': {'single': ft_single, 'mixed': ft_mixed, 'unknown': ft_unknown},
            'thermal_state': dict(sorted(thermal_counts.items(), key=lambda kv: -kv[1])),
            'preservation_state': dict(sorted(preservation_counts.items(), key=lambda kv: -kv[1])),
            'prep_both_known_pct': round(100.0 * both_known / total, 1) if total else 0.0,
        }

    def compare_foods(
        self,
        food_ids: List[int],
        nutrient_ids: List[int] = None,
        basis: str = 'per_100g',
    ) -> Dict:
        """Compare nutritional content of multiple foods.

        Args:
            food_ids: Foods to compare (2–10).
            nutrient_ids: Optional extra NutrientIDs (merged with the default panel set).
            basis: ``per_100g`` (raw CNF values) or ``per_100kcal`` (energy-adjusted density).
        """
        from api.services.cnf_food_type import get_food_type
        from api.services.cnf_prep_state import prep_state_of

        ENERGY_ID = 208
        PROTEIN_ID, FIBRE_ID = 203, 291
        basis = 'per_100kcal' if basis == 'per_100kcal' else 'per_100g'

        try:
            if len(food_ids) > 10:
                raise ValueError("Cannot compare more than 10 foods at once")

            default_nutrients = [
                208, 268, 203, 204, 205, 291, 269,
                301, 303, 304, 305, 306, 307, 309,
                319, 320, 321, 323, 324, 401, 404, 405, 406, 417, 418, 430,
                606, 645, 646, 605, 601,
            ]
            if nutrient_ids:
                target_nutrients = sorted(set(default_nutrients) | {int(n) for n in nutrient_ids})
            else:
                target_nutrients = default_nutrients

            comparison_data = {
                'foods': [],
                'nutrients': {},
                'comparison_date': datetime.now().isoformat(),
                'basis': basis,
            }

            food_name_df = self.data_loader.food_name_df
            has_source_col = 'source' in food_name_df.columns
            na = self.data_loader.nutrient_amount_df

            energy_by_food: Dict[int, float] = {}
            energy_rows = na[(na['NutrientID'] == ENERGY_ID) & (na['FoodID'].isin(food_ids))]
            for row in energy_rows.itertuples(index=False):
                energy_by_food[int(row.FoodID)] = float(row.NutrientValue)

            macro_ids = {PROTEIN_ID, FIBRE_ID, ENERGY_ID}
            macro_sub = na[na['FoodID'].isin(food_ids) & na['NutrientID'].isin(macro_ids)]
            macro_map: Dict[int, Dict[int, float]] = {}
            for row in macro_sub.itertuples(index=False):
                fid = int(row.FoodID)
                bucket = macro_map.get(fid)
                if bucket is None:
                    bucket = {}
                    macro_map[fid] = bucket
                bucket[int(row.NutrientID)] = float(row.NutrientValue)

            for food_id in food_ids:
                food_details = self.get_food_details(food_id)
                if not food_details:
                    continue
                row = food_name_df[food_name_df['FoodID'] == food_id]
                src = 'cnf'
                if not row.empty and has_source_col:
                    src = str(row['source'].iloc[0])
                fid = int(food_id)
                nuts = macro_map.get(fid, {})
                ft = get_food_type(fid)
                ps = prep_state_of(fid)
                comparison_data['foods'].append({
                    'FoodID': fid,
                    'FoodDescription': food_details['FoodDescription'],
                    'FoodCode': str(food_details.get('FoodCode', '')),
                    'FoodGroup': food_details.get('FoodGroupName', 'Unknown'),
                    'FoodGroupID': int(food_details.get('FoodGroupID') or 0),
                    'source': src,
                    'energy_kcal': nuts.get(ENERGY_ID),
                    'protein_g': nuts.get(PROTEIN_ID),
                    'fibre_g': nuts.get(FIBRE_ID),
                    'food_type': ft.get('food_type') if ft else None,
                    'thermal_state': ps.thermal_state if ps else None,
                    'preservation_state': ps.preservation_state if ps else None,
                })

            nutrient_source_df = self.data_loader.nutrient_source_df

            def display_value(raw: float, food_id: int) -> float:
                if basis != 'per_100kcal':
                    return raw
                e = energy_by_food.get(food_id) or 0.0
                if e <= 0:
                    return raw
                return raw / e * 100.0

            for nutrient_id in target_nutrients:
                nutrient_data = na[
                    (na['NutrientID'] == nutrient_id) &
                    (na['FoodID'].isin(food_ids))
                ]

                if nutrient_data.empty:
                    continue

                nutrient_name_row = self.data_loader.nutrient_name_df[
                    self.data_loader.nutrient_name_df['NutrientID'] == nutrient_id
                ]
                nutrient_name = (
                    nutrient_name_row['NutrientName'].iloc[0]
                    if not nutrient_name_row.empty else f"Nutrient {nutrient_id}"
                )
                nutrient_unit = (
                    nutrient_name_row['NutrientUnit'].iloc[0]
                    if not nutrient_name_row.empty else "unit"
                )

                comparison_data['nutrients'][nutrient_name] = {
                    'nutrient_id': int(nutrient_id),
                    'unit': nutrient_unit,
                    'values': {},
                    'by_food_id': {},
                }

                row_src = food_name_df[food_name_df['FoodID'].isin(food_ids)]
                food_database: Dict[int, str] = {}
                if not row_src.empty:
                    for rec in row_src.itertuples(index=False):
                        fid = int(rec.FoodID)
                        if has_source_col:
                            food_database[fid] = str(getattr(rec, 'source', 'cnf') or 'cnf')
                        else:
                            food_database[fid] = 'cnf'

                for _, nrow in nutrient_data.iterrows():
                    food_id = int(nrow['FoodID'])
                    food_name = next(
                        (f['FoodDescription'] for f in comparison_data['foods'] if f['FoodID'] == food_id),
                        f"Food {food_id}",
                    )
                    raw = float(nrow['NutrientValue'])
                    shown = display_value(raw, food_id)
                    comparison_data['nutrients'][nutrient_name]['values'][food_name] = shown

                    ns_id = int(nrow.get('NutrientSourceID', 0) or 0)
                    ns_row = nutrient_source_df[nutrient_source_df['NutrientSourceID'] == ns_id]
                    nutrient_source = (
                        str(ns_row['NutrientSourceDescription'].iloc[0])
                        if not ns_row.empty else 'Unknown'
                    )

                    comparison_data['nutrients'][nutrient_name]['by_food_id'][str(food_id)] = {
                        'value': shown,
                        'value_per_100g': raw,
                        'unit': str(nutrient_unit),
                        'nutrient_source_id': ns_id,
                        'nutrient_source': nutrient_source,
                        'database': food_database.get(food_id, 'cnf'),
                    }

            return comparison_data

        except Exception as e:
            logger.error(f"Error comparing foods: {str(e)}")
            raise

    # =============================================================================
    # Reference Data Operations
    # =============================================================================

    def add_food_source(self, description: str) -> Dict:
        """Add a new food source."""
        return self.data_processor.add_food_source(description)

    def add_nutrient_source(self, description: str) -> Dict:
        """Add a new nutrient source."""
        return self.data_processor.add_nutrient_source(description)

    def add_measure(self, description: str) -> Dict:
        """Add a new measure."""
        return self.data_processor.add_new_measure(description)

    # =============================================================================
    # Data Quality and Integrity
    # =============================================================================

    def check_data_integrity(self) -> Dict:
        """
        Comprehensive data integrity check.
        
        Returns:
            Dictionary with integrity check results
        """
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'checks': {},
                'overall_status': 'passed'
            }
            
            # Check for orphaned records
            food_ids = set(self.data_loader.food_name_df['FoodID'])
            nutrient_food_ids = set(self.data_loader.nutrient_amount_df['FoodID'])
            conversion_food_ids = set(self.data_loader.conversion_factor_df['FoodID'])

            orphaned_nutrients = nutrient_food_ids - food_ids
            orphaned_conversions = conversion_food_ids - food_ids
            foods_without_nutrients = food_ids - nutrient_food_ids
            foods_without_conversions = food_ids - conversion_food_ids

            results['checks']['orphaned_nutrient_records'] = {
                'count': len(orphaned_nutrients),
                'status': 'passed' if len(orphaned_nutrients) == 0 else 'warning',
                'details': list(orphaned_nutrients) if orphaned_nutrients else []
            }

            results['checks']['orphaned_conversion_records'] = {
                'count': len(orphaned_conversions),
                'status': 'passed' if len(orphaned_conversions) == 0 else 'warning',
                'details': list(orphaned_conversions) if orphaned_conversions else []
            }

            results['checks']['foods_without_nutrients'] = {
                'count': len(foods_without_nutrients),
                'status': 'passed' if len(foods_without_nutrients) == 0 else 'warning',
                'details': list(foods_without_nutrients) if foods_without_nutrients else []
            }

            results['checks']['foods_without_conversions'] = {
                'count': len(foods_without_conversions),
                'status': 'passed' if len(foods_without_conversions) == 0 else 'warning',
                'details': list(foods_without_conversions) if foods_without_conversions else []
            }

            # Check for duplicate food descriptions
            duplicate_descriptions = self.data_loader.food_name_df[
                self.data_loader.food_name_df.duplicated(subset=['FoodDescription'], keep=False)
            ]
            
            results['checks']['duplicate_food_descriptions'] = {
                'count': len(duplicate_descriptions),
                'status': 'passed' if len(duplicate_descriptions) == 0 else 'warning',
                'details': duplicate_descriptions[['FoodID', 'FoodDescription']].to_dict('records') if not duplicate_descriptions.empty else []
            }

            # Set overall status
            if any(check['status'] == 'failed' for check in results['checks'].values()):
                results['overall_status'] = 'failed'
            elif any(check['status'] == 'warning' for check in results['checks'].values()):
                results['overall_status'] = 'warning'

            return results
            
        except Exception as e:
            logger.error(f"Error checking data integrity: {str(e)}")
            raise

    def get_database_statistics(self) -> Dict:
        """Get comprehensive database statistics."""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'food_count': len(self.data_loader.food_name_df),
                'nutrient_records': len(self.data_loader.nutrient_amount_df),
                'conversion_records': len(self.data_loader.conversion_factor_df),
                'food_groups': len(self.data_loader.food_group_df),
                'food_sources': len(self.data_loader.food_source_df),
                'nutrient_types': len(self.data_loader.nutrient_name_df),
                'nutrient_sources': len(self.data_loader.nutrient_source_df),
                'measures': len(self.data_loader.measure_name_df),
                'foods_by_group': {},
                'top_nutrients': {}
            }

            food_df = self.data_loader.food_name_df
            if 'source' in food_df.columns:
                stats['cnf_food_count']   = int((food_df['source'] == 'cnf').sum())
                stats['wafct_food_count'] = int((food_df['source'] == 'wafct').sum())
                # FDC-INGEST (2026-06-25): split FDC into its three sub-sources
                # so the analytics surface can show Foundation / SR Legacy /
                # FNDDS coverage independently. `fdc_food_count` is the sum.
                stats['fdc_food_count'] = int((food_df['source'] == 'fdc').sum())
                if 'data_type' in food_df.columns:
                    fdc_mask = food_df['source'] == 'fdc'
                    stats['fdc_foundation_food_count'] = int(
                        ((food_df.loc[fdc_mask, 'data_type']) == 'foundation_food').sum()
                    )
                    stats['fdc_sr_legacy_food_count'] = int(
                        ((food_df.loc[fdc_mask, 'data_type']) == 'sr_legacy_food').sum()
                    )
                    stats['fdc_survey_fndds_food_count'] = int(
                        ((food_df.loc[fdc_mask, 'data_type']) == 'survey_fndds_food').sum()
                    )
                # CIQUAL-INGEST (2026-06-26): fourth catalogue source.
                stats['ciqual_food_count'] = int((food_df['source'] == 'ciqual').sum())
            else:
                stats['cnf_food_count']    = len(food_df)
                stats['wafct_food_count']  = 0
                stats['fdc_food_count']    = 0
                stats['ciqual_food_count'] = 0
            
            # Foods by group
            foods_by_group = self.data_loader.food_name_df.groupby('FoodGroupID').size()
            for group_id, count in foods_by_group.items():
                group_name = self.data_loader.food_group_df[
                    self.data_loader.food_group_df['FoodGroupID'] == group_id
                ]['FoodGroupName'].iloc[0] if not self.data_loader.food_group_df[
                    self.data_loader.food_group_df['FoodGroupID'] == group_id
                ].empty else f"Group {group_id}"
                stats['foods_by_group'][group_name] = int(count)
            
            # Top nutrients by frequency
            nutrient_counts = self.data_loader.nutrient_amount_df.groupby('NutrientID').size().sort_values(ascending=False)
            for nutrient_id, count in nutrient_counts.head(10).items():
                nutrient_name = self.data_loader.nutrient_name_df[
                    self.data_loader.nutrient_name_df['NutrientID'] == nutrient_id
                ]['NutrientName'].iloc[0] if not self.data_loader.nutrient_name_df[
                    self.data_loader.nutrient_name_df['NutrientID'] == nutrient_id
                ].empty else f"Nutrient {nutrient_id}"
                stats['top_nutrients'][nutrient_name] = int(count)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            raise