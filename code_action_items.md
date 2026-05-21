# Code Action Items Surfaced by Group A Literature Review

**Companion to** `literature_extractions.md`, `manuscript_call1.md`, `scenarios.md`.
**Purpose:** track every code change that the page-cited reading of ReCiPe 2016 v1.1 (Huijbregts et al., 2017; RIVM 2016-0104a, 2017), Dekker et al. (2019), Poore & Nemecek (2018) and AGRIBALYSE 3.2 (ADEME, 2024) requires us to make in `ecodish365` *before* Scenarios S1–S8 are run. Keep this file pruned: completed items move to a "Done" section at the bottom.

---

## Pending

Each item below is genuinely outstanding. Resolved audits (HEFI-CODE-1, FCS-CODE-1, HENI-CODE-1, CODE-1 through CODE-7) have moved to the **Done** section below with their implementation logs and numerical headlines.

### HSR-CODE-1 — Reference-food calibration deviations pending HSRC v5 spec verification

**Files:** [`backend/rust_core/src/hsr/threshold_data.rs`](backend/rust_core/src/hsr/threshold_data.rs), [`backend/rust_core/src/hsr/mod.rs`](backend/rust_core/src/hsr/mod.rs).

**Discovered:** 2026-05-21 smoke test against 10 canonical AU reference foods.

| # | Food | Cat | Our stars | Expected AU | Δ |
|---|---|---|---|---|---|
| 1 | Plain water | 1 | 5.0 | 5.0 | 0 |
| 2 | White table sugar | 2 | **2.0** | 0.5 | **+1.5** |
| 3 | Regular cola | 1 | **0.5** | 1.5–2.0 | **−1.0 to −1.5** |
| 4 | Plain whole milk | 1D | **2.5** | ~4.0 | **−1.5** |
| 5 | Plain rolled oats | 2 | 4.5 | 5.0 | −0.5 |
| 6 | Raw chia seeds | 2 | 4.5 | 5.0 | −0.5 |
| 7 | Plain unsweetened almond beverage | 1 | 4.0 | 4.0–5.0 | 0 |
| 8 | Bacon | 2 | 1.5 | 0.5–1.5 | 0 (at edge) |
| 9 | Plain Greek yogurt (full-fat) | 2D | 4.5 | 4.0–4.5 | 0 |
| 10 | Sliced white bread | 2 | 4.0 | 3.0–3.5 | +0.5 to +1.0 |

