"""WAFCT mixed-dish recipes — SUBST-1 Phase 4 regional swap hints."""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

CODE_RE = re.compile(r'^(\d{2})_\d+$')

_WAFCT_XLSX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'raw_wafct', 'WAFCT_2019.xlsx',
)


@dataclass(frozen=True)
class WafctRecipeIngredient:
    code: str
    name_en: str
    weight_g: float


@dataclass(frozen=True)
class WafctRecipe:
    obs_num: str
    code: str
    name_en: str
    ingredients: Tuple[WafctRecipeIngredient, ...]


def _tokenize(text: str) -> Set[str]:
    return {t for t in re.findall(r'[a-z]{3,}', (text or '').lower()) if len(t) >= 3}


@lru_cache(maxsize=1)
def _load_recipes() -> Tuple[WafctRecipe, ...]:
    if not os.path.isfile(_WAFCT_XLSX):
        logger.warning('WAFCT workbook not found at %s', _WAFCT_XLSX)
        return tuple()

    try:
        import openpyxl
    except ImportError:
        logger.warning('openpyxl not available for WAFCT recipe load')
        return tuple()

    wb = openpyxl.load_workbook(_WAFCT_XLSX, read_only=True, data_only=True)
    ws = wb['09 Mixed dishes']
    recipes: List[WafctRecipe] = []
    current: Optional[Dict[str, Any]] = None
    ings: List[WafctRecipeIngredient] = []

    for row in ws.iter_rows(values_only=True):
        r = list(row)
        if not r:
            continue
        col0 = str(r[0]).strip() if r[0] is not None else ''
        col1 = str(r[1]).strip() if len(r) > 1 and r[1] is not None else ''

        if col0.isdigit():
            if current is not None and ings:
                recipes.append(WafctRecipe(
                    obs_num=current['obs_num'],
                    code=current['code'],
                    name_en=current['name_en'],
                    ingredients=tuple(ings),
                ))
            ings = []
            current = {
                'obs_num': col0,
                'code': col1,
                'name_en': str(r[2]).strip() if len(r) > 2 and r[2] else '',
            }
        elif CODE_RE.match(col1):
            try:
                w = float(r[4]) if len(r) > 4 and r[4] is not None else 0.0
            except (TypeError, ValueError):
                w = 0.0
            name = str(r[2]).strip() if len(r) > 2 and r[2] else col1
            ings.append(WafctRecipeIngredient(code=col1, name_en=name, weight_g=w))

    if current is not None and ings:
        recipes.append(WafctRecipe(
            obs_num=current['obs_num'],
            code=current['code'],
            name_en=current['name_en'],
            ingredients=tuple(ings),
        ))

    wb.close()
    logger.info('Loaded %d WAFCT mixed-dish recipes', len(recipes))
    return tuple(recipes)


@lru_cache(maxsize=1)
def _code_to_food_id() -> Dict[str, int]:
    from api.cnf_cache import get_dish_cnf_pipeline

    pipeline = get_dish_cnf_pipeline()
    df = pipeline.data_loader.food_name_df
    wafct = df[df['FoodCode'].astype(str).str.startswith('WAFCT_', na=False)]
    out: Dict[str, int] = {}
    for _, row in wafct.iterrows():
        code = str(row['FoodCode']).replace('WAFCT_', '')
        out[code] = int(row['FoodID'])
    return out


def find_similar_recipes(dish_name: str, *, limit: int = 5) -> List[WafctRecipe]:
    """Return WAFCT mixed dishes whose names overlap the user's dish."""
    if not dish_name or not dish_name.strip():
        return []
    query_tokens = _tokenize(dish_name)
    if not query_tokens:
        return []

    scored: List[Tuple[float, WafctRecipe]] = []
    for recipe in _load_recipes():
        rt = _tokenize(recipe.name_en)
        if not rt:
            continue
        overlap = len(query_tokens & rt)
        if overlap == 0:
            continue
        score = overlap / max(len(query_tokens), 1)
        scored.append((score, recipe))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:limit]]


def recipe_swap_candidates(
    *,
    dish_name: str,
    ingredient_description: str,
    exclude_ids: Set[int],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Suggest replacements drawn from similar WAFCT traditional recipes."""
    code_map = _code_to_food_id()
    if not code_map:
        return []

    ing_tokens = _tokenize(ingredient_description)
    candidates: Dict[int, Dict[str, Any]] = {}

    for recipe in find_similar_recipes(dish_name, limit=8):
        for ri in recipe.ingredients:
            fid = code_map.get(ri.code)
            if fid is None or fid in exclude_ids:
                continue
            rt = _tokenize(ri.name_en)
            if ing_tokens and not (ing_tokens & rt):
                continue
            if fid not in candidates:
                candidates[fid] = {
                    'food_id': fid,
                    'food_description': ri.name_en,
                    'origin': 'wafct_recipe',
                    'label': f'From regional recipe: {ri.name_en[:55]}',
                    'rationale': (
                        f'Used in “{recipe.name_en[:80]}” — a similar West African '
                        f'dish from the WAFCT recipe collection.'
                    ),
                    'recipe_name': recipe.name_en,
                }
            if len(candidates) >= limit * 2:
                break

    return list(candidates.values())[:limit]
