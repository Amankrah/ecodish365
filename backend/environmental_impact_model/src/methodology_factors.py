"""Runtime loader for LCA methodology factor packs.

Provides a single typed access point (`MethodologyFactorPack`) to:
  - Mid-to-endpoint conversion factors per cultural perspective (I/H/E)
  - World 2010 per-person normalisation scores at midpoint AND endpoint level
  - Country-specific endpoint CFs for spatially-explicit impact categories
    (water consumption, freshwater eutrophication, terrestrial acidification)

All values are loaded from JSON packs produced by
`environmental_impact_model.etl.build_recipe2016_factor_packs`. Runtime code
holds no factor numbers; everything traces back to a workbook cell with
SHA-256 checksumming through `recipe2016_factor_packs_meta.json`.

Architecture is namespaced by methodology so a future EF 3.1 / IMPACT World+
pack can plug in without further refactor:

    pack = get_methodology_pack('recipe2016')       # default
    pack.endpoint_factor('climate_change_human', 'H')
    pack.normalization('midpoint', 'H')['Global warming']
    pack.country_endpoint_cf('CAN', 'water_use_human', 'H')  # 0.0 (abundant)
    pack.country_endpoint_cf('USA', 'water_use_human', 'H')  # ~9.8e-7
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pack discovery
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))
_META_NAME = "recipe2016_factor_packs_meta.json"

_PACK_FILES_BY_METHODOLOGY: Dict[str, Dict[str, str]] = {
    "recipe2016": {
        "endpoint": "recipe2016_endpoint_factors.json",
        "normalization": "recipe2016_normalization.json",
        "country": "recipe2016_country_factors.json",
        "meta": _META_NAME,
    },
}

# Map: country-aware impact category in workbook -> list of endpoint pathway
# keys that *can* be substituted with a country-specific CF. v1 supports the
# three water-consumption pathways (volumetric -> per-country endpoint). The
# other two categories (freshwater eutrophication, terrestrial acidification)
# carry per-substance country CFs in the workbook; meaningful substitution
# requires a substance-level LCI inventory which the current pipeline does
# not have, so we expose the data but do NOT return overrides for them.
_COUNTRY_OVERRIDE_PATHWAYS: Dict[str, Dict[str, str]] = {
    # workbook category -> {endpoint_pathway_key: country block sub-key}
    "water_consumption": {
        "water_use_human":                 "endpoint_hh",
        "water_use_ecosystem_terrestrial": "endpoint_terrestrial",
        # The workbook gives a single "all perspectives" value for the aquatic
        # endpoint — applies regardless of I/H/E.
        "water_use_ecosystem_freshwater":  "endpoint_aquatic_all_perspectives",
    },
}


# ---------------------------------------------------------------------------
# Pack class
# ---------------------------------------------------------------------------

class MethodologyFactorPack:
    """In-memory bundle of all factor data for a single LCA methodology."""

    def __init__(self, methodology: str, data_dir: str = _DATA_DIR):
        self.methodology = methodology
        self._data_dir = data_dir
        files = _PACK_FILES_BY_METHODOLOGY.get(methodology)
        if files is None:
            raise ValueError(
                f"Unknown methodology {methodology!r}. Known: "
                f"{sorted(_PACK_FILES_BY_METHODOLOGY)}"
            )

        endpoint_path = os.path.join(data_dir, files["endpoint"])
        norm_path = os.path.join(data_dir, files["normalization"])
        country_path = os.path.join(data_dir, files["country"])
        meta_path = os.path.join(data_dir, files["meta"])

        self._endpoint_pack = self._load_json(endpoint_path)
        self._norm_pack = self._load_json(norm_path)
        self._country_pack = self._load_json(country_path)
        self._meta = self._load_json(meta_path)

        # Validate schema versions match expectation.
        for label, pack in (
            ("endpoint", self._endpoint_pack),
            ("normalization", self._norm_pack),
            ("country", self._country_pack),
        ):
            if pack.get("_schema_version") != "1.0":
                raise ValueError(
                    f"{methodology}/{label} pack schema_version is "
                    f"{pack.get('_schema_version')!r}, expected '1.0'. Re-run ETL."
                )
            if pack.get("_methodology") != methodology:
                raise ValueError(
                    f"{label} pack methodology is {pack.get('_methodology')!r}, "
                    f"expected {methodology!r}."
                )

        # Validate sha256 checksums against meta (best-effort: log if drift).
        self._validate_checksums(endpoint_path, norm_path, country_path)

        # Hoist commonly-accessed sub-structures for fast paths.
        self._endpoints_by_perspective: Dict[str, Dict[str, float]] = \
            self._endpoint_pack["perspectives"]
        self._midpoint_norms: Dict[str, Dict[str, float]] = \
            self._norm_pack["midpoint"]
        self._endpoint_per_pathway_norms: Dict[str, Dict[str, float]] = \
            self._norm_pack["endpoint_per_pathway"]
        self._endpoint_per_aop_norms: Dict[str, Dict[str, float]] = \
            self._norm_pack["endpoint_per_aop"]
        self._country_categories: Dict[str, Any] = \
            self._country_pack["categories"]
        self._countries_iso3: List[str] = \
            list(self._country_pack["countries_available_iso3"])

        logger.info("%s", self.version_string())

    # -- loading helpers ------------------------------------------------

    @staticmethod
    def _load_json(path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Methodology pack file missing: {path}. Run "
                f"`python -m environmental_impact_model.etl.build_recipe2016_factor_packs`."
            )
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _validate_checksums(self, endpoint_path: str, norm_path: str, country_path: str) -> None:
        """Compare each pack's on-disk SHA-256 against the value recorded in meta.

        Mismatch is a warning, not a failure, so a developer hand-editing a
        pack for an ablation doesn't break the runtime — but the divergence
        IS surfaced in `methodology_provenance()` for auditability.
        """
        self._checksum_status: Dict[str, str] = {}
        packs_meta = self._meta.get("packs", {})
        for label, path in (
            ("endpoint_factors", endpoint_path),
            ("normalization", norm_path),
            ("country_factors", country_path),
        ):
            expected = packs_meta.get(label, {}).get("sha256")
            if expected is None:
                self._checksum_status[label] = "no_recorded_sha256"
                continue
            actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
            if actual == expected:
                self._checksum_status[label] = "ok"
            else:
                self._checksum_status[label] = "drift"
                logger.warning(
                    "Methodology pack %s checksum drift: expected %s..., got %s...",
                    label, expected[:12], actual[:12],
                )

    # -- core accessors -------------------------------------------------

    def list_perspectives(self) -> List[str]:
        return sorted(self._endpoints_by_perspective.keys())

    def list_countries(self) -> List[str]:
        return list(self._countries_iso3)

    def list_country_aware_pathways(self) -> List[str]:
        """Endpoint pathway keys for which `country_endpoint_cf` may return a
        country-specific override (rather than just the world-average factor)."""
        out: List[str] = []
        for paths in _COUNTRY_OVERRIDE_PATHWAYS.values():
            out.extend(paths.keys())
        return sorted(out)

    def list_country_aware_categories(self) -> List[str]:
        """Workbook categories present in the country pack (for UI surfacing)."""
        return sorted(self._country_categories.keys())

    def supports_perspective(self, perspective: str) -> bool:
        return perspective in self._endpoints_by_perspective

    def supports_country(self, country: Optional[str]) -> bool:
        return bool(country) and country in self._countries_iso3

    def endpoint_factor(self, pathway_key: str, perspective: str = "H") -> Optional[float]:
        """World-average midpoint-to-endpoint conversion factor for the given
        pathway under the chosen cultural perspective. Returns None if absent
        (e.g. brown coal / peat in I/H, since the workbook only provides them
        under E)."""
        if perspective not in self._endpoints_by_perspective:
            raise ValueError(
                f"Unknown perspective {perspective!r}. Valid: {self.list_perspectives()}"
            )
        return self._endpoints_by_perspective[perspective].get(pathway_key)

    def endpoint_factors_dict(self, perspective: str = "H") -> Dict[str, float]:
        """Full {pathway_key: factor} mapping for the perspective (a copy, safe
        to mutate)."""
        if perspective not in self._endpoints_by_perspective:
            raise ValueError(
                f"Unknown perspective {perspective!r}. Valid: {self.list_perspectives()}"
            )
        return dict(self._endpoints_by_perspective[perspective])

    def normalization(self, level: str = "midpoint", perspective: str = "H") -> Dict[str, float]:
        """World 2010 per-person normalisation scores.

        :param level: 'midpoint' (per midpoint category, kg substance-eq/person/yr),
                      'endpoint' (per endpoint pathway, DALY|species.yr|USD/person/yr),
                      or 'aop' (per area of protection, summed across pathways).
        :param perspective: 'I', 'H', or 'E'.
        """
        if perspective not in self.list_perspectives():
            raise ValueError(
                f"Unknown perspective {perspective!r}. Valid: {self.list_perspectives()}"
            )
        if level == "midpoint":
            return dict(self._midpoint_norms[perspective])
        if level == "endpoint":
            return dict(self._endpoint_per_pathway_norms[perspective])
        if level == "aop":
            return dict(self._endpoint_per_aop_norms[perspective])
        raise ValueError(
            f"Unknown normalisation level {level!r}. Use 'midpoint'|'endpoint'|'aop'."
        )

    def country_endpoint_cf(
        self,
        country: Optional[str],
        pathway_key: str,
        perspective: str = "H",
    ) -> Optional[float]:
        """Country-specific midpoint-to-endpoint conversion factor, if available.

        Returns None when:
          - country is None / unknown
          - pathway_key is not in the v1 country-overridable set
          - the workbook has no entry for that (country, pathway, perspective)

        Callers should fall back to `endpoint_factor(pathway_key, perspective)`
        (world-average) when this returns None.
        """
        if not country or country not in self._countries_iso3:
            return None
        # Find which country category this pathway belongs to.
        category_for_pathway: Optional[str] = None
        sub_key_for_pathway: Optional[str] = None
        for category, pathway_map in _COUNTRY_OVERRIDE_PATHWAYS.items():
            if pathway_key in pathway_map:
                category_for_pathway = category
                sub_key_for_pathway = pathway_map[pathway_key]
                break
        if category_for_pathway is None or sub_key_for_pathway is None:
            return None
        country_block = (
            self._country_categories
            .get(category_for_pathway, {})
            .get("countries", {})
            .get(country)
        )
        if country_block is None:
            return None
        sub = country_block.get(sub_key_for_pathway)
        if sub is None:
            return None
        # `endpoint_aquatic_all_perspectives` is a flat scalar (no perspective
        # split); `endpoint_hh` / `endpoint_terrestrial` are per-perspective dicts.
        if isinstance(sub, dict):
            return sub.get(perspective)
        return sub

    def water_stress_index(self, country: Optional[str]) -> Optional[float]:
        """Country water-requirement ratio (0–1, AWaRe-like) from the workbook.
        Useful for narrative and methodology display; not consumed by the LCA
        math directly."""
        if not country or country not in self._countries_iso3:
            return None
        return (
            self._country_categories
            .get("water_consumption", {})
            .get("countries", {})
            .get(country, {})
            .get("water_stress_index")
        )

    def country_workbook_name(self, country: Optional[str]) -> Optional[str]:
        """Original workbook display name for an ISO-3 code (UI tooltips)."""
        if not country or country not in self._countries_iso3:
            return None
        for cat in ("water_consumption", "freshwater_eutrophication",
                    "terrestrial_acidification"):
            block = (self._country_categories.get(cat, {})
                     .get("countries", {}).get(country))
            if block:
                return block.get("_workbook_name")
        return None

    def methodology_provenance(self) -> Dict[str, Any]:
        """Provenance block for `get_data_quality_report` and API responses."""
        packs_meta = self._meta.get("packs", {})
        return {
            "methodology": self.methodology,
            "methodology_version": self._meta.get("methodology_version"),
            "schema_version": self._meta.get("schema_version"),
            "etl_git_rev": self._meta.get("etl_git_rev"),
            "extracted_at_utc": self._meta.get("extracted_at_utc"),
            "endpoint_pack_sha256": packs_meta.get("endpoint_factors", {}).get("sha256"),
            "normalization_pack_sha256": packs_meta.get("normalization", {}).get("sha256"),
            "country_pack_sha256": packs_meta.get("country_factors", {}).get("sha256"),
            "checksum_status": dict(self._checksum_status),
            "source_workbooks": [
                packs_meta.get("endpoint_factors", {}).get("source_file"),
                packs_meta.get("normalization", {}).get("source_file"),
                packs_meta.get("country_factors", {}).get("source_file"),
            ],
        }

    def version_string(self) -> str:
        """Compact one-line version string for logs and API metadata."""
        packs_meta = self._meta.get("packs", {})
        ep_sha = packs_meta.get("endpoint_factors", {}).get("sha256", "?")[:12]
        return (
            f"{self.methodology}:{self._meta.get('methodology_version','?')}:"
            f"endpoint_sha={ep_sha}:perspectives={len(self._endpoints_by_perspective)}:"
            f"countries={len(self._countries_iso3)}"
        )


# ---------------------------------------------------------------------------
# Singleton accessor (mirrors `cnf_integrator.get_cnf_integrator` pattern)
# ---------------------------------------------------------------------------

_pack_cache: Dict[str, MethodologyFactorPack] = {}
_pack_lock = threading.Lock()


def get_methodology_pack(methodology: str = "recipe2016") -> MethodologyFactorPack:
    """Return the singleton pack for the given methodology. Thread-safe lazy load."""
    if methodology in _pack_cache:
        return _pack_cache[methodology]
    with _pack_lock:
        if methodology in _pack_cache:
            return _pack_cache[methodology]
        pack = MethodologyFactorPack(methodology=methodology)
        _pack_cache[methodology] = pack
        return pack


def reset_methodology_cache() -> None:
    """Test hook: drop the cached singletons so the next `get_methodology_pack`
    re-reads the JSON files. Used by ETL re-run tests."""
    with _pack_lock:
        _pack_cache.clear()


def list_available_methodologies() -> List[str]:
    """All registered LCA methodologies, including ones using simplified packs."""
    out = set(_PACK_FILES_BY_METHODOLOGY.keys())
    for m in _SIMPLE_PACK_FILES_BY_METHODOLOGY:
        out.add(m)
    return sorted(out)


# ---------------------------------------------------------------------------
# Simplified-pack methodologies
# ---------------------------------------------------------------------------
#
# Some methodologies do not need the full ReCiPe-shaped endpoint x perspective x
# country pack triple. EF 3.1 is the canonical example: it has 16 fixed
# midpoint indicators with a single-score weighting formula, no cultural
# perspectives, no per-country CFs. For these we register a single metadata
# JSON file and expose it through ``EF31MethodologyPack``-style accessors.

_SIMPLE_PACK_FILES_BY_METHODOLOGY: Dict[str, str] = {
    "ef31": "ef31_methodology.json",
}


class EF31MethodologyPack:
    """In-memory bundle of EF 3.1 indicator metadata + (when populated) the
    JRC normalisation and weighting factors.

    Per-food midpoint values are NOT stored here: they live alongside each
    AGRIBALYSE v32 catalogue entry under ``ef31_indicators_per_100g``. This
    pack exposes only methodology-level information (indicator names, units,
    weighting factors when present, JRC source citation), so a caller can
    iterate the 16 indicators consistently across foods.

    The pack ships with normalisation_per_person_per_year and weighting_pct
    set to ``null`` until the JRC EF 3.1 workbook ETL populates them. The
    verification harness ``_smoke_ef31_pack_verify.py`` gates any candidate
    set of factors against AGRIBALYSE's stored single scores; until that
    smoke test passes the precomputed catalogue value should be used directly.
    """

    def __init__(self, methodology: str = "ef31", data_dir: str = _DATA_DIR):
        self.methodology = methodology
        self._data_dir = data_dir
        fname = _SIMPLE_PACK_FILES_BY_METHODOLOGY.get(methodology)
        if fname is None:
            raise ValueError(
                f"Unknown simple-pack methodology {methodology!r}. Known: "
                f"{sorted(_SIMPLE_PACK_FILES_BY_METHODOLOGY)}"
            )
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"EF31 methodology pack missing: {path}."
            )
        with open(path, "r", encoding="utf-8") as fh:
            self._pack: Dict[str, Any] = json.load(fh)
        if self._pack.get("_schema_version") != "1.0":
            raise ValueError(
                f"{methodology} pack schema_version is "
                f"{self._pack.get('_schema_version')!r}, expected '1.0'."
            )
        if self._pack.get("_methodology") != methodology:
            raise ValueError(
                f"{methodology} pack methodology is "
                f"{self._pack.get('_methodology')!r}, expected {methodology!r}."
            )

    def list_indicator_names_fr(self) -> List[str]:
        """Canonical French indicator names (the AGRIBALYSE catalogue keys)."""
        return list(self._pack["indicators"].keys())

    def indicator_spec(self, name_fr: str) -> Optional[Dict[str, Any]]:
        return self._pack["indicators"].get(name_fr)

    def normalisation_for(self, name_fr: str) -> Optional[float]:
        spec = self._pack["indicators"].get(name_fr) or {}
        return spec.get("normalisation_per_person_per_year")

    def weighting_pct_for(self, name_fr: str) -> Optional[float]:
        spec = self._pack["indicators"].get(name_fr) or {}
        return spec.get("weighting_pct")

    def has_full_factors(self) -> bool:
        """True iff every indicator has both normalisation and weighting populated."""
        for spec in self._pack["indicators"].values():
            if spec.get("normalisation_per_person_per_year") is None:
                return False
            if spec.get("weighting_pct") is None:
                return False
        return True

    def single_score_indicator_name(self) -> str:
        return self._pack["single_score_indicator"]["name_fr"]

    def methodology_provenance(self) -> Dict[str, Any]:
        return {
            "methodology": self.methodology,
            "methodology_version": self._pack.get("methodology_version"),
            "schema_version": self._pack.get("_schema_version"),
            "status": self._pack.get("_status"),
            "source": self._pack.get("_source"),
            "has_full_factors": self.has_full_factors(),
        }


_ef31_pack_cache: Optional[EF31MethodologyPack] = None
_ef31_pack_lock = threading.Lock()


def get_ef31_pack() -> EF31MethodologyPack:
    """Process-wide singleton accessor for the EF 3.1 methodology pack."""
    global _ef31_pack_cache
    if _ef31_pack_cache is not None:
        return _ef31_pack_cache
    with _ef31_pack_lock:
        if _ef31_pack_cache is None:
            _ef31_pack_cache = EF31MethodologyPack()
        return _ef31_pack_cache


def reset_ef31_cache() -> None:
    """Test hook."""
    global _ef31_pack_cache
    with _ef31_pack_lock:
        _ef31_pack_cache = None