**Pattern.** Four of ten reference foods deviate by ≥ 1.0 stars from canonical AU label values. The pure-sugar and dairy-beverage cases (#2 and #4) are the most concerning — the algorithm under-penalises pure sugar and under-rewards plain milk.

**Resolution path.** Requires the canonical specification document — the **Guide for Industry to the Health Star Rating Calculator (HSRC), Version 5** (Health Star Rating Advisory Committee, 2016) — wishlist entry 14, still pending retrieval. Hosted at `healthstarrating.gov.au` (Australian Government Department of Health). Once retrieved:

1. Audit `threshold_data.rs` baseline-point and modifying-point tables against the Guide's per-category matrices (categories 1, 1D, 2, 2D, 3, 3D).
2. Audit `mod.rs` star-thresholds against the Guide's score-to-star cut-off tables.
3. Re-run this smoke test and verify all 10 reference foods are within ±0.5 stars.

Until the v5 Guide is in hand, HSR results in §4 / §5 of the manuscript carry a documented calibration caveat.

---

### CODE-6 — AGRIBALYSE v3.2 errata guard in the LCA matcher [DEFERRED to S7]

The LCA matcher is currently greenfield (no Python or Rust implementation yet). When the matcher is built as part of Scenario S7 (`scenarios.md`), it must refuse matches against the known-errata Ciqual codes documented by ADEME (eggs, Bleu-Blanc-Coeur, quinoa, codes 26232, 26013, 25998, 26037, 26034, 27029, 9901) and fall back to the Poore & Nemecek group default with a logged warning. Documented for traceability; no action today.

---

### Other small-but-feasible follow-ups (HENI v1 simplifications)

These were explicitly logged as v1 simplifications during HENI-CODE-1 implementation. They are tractable from existing literature but do not block any current smoke test:

- **HENI-CODE-1.x — disease-attribution weights**. Rederive the per-risk disease-share weights from the full 6 195-pair GBD 2016 RR matrix instead of the equal-share-per-outcome scheme implemented in v1 (Stylianou 2021 SI Table 1 documents the mapping but not the strata-level weights). Requires GBD 2016 RR-matrix data acquisition.
- **GBD vintage upgrade** (2016 → 2019 → 2023). Cardinaals et al. (2024) used GBD 2019; GBD 2023 (with the revised trans-fat TMREL, *Lancet* 2025;406:1880) is the most recent vintage. Requires new RR-matrix data.
- **TFA imputation regression** (Stylianou et al. 2018, R² = 0.69). Replaces the current zero-with-warning behaviour when CNF lacks measured TFA. Requires the regression coefficients from Stylianou 2018 (not in our extractions yet).
- **Energy-relative TMRELs** for PUFA (11 % energy) and trans-fat (0.5 % energy). Currently uncapped in the absolute-gram table with an advisory warning. Feasible from existing C15-SI Table 1 data — ~30 minutes of refactor work.

### Data-dependent follow-ups (blocked on literature retrieval)

- **Rana et al. 2021 free-sugars supplement** to CNF (*Nutrients* 13(5):1471). HEFI-CODE-1C added a `c9_imputation_note` disclosure; full integration awaits the supplement dataset.
- **Page-accurate monetary value updates** for CODE-4 categories. `monetary_values` figures are unchanged; only source attribution was added. Awaiting Group H PDFs (CE Delft 2024 Environmental Prices Handbook, True Price Foundation 2024, ECCC 2023 SC-GHG Technical Update).

### Out-of-scope

- **Frontend** UI rendering of the new additive API keys (`factor_confidence_by_category`, `value_sources`, `data_quality`, HENI `disease_breakdown.methodology`, per-field `metadata.units` dict, HEFI `c9_imputation_note`). Backend is complete; UI integration is a separate task.

## Done

### 2026-05-20 — CODE-1, CODE-2, CODE-3, CODE-4, CODE-5, CODE-7 implemented

**Files modified:**
- [backend/environmental_impact_model/src/life_cycle_assessment.py](backend/environmental_impact_model/src/life_cycle_assessment.py): module rewrite. Added `RECIPE_ENDPOINT_FACTOR_PROVENANCE` (page-cited Table 1.5 source for every endpoint factor), `LCA_FACTOR_CONFIDENCE` (per-category confidence rating), `NORMALIZATION_FACTORS_RECIPE2016_PUBLISHED` and `NORMALIZATION_FACTORS_PROPOSED_2024_UNSOURCED` constants. Split CH₄ midpoint key into `ch4_biogenic` (34) / `ch4_fossil` (36). Rewrote `calculate_endpoint_impacts` to add ionising radiation, photochemical ozone (HH + terrestrial), water use (HH + terrestrial + freshwater), marine eutrophication, and climate-change-to-freshwater pathways. Renamed `calculate_single_score` parameter to `normalization_set` with a backwards-compatible `use_updated_normalization` shim and a deprecation warning. Added `get_factor_confidence_by_category` accessor. Replaced the dead "RIVM October 2024" comment.
- [backend/environmental_impact_model/src/monetization.py](backend/environmental_impact_model/src/monetization.py): removed the two "consultation with Raphael" comments; added a `monetary_value_sources` dict carrying `{source, currency_year, status, last_verified}` per category; added `get_monetary_value_sources()` accessor.
- [backend/api/views/environmental_views.py](backend/api/views/environmental_views.py): the three LCA call sites (comprehensive analysis, food comparison, food profile) now attach `factor_confidence_by_category`, `data_quality`, and `value_sources` to their payloads; the `format_environmental_results` formatter surfaces these as additive keys.

**Verification (smoke test against stub meal with synthetic midpoint vector):**
- All endpoint pathways execute without exception.
- `factor_confidence_by_category` returns all 18 midpoint categories with `{level, rationale}`.
- `get_data_quality_report` returns the new keys `confidence_by_category`, `endpoint_factor_provenance`, and the expanded `known_issues` block.
- `sanity_check` includes the new `fossil_scarcity_approximation` and the rewritten `gwp_reference` line.
- `calculate_single_score`: both branches and the deprecation shim produce equal results.
- No remaining matches for `Raphael` or `consultasion` in `backend/`.

**Numerical impact for the manuscript (S2 / S5 calibration).** Against the same synthetic midpoint vector, the endpoint factor correction changes the single-score from the *old* point-estimate to **~1.52 (recipe2016_published)** vs **~1.56 (proposed_2024_unsourced)** — the two normalisation branches differ by ~3 %, while the endpoint-factor correction itself shifts climate-change-to-HH by **4.4×** (2.1×10⁻⁷ → 9.3×10⁻⁷), terrestrial-acidification-to-ecosystems by ~**1.3×10⁵**, and freshwater-eutrophication-to-ecosystems by ~**4.7×10²**. Comparison ratios with reference meals (the user-facing claim) remain unchanged because they are scale-invariant.

### 2026-05-21 — HENI-CODE-1 implemented (canonical HENI factor table + carve-outs + TMREL hard cap)

**Files modified (8):**

- [backend/rust_core/src/heni/factors.rs](backend/rust_core/src/heni/factors.rs) — replaced `HENI_FACTORS` verbatim with Stylianou et al. 2021 SI Table 3 p. 8 values in the published sign convention (negative = beneficial, positive = detrimental), added the new `legumes` / `fiber_other` / `fiber_fvlw` components for the 16-component schema, added `HENI_FACTOR_BOUNDS` (95 % CI bounds for the Monte Carlo uncertainty layer), replaced `EFFECTIVE_INTAKE_RANGES` with TMRELs from C15-SI Table 1 pp. 4–5 (omega_3 0.250 g, sodium 3.49 g, etc.), replaced `DISEASE_BURDEN_ATTRIBUTION` + `RISK_FACTOR_DISEASE_MAPPING` with a single `RISK_FACTOR_DISEASE_WEIGHTS` dict carrying equal-share-per-outcome weights derived from C15-SI Table 1, widened `is_nutrient_factor` to the 7-nutrient canonical set, and added a module-level provenance docstring block.
- [backend/rust_core/src/heni/engine.rs](backend/rust_core/src/heni/engine.rs) — flipped `MINUTES_PER_UDALY` from `+0.5256` to `−0.5256` so that user-facing `health_impact_minutes > 0` remains "good for health" under the Stylianou DRF sign; replaced the soft-cap + 0.5× linear taper with a hard cap at TMREL per the canonical methodology; rewrote `disease_breakdown` to consume the new per-risk weights; added three inline tests (`sodium_only_is_detrimental`, `stylianou_chicken_wing_worked_example`, `disease_breakdown_sums_to_total`) on top of the two updated existing ones.
- [backend/heni_calculator/heni/calculator/heni_calculator_methods.py](backend/heni_calculator/heni/calculator/heni_calculator_methods.py) — full rewrite. Added `_apply_double_counting_carve_outs` that strictly implements Stylianou 2021 SI §S2.9 pp. 35–36 (milk DRF only applies to dairy foods → suppress calcium when milk is present; fibre routes to `fiber_fvlw` when any of fruits/vegetables/legumes/whole_grains is co-present, otherwise to `fiber_other`). Added `legumes` to the food-group mapping. Added plant-milk filter (`soy milk`, `almond beverage`, etc. excluded from dairy DRF per GBD 2017 definition). Added refined SSB filter (`water`, `tea`, `coffee`, `juice` excluded). Added TFA imputation flag — when CNF has no measured TFA, emit `trans_fat = 0.0` with a `__imputation_warnings__` audit string. Audit-trail metadata propagated to API via two sentinel keys the aggregator strips before passing to Rust.
- [backend/heni_calculator/heni/calculator/heni_calculator.py](backend/heni_calculator/heni/calculator/heni_calculator.py) — taught the meal aggregator to strip the two sentinel keys (`__audit_carve_outs__`, `__imputation_warnings__`), aggregate them across ingredients, attach to the `HENIResult` for downstream API surfacing, and defensively guard the inner loop against non-numeric values.
- [backend/heni_calculator/heni/config/heni_factors.py](backend/heni_calculator/heni/config/heni_factors.py) — added `legumes`, `fiber_other`, `fiber_fvlw` to `HENI_RISK_FACTOR_KEYS`; removed obsolete `fiber`. Now 16 keys matching the canonical 16-component schema.
- [backend/heni_calculator/heni/categorization/rule_based_categorizer.py](backend/heni_calculator/heni/categorization/rule_based_categorizer.py) — added `legumes` category rules, plant-milk filter, non-SSB beverage filter, fibre-source routing (fiber_fvlw vs fiber_other based on f/v/l/w co-presence), fruit-juice exclusion from fruits DRF, poultry-as-neutral handling.
- [backend/heni_calculator/heni/categorization/llm_categorizer.py](backend/heni_calculator/heni/categorization/llm_categorizer.py) — migrated legacy `fiber` key to `fiber_other` / `fiber_fvlw` in the validator; updated all 16 factor descriptions in `_get_factor_description` to match GBD 2017 exposure definitions (Lancet 2019;393:1960) and Stylianou SI §S2.9; removed the broken `initial_categories` reference that was an undefined-name bug.
- [backend/api/views/heni_views.py](backend/api/views/heni_views.py) — rewrote the API metadata block: `units` is now a per-field dict (μDALY for `total_heni_score`, minutes for `health_impact_minutes`); added `factor_source` (page-cited Stylianou ref), `epidemiology_vintage` ("GBD 2016"), `conversion_constant` ("−0.5256 min/μDALY"), `methodology_version` ("Stylianou2021-Suppl-Table-3"), `double_counting_carve_outs_applied` list, `known_caveats` list.
- [backend/heni_calculator/tests/test_heni_daly_rust.py](backend/heni_calculator/tests/test_heni_daly_rust.py) — replaced the legacy `fiber` key with `fiber_other` in the exact-match test, added five new tests (`omega3_is_beneficial_under_stylianou_sign`, `sodium_is_detrimental_under_stylianou_sign`, `stylianou_2021_chicken_wing_worked_example`, `tmrel_hard_cap_applied`, `disease_breakdown_sums_to_total`), and flipped the existing `female_adjustment` / `disable_age_adjustment` tests to use `abs()` since under the new sign convention beneficial-only meals produce negative `total_heni_score` values.

**Verification (`cargo test --lib heni` + `python manage.py test heni_calculator`):**

- All 5 Rust unit tests pass; all 8 Python tests pass.
- Stand-alone smoke test against the **Stylianou 2021 SI §S2.2 (p. 13) chicken-wing worked example**: an 85 g serving with 1.85 g PUFA, 0.0281 g calcium, 0.492 g sodium, 0.139 g TFA produces `health_impact_minutes = −3.257 min/serving`. Published Stylianou value is `−3.3 min/serving`. **Delta = +0.043 min** (well inside the ±0.3 min tolerance attributable to factor-table rounding).
- Per-component μDALY decomposition matches the published Stylianou arithmetic to 4 sig figs: PUFA −1.110, calcium −0.143, sodium +6.839, TFA +0.612, sum +6.197 μDALY → ×(−0.5256) = −3.257 min.
- Direct `_apply_double_counting_carve_outs` regression: milk-vs-calcium suppression, fibre→fiber_fvlw (with f/v/l/w co-present), fibre→fiber_other (without), and combined carve-outs all behave as specified by C15-SI §S2.9.
- Disease-breakdown invariant: across-outcome sum equals `total_heni_score` to fp tolerance (test `disease_breakdown_sums_to_total`).
- No remaining matches for the legacy factor magnitudes (`57.0`, `25.0`) or for the positive `MINUTES_PER_UDALY = 0.5256` in the HENI module.

**Numerical impact for the manuscript (§4 / §5, S4 / S5).**

The factor-table correction is large: across the 16 components the per-gram DRFs change by 5–40× in magnitude with sign flipped for 8 of 16. Comparison ratios across meals are **not** scale-invariant under sign flips, so all HENI numbers in any earlier draft are superseded. With the new canonical table:

| Worked example | Old code | New (Stylianou-aligned) | Published Stylianou |
|---|---|---|---|
| Chicken wing, 85 g | n/a (different unit) | **−3.257 min/serving** | **−3.3 min/serving** |
| 1.0 g sodium only | +8.0 μDALY (beneficial?) | **+13.9 μDALY** → −7.31 min (detrimental) | matches |
| 0.20 g omega_3 only | +11.4 μDALY | **−16.2 μDALY** → +8.51 min (beneficial) | matches |

User-facing convention is preserved: positive `health_impact_minutes` = adds healthy life; negative = shortens it. The internal `total_heni_score` is now in Stylianou's signed μDALY (positive = net damage).

**Manuscript §7.4 status update.** The line "deviations of order 5–40× in magnitude and inconsistent sign convention have been documented and logged for resolution" can now be removed; HENI results in §4 / §5 are unblocked.

### 2026-05-21 — HEFI-CODE-1 implemented (sodium unit fix + threshold update + free-sugars provenance)

**Files modified (6):**

- [backend/rust_core/src/hefi/scoring.rs](backend/rust_core/src/hefi/scoring.rs) — removed the `× 1000.0` multiplier from the SODDEN ratio at line 130 so the value is now in mg/kcal (matching Brassard 2022a Table 2 p. 600 unit column). Updated the module docstring with a HEFI-CODE-1 audit note. Replaced the inline `perfect_diet_maxes_components` test (which used an unrealistic `sodium_mg = 1.0` to dodge the unit bug) with a realistic `sodium_mg = 1500.0` (0.75 mg/kcal at 2000 kcal). Added three new inline tests: `brassard_sodium_scoring_curve` (verifies the interpolation between 0.9 max-score and 2.0 zero-score thresholds at seven points), and `national_mean_in_brassard_published_range` (a national-mean-like input must land inside Brassard 2022b's [22.1, 62.9] 1st-99th percentile band).
- [backend/rust_core/src/hefi/thresholds.rs](backend/rust_core/src/hefi/thresholds.rs#L52) — `sodium_density_min: 1.0` → `0.9` per Brassard 2022a Table 2 p. 600. Added a provenance comment.
- [backend/hefi_calculator/hefi/config.py](backend/hefi_calculator/hefi/config.py#L30) — mirror change: `sodium_density_min: float = 0.9` with citation.
- [backend/hefi_calculator/hefi/models.py](backend/hefi_calculator/hefi/models.py) — added `c9_imputation_note: str = ""` field to `HEFIResult`.
- [backend/hefi_calculator/hefi/algorithm.py](backend/hefi_calculator/hefi/algorithm.py) — populates `c9_imputation_note` with the standard Rana 2021 imputation disclosure string (cites Brassard 2022a Discussion p. 603).
- [hefi_technical_report.md](hefi_technical_report.md) line 96 — replaced `Sodium_Density = Sodium_mg / Total_Energy_kcal × 1000` with the canonical mg/kcal formula. Added a 2026-05-21 audit-history footnote documenting the unit fix.

**Verification (`cargo test --lib hefi` + `python manage.py test hefi_calculator`):**

- All 11 Rust HEFI tests pass — including the three new published-anchor tests.
- All Python HEFI tests pass; the `c9_imputation_note` field is populated end-to-end through the `HEFIResult` payload.
- Standalone smoke test against the perfect-diet inputs with realistic sodium (1500 mg / 2000 kcal): `total_score = 80.00 / 80` exactly (was **70.00 / 80** pre-audit because C10 was structurally locked at 0).
- Brassard sodium scoring curve reproduces at seven canonical points:

  | sodium mg/kcal | C10 (post-audit) | Brassard expected | Δ |
  |---|---|---|---|
  | 0.50 | 10.000 | 10.000 | 0 |
  | 0.80 | 10.000 | 10.000 | 0 |
  | 0.90 | 10.000 | 10.000 | 0 |
  | 0.95 | 9.545 | 9.545 | 0 |
  | 1.00 | 9.091 | 9.091 | 0 |
  | 1.50 | 4.545 | 4.545 | 0 |
  | 2.00 | 0.000 | 0.000 | 0 |

- National-mean-like inputs → 49.86 / 80, inside Brassard 2022b's [22.1, 62.9] 1st-99th percentile band.
- No stale references to `× 1000` SODDEN or `sodium_density_min: 1.0` remain.

**Manuscript implication.** Every meal scored by the production pipeline previously lost 5-10 HEFI points because C10 was silently locked at 0. After this audit, HEFI numbers in §4 / §5 reflect the published Brassard 2022a scoring methodology and the canonical perfect-diet inputs reproduce 80/80 exactly.

### 2026-05-21 — FCS-CODE-1 implemented (Mozaffarian 2021 SI Table S3 rescaling)

**Files modified (2):**

- [backend/rust_core/src/fcs/engine.rs](backend/rust_core/src/fcs/engine.rs#L144-L149) — replaced the `[-70, +70]` linear stretch with `FCS = 100 - ((26.1 - raw_truncated) / 36.7) × 99` and truncation at the empirical 5th/95th percentiles (−10.7 and 26.1), citing Mozaffarian 2021 SI Table S3 footnote * (p. 11). Uses the published denominator 36.7 verbatim (not the derived 36.8) to reproduce paper worked examples exactly. Replaced the `fcs_scale_endpoints` inline test with `fcs_scale_endpoints_mozaffarian` (raw −10.7 → 1.0; raw 26.1 → 100.0; clamping below −10.7 and above 26.1). Added two new published-anchor tests: `fcs_raw_zero_below_published_mean` (raw 0 → 29.59) and `fcs_mozaffarian_midpoint_reference` (raw 7.7 → 50.37). Updated `all_zero_domains_yields_fcs_in_range` to also assert the empty-attribute case lands at 29.59.
- [backend/fcs_calculator/tests/test_fcs_rust.py](backend/fcs_calculator/tests/test_fcs_rust.py) — `test_golden_food_29_scores_stable`: expected FCS for food_id 29 (raw `original_score = -2.96`) updated from 48.41 (pre-audit, under the [-70, +70] stretch) to **21.61** (post-audit, under the Mozaffarian formula). Pre-existing assertions that `original_score = -2.96` and `nova_category = "PROCESSED_FOODS"` are unchanged.

**Verification (`cargo test --lib fcs` + `python manage.py test fcs_calculator`):**

- All 4 Rust FCS tests pass — including the three new published-anchor tests.
- All 4 Python FCS tests pass (including the updated golden test for food_id 29 = 21.61).
- Rust unit tests verify the formula reproduces Mozaffarian's anchor points exactly: raw=−10.7 → 1.00; raw=0 → 29.59; raw=7.7 → 50.37; raw=26.1 → 100.00.
- No stale references to the `[-70, +70]` endpoints remain.

**Manuscript implication.** The published Mozaffarian/Barrett cut-offs (≥70 encourage / 31-69 moderate / ≤30 minimize) are now structurally usable: under the previous compressed [-70, +70] stretch, all foods clustered near FCS = 50 and the ≥70 band was effectively unreachable. After the fix, the cut-off-based decision support cited in manuscript §3.2 is reproducible from the pipeline. Food-level rank ordering across the catalogue is preserved (the new formula is a strictly monotonic transformation of the old over the published truncation range) but absolute FCS magnitudes move significantly — bad-quality foods drop from ~50 toward ~10-20; good-quality foods rise from ~50 toward ~70-100. This is the expected method-version bump.

*All open follow-ups are consolidated in the top-of-file **Pending** section (HSR-CODE-1; CODE-6 deferred to S7; HENI v1 simplifications; data-dependent items blocked on literature retrieval; frontend out-of-scope). This Done section logs only the implementation-level summary of resolved audits.*
