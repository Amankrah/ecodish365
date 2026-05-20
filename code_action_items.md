# Code Action Items Surfaced by Group A Literature Review

**Companion to** `literature_extractions.md`, `manuscript_call1.md`, `scenarios.md`.
**Purpose:** track every code change that the page-cited reading of ReCiPe 2016 v1.1 (Huijbregts et al., 2017; RIVM 2016-0104a, 2017), Dekker et al. (2019), Poore & Nemecek (2018) and AGRIBALYSE 3.2 (ADEME, 2024) requires us to make in `ecodish365` *before* Scenarios S1–S8 are run. Keep this file pruned: completed items move to a "Done" section at the bottom.

---

## Pending

### CODE-1 — Distinguish biogenic vs. fossil CH₄ in GWP factors [HIGH]

**File:** [`backend/environmental_impact_model/src/life_cycle_assessment.py:39`](backend/environmental_impact_model/src/life_cycle_assessment.py#L39)

**Current code:**
```python
'ch4': 34.0,  # single value — does not distinguish biogenic vs fossil
'n2o': 298.0,
```

**Required change.** Per RIVM 2016-0104a Table 2.2 (pp. 29–34), Hierarchist GWP₁₀₀ is:
- CH₄ biogenic = 34 (correct in current code)
- CH₄ fossil = 36
- N₂O = 298 (correct)

In food systems this matters: enteric fermentation and manure decomposition are biogenic; natural-gas fugitive emissions from upstream processing are fossil. Split the key:
```python
'ch4_biogenic': 34.0,
'ch4_fossil': 36.0,
```
and update emission-source routing in the LCI integrator accordingly.

**Why it matters for the paper.** ~24 % of food GHG burden is enteric (Poore & Nemecek, 2018, p. 4, fig. 3). Misallocating it would distort the beef-vs-legume scenario in S5.

---

### CODE-2 — Verify all encoded ReCiPe CFs against RIVM Table 1.5 (p. 25) [HIGH]

**File:** [`backend/environmental_impact_model/src/life_cycle_assessment.py:64`](backend/environmental_impact_model/src/life_cycle_assessment.py#L64) (the `endpoint` dict).

**Current code (Hierarchist endpoint factors):**
```python
'climate_change_human': 2.1e-7,         # DALY/kg CO2-eq
'particulate_matter_human': 6.2e-4,     # DALY/kg PM2.5-eq
'ozone_depletion_human': 1.05e-3,       # DALY/kg CFC-11-eq
'climate_change_ecosystem': 9.8e-15,    # species.yr/kg CO2-eq
'terrestrial_acidification_ecosystem': 1.6e-12,
'freshwater_eutrophication_ecosystem': 1.3e-9,
'land_use_ecosystem': 1.8e-10,
'fossil_scarcity': 0.041,               # USD2013/kg oil-eq
'mineral_scarcity': 1.93,
'water_scarcity': 0.16,
```

**RIVM Table 1.5 (p. 25), Hierarchist column (canonical values):**
| Pathway | Unit | H |
|---|---|---|
| Climate change → HH | yr / kg CO₂ | **9.3 × 10⁻⁷** |
| Ozone depletion → HH | yr / kg CFC-11 | **5.3 × 10⁻⁴** |
| Fine PM formation → HH | yr / kg PM2.5 | **6.3 × 10⁻⁴** |
| Climate change → terrestrial ecosystems | species·yr / kg CO₂ | **2.8 × 10⁻⁹** |
| Acidification → terrestrial ecosystems | species·yr / kg SO₂ | **2.1 × 10⁻⁷** |
| Freshwater eutrophication → ecosystems | species·yr / kg P | **6.1 × 10⁻⁷** |
| Land use → ecosystems | species / m²·yr crop | **8.9 × 10⁻⁹** |
| Minerals → resources | US$₂₀₁₃ / kg Cu | **0.23** |
| Fossils (crude oil) | US$₂₀₁₃ / kg crude oil | **0.46** |
| Water consumption → HH | yr / m³ | **2.2 × 10⁻⁶** |

**Discrepancies to investigate.** Several encoded factors deviate from the published H values, e.g.:
- `climate_change_human` 2.1 × 10⁻⁷ vs. published 9.3 × 10⁻⁷ (≈ 4× low).
- `climate_change_ecosystem` 9.8 × 10⁻¹⁵ vs. published 2.8 × 10⁻⁹ (very large discrepancy — suspect unit confusion).
- `freshwater_eutrophication_ecosystem` 1.3 × 10⁻⁹ vs. published 6.1 × 10⁻⁷.
- `mineral_scarcity` 1.93 vs. published 0.23.
- `water_scarcity` 0.16 vs. published 2.2 × 10⁻⁶ for HH endpoint (the 0.16 in code is monetisation, not endpoint).

Action: open an audit ticket, walk every factor against Table 1.5 / Tables 2.2–13.x of RIVM 2016-0104a, document the source per factor in a sidecar JSON, and reconcile. This is the single biggest scientific-rigour risk in the manuscript today.

---

### CODE-3 — Remove "2024 RIVM normalisation revision" references [HIGH]

**Files affected:**
- [`backend/environmental_impact_model/src/life_cycle_assessment.py:271`](backend/environmental_impact_model/src/life_cycle_assessment.py#L271): the `use_updated_normalization=True` branch.
- Any comment referring to "RIVM October 2024 normalization".

**Why.** Confirmed via the page-cited reading of RIVM 2016-0104a: the document is dated October 2017 and contains no post-2017 normalisation table. We have no evidence that a "RIVM October 2024" artefact exists.

**Action.** Either (a) locate the actual post-2017 RIVM normalisation document and cite it, or (b) revert to the ReCiPe2016 published normalisation factors (Sleeswijk et al. 2008 / Wegener Sleeswijk et al. 2008 — same family) and label them as such. Until (a) is resolved, default behaviour should be the documented ReCiPe2016 normalisation, with the branch path renamed `use_recipe2016_published_normalization`.

---

### CODE-4 — Replace personal-communication monetary values [HIGH]

**File:** [`backend/environmental_impact_model/src/monetization.py:23-26`](backend/environmental_impact_model/src/monetization.py#L23-L26)

**Current code:**
```python
# Corrected monetary values based in consultasion with Raphael LCA expert.
'Global warming': 221.0,  # CAD per tonne CO2-eq CORRECTED based on True Price Foundation data
```

**Action.** Replace every "consultation with Raphael LCA expert" reference with a citable equivalent:
- ECCC SC-GHG 2023 update (Ref. 24 in `manuscript_call1.md`) for `Global warming`.
- CE Delft Environmental Prices Handbook 2024 update (wishlist H48) for non-GHG categories.
- True Price Foundation 2024 methodology (wishlist H49) for items already drawn from True Price.

Every value must carry an inline source identifier and a `last_verified` ISO date.

---

### CODE-5 — Tag low-confidence toxicity outputs in pipeline output [MEDIUM]

ReCiPe 2016 v1.1 explicitly flags toxicity factors as low-reliability (Huijbregts et al., 2017, §4; RIVM 2017, §1.3, p. 20). AGRIBALYSE concurs ("encore peu robustes", ADEME 2024). The current code already maintains a `factor_confidence` dict at [`life_cycle_assessment.py:23-28`](backend/environmental_impact_model/src/life_cycle_assessment.py#L23-L28) — propagate this to the JSON API response so the frontend can render a confidence chip per midpoint category.

---

### CODE-6 — Handle AGRIBALYSE v3.2 errata explicitly in the LCA matcher [MEDIUM]

When the S7 LLM matcher selects a CNF→Agribalyse mapping, refuse matches against the known-errata codes documented by ADEME (eggs, Bleu-Blanc-Coeur, quinoa, Ciqual codes 26232, 26013, 25998, 26037, 26034, 27029, 9901) and fall back to the Poore & Nemecek group default with a logged warning. Documented in `manuscript_call1.md` §7.2.

---

### CODE-7 — Strip biogenic-CH₄ from fossil resource scarcity reporting [LOW]

ReCiPe fossil resource scarcity has no constant midpoint-to-endpoint factor; the endpoint is resolved per resource (RIVM 2017, p. 25, Table 1.5, footnote 3; Ch. 14, p. 103). Make sure the code does not silently apply a constant for this category.

---

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

### Still pending

- **CODE-6** — AGRIBALYSE matcher errata guard. Deferred to S7 implementation (greenfield; no existing matcher code to wrap today).
- **Page-accurate monetary value updates.** `monetary_values` numerical figures are unchanged; only source attribution was added. Replace once literature group H PDFs (CE Delft 2024, True Price 2024, ECCC 2023 SC-GHG) are retrieved.
- **Frontend.** The new API keys (`factor_confidence_by_category`, `value_sources`, `data_quality`) are additive; UI integration to render a confidence chip per impact category is a separate task.
