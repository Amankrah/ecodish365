# HENI Rust integration plan (HSR / FCS–style)

## Goal

Make **HENI numeric scoring canonical in `rust_core`**: Python owns CNF I/O, ingredient construction, and **risk-factor extraction** (string rules + optional LLM); Rust owns **DALY aggregation, normalization, disease attribution, and health interpretation** for a given `risk_factor_amounts` map. **No duplicate Python scoring path** after cutover; **fail fast** if `rust_core` is missing (clear `ImportError` with `maturin develop`).

## What stays in Python

| Area | Reason |
|------|--------|
| `HENICNFIntegrator` / `Ingredient` | CNF reads, kcal, nutrient dicts |
| `extract_risk_factors_from_ingredient` | CNF nutrient name strings, food group labels, description heuristics, LLM |
| `calculate_meal_heni` response shaping | API JSON layout, rounding |
| `heni_views` analysis helpers | Policy / narrative helpers (non-core math) |
| `calculate_population_impact` | Optional; uses `HENIResult` fields |

## What lives in Rust (single source of truth)

Mirroring `heni/core/daly_calculator.py` + `heni/config/heni_factors.py`:

- `HENI_FACTORS`, `EFFECTIVE_INTAKE_RANGES`, `RISK_FACTOR_DISEASE_MAPPING`, `DISEASE_BURDEN_ATTRIBUTION`, `AGE_GENDER_ADJUSTMENTS`
- Effective-amount / diminishing returns above max range
- Total μDALY, per-100 kcal / g / serving- Nutrient vs food-group contribution buckets
- Disease burden breakdown (using **raw** `amount` × factor, same as Python)
- Range warnings, health impact minutes (`× 0.5256`), category + description string

## PyO3 API

Expose `rust_core.heni`:

- `compute_heni(risk_factors, total_energy_kcal, total_weight_grams, serving_size_grams=100.0, age_group="adult_male", apply_age_adjustment=True) -> dict`

Keys align with fields needed to build `HENIResult` in Python.

## Phased delivery

| Phase | Work | Exit |
|-------|------|------|
| **A** | Golden vectors: fixed `risk_factor_amounts` + energy/weight → snapshot totals and breakdowns | Done: `heni::engine` unit tests + `heni_calculator/tests/test_heni_daly_rust.py` |
| **B** | Implement `rust_core/src/heni/*`; register submodule | Done: `rust_core.heni.compute_heni` |
| **C** | `DALYCalculator.calculate_heni_score` delegates to Rust only | Done: fail-fast `ImportError` without `rust_core` |
| **D** | Hardening: replace `meals/services.py` internal HTTP HENI call with in-process calculator | Done: `HENICalculator` + shared `_get_heni_cnf_integrator()` |

## Parity notes

- Unknown `age_group` → adjustment `1.0` (same as Python `.get(..., 1.0)`).
- Disease breakdown ignores effective-range capping (matches current Python).
- LLM outputs remain merged into `risk_factors` in Python before Rust runs.

## Reference files

| File | Role |
|------|------|
| `heni/config/heni_factors.py` | **Risk-factor names only**; numeric weights live in `rust_core/src/heni/factors.rs` |
| `heni/service.py` | Shared CNF integrator + `calculate_meal_heni_response` for API and `meals` |
| `heni/core/daly_calculator.py` | Thin FFI to `rust_core.heni.compute_heni` |
| `rust_core/src/fcs/mod.rs` | PyO3 registration pattern |
