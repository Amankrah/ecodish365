"""HEFI-2019 scoring.

The numerical core lives in Rust (`rust_core.hefi`, built from
`backend/rust_core/src/hefi`). This module is a thin shim: it translates
between `HEFIInputs` / `HEFIResult` dataclasses and the Rust dict API, and
preserves the original public signature so callers don't change.

If `rust_core` is missing, raise at import time with the same build hint
that HSR's provider uses, so failures are loud and consistent.
"""
from typing import Dict

from .config import HEFIConfig
from .models import HEFIInputs, HEFIComponentScores, HEFIResult

try:
    from rust_core import hefi as _rust_hefi
except ImportError as exc:  # pragma: no cover - environment error
    raise ImportError(
        "rust_core.hefi is not available. Build the Rust extension with:\n"
        "    cd backend/rust_core && maturin develop --release\n"
        f"Underlying error: {exc}"
    ) from exc


_COMPONENT_KEYS = (
    "c1_vf",
    "c2_wholegr",
    "c3_grratio",
    "c4_profoods",
    "c5_plantpro",
    "c6_beverages",
    "c7_fattyacid",
    "c8_sfat",
    "c9_freesugars",
    "c10_sodium",
)


def compute_hefi(inputs: HEFIInputs, config: HEFIConfig = HEFIConfig()) -> HEFIResult:
    # `config` is accepted for API compatibility. The Rust side uses the
    # HEFI-2019 official thresholds baked into `rust_core::hefi::thresholds`;
    # the Python `HEFIConfig` only ever carried those same defaults, so
    # behavior is unchanged.
    del config

    payload = {
        "total_foods_ra": inputs.total_foods_ra,
        "vf_ra": inputs.vf_ra,
        "whole_grains_ra": inputs.whole_grains_ra,
        "total_grains_ra": inputs.total_grains_ra,
        "protein_foods_ra": inputs.protein_foods_ra,
        "plant_protein_foods_ra": inputs.plant_protein_foods_ra,
        "total_beverages_g": inputs.total_beverages_g,
        "recommended_beverages_g": inputs.recommended_beverages_g,
        "energy_kcal": inputs.energy_kcal,
        "sfa_g": inputs.sfa_g,
        "mufa_g": inputs.mufa_g,
        "pufa_g": inputs.pufa_g,
        "free_sugars_g": inputs.free_sugars_g,
        "sodium_mg": inputs.sodium_mg,
    }

    out = _rust_hefi.compute_hefi(payload)
    scores_dict = out["component_scores"]
    component_scores = HEFIComponentScores(
        **{k: float(scores_dict[k]) for k in _COMPONENT_KEYS}
    )
    ratios: Dict[str, float] = {k: float(v) for k, v in out["ratios"].items()}
    # Standard free-sugars imputation disclosure. Surfaced through HEFIResult
    # so downstream consumers can warn that C9 uses CNF SUGARS, TOTAL as a
    # proxy until the Rana et al. 2021 free-sugars supplement is integrated.
    # See Brassard 2022a Discussion p. 603.
    c9_imputation_note = (
        "C9 free sugars uses CNF SUGARS, TOTAL as a proxy; "
        "Rana et al. 2021 free-sugars supplement integration is pending. "
        "For foods with significant intrinsic sugars (whole fruit, milk, "
        "plain yogurt) this systematically over-counts free sugars and "
        "under-scores C9. See Brassard 2022a Discussion p. 603."
    )
    return HEFIResult(
        inputs=inputs,
        ratios=ratios,
        component_scores=component_scores,
        total_score=float(out["total_score"]),
        c9_imputation_note=c9_imputation_note,
    )
