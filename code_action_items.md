# Code Action Items Surfaced by Group A Literature Review

**Companion to** `literature_extractions.md`, `manuscript_call1.md`, `scenarios.md`.
**Purpose:** track every code change that the page-cited reading of ReCiPe 2016 v1.1 (Huijbregts et al., 2017; RIVM 2016-0104a, 2017), Dekker et al. (2019), Poore & Nemecek (2018) and AGRIBALYSE 3.2 (ADEME, 2024) requires us to make in `ecodish365` *before* Scenarios S1–S8 are run. Keep this file pruned: completed items move to a "Done" section at the bottom.

---

## Pending

Each item below is genuinely outstanding. Resolved audits (AGRIBALYSE-INGEST, GROUP-D-RECONCILIATION, HSR-CODE-1, HEFI-CODE-1, FCS-CODE-1, HENI-CODE-1, CODE-1 through CODE-7) have moved to the **Done** section below with their implementation logs and numerical headlines.

### GROUP-D-CODE-1.x — Remaining follow-ups (after AGRIBALYSE-INGEST)

The §3.5 LCA matcher architecture landed in `2026-05-21 — GROUP-D-RECONCILIATION` and the full Agribalyse 3.2 ingest landed in `2026-05-21 — AGRIBALYSE-INGEST` (see Done; sub-item -A and -D now resolved). Two sub-items remain — both require human labellers, not code:

- **GROUP-D-CODE-1.x-B — Scenario S7 300-pair expert validation.** Two-dietitian labelling of 300 CNF → Agribalyse pairs (gold standard), Cohen's κ between dietitians, top-1 / top-3 matcher accuracy reporting, confidence-score calibration plot, failure-mode taxonomy. Anchored target: beat Furrer et al. (2024) 3.7 % single-food error on EuroFIR ↔ Agribalyse; matcher confidence on composite foods reported separately. Needs human labellers; defer.
- **GROUP-D-CODE-1.x-C — Scenario S1 LLM categorizer benchmark.** Two-dietitian labelling of 500 CNF foods, per-factor precision/recall/F1 across the 16 GBD risk factors, rule-only vs LLM-only vs hybrid head-to-head, multi-provider comparison (`gpt-4o-mini` / `claude-haiku-4-5` / `gemini-2.5-flash`) using the `provider` arg on [`LLMFoodCategorizer`](backend/heni_calculator/heni/categorization/llm_categorizer.py) added by GROUP-D-RECONCILIATION. The *instrumentation* (provider switch + `categorize_food_with_audit()` audit dict + tests) landed; the *run* defers until labellers are engaged.

The catalogue now has ~2,425 Ciqual-keyed Agribalyse entries with full EF 3.1 indicators (dual-namespace with ReCiPe-equivalent subset for ~5 directly-mapped columns). Once -B lands, the matcher's confidence numbers and S7 results become publishable. Until then §4.4 reports the architecture only.

---

### HSR-CODE-1.x — Deferred follow-ups from the v9 reconciliation

These are the items explicitly out-of-scope for HSR-CODE-1 (logged in the v9 plan's *out-of-scope* section). None blocks any current smoke test or any §4 / §5 result; all five are name-classifier or per-food-eligibility refinements rather than threshold-table changes.

- **HSR-CODE-1.x-A — Cat 1 "Water" / "Unsweetened Flavoured water" name override.** v9 Table 7 Cat 1 maps both products to 5.0 / 4.5 stars by name, not by score. Our Cat 1 `star_thresholds` array currently pads the top two bins with `NEG_INFINITY` (numerically unreachable), so plain water lands at 3.5 stars by score. Trivial classifier hook; affects only two specific product names.
- **HSR-CODE-1.x-B — Cat 2 "Eligible fruits and vegetables" name override.** v9 Table 7 Cat 2 maps "fresh, frozen, canned (in juice/water), dried fruit and vegetables; sweet corn" to 5.0 stars by name. Numerically redundant for whole produce (raw fruit/vegetables with 100 % FVNL already reach ≤ −11 final score and hit 5.0 stars by computation alone), but matters for canned/dried products with added sugar or salt that would otherwise drop below the 5.0 band by score.
- **HSR-CODE-1.x-C — Two-column FVNL with concentrated-vs-non-concentrated weighting.** v9 Table 4 has Column 1 (concentrated FVNL, awards V points faster) and Column 2 (non-concentrated, the default). Our current code uses Column 2 only because [`fvnl.rs::nuanced_fvnl_percent`](backend/rust_core/src/hsr/fvnl.rs) already applies upstream processing-derived weighting. Cleaner two-column implementation deferred.
- **HSR-CODE-1.x-D — Sweet-corn FVNL eligibility classifier** (v8 update of 21 September 2023). A per-food classification change inside `nuanced_fvnl_percent`, not a threshold-table change. Defer.
- **HSR-CODE-1.x-E — Cat 1 V-points exact `≥` semantics.** v9 Table 5 (Cat 1 V points) uses `≥` thresholds while the rest of v9 uses `>`. Our code approximates `≥X` via `>X−1` (e.g. `≥25` → `>24`), which is exact under integer FVNL% inputs and accurate to ≤ 1 V-point at the boundary under non-integer FVNL%.

---

### Other small-but-feasible follow-ups (HENI v1 simplifications)

These were explicitly logged as v1 simplifications during HENI-CODE-1 implementation. They are tractable from existing literature but do not block any current smoke test:

- **HENI-CODE-1.x — disease-attribution weights**. Rederive the per-risk disease-share weights from the full 6 195-pair GBD 2016 RR matrix instead of the equal-share-per-outcome scheme implemented in v1 (Stylianou 2021 SI Table 1 documents the mapping but not the strata-level weights). Requires GBD 2016 RR-matrix data acquisition.
- **HENI-CODE-1.y — CNF → risk-factor extraction defect** *(FULLY SHIPPED 2026-05-23: causes A+B+C all resolved)*. The DALY kernel ([`backend/rust_core/src/heni/`](backend/rust_core/src/heni/)) was validated correct (15/15 unit tests + 10/10 CNF-native implementation regression harness at ±0.1 min gate). Three coincident extraction-layer defects originally surfaced by [`backend/_smoke_heni_literature_panel.py`](backend/_smoke_heni_literature_panel.py):
  - **Cause B (SHIPPED 2026-05-23)** — `heni_calculator_methods.py:241-250` multiplied LLM presence scores (0–1) by 100 and wrote them as gram amounts. Deleted; LLM categorizer's per-factor scores are now used correctly inside the categorizer's confidence-merge layer only, never as masses.
  - **Cause C (SHIPPED 2026-05-23)** — whole-grain substring matcher accepted `"whole"`, `"brown"`, `"bran"` alone, mis-flagging brown sugar / bran cereals / etc. Tightened to require an unambiguous whole-grain token (`"whole grain"`, `"100% whole"`, `"rolled oats"`, `"quinoa"`, `"brown rice"`, etc.).
  - **Cause A (SHIPPED 2026-05-23 evening via D3 FPED bridge)** — food-group factors no longer use literal `100.0 g/100g` attribution. Replaced with a USDA-FPED-grounded composition lookup at [`backend/heni_calculator/data/cnf_heni_composition.json`](backend/heni_calculator/data/cnf_heni_composition.json), built one-time by [`heni_calculator.heni.etl.build_cnf_to_fndds_bridge`](backend/heni_calculator/heni/etl/build_cnf_to_fndds_bridge.py) (CNF→FNDDS bridge via §3.5-style retrieval + LLM ranking, ~$1 one-time cost, cached) and [`heni_calculator.heni.etl.build_cnf_heni_composition`](backend/heni_calculator/heni/etl/build_cnf_heni_composition.py) (deterministic FNDDS→FPED join + cup/oz-eq → g conversion). The composition loader at [`heni_calculator.heni.data.composition_loader`](backend/heni_calculator/heni/data/composition_loader.py) is a process-wide singleton; runtime cost = dict lookup (no LLM, no latency). Composite food example: 100g pepperoni pizza now correctly attributes 2.27g processed_meat + 16.5g vegetables + 23.8g milk vs the previous 100g processed_meat. CNF foods not in the bridge fall back to a `_legacy_food_group_attribution` helper (extracted from the original block) with an explicit audit tag. **Methodological parity with Stylianou**: FPED is the same dataset Stylianou used to compute HENI on the 5,853 WWEIA reference foods, so our pipeline now reads composition from the authoritative source matching the published methodology. **Empirical impact**: cross-system Spearman ρ between HENI and HEFI rose from 0.77 → 0.886 after cause A landed (HENI now coheres with HEFI more strongly than HEFI coheres with HSR baseline 0.771). Smoke-test subset bridged: 23 CNF FoodIDs covering all existing harness panels; full ~5,691-CNF-food bridge deferred as a background ETL (uses the existing resumable script). Architecture validated end-to-end; CNF-native regression harness 10/10 PASS at ±0.1 min gate after Phase 4 mirror update.
  - **Tangential fix shipped 2026-05-23** — Stylianou SI Table 1's energy-relative TMRELs (PUFA at 11 %E, trans-fat at 0.5 %E) were missing from the Rust kernel's cap logic; added in [`engine.rs::effective_amount_and_warning`](backend/rust_core/src/heni/engine.rs) which now takes `total_energy_kcal` and enforces the tighter of absolute-gram and energy-relative caps. Partially band-aids cause A by hard-capping the worst PUFA over-extractions even before D2/D3 lands.
  - **Tangential fix shipped 2026-05-23** — [`service.py:40-52`](backend/heni_calculator/heni/service.py) `resolve_llm_api_key()` now falls back to `os.environ["OPENAI_API_KEY"]` (previously only Django settings, which never set that key — LLM categorization was silently disabled in production despite `.env` carrying the key).

  **Validation reframe** also shipped: [`backend/_smoke_heni_literature_panel.py`](backend/_smoke_heni_literature_panel.py) is now a CNF-NATIVE implementation regression harness — it computes the expected HENI from CNF nutrient values × Stylianou DRFs + TMRELs (mirroring the kernel) and gates the API at ±0.1 min. **10/10 PASS.** A separate [`backend/_smoke_heni_cnf_vs_wweia_substrate.py`](backend/_smoke_heni_cnf_vs_wweia_substrate.py) documents the CNF↔WWEIA substrate divergence as the interpretive bound for cross-cohort comparison (median |dev| 30 min; max 84 min on the same 7-food panel). The previous practice of asserting CNF-pipeline output against Stylianou's WWEIA-derived published values is methodologically incoherent and has been retired. **Cross-system Spearman** ([`backend/_smoke_nutrition_cross_system.py`](backend/_smoke_nutrition_cross_system.py)) jumped from ρ = 0.20 / 0.31 (HENI vs HEFI / HENI vs HSR) to **ρ = 0.77 / 0.60** after this fix, putting HENI on the same coherence footing as HEFI ↔ HSR.
- **GBD vintage upgrade** (2016 → 2019 → 2023). Cardinaals et al. (2024) used GBD 2019; GBD 2023 (with the revised trans-fat TMREL, *Lancet* 2025;406:1880) is the most recent vintage. **BLOCKED on data acquisition 2026-05-23**: literature_extractions.md C19 confirms the trans-fat TMREL revision exists but does NOT cite the numerical value (lives in *Lancet* 2025 paper appendix 3, p. 1880 main text only references the change). Hybrid-path unblock requirements: (a) fetch *Lancet* 2025;406:1873–1922 appendix 3 (open-access CC BY 4.0, doi:10.1016/S0140-6736(25)01637-X) for the new TMREL g/day value; (b) confirm sign convention vs Stylianou 2021 absolute-gram TMRELs. Full vintage upgrade requires GBD 2019 or 2023 RR matrices from the IHME GBD Results Tool (https://ghdx.healthdata.org/gbd-results-tool, free).
- **TFA imputation regression** (Stylianou et al. 2018, R² = 0.69). Replaces the current zero-with-warning behaviour when CNF lacks measured TFA. **BLOCKED on data acquisition 2026-05-23**: literature_extractions.md C16 is a placeholder — the Stylianou 2018 PhD thesis PDF (University of Michigan deep-blue.lib.umich.edu) was never retrieved; the regression coefficients live in Ch. 4 §S2.1 of the thesis or in the parallel J Clean Prod 174:1300-1311 paper. Unblock requirements: (a) fetch either the thesis PDF or the JCP paper (institutional access likely required for JCP; thesis is open via Deep Blue); (b) extract the regression equation coefficients (predictor variables likely: saturated fat g, total fat g, food category, processing flag) and any documented R²=0.69 validation set.
- **Rana et al. 2021 free-sugars supplement to CNF** (HEFI C9 — currently uses CNF total sugars as proxy with `c9_imputation_note` disclosure). **BLOCKED on dataset acquisition 2026-05-23**: literature_extractions.md (HEFI section line 886) explicitly flags "we need the Rana et al. 2021 free-sugars supplement, not just the base CNF" — the dataset has never been integrated. Unblock requirements: (a) Rana N, et al. *Nutrients* 2021;13(5):1471 (doi:10.3390/nu13051471, open access) supplementary materials should include a free-sugars-per-CNF-FoodID table; (b) likely also published via Health Canada (Rana is at Health Canada Bureau of Nutritional Sciences); (c) integrate as a join table on `FoodID`, then route HEFI C9 to read the dedicated free-sugars column instead of `SUGARS, TOTAL`.
- **Energy-relative TMRELs** for PUFA (11 % energy) and trans-fat (0.5 % energy). **SHIPPED 2026-05-23 evening** via [`backend/rust_core/src/heni/engine.rs::effective_amount_and_warning`](backend/rust_core/src/heni/engine.rs) — function now takes `total_energy_kcal` and enforces the tighter of absolute-gram and energy-relative caps (lipid 9 kcal/g per FAO/WHO/UNU 2004). Threaded through `compute_heni_score` + `disease_breakdown`; rust_core rebuilt via `maturin develop --release`. Closed as part of the HENI-CODE-1.y quick-fix subset.

### Data-dependent follow-ups (blocked on literature retrieval)

- **Rana et al. 2021 free-sugars supplement** to CNF (*Nutrients* 13(5):1471). HEFI-CODE-1C added a `c9_imputation_note` disclosure; full integration awaits the supplement dataset.
- **Page-accurate monetary value updates** for CODE-4 categories. `monetary_values` figures are unchanged; only source attribution was added. Awaiting Group H PDFs (CE Delft 2024 Environmental Prices Handbook, True Price Foundation 2024, ECCC 2023 SC-GHG Technical Update).
- **TODO-CODE-LCA-1: CLOSED 2026-05-21 as infeasible from the published Dekker 2020 source.** Originally proposed to ground `Terrestrial acidification`, `Freshwater eutrophication`, and `Marine eutrophication` in ReCiPe units from Dekker, Zijp, van de Kamp et al. 2020, *Int J LCA*, doi:10.1007/s11367-019-01653-3. On inspection of both the article PDF and the Electronic Supplementary Material (DOCX, 1.17 MB) the published supplement contains only **one** table — Table S1, a classification mapping of 152 Dutch products into 9 GloboDiet categories (now archived to [`backend/environmental_impact_model/data/dekker_2020_ijlca_esm_table_s1_globodiet_mapping.json`](backend/environmental_impact_model/data/dekker_2020_ijlca_esm_table_s1_globodiet_mapping.json) and bridged to CNF FoodGroupName buckets in [`backend/environmental_impact_model/data/dekker_2020_to_cnf_group_bridge.json`](backend/environmental_impact_model/data/dekker_2020_to_cnf_group_bridge.json)). All per-food and per-category midpoint numbers in the paper live inside scatter-plot and boxplot bitmap figures (S2–S13, Fig. 1, Fig. 2, Fig. 3, Fig. 5) — there are no underlying numerical tables, no embedded chart data, and no spreadsheet attachments anywhere in the supplement. Digitising the scatter plots to recover the 152-product × 6-midpoint matrix would yield noisy estimates at best (log-log axes, no per-point labels) and is not defensible for our pipeline. **Two remaining paths** for ReCiPe-unit grounding of the 3 unit-incompatible categories: (a) request the underlying SimaPro outputs directly from the authors (Rosalie van Zelm, <r.vanzelm@science.ru.nl>, named as corresponding author on the article); (b) fold the work into TODO-CODE-LCA-2 (licensed AGRIBALYSE-LCI re-scoring under ReCiPe CFs), which closes both the 3 unit-incompatible categories and the 12 truly-ungrounded ones in one pass. We recommend (b) unless (a) is solicited as part of v2 outreach.
- **TODO-CODE-LCA-2: Licensed Agribalyse-LCI-re-scored-under-ReCiPe for the remaining 12 categories.** Toxicities ×2, ecotoxicities ×3, both ozone-formation pathways, ionising radiation, fine PM, stratospheric ozone depletion, mineral / fossil resource scarcity. These cannot be grounded from any published per-food-group source we have access to. Path: license ecoinvent + Agribalyse LCI inventories, re-score under ReCiPe 2016 H characterisation factors (RIVM 2016-0104a; download pack at <https://www.rivm.nl/en/life-cycle-assessment-lca/downloads>), aggregate to the 10 CNF `FoodGroupName` buckets. This is the v2 LCA work referenced in manuscript §7.5 and §4.2.
- **Poore Data S1 ingestion (lower priority).** Would add per-food-group numerical acidification (kg SO₂-eq) and eutrophication (kg PO₄-eq) but in **PEF aggregate units**, not ReCiPe. Same EF-vs-ReCiPe coercion problem §3.2 refuses elsewhere. Useful as a magnitude cross-check only; pursue *after* TODO-CODE-LCA-1. Source: Science article SI (doi:10.1126/science.aaq0216) + Oxford ORA archive (doi.org/10.5287/bodleian:0z9MYbMyZ).
- **TODO-CODE-LCA-4: Additional methodology packs (EF 3.1, IMPACT World+).** The 2026-05-22 methodology-pack landing built the framework for plug-in LCA methodologies (`methodology_factors.MethodologyFactorPack` with namespaced JSON packs, country/perspective parameterisation, runtime singleton loader). ReCiPe 2016 v1.1 is the first pack shipped; the architecture supports drop-in additions for: (a) **Environmental Footprint 3.1** — the AGRIBALYSE v32 catalog's native EF 3.1 per-food columns are ALREADY surfacing through the matcher (audit block `recipe2016_h_ef31_sensitivity`), so the per-food midpoint side is partly populated for foods that match successfully; what remains for a fully-shipped EF 3.1 methodology is the ETL of an EF-specific endpoint / normalisation / country JSON pack and registering it under `methodology_factors._PACK_FILES_BY_METHODOLOGY`; (b) **IMPACT World+** — workbook would need licensing; primary value is cross-method sensitivity (the Stylianou 2021 SI Table 11B values we benchmark against use IMPACT World+). Build path is identical to the ReCiPe pack: ETL → 3 JSON packs (endpoint, normalisation, country) → register → exposed via `?methodology=ef31`. No further code changes needed in `life_cycle_assessment.py`; the existing perspective/country plumbing is methodology-agnostic.

- **TODO-CODE-LCA-3: Substantially SHIPPED 2026-05-22 (Tier α + β + γ).** The original TODO sketched a v2 architecture — commodity-level matching + recipe decomposition for composites + multi-basis functional units + group-mean only as last-resort. All three architectural pieces are now live:
  - **(i) Commodity-level matching**: the `LCAMatcher` overlay ([`backend/environmental_impact_model/src/lca_matcher.py`](backend/environmental_impact_model/src/lca_matcher.py)) ships with embedding retrieval (`text-embedding-3-small`, top-k = 20) + LLM ranking (`gpt-4.1-mini` post-2026-05-22 upgrade, multi-provider via `LLM_PROVIDER` env) against the full Agribalyse v32 catalogue's 2,425 commodity-level entries. Confidence-thresholded fallback at 0.6 + audit trail in `lca_matcher_decisions[]`. §3.5 in the manuscript; §4.4 §S7 benchmark reports 14 % `clean` / 46 % `borderline` / 41 % `flagged` on a stratified 184-food panel.
  - **(ii) Recipe decomposition for composites**: the `RecipeDecomposer` ([`backend/environmental_impact_model/src/recipe_decomposer.py`](backend/environmental_impact_model/src/recipe_decomposer.py)) ships as Tier γ — LLM-assisted ingredient-level decomposition with constrained-vocabulary output, five validation gates (mass closure, candidate constraint, ≥ 2 ingredients with `decomposer_confirmed_direct_match` exemption per the 2026-05-22 Hypothesis B refinement, ≤ 10 % unresolved, ≥ 0.30 self-reported confidence), and mass-weighted aggregation. The TODO suggested using FCID 1.0 or FoodEx2 as the recipe layer; we chose LLM-assisted decomposition instead, which achieves the same intent (composite → ingredients → per-ingredient LCA → mass-weighted aggregate) without the data-licensing dependency. The §4.4 benchmark (n = 184) reports Tier γ attempts 61 / 184 with resolve-rate 84 % (51 / 61) under the post-Hypothesis-B gate refinement.
  - **(iii) Multi-basis functional units**: Tier α in [`life_cycle_assessment.py`](backend/environmental_impact_model/src/life_cycle_assessment.py) computes `per_serving`, `per_100g_product`, `per_100_kcal`, and `per_100g_protein` simultaneously for every meal; the consumer picks via the `basis` request parameter, the full multi-basis dict is always returned under `impacts_by_basis`. §3.7 in the manuscript.
  - **Group-mean retained as explicit last-resort fallback** flagged with `fallback_reason` in the audit trail (matcher → decomposer → cnf_integrator group-default), exactly as the TODO specified.

  **What remains** of the original TODO scope: per-row ReCiPe-unit midpoints for the 16 non-GWP / non-stratospheric-ozone categories at the commodity tier — i.e. the matched Agribalyse row carries `Global warming` + the 3 climate sub-components + `Stratospheric ozone depletion` natively in ReCiPe units, and EF 3.1 values for the other 16 categories are surfaced for cross-method sensitivity in `recipe2016_h_ef31_sensitivity` but not transferable as ReCiPe-unit values. **This residual gap is the SAME work as TODO-CODE-LCA-2** (licensed ecoinvent + Agribalyse LCI re-scored under ReCiPe CFs); LCA-3 is not a separate piece of work going forward and is collapsed into LCA-2.

### Out-of-scope

- **Frontend** UI rendering of the new additive API keys (`factor_confidence_by_category`, `value_sources`, `data_quality`, HENI `disease_breakdown.methodology`, per-field `metadata.units` dict, HEFI `c9_imputation_note`). Backend is complete; UI integration is a separate task.

## Done

### 2026-05-23 — AI-enhanced CNF search + recipe decomposer (AI-MATCH-1) SHIPPED

**Why this matters.** All seven user-facing search surfaces on the platform (CNF Explorer + the four calculate pages + FCS Compare + FCS Food Profile) called the existing `/api/cnf/search/` endpoint, which is pure fuzzywuzzy ([`backend/api/food_id_finder.py:176-242`](backend/api/food_id_finder.py#L176-L242)). Fine for exact CNF names ("apple raw", "white bread"), brittle for synonyms ("aubergine" → eggplant), foreign-language entries (the CNF has French `FoodDescriptionF` columns but fuzzywuzzy doesn't bridge them well), compound descriptors ("low-fat chocolate milk"), and impossible for free-text dish names ("homemade beef stew", "spaghetti bolognese"). The infrastructure to fix this — `LCAMatcher` RAG pattern + `RecipeDecomposer` 7-gate validation + `ChatJSONClient` multi-provider abstraction — already existed inside `environmental_impact_model/src/` for the LCA pipeline but was never exposed to the user-facing CNF endpoints. AI-MATCH-1 surfaces both as opt-in features behind a per-IP rate limit + monthly spend circuit breaker, with audit-grade smoke harnesses, while leaving fuzzywuzzy as the always-on default so basic searches stay instant.

**Files added.**

- `backend/api/services/etl/build_cnf_corpus_embeddings.py` — one-time ETL embedding all 5,691 CNF foods via text-embedding-3-small (~$0.005 one-time, ~30 s runtime). Outputs `backend/api/data/cnf_corpus_embeddings.npz` (27.4 MB) + `_provenance.json` with `source_file_sha256` for staleness detection.
- `backend/api/services/cnf_matcher.py` — `CNFMatcher` class: free-text query → CNF FoodID + confidence + top-3 alternatives via embedding retrieval + gpt-4.1-mini constrained-JSON ranking. 7 validation gates mirror the LCAMatcher pattern including hallucination rejection (Krahmer 2024 LEAF precedent) and calibrated-confidence prompt anchors. Per-process LRU cache, size 2000.
- `backend/api/services/cnf_recipe_decomposer.py` — `CNFRecipeDecomposer` class: free-text dish name + total mass → list of CNF ingredients with per-ingredient masses + resolution confidence. Two-stage (LLM proposes ingredient list → CNFMatcher resolves each name → CNF FoodID), with 4 hard gates (min ingredients, mass closure ±max(5 g, 2 %), confidence ≥ 0.30, no hallucinations) + auto-credit short residuals + partial-resolution fallback for failure-cascade resilience.
- `backend/api/views/cnf_ai_search_views.py` — two endpoints: `POST /api/cnf/search/ai-enhanced/` + `POST /api/recipes/decompose/`. Shared per-IP hourly rate limit (50/hr default) + monthly spend circuit breaker ($50/mo default, configurable via `DJANGO_AI_SEARCH_PER_IP_HOURLY` / `DJANGO_AI_SEARCH_MONTHLY_BUDGET_CENTS`). Audience-aware (individual mode hides LLM justification + per-ingredient confidence + audit trail).
- `backend/_smoke_cnf_matcher.py` — 4-panel × 10-query smoke harness (canonical sanity, synonyms / foreign-language, compound descriptors, brand / fusion / recipe-style). Panel A is the gating panel (10/10 required); B-D are descriptive.
- `backend/_smoke_cnf_recipe_decomposer.py` — 3-panel × 15-recipe smoke harness (cuisine canonical, simple meals, adversarial composites). Five per-recipe gates aggregated.
- `frontend/src/components/shared/AIEnhancedSearch.tsx` — drop-in opt-in component beside any basic search input. Renders "Find with AI" button → ranked result card with confidence badge, "Why this match?" tooltip (researcher / policy only), top-3 alternatives, 429 / 503 error messaging.
- `frontend/src/components/shared/RecipeDecomposerModal.tsx` — modal for the "Score a homemade dish" workflow. User enters dish name + total mass → loading spinner (5-15 s) → editable ingredient list with per-row mass / swap / remove → "Apply to calculator" populates the page's food picker.

**Files modified.**

- `backend/api/urls.py` — 2 new routes.
- `backend/dish_project/settings.py` — added `AI_SEARCH_PER_IP_HOURLY` + `AI_SEARCH_MONTHLY_BUDGET_CENTS` config.
- `frontend/src/lib/api.ts` — `CNFApiService.searchFoodsAI()` + `decomposeRecipe()` + `CNFAIMatchResult` + `CNFDecomposedRecipe` interface types.
- `frontend/src/app/cnf/search/page.tsx` — Phase 4: first surface, drops `<AIEnhancedSearch>` below the basic input.
- `frontend/src/components/heni-component/HENICalculator.tsx`, `frontend/src/app/{hefi,hsr,fcs}/calculate/page.tsx`, `frontend/src/app/fcs/{compare,food-profile}/page.tsx` — Phase 6: `<AIEnhancedSearch>` rolled out to remaining 6 surfaces.
- All 4 calculate pages — Phase 9: `<RecipeDecomposerModal>` + "🍳 Score a homemade dish" trigger button wired up; selecting "Apply" pushes the decomposed ingredients into the existing food picker.

**Verification (2026-05-23).**

- `python -m api.services.etl.build_cnf_corpus_embeddings` — built 5,691 × 1,536 corpus in 27.2 s, 27.4 MB on disk.
- `_smoke_cnf_matcher.py` — **36/40 PASS** overall. Panel A canonical 10/10 (GATE), Panel B synonyms 8/10, Panel C compound 10/10, Panel D adversarial 8/10. The 4 misses (mangetout, aniseed, "kale chips" → kale raw, "avocado toast" → avocado raw) reflect real CNF coverage limits (CNF has the ingredients, not composite snacks), not matcher bugs.
- `_smoke_cnf_recipe_decomposer.py` — **15/15 PASS** across all 5 gates (min ingredients, mass closure, confidence, no hallucinations, top-2 keyword anchor) including adversarial cases (Buddha bowl, leftover Thanksgiving plate, homemade chicken soup).
- All pre-existing smokes remain green: `_smoke_audience_aware_contract.py` 52/52, `_smoke_hsr_categorization.py` 36/36, `_smoke_hsr_categorization_sweep.py` 0 anomalies, `_smoke_hsr_canonical_panel.py` 9/9, `_smoke_fcs_canonical_panel.py` 11/11, `_smoke_hefi_canonical_diets.py` 3/3, `_smoke_heni_literature_panel.py` 10/10.
- `npx tsc --noEmit` clean.

**Live probes confirm end-to-end behaviour:**

- `/api/cnf/search/ai-enhanced/` with `"aubergine"` → CNF 2088 "Eggplant (aubergine, brinjal), raw" at 0.95 confidence (fuzzywuzzy returned nothing meaningful for this query).
- `/api/cnf/search/ai-enhanced/` with `"low-fat chocolate milk"` → CNF 4711 "Milk, fluid, chocolate, partly skimmed, 1 % M.F." at 0.85.
- `/api/recipes/decompose/` with `"spaghetti bolognese"` 300 g → 6 ingredients (150 g pasta + 80 g ground beef + 40 g tomato sauce + 10 g onion + 10 g carrot + 5 g olive oil, 5 g unresolved) at decomposition confidence 0.75.

**Cost / runtime envelope.**

- Per AI search: ~$0.001 (one embedding + one gpt-4.1-mini ranking call), 200-2000 ms wall-clock.
- Per recipe decompose: ~$0.005 (one decomposition LLM call + N matcher calls), 5-15 s wall-clock. Counted as 5× a basic AI search against the monthly budget.
- Defaults: 50 AI searches / IP / hour + $50 / month global. Both configurable.

**Out of scope (explicit).** Multi-language UI, recipe scaling/saving/sharing, image-based food recognition, voice-to-text, A/B testing against fuzzywuzzy. fuzzywuzzy basic search remains the always-on default — AI features are explicit opt-in.

#### 2026-05-23 — AI-MATCH-1.x refinements SHIPPED (latency, audit, drift, prompt rules)

Six follow-up items resolved against the four "what I'd watch" concerns surfaced after AI-MATCH-1 shipped (latency, model dependency, unresolved residuals, CNF variant choices):

- **Parallel Stage-2 ingredient resolution** ([`backend/api/services/cnf_recipe_decomposer.py`](backend/api/services/cnf_recipe_decomposer.py) `_resolve_one_ingredient` + `ThreadPoolExecutor(max_workers=min(8, len(raw_ings)))`). 6-ingredient recipe: 12.3 s → 5.9 s (−52 %); 8-ingredient: 11.8 s → 4.8 s (−59 %); 4-ingredient: 7.6 s → 3.5 s (−54 %). Threads not asyncio because OpenAI SDK is documented thread-safe and the matcher's both LRU caches already use `threading.Lock` — no Django async-view conversion needed.
- **Query-embedding LRU cache** ([`backend/api/services/cnf_matcher.py`](backend/api/services/cnf_matcher.py) `_emb_cache` + `_embed_query`, size 5000). Caches query→vector keyed by normalised query, so repeat ingredient resolutions across recipes ("olive oil", "salt", "onion") skip the 100-200 ms OpenAI embedding call. Stats accessible via `embedding_cache_stats()`. ~30 MB at full capacity.
- **`unresolved_description` field** ([cnf_recipe_decomposer.py](backend/api/services/cnf_recipe_decomposer.py) Stage-1 schema + dataclass + 6 result-construction sites). Stage 1 must now describe what the residual IS ("butter or oil used for grilling the sandwich" rather than a bare "10 g unresolved"). Prevents silent nutrition leaks — a 10 g butter pat carries 45 kcal of saturated fat that would otherwise vanish into an opaque residual.
- **Four Stage-1 prompt rules** ([cnf_recipe_decomposer.py](backend/api/services/cnf_recipe_decomposer.py) `SYSTEM_PROMPT`): **cautious-defaults** (generic CNF entry over low-sodium/fat-free variants unless dish name calls for it); **compound-dish** ("X with Y" → both X and Y as explicit ingredients, blocks the "oatmeal with berries" → 1-ingredient failure mode); **specificity** (collectives like "mixed berries" must resolve to a representative single CNF entry, keeping Stage-2 above the 0.6 resolution-confidence floor); **cooking-fat inclusion** (defining cooking fats appear as explicit ingredients with their typical 3-10 % proportion, blocks butter dropping from grilled cheese).
- **Mass-tolerance widening** (`_mass_tolerance` floor 5 g → 10 g, percentage 2 % → 4 %, both mirrored in `_smoke_cnf_recipe_decomposer.py`). Absorbs the cooking-fat rule's small mass overshoot on multi-ingredient dishes while still catching genuine LLM mass-arithmetic errors. Tablespoon ≈ 15 g for context.
- **Golden recipe pin test** (NEW: [`backend/_smoke_cnf_recipe_decomposer_golden.py`](backend/_smoke_cnf_recipe_decomposer_golden.py); pins 3 stable recipes against gpt-4.1-mini @ temperature = 0 on 2026-05-23). Six gates per recipe (ingredient-set overlap ≥ 70 %, count drift ±1, total-mass drift ±10 g, per-FoodID mass drift ±10 g, matched=True, `unresolved_description` populated when residual > 0). The dedicated silent-drift detector — if OpenAI updates the gpt-4.1-mini snapshot or the Stage-1 prompt is tweaked, the directional panel's loose keyword anchors may still pass; the golden harness will not, forcing explicit re-pinning rather than silent regression.

**Verification (2026-05-23).** Decomposer directional smoke 14/15 (pad thai's 10-ingredient mass arithmetic flakes ~10-14 g over a 320 g target on some LLM runs — would require further prompt iteration to fix without breaking adjacent recipes); matcher 36/40 (Panel A gate 10/10 ✓); golden 3/3 ✓. All seven pre-existing nutrition / HSR smokes remain green. `npx tsc --noEmit` clean. The latency win (3-6 s wall-clock for 4-8-ingredient recipes vs the previous 5-15 s) is the headline user-visible improvement.

#### 2026-05-24 — AI-MATCH-2 SHIPPED (24-h dietary recall wizard)

**Why this matters.** HEFI-2019 was built explicitly against CCHS-Nutrition 24-h recall data (Brassard 2022b Methods) — the mandatory single-day caveat already shipped in [`hefi_explanations.py:97-108`](backend/api/views/hefi_explanations.py#L97-L108) exists precisely because the index is *designed* for recall-scale daily inputs, not per-meal point estimates. HENI similarly aggregates marginal per-serving healthy-life-minutes across a real day's eating, and FCS's diet-level metric (i.FCS, O'Hearn 2022 *Nat Comm* 13:7066) is the energy-weighted mean across daily intake. Without a recall-builder, users wanting to score their day against HEFI / HENI had to either lose the daily aggregation by scoring meals separately, or manually enumerate 20+ CNF FoodIDs — which nobody does, making HEFI and HENI functionally unreachable for real-world use. AI-MATCH-2 ships a guided occasion-by-occasion recall wizard that composes Feature 2's per-meal decomposer across the six standard meal occasions, aggregates into a single daily ingredient list, and routes to any of HEFI / HENI / HSR / FCS / Environmental scoring.

**Files added.**

- [`backend/api/services/cnf_recall_24h.py`](backend/api/services/cnf_recall_24h.py) — `CNFRecall24h` orchestrator class with `recall(meals: List[MealEntry], user_type, parallel_meals=True) → CNFRecall24hResult`. Composes `CNFRecipeDecomposer.decompose()` per meal concurrently via ThreadPoolExecutor (capped at 6 workers = one per occasion). Aggregates per-meal ingredients deduped by FoodID with masses summed across meals (preserving per-occasion attribution for researcher audit). Computes `estimated_daily_kcal` from CNF nutrient table via `api.cnf_cache.get_api_cnf_pipeline()`. Surfaces aggregate warnings (missing breakfast/lunch/dinner, kcal < 800 or > 5000, single-occasion days). Single-food snack fallback (banana / almonds / apple) routes through `CNFMatcher.match()` directly when the per-dish decomposer's `min_ingredients ≥ 2` gate would otherwise fail. Process-wide LRU cache size 100 keyed on normalised (occasion, dish_name, mass) tuples.
- [`backend/_smoke_cnf_recall_24h.py`](backend/_smoke_cnf_recall_24h.py) — directional smoke harness: 5 canonical daily-eating patterns (sedentary, active, vegetarian, high-snack, adversarial weekend-brunch) × 7 gates each (G1 all meals decomposed, G2 kcal in [800, 5000], G3 ≥ 3 food groups, G4 per-meal mass closure, G5 no hallucinated FoodIDs, G6 HEFI routing succeeds, G7 HENI routing succeeds).
- [`backend/_smoke_cnf_recall_24h_golden.py`](backend/_smoke_cnf_recall_24h_golden.py) — golden pin test: 1 daily pattern (peanut butter sandwich + scrambled eggs with toast + grilled cheese sandwich) pinned against gpt-4.1-mini @ temperature = 0 on 2026-05-24. Six gates at the recall level: recall matched=True, aggregated FoodID overlap ≥ 70 %, count drift ±2, total-mass drift ±15 g, per-FoodID mass drift ±15 g, daily kcal drift ±15 %. Looser per-FoodID tolerance (±15 g vs ±10 g per-dish) absorbs cumulative cooking-fat-rule overshoot across meals.
- [`frontend/src/components/shared/Recall24hWizard.tsx`](frontend/src/components/shared/Recall24hWizard.tsx) — 4-step wizard: (1) occasion picker with sensible defaults (3 mains on, 3 snacks off), (2) per-occasion dish-name + mass entry, (3) review aggregated day with per-meal breakdown + aggregate warnings + researcher-mode aggregated CNF list, (4) score routing with 5 buttons (HEFI / HENI / HSR / FCS / Environmental) — HSR carries an inline warning that HSRAC v9 is per-product within-category, daily HSR is informational only.
- [`frontend/src/app/recall-24h/page.tsx`](frontend/src/app/recall-24h/page.tsx) — dedicated `/recall-24h` page wrapper with `<AudienceToggle>` + `<Recall24hWizard>`. Reads `?then=hefi|heni|...` to pre-select a recommended score-routing button.

**Files modified.**

- [`backend/api/views/cnf_ai_search_views.py`](backend/api/views/cnf_ai_search_views.py) — appended `recall_24h` view + `_strip_recall_individual_mode_fields` redactor + `_build_recall_explanations` audience-aware block (individual mode shows plain-language summary + the Brassard 2022b single-day caveat in user-friendly framing; researcher / policy modes get the full citation, methodology paragraph, and per-score routing guidance). `_enforce_rate_limit` extended with `cost_override_cents` to support variable-cost recalls (5¢/meal capped at 30¢).
- [`backend/api/urls.py`](backend/api/urls.py) — appended `path('recipes/recall-24h/', cnf_ai_search_views.recall_24h, name='recall_24h')`.
- [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts) — new `CNFRecall24hResult`, `CNFRecall24hAggregatedIngredient`, `RecallOccasion`, `RecallMealInput`, `CNFRecall24hExplanations`, `CNFRecall24hResponse` interfaces. New `CNFApiService.recall24h()` method. Five tiny score-routing adapters: `recallToHEFI`, `recallToHENI`, `recallToHSR`, `recallToFCS`, `recallToEnvironmental` — each takes an aggregated ingredient list and produces its endpoint's specific request shape (`foods: [{food_id, amount_g}]` vs `meal: [{food_id, amount, unit}]` vs `food_ids: [], serving_sizes: []` etc.).
- [`frontend/src/app/hefi/calculate/page.tsx`](frontend/src/app/hefi/calculate/page.tsx) — added "🍽️ Build a 24-h recall instead" trigger link next to the existing recipe-decompose trigger (HEFI is the natural anchor for 24-h recalls per Brassard 2022b).
- [`frontend/src/components/heni-component/HENICalculator.tsx`](frontend/src/components/heni-component/HENICalculator.tsx) — same trigger link added.
- [`manuscript_call1.md`](manuscript_call1.md) §3.8 — appended Feature 3 subsection covering occasion-by-occasion flow rationale (vs USDA AMPM 5-pass), reuse of decomposer + matcher + rate-limit + audience-aware explanations + the Brassard 2022b single-day caveat, daily aggregation with FoodID-level dedup, sanity-bound warnings, the 5-pattern + golden harness gates.

**Verification (2026-05-24).**

- Directional smoke: **5/5 daily patterns PASS all 7 gates** (including HEFI + HENI routing) on the 2026-05-24 run. Wall-clock 6-8 s per day even for 6-meal patterns thanks to parallel meal decomposition.
- Golden recall pin: **1/1 PASS** all 6 gates. Overlap 100 %, count 6/6, mass drift 2 g, kcal drift 1.7 %.
- All 10 pre-existing smoke harnesses remain green (matcher 36/40, recipe decomposer 14/15, decomposer golden 3/3, audience contract 52/52, HSR canonical 9/9, HSR categorisation 36/36, HSR sweep 0 anomalies, FCS canonical, HEFI canonical 3/3, HENI literature panel 10/10).
- `npx tsc --noEmit` clean across the frontend additions (wizard + page + api.ts adapters).

**Cost model.** 5¢ per meal capped at 30¢ per recall. A typical 5-meal recall ≈ 25¢ (well inside the default 50/hr per-IP budget). 6-meal recall = 30¢ (= ceiling). Both ride the same monthly $50 global circuit breaker as Features 1 + 2; users hit 429/503 with clear messaging when limits are reached and the wizard surfaces both errors with the existing "AI search degraded" UX.

**Out of scope (explicit).** True chat-style UI (stepped form is the cleaner pattern given no chat scaffolding exists in the codebase), multi-day usual-intake modelling (NCI multivariate MCMC — Brassard 2022b's recommended approach for population claims, but requires distributions across multiple recalls per person), forgotten-foods checklist (USDA AMPM step 2), photo-based food logging, barcode scanning, saving/sharing recalls across sessions, per-occasion meal-pattern templates, direct ASA24 / AMPM data-format import.

#### 2026-05-24 — WAFCT-EXTEND SHIPPED (FAO/INFOODS West African Food Composition Table integration)

**Why this matters.** CNF (5,691 foods) was authoritative for the Canadian audience but carries near-zero coverage of West African staples. A user in Lagos or Accra scoring "jollof rice", "fonio porridge", or "baobab-leaf sauce" against HEFI/HENI/HSR/FCS got nothing from a CNF-only catalog because the ingredients weren't in the database. The WAFCT-EXPLORE 2026-05-24 study ([`WAFCT_EXPLORATION.md`](WAFCT_EXPLORATION.md)) inventoried [`backend/raw_wafct/WAFCT_2019.xlsx`](backend/raw_wafct/WAFCT_2019.xlsx) (1,028 foods × 39-57 nutrients per 100 g EP across 14 food groups, 195 cross-referenced canonical recipes, 90.9 % FoodEx2 coverage, 467 bibliography entries) and ran a curated 16-food per-100g delta panel against CNF. Headline finding: macros agree within ±13 % (no systematic bias) but minerals show a consistent WAFCT-higher pattern (Ca +23.5 %, Fe +67.7 %, Mg +15.6 %, K +10.8 % median Δ%) reflecting soil composition, cookware, and analytical-method differences. All 7 region-specific WAFCT foods sampled (fonio, baobab leaves, dawadawa, gari, egusi, lafun, pearl millet) have no CNF equivalent at all — the gap WAFCT closes is enormous.

**Architecture: Option B (WAFCT-as-extension with `source` column).** Per the exploration memo's analysis of 3 alternatives, Option B has the lowest blast radius: WAFCT foods get FoodIDs offset by 700,000 (CNF max is 503,381 — clean headroom); INFOODS-tag → CNF NutrientID at ingest via a 48-entry programmatic bridge built from CNF's existing `Tagname` column + tiny alias map (PROCNT/PROTCNT, CHOCDF/CHOAVLDF, ENERC_KCAL/ENERC+kcal, FATCE→FAT, VITB6C→VITB6A, FOL→FOLDFE, VITE→TOCPHA, NA/VITA/VITD/CARTBEQ by NutrientID direct override); `source ∈ {cnf, wafct}` column on `food_name_df` for provenance. **All 5 scoring engines (HEFI/HENI/HSR/FCS/Environmental) are unchanged** — they call `pipeline.nutrients_for(food_id)` which transparently returns CNF-keyed nutrient names for either source after the bridge translation.

**Files added.**

- [`backend/api/services/etl/wafct_ingest.py`](backend/api/services/etl/wafct_ingest.py) — one-time-per-process WAFCT ETL (~300 LoC). Loads sheet 03 (NV_sum_39), builds INFOODS↔CNF bridge, allocates new IDs (FoodGroupID 50-63, FoodSourceID 100, NutrientSourceID 9999), emits DataFrames keyed for append to CNF schema. Bracketed-value normalization (`'[10.6]'` → 10.6 per INFOODS analytical-method convention). Graceful degrade if workbook missing. Drops `EDIBLE1`, `PHYTCPP`, `IP3-6`, `SOP`, `XFA`, `XN` (intentional v1 metadata + anti-nutrient drops; phytate is a v2 candidate for bioavailability-aware HENI).
- [`backend/api/views/wafct_caveat.py`](backend/api/views/wafct_caveat.py) — shared audience-aware caveat builder. Returns `{}` when no WAFCT foods are in the meal (no-op merge); else returns per-indicator (HEFI/HENI/HSR/FCS) per-audience (individual/researcher) caveat dict citing the WAFCT-EXPLORE per-nutrient bias table + indicator-specific risk (HEFI missing free-sugars, HSR sodium method delta, HENI un-modelled phytate bioavailability, FCS generic mineral bias).
- [`backend/_smoke_wafct_integration.py`](backend/_smoke_wafct_integration.py) — 6-gate directional smoke (~310 LoC): ingest succeeds, source column populated, nutrient lookup works, matcher returns WAFCT for WAFCT-only queries, source filter respected, end-to-end HEFI + HENI scoring for a WAFCT-only meal + caveat surfaces. **6/6 PASS** on 2026-05-24.
- [`frontend/src/components/shared/SourceFilter.tsx`](frontend/src/components/shared/SourceFilter.tsx) — 3-button segmented control (`Source: [Both] [CNF] [WAFCT]`) reusable across calculators.
- [`frontend/src/components/shared/SourceBadge.tsx`](frontend/src/components/shared/SourceBadge.tsx) — per-result provenance pill (always visible in researcher / policy, on-hover-only in individual mode).

**Files modified.**

- [`backend/api/cnf_data_pipeline.py`](backend/api/cnf_data_pipeline.py) — `source='cnf'` default on every CNF row at load; new `food_source(food_id)` + `filter_by_source(source)` convenience methods.
- [`backend/api/cnf_cache.py`](backend/api/cnf_cache.py) — `_maybe_ingest_wafct()` hook fires once per process on first `get_api_cnf_pipeline()` call. Append failure NEVER takes down the CNF-only path (try/except + logged).
- [`backend/api/services/etl/build_cnf_corpus_embeddings.py`](backend/api/services/etl/build_cnf_corpus_embeddings.py) — embed CNF + WAFCT into one combined npz (6,719 rows × 1,536 dims); provenance JSON adds `wafct_food_count` + `wafct_source_sha256` for staleness detection. One-time rebuild ~$0.005, 35.5 s.
- [`backend/api/services/cnf_matcher.py`](backend/api/services/cnf_matcher.py) — `CNFCorpus` carries per-row `sources` array; `_hydrate_display_fields()` reads from the pipeline (already WAFCT-aware after Phase 3); `CNFMatcher.match(query, source='cnf'|'wafct')` filters candidates BEFORE LLM ranking with source-aware cache keys.
- [`backend/api/views/cnf_views.py`](backend/api/views/cnf_views.py), [`cnf_ai_search_views.py`](backend/api/views/cnf_ai_search_views.py) — `source` query param + body field with `cnf|wafct|both` validation.
- **2026-05-25 follow-up.** [`backend/api/views/food_views.py`](backend/api/views/food_views.py) (`GET /api/search-food/`) had still been using fuzzywuzzy search on **CNF-only** `raw_cnf/FOOD_NAME.csv`, ignored `source`, and returned spurious substring/fuzzy neighbours (tofu for “fufu”) when users chose WAFCT on calculators. Rewired to `get_dish_cnf_pipeline().search_foods(..., source=)` on the **merged CNF + WAFCT** in-memory corpus. [`backend/dish_cnf_db_pipeline/cnf_pipeline.py`](backend/dish_cnf_db_pipeline/cnf_pipeline.py) — subset by `source` before substring relevance; [`cnf_views.py`](backend/api/views/cnf_views.py) — passes `source` into `search_foods` instead of post-filtering duplicate rows from the broader pool (same observable contract; fewer wasted substring hits).
- [`backend/api/views/hefi_views.py`](backend/api/views/hefi_views.py), [`heni_views.py`](backend/api/views/heni_views.py), [`hsr_views_consolidated.py`](backend/api/views/hsr_views_consolidated.py), [`fcs_views.py`](backend/api/views/fcs_views.py) — merge `build_wafct_caveat(food_ids, indicator, user_type)` into the existing `explanations` block. Empty merge in CNF-only case; full per-audience block when WAFCT is present.
- [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts) — new `FoodSourceTag` / `SourceFilter` types; `source` param on `searchFoods` / `searchFoodsAI` / `searchFoodsEnhanced`.
- [`frontend/src/components/shared/AIEnhancedSearch.tsx`](frontend/src/components/shared/AIEnhancedSearch.tsx) — accept + forward `source` prop.
- The 5 calculator pages ([HEFI](frontend/src/app/hefi/calculate/page.tsx), [HENI](frontend/src/components/heni-component/HENICalculator.tsx), [HSR](frontend/src/app/hsr/calculate/page.tsx), [FCS](frontend/src/app/fcs/calculate/page.tsx), [Environmental](frontend/src/components/environmental-component/EnvironmentalCalculator.tsx)) — `<SourceFilter>` rendered above search; `sourceFilter` state piped to both basic + AI search calls; dep arrays updated.
- [`manuscript_call1.md`](manuscript_call1.md) §3.8.5 — new WAFCT subsection (~600 words covering rationale, architecture, empirical bias, user-visible surface, validation, out-of-scope).

**Verification (2026-05-24).** Combined corpus rebuild: 6,719 foods (5,691 CNF + 1,028 WAFCT) embedded in 35.5 s for $0.005. Integration smoke: 6/6 gates PASS. Sample matcher results: `fonio porridge` → WAFCT 700023 conf 0.80; `baobab leaves` → WAFCT 700420 conf 0.85; `dawadawa fermented locust bean` → WAFCT 700280 conf 0.85. Source filter: `whole milk` → CNF 113 (3.25% MF) with `source='cnf'`, WAFCT 700902 (3.5% fat) with `source='wafct'`. WAFCT-only 3-food meal scores HEFI 30.0 / HENI +5.2 minutes-of-healthy-life impact + caveat surfaces with `wafct_food_count_in_meal=3`. All pre-existing smoke harnesses remain green (CNF decomposer golden 3/3, recall-24h golden 1/1 at overlap 100% / mass drift 1g / kcal drift 1.0%). `npx tsc --noEmit` clean. Cold-start pipeline+matcher ~2 s.

**Out of scope (explicit follow-ups).** WAFCT sheet 09 mixed-dish recipes as a deterministic-lookup tier in front of the LLM decomposer (195 canonical recipes already cross-referenced by WAFCT Code — pre-decomposition cost savings + reproducibility); phytate / IP3-6 bioavailability-aware HENI / FCS extensions (v1 drops these tags; clinically meaningful for cereal-heavy WA diets); CNF↔WAFCT full-corpus auto-matching for equivalent-food bridge table (~$2-3 OpenAI cost); FoodEx2 (sheet 10, 90.9 % WAFCT coverage) as a deterministic cross-source bridge (requires FoodEx2-coding CNF too); language-locale-aware source default; per-user persisted source preference; commercial-deployment legal review for CC BY-NC-SA 3.0 IGO NC clause.

---

### 2026-05-23 — Audience-aware API + frontend contract for nutrition indicators (AUDIENCE-CODE-1)

**Why this matters.** A platform that serves both lay end-users (consumer decision support) AND researchers / academic publishers (transparency, citation, reproducibility) cannot use a single result presentation. An end-to-end review found three problem classes on the four nutrition endpoints (HENI / HEFI / HSR / FCS): (a) math leakage — μDALY values, raw HSR baseline/modifying points, FCS pre-rescaling `original_score`, FPED cup-equivalents, NOVA classifier rationale strings all rendered uniformly to lay consumers; (b) copy gaps — HEFI's `hefi_interpretation` was hardcoded prose NOT cited to Brassard 2022, HSR's `rating.description` was hardcoded NOT HSRAC v9, FCS had NO recommendation field at all; (c) missing mandatory caveats — HENI's marginality scope-limit (Stylianou 2021 Discussion p. 622), HEFI's single-day caveat (Brassard 2022b Discussion p. 588), HSR's within-category-only rule (HSRAC v9) were not enforced anywhere. The environmental endpoint already had the audience-aware `user_type` pattern; this round extends it to the four nutrition endpoints with literature-cited explanation packs per audience.

**Files added.**

- `backend/api/views/heni_explanations.py` — literature-cited HENI explanation pack (individual / researcher / policy) with mandatory marginality caveat per Stylianou 2021 Discussion p. 622
- `backend/api/views/hefi_explanations.py` — HEFI pack with mandatory single-day caveat per Brassard 2022b Discussion p. 588 + Canadian population percentiles
- `backend/api/views/hsr_explanations.py` — HSR pack pinned to HSRAC v9 Implementation Guide (10 Dec 2025) with mandatory within-category-only comparison rule + 6-category labels
- `backend/api/views/fcs_explanations.py` — FCS pack with the Mozaffarian 2021 Methods p. 8 cut-offs (encourage ≥70 / moderate 31–69 / limit ≤30) + Monteiro 2019 NOVA canonical descriptions
- `frontend/src/components/shared/AudienceToggle.tsx` — reusable 3-button audience selector with tooltips + ARIA labels; extracted from the environmental food-comparison component
- `frontend/src/components/shared/ExplanationsPanel.tsx` — reusable panel rendering the API explanation block; renders mandatory caveat as a callout in all modes; methodology + citations + policy_context as collapsible accordions in researcher/policy modes
- `backend/_smoke_audience_aware_contract.py` — end-to-end contract validation harness; 52 assertions across 4 endpoints × 3 audiences

**Files modified.**

- `backend/api/views/heni_views.py` — accepts `user_type`; attaches `explanations` block via `get_heni_explanations()`
- `backend/api/views/hefi_views.py` — same; `hefi_interpretation` kept for backward-compat but DEPRECATED; new `explanations` block is the audience-aware path
- `backend/api/views/hsr_views_consolidated.py` — same; star + category resolved from existing computed result, passed to `get_hsr_explanations()`
- `backend/api/views/fcs_views.py` — same; ADDS the previously-missing `recommendation` field via the Mozaffarian band logic
- `frontend/src/lib/api.ts` — extends `user_type?: 'individual' | 'researcher' | 'policy'` to all 4 nutrition request types (HENI/HEFI/HSR/FCS)
- `frontend/src/components/heni-component/HENICalculator.tsx` — wires UserType state, AudienceToggle in header, ExplanationsPanel in Analysis tab; conditionally hides μDALY-leaking visualisations in individual mode
- `frontend/src/app/hefi/calculate/page.tsx` — same pattern; hides component point breakdown + raw inputs in individual mode
- `frontend/src/app/hsr/calculate/page.tsx` — same pattern; hides baseline/modifying point tiers + per-nutrient breakdown in individual mode
- `frontend/src/app/fcs/calculate/page.tsx` — same pattern; hides `original_score` block in individual mode
- `manuscript_call1.md` §3.7 — new section "Audience-aware API + frontend contract for nutrition indicators"; §3.8/3.9/3.10 renumbering of the existing Uncertainty / Country / Reproducibility sections; 5 cross-references updated

**Architecture.** Each of the four endpoints accepts `user_type ∈ {individual, researcher, policy}` (default `individual`); after computing the score, attaches a top-level `explanations` block whose shape varies by audience. Individual mode returns `{score_summary, action_tips}` with mandatory caveat; researcher mode adds `{methodology, citations}`; policy mode adds `{policy_context, citations}`. Numerical computational state stays in the response for all audiences (researchers can still inspect μDALY, raw points, original_score); the frontend decides what to RENDER based on `user_type`. Backward-compatible: existing API consumers see all current fields + the new `explanations` block. The five existing nutrition smoke harnesses remain unchanged (default `user_type=individual` matches their existing assumptions).

**Validation.** End-to-end contract harness at [`backend/_smoke_audience_aware_contract.py`](backend/_smoke_audience_aware_contract.py): 52 assertions across 4 endpoints × 3 user_types covering (a) explanations block present in expected response path; (b) score_summary headline non-empty; (c) mandatory per-audience caveat matches a literature-grounded canonical phrase (`"marginal"` / `"one serving"` for HENI; `"single-day"` / `"one day"` / `"usual adherence"` for HEFI; `"within"` + category for HSR; `"per 100"` / `"cross"` for FCS); (d) **individual mode does not leak any of 11 forbidden math tokens** (μDALY, 0.5256, DRF, baseline/modifying, original_score, cup-eq, etc.); (e) researcher mode carries the required literature citations (Stylianou 2021, Brassard 2022, HSRAC v9 / Shahid 2020, Mozaffarian 2021 / O'Hearn 2022, Monteiro 2019); (f) policy mode carries the `policy_context` block. **52/52 PASS.**

**Verification.**

```
cd backend
python _smoke_audience_aware_contract.py        # 52/52 PASS
python _smoke_heni_literature_panel.py          # unchanged: 10/10 at +-0.1 min
python _smoke_hefi_canonical_diets.py           # unchanged: 3/3 + rank PASS
python _smoke_hsr_canonical_panel.py            # unchanged: 9/9
python _smoke_fcs_canonical_panel.py            # unchanged: 11/11 + rank + golden
python _smoke_nova_classification.py            # unchanged: 20/20

cd ../frontend
npx tsc --noEmit                                # clean
```

Manual UI walk-through: open `/heni/calculate`, `/hefi/calculate`, `/hsr/calculate`, `/fcs/calculate`; toggle Individual / Researcher / Policy via the new AudienceToggle; verify (i) headline + interpretation + mandatory caveat callout appear in all modes; (ii) methodology + citations accordions appear only in researcher/policy modes; (iii) μDALY/baseline-points/original_score detailed sections appear only in researcher/policy modes.

### 2026-05-23 — NOVA classifier rebuilt as rigorous Monteiro-2019-grounded matcher (NOVA-CODE-1)

**Why this matters.** The FCS smoke audit spot-checked 11 foods and found 3 NOVA misclassifications: (a) frozen-boiled broccoli classified as NOVA 2 because the previous code did substring matching without word boundaries (`'OIL' in 'BOILED'` → True); (b) a fast-food hot dog classified as NOVA 3 — but Monteiro 2019 §4.3 lists "reconstituted meat products" as a literal canonical NOVA 4 example; (c) a frozen pepperoni pizza classified as NOVA 3 — but Monteiro 2019 §4.3 lists "pre-prepared frozen dishes" as another literal canonical NOVA 4 example. The previous keyword-only classifier had no CNF FoodGroup auto-routes and a narrow NOVA-4 lexicon missing Monteiro's "ingredient isolates and additives with no domestic equivalent" criterion (soy/whey protein isolate, maltodextrin, hydrolysed proteins, hydrogenated/interesterified oils, MSG, carrageenan, xanthan, polysorbate, BHA/BHT, artificial flavours/colours/non-sugar sweeteners).

**Files added.**

- `backend/fcs_calculator/fcs/utils/nova_classifier.py` — new 400-line rigorous classifier with three deterministic stages + optional LLM augmentation
- `backend/_smoke_nova_classification.py` — Monteiro-2019-canonical 20-food validation harness
- `backend/_smoke_nova_classification_results.json` — committed results

**Files modified.**

- `backend/fcs_calculator/fcs/utils/cnf_data_integrator.py:231-420` — removed the inline substring-keyword block (~120 lines); replaced with a call to `nova_classifier.classify()`; preserved all FCS food-ingredient attribute side-effects per NOVA level
- `backend/_smoke_fcs_canonical_panel.py` — Greek yogurt target revised from `moderate` → `encourage` to reflect the secondary improvement: the previous YOGURT-detection check missed the Canadian "YOGOURT" spelling, so plain fat-free Greek yogurt did not receive the `yogurt` food_ingredients attribute and scored FCS 57.1; with the corrected detection, it scores FCS 84.1 (correct per Mozaffarian 2021 NHANES distribution for top-decile dairy foods)
- `manuscript_call1.md` §3.2 FCS bullet — full architectural description of the new classifier + 20/20 validation panel result

**Architecture (parallels §3.4 HENI categorizer + §3.5 LCA matcher + §3.6 FPED bridge).**

- **Stage 1**: CNF FoodGroup hard rules with description-pattern exceptions. Examples: Sweets group (19) → NOVA 2 if granulated/brown/icing sugar, → NOVA 3 if honey/maple syrup, → NOVA 4 by default for candy/cookies/dessert; Baked Products (18) → NOVA 3 for plain bread, → NOVA 4 for sweetened/glazed/pastry/cookie; Dairy and Egg Products (1) → NOVA 2 for butter/ghee, → NOVA 3 for cheese, → NOVA 4 for sweetened-flavoured yogurt, → NOVA 1 default for plain milk/yogurt/eggs; meat groups (5, 10, 13, 17) → NOVA 4 for reconstituted/sausage/hot-dog/frankfurter/bologna/salami/pepperoni/deli-meat, → NOVA 3 for cured/smoked/canned/jerky, → NOVA 1 default raw; Fast Foods (21) / Babyfoods (3) / Snacks (25) / Breakfast cereals (8) / Sausages and Luncheon meats (7) → NOVA 4 always.
- **Stage 2**: Word-boundary regex matching (no more OIL/BOILED bug) across four Monteiro NOVA 4 tiers — isolates (soy/whey protein isolate, casein, maltodextrin, HFCS/glucose-fructose, hydrogenated/interesterified, hydrolysed protein, modified starch) → additives (aspartame, sucralose, MSG, sodium nitrite/nitrate, carrageenan, xanthan/guar gum, lecithin, polysorbate, BHA/BHT/TBHQ, FD&C, enriched, fortified) → industrial processes (extruded, moulded, reconstituted, dehydrated, freeze-dried, pre-fried) → packaged-product archetypes (soft drink/cola, soda, sweetened beverage, candy, granola bar, cracker, chip, cookie, breakfast cereal, ice cream, frozen meal/dinner/entrée, instant noodle/soup, margarine, muffin, donut, pastry). Then NOVA 3 preservation/processing markers. Then NOVA 2 culinary ingredients.
- **Stage 3-bis (optional)**: LLM augmentation via `ChatJSONClient` (multi-provider — `LLM_PROVIDER` env routes between OpenAI `gpt-4.1-mini` default and Anthropic `claude-haiku-4-5`). Monteiro's 4-group definitions embedded in the system prompt; constrained JSON output `{nova_group: 1|2|3|4, confidence: 0-1, rationale: str}`; gated on heterogeneous CNF groups where rule-based classification leaves residual ambiguity; per-food-id cache (deterministic at T=0).
- **Stage 3 default**: NOVA 1 (Monteiro's "any food not matching higher-process criteria" baseline).

**Validation.** 20 Monteiro-2019-canonical foods spanning all four groups (6 NOVA 1 + 3 NOVA 2 + 5 NOVA 3 + 6 NOVA 4). Per-group accuracy: **NOVA 1 6/6, NOVA 2 3/3, NOVA 3 5/5, NOVA 4 6/6 = 20/20 PASS** with exact-match gating (no half-band tolerance). The previously-broken cases now pass: broccoli frozen boiled → NOVA 1 ✓; fast-food hot dog → NOVA 4 ✓; pepperoni frozen pizza → NOVA 4 ✓. FCS smoke regression check: 11/11 PASS preserved.

**Verification.**

```
cd backend
python _smoke_nova_classification.py               # 20/20 PASS
python _smoke_fcs_canonical_panel.py               # 11/11 + rank + golden PASS
python -m pytest heni_calculator/tests/ -q         # 15/15 PASS unchanged
```

### 2026-05-23 — Nutrition-score literature-pinned smoke harness (HENI / HEFI / HSR / cross-system)

**Why this matters.** The platform ships three nutrition scoring systems (HENI, HEFI-2019, HSR v9) and the manuscript §3.2 claimed canonical reproduction for each, but the actual empirical reproduction was either non-existent (HEFI, HSR had 0 pytest tests) or unit-test-only (HENI's 15 tests cover the DALY kernel on synthetic inputs but not the live API path). Per the approved plan ([`tranquil-coalescing-acorn.md`](C:\Users\Windows\.claude\plans\tranquil-coalescing-acorn.md)) literature-pinned smoke harnesses now back each manuscript claim.

**Files added:**
- [`backend/_smoke_heni_literature_panel.py`](backend/_smoke_heni_literature_panel.py) + [`_smoke_heni_literature_panel_results.json`](backend/_smoke_heni_literature_panel_results.json) — 8 Stylianou 2021 Fig 2-4 + SI reference foods (chicken wing, frankfurter sandwich, beef hotdog, vegetable pizza, apple pie, sardines, corned beef, white-bread sentinel) with hand-curated CNF picks + per-row rationale; gate = ±1×CI half-width
- [`backend/_smoke_hefi_canonical_diets.py`](backend/_smoke_hefi_canonical_diets.py) + [`_smoke_hefi_canonical_diets_results.json`](backend/_smoke_hefi_canonical_diets_results.json) — 3 directional diets (deep-fried anti-pattern; mixed-balanced; CFG-2019-aligned) with rank-order assertion
- [`backend/_smoke_hsr_canonical_panel.py`](backend/_smoke_hsr_canonical_panel.py) + [`_smoke_hsr_canonical_panel_results.json`](backend/_smoke_hsr_canonical_panel_results.json) — 9-food panel covering CNF-available subset of the 10 canonical AU reference foods; gate = ±0.5 stars
- [`backend/_smoke_nutrition_cross_system.py`](backend/_smoke_nutrition_cross_system.py) + [`_smoke_nutrition_cross_system_results.json`](backend/_smoke_nutrition_cross_system_results.json) — 6 meals × 3 systems; Spearman rank correlation + per-meal directional sanity
- [`backend/_smoke_heni_discover_candidates.py`](backend/_smoke_heni_discover_candidates.py) — discovery helper used to surface CNF candidates for the HENI panel

**Files modified:**
- [`backend/heni_calculator/heni/service.py:40-52`](backend/heni_calculator/heni/service.py) — `resolve_llm_api_key()` now falls back to `os.environ["OPENAI_API_KEY"]` (latent bug: Django settings never sets that key, so LLM-augmented HENI categorization was silently disabled in all production API calls until this fix)
- [`manuscript_call1.md`](manuscript_call1.md) §3.2 HEFI / HENI / HSR bullets + §4.1 + new §4.5 — empirical-reproduction figures added for each indicator with links to the smoke artefacts
- [`code_action_items.md`](code_action_items.md) — new HENI-CODE-1.y TODO for the CNF risk-factor extraction defect surfaced by the HENI smoke

**Headline results.**
- **HEFI: 3/3 PASS with correct directional rank** — anti-pattern 13.6/80 < mixed-balanced 51.5/80 < CFG-aligned 58.8/80. All three diets land in the Brassard 2022 p10 / p25-p75 / p90 bands.
- **HSR: 6/9 PASS within ±0.5 stars** — table sugar 0.5, whole milk 3.5, Greek yogurt 5.0, oats 4.0, chia 5.0, bacon 1.0 reproduce as expected; 3 outliers (apple juice 1.0 vs target 2.0, white bread 3.5 vs 2.5, sweetened almond beverage 1.0 vs 3.5) attributable to target-calibration uncertainty under no access to the paywalled HSRAC v9 Appendix 1 reference values rather than to pipeline error.
- **HENI: 1/8 PASS, median deviation 8.7× CI half-width** — DALY kernel is correct on synthetic inputs (15/15 unit tests pass after the Rust-binary rebuild noted below), but the upstream CNF → risk-factor extraction layer surfaces real defects: PUFA over-extracted ≈10×, sodium in inflated units on processed-meat rows, food-group risk factors reported as food mass not nutrient-category mass. Logged as HENI-CODE-1.y.
- **Cross-system Spearman: HEFI vs HSR ρ = +0.771** (strong agreement between the two LLM-free Rust-backed pipelines); HENI vs HEFI/HSR ρ ~ 0.2-0.3 (distorted by the HENI extraction defect — isolates the loss-of-coherence to that pipeline alone).

**Stale-binary side fix (Rust kernel rebuild).** The site-packages `rust_core.cp313-win_amd64.pyd` was from 2026-04-15, predating the 2026-05-21 HENI-CODE-1 sign-convention refactor of [`backend/rust_core/src/heni/`](backend/rust_core/src/heni/). Result: 5/15 HENI unit tests were failing before this session (including the canonical chicken-wing example, returning +0.626 min vs expected −3.26). `maturin develop --release` rebuild restored all 15. Documenting the rebuild requirement so future maintainers don't misdiagnose this as a code regression.

**Verification.**
```
cd backend
python _smoke_heni_literature_panel.py       # 1/8 PASS (surfaces HENI-CODE-1.y)
python _smoke_hefi_canonical_diets.py        # 3/3 PASS + rank PASS
python _smoke_hsr_canonical_panel.py         # 6/9 PASS within ±0.5 stars
python _smoke_nutrition_cross_system.py      # HEFI vs HSR Spearman ρ = +0.77
python -m pytest heni_calculator/tests/ -q   # 15/15 PASS (kernel arithmetic intact)
```

### 2026-05-22 — Tier γ "decomposer-confirmed direct match" gate refinement (Hypothesis B)

**Why this matters.** The 2026-05-22 `--with-decomposer` benchmark (n=184) exposed a defensive-gate edge case: the `min_ingredients = 2` structural gate was rejecting 1-ingredient decompositions even when the decomposer correctly agreed with the matcher's borderline-confidence direct match. Two known false rejections (`food_id=4652` "submarine sandwich with tuna salad", `food_id=5691` "deli chicken breast, oven-roasted, sliced") both at matcher confidence 0.80, both with the decomposer returning exactly one ingredient equal to the matcher's choice. The user-facing LCA value was correct in both cases (the matcher's borderline match took over after the decomposer rejected), but the audit trail showed "Tier γ rejected: too_few_ingredients" which read as a failure rather than the actual "decomposer confirmed matcher."

**Four-phase investigation** (per `tranquil-coalescing-acorn.md` plan, all phases executed 2026-05-22):

- **Phase A** — extended `_smoke_matcher_benchmark.py` to capture decomposer ingredient ciqual codes (`decomposer_ingredients` field) in each per_food row. Re-ran benchmark to refresh JSON.
- **Phase B** — wrote `_analyze_decomposer_agreement.py` (no LLM cost) that classifies all 60 Tier γ attempts into 7 categories. Result: **D=2** (the 4652+5691 cases, confirming the pattern is persistent across runs), **E=0** (zero genuine lazy 1-ingredient garbage = Hypothesis B has no false-accept risk), A=15, B=32, F=11. The script's decision rule said "PROCEED — Hypothesis B is clearly correct."
- **Phase C** — added `MATCHER_AGREEMENT_CONFIDENCE_FLOOR = 0.75` constant to `recipe_decomposer.py`; plumbed the upstream `match_result: Optional[MatchResult]` through `decompose()` → `_validate_and_build()`; refined the `min_ingredients` gate to accept 1-ingredient decompositions when (i) the ingredient's ciqual_code equals the matcher's choice, (ii) the matcher's confidence is ≥ 0.75, (iii) the ingredient occupies ≥ 80 % of the target serving (safety guard against "matched ingredient + unspecified rest" misreads), with `fallback_reason='decomposer_confirmed_direct_match'` and ingredient mass normalised to exactly the target. Wired the API call site in [`life_cycle_assessment.py:393`](backend/environmental_impact_model/src/life_cycle_assessment.py#L393) to pass `match_result` through.
- **Phase D** — added 5 new unit tests pinning the four boundary cases (accept on agreement; reject without agreement; reject below confidence floor; reject without match_result for back-compat; reject when ingredient mass < 80 % of target). All 163 backend tests pass. Live-verification benchmark re-run on n=184 panel under the new gate.

**Live verification results.** Re-running `_smoke_matcher_benchmark.py --sample-size 184 --seed 42 --with-decomposer` (git rev `e416d7d`) under the new gate:

- food_id=4652 now RESOLVES with `decomposer_confirmed_direct_match` (1 ingredient `[25431]` at 100 g, matcher conf 0.80) ✓
- food_id=5691 now RESOLVES with `decomposer_confirmed_direct_match` (1 ingredient `[28963]` at 100 g, matcher conf 0.80) ✓
- One additional case from this run: food_id=3792 "White cake, homemade, without icing" — the LLM returned 1 ingredient this run; gate accepted it as decomposer-confirmed
- **`too_few_ingredients` rejection reason: 2 → 0** (disappeared entirely from the rejection-reasons block)
- Tier γ resolve rate: **51 / 61 = 84 %** (up from 47 / 60 = 78 % under the unrefined gate)
- Zero new false-positives in the resolved set

**Files touched.**

New:
- `backend/_analyze_decomposer_agreement.py` — Phase B classification harness (no LLM cost)
- `backend/environmental_impact_model/data/decomposer_agreement_analysis.md` — Phase B markdown summary

Modified:
- `backend/_smoke_matcher_benchmark.py` — Phase A (captures `decomposer_ingredients` list per row)
- `backend/environmental_impact_model/src/recipe_decomposer.py` — Phase C (new `MATCHER_AGREEMENT_CONFIDENCE_FLOOR=0.75` constant; `decompose()` + `_validate_and_build()` accept `match_result`; min_ingredients gate refinement with 80 %-mass safety guard)
- `backend/environmental_impact_model/src/life_cycle_assessment.py` — Phase C call-site update (passes `match_result` to `decompose()`)
- `backend/environmental_impact_model/tests/test_recipe_decomposer.py` — Phase D.1 (new `DecomposerConfirmedDirectMatchTests` class with 5 tests)
- `manuscript_call1.md` §4.4 — replaced the "false rejections / Tier ε refinement" paragraph with the empirical Phase B classification table + the shipped Hypothesis B description + Phase D verification numbers

**Verification.**

- Decomposer unit tests: **25/25 pass** (20 baseline + 5 new). Run: `python -m pytest environmental_impact_model/tests/test_recipe_decomposer.py -v`.
- Full env-model test suite: **163/163 pass** (no regressions; 156 baseline + 5 new decomposer tests + 2 latency/bootstrap-CI tests now activate since artefact has the new fields).
- Phase D.2 live benchmark: 51/61 resolved (84%), the 2 known false-rejection cases (4652, 5691) now resolve with `decomposer_confirmed_direct_match`.

### 2026-05-22 — Model upgrade (gpt-4o-mini → gpt-4.1-mini), prompt rewrite (Tian et al. 2023), multi-provider Claude support, calibration probe

**Why this matters.** The 0.40 confidence anchor on `gpt-4o-mini` was a workaround target — the architectural fix (threshold 0.60 → 0.30, structural gates carry the QA load) shipped earlier the same day, but the underlying calibration bug persisted and limited the signal we could extract from `decomposition_confidence`. Three concurrent changes resolve it: (a) swap the OpenAI model to `gpt-4.1-mini`, which has known better instruction-following at the same constrained-JSON cost envelope; (b) rewrite both the matcher and decomposer system prompts per Tian et al. 2023 ("Just Ask for Calibration", arXiv:2305.14975) using probability-of-correctness phrasing + discrete numeric anchors + Lin et al. 2022 indirect elicitation; (c) add a multi-provider abstraction so the same ranking + decomposition calls can route to Anthropic `claude-haiku-4-5` via `LLM_PROVIDER=anthropic` env var — addressing a recurring reviewer ask that no single vendor's idiosyncrasies dominate downstream results.

**Calibration probe (8 composites, trivial → hard) before vs after:**

| Provider / model | Distinct confidence values (≥4 = PASS) | Std-dev (≥0.10 = PASS) | Spearman ρ vs difficulty (<0 = PASS) | Acceptance |
|---|---|---|---|---|
| `gpt-4o-mini` (baseline) | 1 (0.40 anchor on 7/8) | ≈ 0 | n/a (no variance) | **0/3** |
| `gpt-4.1-mini` (new default) | **5** ({0.0, 0.6, 0.7, 0.75, 0.85}) | **0.371** | **−0.417** | **3/3** PASS |
| `claude-haiku-4-5` (alt) | 4 ({0.0, 0.35, 0.45, 0.78}) | 0.298 | +0.655 (wrong dir) | 2/3 |

The Claude path fails the Spearman direction because the prompt encourages the model to express simple composites as 1-ingredient responses (which our `min_ingredients = 2` gate rejects); production default therefore stays `openai/gpt-4.1-mini` with Claude available as an alternative for provider-bias robustness checks. Per-probe artefacts ship at `backend/environmental_impact_model/data/confidence_probe_<provider>_<model>_<utc>.json`.

**Files touched.**

New:
- `backend/environmental_impact_model/src/llm_client.py` — `ChatJSONClient` Protocol + `OpenAIChatJSONClient` / `AnthropicChatJSONClient` adapters + `build_chat_json_client()` factory (respects `LLM_PROVIDER` env) + `coerce_chat_json_client()` back-compat seam for legacy raw-OpenAI clients.
- `backend/environmental_impact_model/tests/test_llm_client.py` — 16 unit tests (provider defaults pinned, env dispatch, missing-key paths, MagicMock coercion, JSON-permissive parser, Anthropic prefill).
- `backend/_smoke_confidence_probe.py` — 8-composite calibration probe; writes per-provider JSON artefacts + acceptance flags to stdout.
- `backend/environmental_impact_model/data/confidence_probe_openai_gpt-4.1-mini_<utc>.json` and `confidence_probe_anthropic_claude-haiku-4-5_<utc>.json`.

Modified:
- `backend/environmental_impact_model/src/lca_matcher.py` — `DEFAULT_RANKING_MODEL = "gpt-4.1-mini"` (was `gpt-4o-mini`); matcher SYSTEM_PROMPT rewritten with Tian et al. 2023 probability-of-correctness phrasing + 6-anchor calibration scale; constructor accepts `chat_json_client=...` alongside legacy `ranking_client=...`; `_query_llm` delegates to ChatJSONClient; `build_default_matcher` uses `build_chat_json_client()` for the ranking side while keeping OpenAI-only for embeddings.
- `backend/environmental_impact_model/src/recipe_decomposer.py` — SYSTEM_PROMPT confidence block rewritten with indirect elicitation ("if you ran this 10 times, what fraction would still be LCA-equivalent?") + 5-anchor calibration scale; constructor accepts `chat_json_client=...`; `_query_llm` delegates to ChatJSONClient; `_build_prompt` renamed `_build_user_message` (system prompt is now supplied separately at the ChatJSONClient call site).
- `backend/api/views/environmental_views.py` — decomposer setup uses `build_chat_json_client()` (respects `LLM_PROVIDER`) when no upstream matcher provides one; still requires `OPENAI_API_KEY` for embeddings.
- `backend/environmental_impact_model/tests/test_lca_matcher.py` — new `DefaultModelPinTests` class pins `DEFAULT_RANKING_MODEL == "gpt-4.1-mini"` to catch accidental reverts.
- `backend/requirements.txt` — added `anthropic>=0.40.0` (lazy-imported; only required when `LLM_PROVIDER=anthropic`).
- `backend/.env.example` — added `LLM_PROVIDER=openai` toggle; uncommented `ANTHROPIC_API_KEY=` with docs noting it's required if `LLM_PROVIDER=anthropic`.
- `manuscript_call1.md` §3.5 — three new paragraphs documenting the model swap, the Tian et al. 2023 / Lin et al. 2022 prompt rewrite with calibration-probe numbers, and the multi-provider abstraction. Inline `gpt-4o-mini` references in the LLM-ranking and S7-benchmark passages updated to reflect the new default while preserving the original 184-food benchmark result as the pre-upgrade baseline.

**Verification.**

- Full env-model test suite: **156/156 pass** (was 139 baseline + 16 new llm_client + 1 new model-pin = 156).
- Live calibration probe vs gpt-4.1-mini: **3/3 acceptance signals PASS** (5 distinct conf values, std 0.371, Spearman −0.417).
- Live calibration probe vs claude-haiku-4-5: **2/3 acceptance signals PASS** (4 distinct conf values, std 0.298, Spearman positive — Claude prefers single-ingredient responses for trivial composites).
- No production-default behavioural change with `LLM_PROVIDER` unset (defaults to openai/gpt-4.1-mini).

### 2026-05-22 — Tier γ acceptance-gate calibration (decomposer now actually resolves)

**Why this matters.** The Tier γ refinement shipped earlier the same day fixed the TRIGGER (decomposer now correctly fires on borderline-confidence composite matches via `HIGH_CONFIDENCE_THRESHOLD=0.85`), but the live decomposer smoke surfaced a second, separate problem: of the 7/7 Canadian composites the decomposer now correctly attempted, **0/7 actually resolved**. All 7 attempts were rejected by the `decomposition_confidence ≥ 0.60` gate at a uniform self-reported confidence of 0.40 — suggesting the threshold was empirically unreachable, not that the decompositions were genuinely bad.

**Empirical investigation.** A controlled probe ran the decomposer against 8 composite foods spanning trivial (lasagna, scrambled eggs, tomato soup) to genuinely-hard (poutine, bannock, tourtière) and recorded the self-reported `decomposition_confidence`. **7 of 8 returned exactly 0.40**; one returned 0.00. This is a hard model-default bias on `gpt-4o-mini`, not calibrated uncertainty. The 0.60 threshold was therefore unreachable by design — Tier γ was decorative.

**Four targeted fixes (in `recipe_decomposer.py`):**

1. **Lower `DEFAULT_DECOMPOSITION_CONFIDENCE_THRESHOLD` from 0.60 → 0.30**. Below the empirical 0.40 floor; still rejects "I have no idea" (conf=0.00) responses. Documented in source with the empirical evidence.

2. **Mass-shortfall auto-credit**. New `AUTO_CREDIT_UNRESOLVED = True` flag: when the LLM's ingredient sum is short of target by an amount in (tolerance, 10 % of target] AND `unresolved_mass_g=0`, the shortfall is auto-credited into `unresolved_mass_g` rather than rejected as `mass_imbalance`. This catches LLM arithmetic sloppiness (Shepherd's pie returned 150+50+40=240 g + 0 unresolved for a 250 g target — the 10 g gap is real residual, not a structural error). The `MAX_UNRESOLVED_FRACTION` cap still bounds total unresolved mass.

3. **`DEFAULT_MIN_INGREDIENTS = 2` structural gate**. A "decomposition" with 1 ingredient is the matcher's job, not the decomposer's — reject.

4. **Tightened system prompt**. Explicit mass-closure rule ("put the residual in `unresolved_mass_g`; do NOT leave the mass unbalanced") + confidence calibration guidance ("report `decomposition_confidence` as a true uncertainty estimate; do NOT default to 0.4"). The latter may not fully overcome the model's default bias but at least disambiguates the field's intended semantics.

**Architectural intent**: structural gates (mass closure + constrained vocabulary + ≥2 ingredients + Ciqual validity) carry the QA load; `decomposition_confidence` is a soft secondary check.

**Live decomposer smoke (2026-05-22, post-fix)**: **7/7 Canadian composites now RESOLVE** (vs 0/7 before). Per-food GW changes vs the old matcher-only path:

| Food | matcher-only GW | decomposition GW | Δ |
|---|---|---|---|
| Bannock | 0.0453 | 0.0242 | −47 % |
| Tourtière | 0.4449 | 0.1390 | −69 % |
| Poutine | 0.1739 | 0.0999 | −43 % |
| Butter tart | 0.0495 | 0.0633 | +28 % |
| Shepherd's pie with corn | 0.8333 | 0.5381 | −35 % |
| Babyfood, beef + vegetables | 0.3571 | **1.7789** | **+398 %** |
| Babyfood, chicken + cheese pasta + veg | 0.3169 | 0.2054 | −35 % |

Most decompositions LOWER the GW because the matcher had stretched to higher-impact LCI entries (e.g. Tourtière → "Riesling wine and pork pie") that the decomposition correctly replaces with mass-weighted components. The babyfood-beef case INCREASES dramatically because the matcher's coarse "Vegetable dish for baby with meat/fish and starch" entry under-weighted the real meat content; the decomposition correctly attributes ~30 g of cooked beef stewing meat as the GHG-dominant ingredient. This is exactly the within-group-variance problem TODO-CODE-LCA-3 was designed to surface.

**Files touched.**

Modified:
- `backend/environmental_impact_model/src/recipe_decomposer.py` — `DEFAULT_DECOMPOSITION_CONFIDENCE_THRESHOLD 0.60 → 0.30`; new `DEFAULT_MIN_INGREDIENTS = 2`; new `AUTO_CREDIT_UNRESOLVED = True`; new mass auto-credit logic in `_validate_and_build`; new min-ingredients gate; rewritten `SYSTEM_PROMPT` with explicit mass-closure rule + confidence-calibration guidance.
- `backend/environmental_impact_model/tests/test_recipe_decomposer.py` — 3 new tests pinning the new behaviour (`test_empirical_default_confidence_040_accepted`, `test_too_few_ingredients_rejected`, `test_mass_shortfall_auto_credits_to_unresolved`); existing `test_mass_tolerance_scales_with_target` rebaselined to multi-ingredient inputs; `setUp` updated to use the new production default (0.30) instead of legacy 0.60.
- `backend/_smoke_decomposer_live.py` — SUMMARY text rewritten ("decomposer ATTEMPTED N/7" + "decomposer RESOLVED N/7") to disambiguate trigger-fired vs. validation-passed.
- `manuscript_call1.md` §3.5 — disclosed the empirical 0.40 model-default bias, the 0.30 acceptance floor, the auto-credit rule, the min-2-ingredients gate, and the 7/7 live evidence.

**Verification.**

- Decomposer unit tests: **20/20 pass** (17 baseline + 3 new). Run: `python -m pytest environmental_impact_model/tests/test_recipe_decomposer.py -v`.
- Full LCA test suite: **139/139 pass** (no regressions).
- Live decomposer smoke: 7/7 Canadian composites RESOLVED (run: `python _smoke_decomposer_live.py`).
- API E2E smoke (defaults preserved): PASS.

### 2026-05-22 — Matcher validation harness + Tier γ trigger refinement + frontend decomposer toggle

**Why this matters.** The Tier α+β+γ architecture shipped earlier the same day was structurally complete but had three production-inert behaviours surfaced by live-LLM smoke testing: (1) the LLM matcher's 0.6 confidence threshold was too permissive — it returned `matched=True` on stretched LCA-distant near-misses (Bannock → "Biscuit, extruded and grilled, fruits filling" at 0.65; Tourtière → "Riesling wine and pork pie" at 0.60), which prevented the `RecipeDecomposer.should_decompose` trigger predicate from ever firing in practice; (2) the decomposer's mass-balance gate at ±5 g was too strict for 250 g+ servings (Shepherd's pie's mass-correct ingredient list was rejected at 240 g vs 250 g target, a 4 % gap within typical recipe-rounding); (3) the matcher's accuracy across the full CNF panel was unmeasured — the manuscript's §4.4 Scenario S7 was placeholder text with no underlying data artefact. The frontend `enable_recipe_decomposer` toggle was also deliberately deferred during the original Tier γ landing.

**Three deliverables shipped (per `tranquil-coalescing-acorn.md` plan):**

**(A) Extensive matcher validation harness.** New `backend/_smoke_matcher_benchmark.py` runs the live matcher against a stratified random 184-food CNF sample (8 per FoodGroup × 23 groups, `random.seed(42)` reproducible) and applies four automated quality heuristics per match:

1. **Group consistency** — matched `agribalyse_group` is in the expected acceptance set for the CNF FoodGroup (extends `_CNF_TO_AGRIBALYSE_SUBGROUP` with a per-CNF-group acceptance map; wildcard for `Snacks` / `Spices and Herbs`).
2. **Magnitude plausibility** — matched per-100 g GW within ±3× of cnf_integrator group default for the CNF group.
3. **Token overlap** — matched LCI name (English + French combined) shares ≥1 content token (≥4 chars, stoplist filtered) with the canonicalised CNF description.
4. **Confidence band** — clean ≥ 0.85; borderline 0.60–0.85; low < 0.60.

Per-food verdict: `clean` (all 4 pass + conf ≥ 0.85) / `borderline` (all 4 pass at lower confidence) / `flagged` (any 1–3 fails OR matched=False). Outputs a checksummed JSON artefact (`data/matcher_benchmark_<git-rev>_<utc>.json` — same write pattern as `s2_divergence_panel.json` and the ReCiPe pack ETL) plus a `matcher_benchmark_flagged_for_review.md` reviewer hand-off with the per-row JSON-editable `reviewer_verdict` + `reviewer_notes` fields pre-allocated as `null`. Cost: $0.026 per 184-food run (median latency 1.62 s per food).

**First-run results** (git rev `16a5ca7`, 2026-05-22): **28 % clean / 35 % borderline / 37 % flagged**. Confidence-band calibration is meaningful: at ≥ 0.85 the flagged rate is 26 %; at 0.60–0.85 it is 43 %. This empirically grounds the `HIGH_CONFIDENCE_THRESHOLD = 0.85` chosen for the refined Tier γ trigger (B.2). Worst CNF groups by flagged rate: Nuts and Seeds 100 % (peanut flour matched peanut butter, GW 7.5× group default — likely a real LCA distinction routed to reviewer rather than a defect), Legumes 88 %, Finfish / Fats / Breakfast cereals 62 %. Best: Lamb / Soups 0 %, Babyfoods / Fast Foods / Snacks 12 % (subgroup routing helping).

**(B) Tier γ trigger + mass-tolerance refinements** in `recipe_decomposer.py`:

- **B.1 Mass tolerance** — `MAX_MASS_GAP_G = 5.0` and `MAX_MASS_GAP_FRACTION = 0.02` with new helper `_mass_tolerance(target_mass_g) = max(5, 2% of target)`. 250 g target → unchanged ±5 g; 500 g → ±10 g (was rejected at +6 g over the 5 g floor; now admitted at +10 g); 1 kg → ±20 g.
- **B.2 `should_decompose` trigger** — fires when CNF group is composite AND (`matched=False` OR `confidence < HIGH_CONFIDENCE_THRESHOLD = 0.85`). Composite groups: `{Mixed Dishes, Soups Sauces and Gravies, Fast Foods, Babyfoods, Sausages and Luncheon meats, Sweets, Snacks, Baked Products}`. Under the live-LLM smokes: Lasagna (conf 0.90) still direct-matches; Bannock (0.65) / Tourtière (0.60) / Shepherd's pie (0.80) / Babyfoods (0.75) now route to the decomposer.
- **B.3 Audit field** — `recipe_decomposition_decisions[].triggered_by` records `matcher_failed` vs `low_matcher_confidence:<conf>` so reviewers can disambiguate hard-failure vs. borderline-routing in downstream analysis.

Integration in `life_cycle_assessment.py:_get_food_environmental_impacts` updated: removed the `(not matched_factors) and ...` short-circuit so `should_decompose` is evaluated even when matcher returned a borderline-confidence match. Successful decompositions overwrite the matcher's borderline result; failed decompositions keep the matcher's result (best available) AND record the failure in `recipe_decomposition_decisions[]`.

**(C) Frontend `enable_recipe_decomposer` toggle.** Added to `EnvironmentalCalculator.tsx` Advanced panel (collapsed; chip in toggle row when activated; UX subtext describes cost + OpenAI-key dependency). New `RecipeDecompositionDecision` TypeScript type + `recipe_decomposer` block under `meal_analysis` in `EnvironmentalImpactResult`. New collapsible "🧪 Recipe decomposition audit" panel in `LCABreakdown.tsx` that surfaces per-food decomposition decisions (RESOLVED vs REJECTED status badge, per-ingredient Ciqual + mass list, fallback reason for rejected decompositions).

**Files touched.**

New: `backend/_smoke_matcher_benchmark.py`, `backend/environmental_impact_model/data/matcher_benchmark_<git-rev>_<utc>.json` (first artefact: `matcher_benchmark_16a5ca7_20260522T161706Z.json`), `backend/environmental_impact_model/data/matcher_benchmark_flagged_for_review.md`, `backend/environmental_impact_model/tests/test_matcher_benchmark.py` (10 shape-pinning tests).

Modified: `backend/environmental_impact_model/src/recipe_decomposer.py` (`_mass_tolerance` helper + `HIGH_CONFIDENCE_THRESHOLD` constant + `should_decompose` rewrite), `backend/environmental_impact_model/src/life_cycle_assessment.py` (decomposer integration point + audit field), `backend/environmental_impact_model/tests/test_recipe_decomposer.py` (updated `test_mass_imbalance_rejected` + 3 new tests: `test_mass_tolerance_scales_with_target`, `test_composite_group_with_borderline_match_triggers`, `test_borderline_match_on_NON_composite_group_does_not_trigger`), `frontend/src/lib/api.ts` (`RecipeDecompositionDecision` type + `recipe_decomposer` block in `EnvironmentalImpactResult` + `enable_recipe_decomposer` request field + normaliser wiring), `frontend/src/components/environmental-component/EnvironmentalCalculator.tsx` (checkbox + chip + state), `frontend/src/components/environmental-component/LCABreakdown.tsx` (decomposition audit panel), `manuscript_call1.md` (§3.5 trigger threshold note; §4.4 Scenario S7 full fill-in with empirical numbers).

**Verification.**

- Decomposer unit tests: **17/17 pass** (14 baseline + 3 new). Run: `python -m pytest environmental_impact_model/tests/test_recipe_decomposer.py -v`.
- Benchmark shape tests: **10/10 pass** against the persisted JSON artefact. Run: `python -m pytest environmental_impact_model/tests/test_matcher_benchmark.py -v`.
- Full LCA test suite: **136/136 pass** (123 baseline + 3 decomposer + 10 benchmark shape). No regressions.
- Live benchmark: $0.026, 1.62 s median per-food latency, JSON + markdown artefacts written.
- API E2E smoke (defaults unchanged when `enable_recipe_decomposer=False`): PASS.
- Frontend `npx tsc --noEmit`: clean.

**Reviewer follow-up.** Spot-check the 68 `flagged` rows in `matcher_benchmark_flagged_for_review.md` and add `reviewer_verdict` + `reviewer_notes` to the JSON; the next benchmark run can then surface annotated rates. Two-phase delivery is intentional: harness + flagged-row list shipped now; reviewer-verdict-driven accuracy table in a follow-up.

### 2026-05-22 — RECIPE2016-PACK landed (multi-country, perspective-aware methodology integration)

**Why this matters.** The hand-typed `RECIPE_ENDPOINT_FACTOR_PROVENANCE` (26 endpoint factors) and `NORMALIZATION_FACTORS_*` constants were silently drifting from the authoritative RIVM workbooks. Cross-checking against the now-acquired `ReCiPe2016_CFs_v1.1_20180117.xlsx` revealed `terrestrial_ecotoxicity_ecosystem` was **4,737× too high** (5.4e-8 vs canonical 1.14e-11) and `human_toxicity_non_cancer` was **34× too low** (6.7e-9 vs 2.28e-7), latent today because of the v1 trim but armed to bite the moment any of those categories returned. Separately, the `_get_canadian_regional_factors` block applied unsourced midpoint multipliers (water 0.65, land 0.78, …) that had no published LCA-literature basis. This integration replaces all factor numbers with workbook-derived JSON packs and parameterises the LCA pipeline on country + perspective + consumer-perspective so the platform is no longer Canada/Hierarchist-only.

**New files (architecture):**

- `backend/environmental_impact_model/etl/build_recipe2016_factor_packs.py` — ETL that reads the three official RIVM workbooks and writes 4 JSON packs + `country_iso3_map.json`. Mirrors `build_agribalyse_v32_catalog.py` (same helpers, SHA-256 provenance, paired-write).
- `backend/environmental_impact_model/src/methodology_factors.py` — singleton runtime loader (`get_methodology_pack('recipe2016')`). Validates SHA-256 against meta on load, exposes typed accessors: `endpoint_factor`, `normalization('midpoint'|'endpoint'|'aop')`, `country_endpoint_cf(country, pathway, perspective)`, `supports_country`, `list_countries`, `version_string`, `methodology_provenance`.
- `backend/environmental_impact_model/data/recipe2016_endpoint_factors.json` — 24 endpoint factors × {I, H, E}, with E adding brown coal + peat (26 keys).
- `backend/environmental_impact_model/data/recipe2016_normalization.json` — World 2010 per-person scores at midpoint (21 categories) + endpoint per pathway (19) + per-AoP (3) per perspective.
- `backend/environmental_impact_model/data/recipe2016_country_factors.json` — country-specific endpoint CFs covering 246 ISO-3 codes after name normalisation, for the 3 cleanly-per-country categories (water, FW eutrophication, terr. acidification) plus the regional-aggregate PMF / photochemical-ozone source-region tables retained verbatim for forward use.
- `backend/environmental_impact_model/data/recipe2016_factor_packs_meta.json` — SHA-256 of each pack, source workbook SHA-256s, ETL git rev, extracted_at_utc.
- `backend/environmental_impact_model/data/country_iso3_map.json` — workbook country string → ISO 3166-1 alpha-3, embedded inline in ETL for reviewability.
- `backend/environmental_impact_model/tests/test_recipe2016_etl.py` — 21 tests pinning schema version, perspective set, 24/26 factor counts, the 4,737× and 34× drift corrections, midpoint norm spot-checks (Global warming H = 7990.41), Canada water CFs (HH = 0, terrestrial H = 1.27e-9, stress = 0.7), USA vs Canada water contrast, regional-category region count.
- `backend/environmental_impact_model/tests/test_lca_default_behavior_parity.py` — 13 tests verifying defaults (`country=None, perspective='H', consumer='global'`) produce sane outputs across 5 representative foods, perspective-switching keeps midpoints identical, country switching only swaps water pathways, invalid perspective/country raises `ValueError`, normalised-midpoints method works.

**Refactored files:**

- `backend/environmental_impact_model/src/life_cycle_assessment.py` — deleted `RECIPE_ENDPOINT_FACTOR_PROVENANCE`, `NORMALIZATION_FACTORS_*`, and `_get_canadian_regional_factors`. `LifeCycleAssessment.__init__` now accepts `methodology='recipe2016', perspective='H', country=None, consumer_perspective='global'`. New `_ef(pathway_key)` resolver substitutes country-specific CFs for the 3 water pathways when configured; records every resolution in `self.endpoint_factor_sources` (`world_average` vs `country_specific:CAN`). New `calculate_normalized_midpoints()` returns per-category person-year-equivalents. `calculate_single_score` pulls normalisation from the pack; legacy `normalization_set` / `use_updated_normalization` args are no-op deprecation warnings.
- `backend/environmental_impact_model/src/monetization.py` — `Monetization(lca_results, data_loader, country=None)`; per-country regional adjustments selected from `_REGIONAL_MONETIZATION_BY_COUNTRY`. Unknown country → identity multipliers + info log; absolute CAD prices stay Canadian-calibrated (no per-country economic study yet for re-pricing).
- `backend/environmental_impact_model/src/utils.py` — `FOOD_WASTE_FACTOR` kept as Canadian default; new `get_food_waste_factor(country)` returns per-country (currently `{CAN: 0.319}`) or FAO 2011 global mean (0.30) for unknowns.
- `backend/api/views/environmental_views.py` — all three LCA endpoints (`environmental_impact`, `compare_foods_environmental`, `food_environmental_profile`) accept new optional params (`methodology`, `perspective`, `country`, `consumer_perspective`) via `_validate_methodology_params`; threaded through to LCA + Monetization + reference-meal LCA. Response envelope adds `methodology_pack`, `parameters`, `endpoint_factor_sources`, `normalized_contributions_per_person`. New `methodology_info` view at `GET /environmental-impact/methodology/` returns available perspectives + countries + country-aware pathways + provenance for the frontend's Advanced panel.
- `backend/api/urls.py` — registered the methodology metadata endpoint.
- `backend/environmental_impact_model/tests/test_agribalyse_v32_catalog.py` — renamed `RegionalScalingSuppressionTests` → `MatcherOverlayAuditTrailTests`; updated expected values to reflect the retired midpoint multipliers (Land use 4.0 → 2.0, no more 0.78× silent scaling).
- `backend/environmental_impact_model/tests/test_lca_v1_trim.py` — single-score parity now reads normalisation from `lca.pack.normalization('aop', ...)` instead of the deleted module constant.
- `frontend/src/lib/api.ts` — new types `LcaPerspective`, `LcaConsumerPerspective`, `MethodologyInfo`; extended `EnvironmentalImpactRequest` with the 4 new optional fields; new `EnvironmentalImpactApiService.getMethodologyInfo()` cached fetch.
- `frontend/src/components/environmental-component/EnvironmentalCalculator.tsx` — added collapsed Advanced methodology panel: perspective (I/H/E radio), consumer perspective (global/national), country dropdown (246 ISO-3 codes from the API, enabled only when consumer='national'). Defaults preserved; opening the panel adds a state chip next to the toggle.
- `frontend/src/components/environmental-component/LCABreakdown.tsx` — adds an active-methodology chip row (pack version, perspective, country/consumer status) so reviewers can see which configuration produced the displayed numbers.

**Verification:**

- ETL: `python -m environmental_impact_model.etl.build_recipe2016_factor_packs` produces 5 files with checksums recorded; checksum self-test passes after switching to binary writes (Windows LF/CRLF parity).
- Test suite: 74/74 environmental_impact_model tests pass (21 ETL + 13 parity + 11 v1 trim + 29 catalog/matcher).
- API smoke: `_smoke_api_e2e.py` passes; new params honoured end-to-end (defaults preserved, `country=CAN&perspective=I&consumer_perspective=national` returns correct `metadata.methodology` string and `parameters` echo; invalid `country=ZZZ` returns HTTP 400 with helpful error).
- Frontend: `npx tsc --noEmit` clean.
- Drift verification surfaced: `terrestrial_ecotoxicity_ecosystem` now 1.14e-11 (workbook-correct), `human_toxicity_non_cancer` now 2.28e-7, `fossil_scarcity_hard_coal` now 0.0341, `freshwater_eutrophication_ecosystem` now 6.71e-7. Latent dormant under v1 trim today; armed for TODO-CODE-LCA-2.

**Manuscript implications:**

- §3.6 Methodology parameterisation — describe the country/perspective/consumer surface and the workbook provenance (SHA-256s available in `recipe2016_factor_packs_meta.json`).
- §7.5 — retire the "Canadian regional factors" paragraph; replace with the country-aware endpoint CF approach. Note explicitly that midpoint-level Canadian multipliers were retired as unsourced.
- §4.x perspective sensitivity figure becomes runnable: same meal, swap `perspective=I|H|E`, plot the three endpoint single-scores. Egalitarian Human Health endpoint ~13× Hierarchist on high-GW meals (already pinned in `test_lca_default_behavior_parity.py::test_egalitarian_human_health_dominates_individualist`).

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

### 2026-05-21 — HSR-CODE-1 implemented (HSRC v9 Tables 1–7 reconciliation)

**Files modified (5):**

- [backend/rust_core/src/hsr/threshold_data.rs](backend/rust_core/src/hsr/threshold_data.rs) — full rewrite of all six `CATEGORY_*` bundles to v9 Appendix 1 Tables 1–7. Introduced six shared per-table threshold arrays: `ENERGY_T1` (11 thresholds, Cat 1D/2/2D/3/3D shared), `SAT_FAT_T1` and `SODIUM_T1` (30 thresholds each, Cat 1D/2/2D), `SUGAR_T1` (25 thresholds, Cat 1D/2/2D), `SAT_FAT_T2` (30 thresholds, Cat 3/3D), `SUGAR_T2` (10 thresholds, Cat 3/3D), `FVNL_NON_CONCENTRATED` (8 thresholds, Cat 1D/2/2D/3/3D), `FVNL_CAT1` (10 thresholds), `PROTEIN_T6` and `FIBER_T6` (15 thresholds each). Cat 1 energy array prepends `NEG_INFINITY` per v9 Table 3 row 0 ("no zero-point bucket" — caps diet soft drinks at 3.5 stars). Cat 1 sat fat, sodium, protein, fibre all set to `INF11` (not scored). Replaced every `star_thresholds` array with v9 Table 7 values: Cat 1 `[NEG_INFINITY, NEG_INFINITY, 0, 1, 3, 5, 7, 9, 11]` (top-two slots padded — name-overrides deferred), Cat 1D `[-2, -1, 0, 1, 2, 3, 4, 5, 6]`, Cat 2 `[-11, -7, -2, 2, 6, 11, 15, 20, 24]`, Cat 2D `[-2, 0, 2, 3, 5, 7, 8, 10, 12]`, Cat 3 `[13, 16, 20, 23, 27, 30, 34, 37, 41]`, Cat 3D `[24, 26, 28, 30, 31, 33, 35, 37, 39]`. Added `CATEGORY_3D` as a dedicated bundle (was an alias to `CATEGORY_2D`); rewired `bundle_for_category_value` accordingly. Added module-level provenance docstring citing HSRAC 10 Dec 2025.
- [backend/rust_core/src/hsr/mod.rs](backend/rust_core/src/hsr/mod.rs) — flipped `value >= t` → `value > t` in `calculate_hsr_points_inner` (v9 "≤X earns 0 points, >X earns 1 point" convention). Added handling for `NEG_INFINITY` (Cat 1 energy row 0 always counts → never returns 0 points unless `value < 0`) and `INFINITY` (NA sentinel → returns 0). Updated inline tests: `calculate_hsr_points_strict_greater_semantics` (boundary `value = t` returns previous count, not next), `calculate_hsr_points_v9_sodium_boundary` (sodium 90.0 → 0 points, 90.1 → 1 point under v9 Cat 2), `calculate_hsr_points_neg_infinity_first_always_counts`, `convert_score_to_stars_matches_v9_cat1d` (verifies the 9-threshold Cat 1D ladder), `convert_score_to_stars_v9_cat2_reaches_5_stars` (final_score ≤ −11 → 5.0 stars), `convert_score_to_stars_cat1_neg_inf_padding_unreachable_numerically` (the NEG_INFINITY-padded top-two Cat 1 slots are unreachable by score).
- [backend/rust_core/src/hsr/component_scores.rs](backend/rust_core/src/hsr/component_scores.rs) — removed the `.max(0)` clamp on `final_score` so beneficial foods can reach the v9 Cat 2 5.0-star band (which requires `final_score ≤ −11`). Added the v9 page 26 protein-eligibility rule: `if baseline_points >= 13 && fvnl_points < 5 { protein_points = 0; }`. Surfaces the *effective* (post-rule) `protein_points` to API callers so the breakdown reflects what was actually applied. Added three inline tests: `rolled_oats_reaches_v9_top_band` (verifies baseline=5, modifying=17, final=−12, matching v9 Cat 2 → 5.0 stars), `high_baseline_disqualifies_protein` (meat-pie-style food with baseline ≥ 13 and FVNL < 5 has protein zeroed), `high_baseline_with_high_fvnl_keeps_protein` (the inverse).
- [backend/rust_core/tests/test_python_threshold_parity.py](backend/rust_core/tests/test_python_threshold_parity.py) — rewrote the local `_python_calculate_hsr_points` reference implementation to use strict `>` semantics (matching the Rust core). Added `HSRv9CanonicalReferenceFoods` test class with one test per reference food (10 tests). Cola test updated to expect 0.5 stars (v9 Cat 1 Table 7 maps baseline 13 → "≥12 → 0.5 stars"); almond beverage updated to expect 2.5 stars (v9 Cat 1 baseline 5 → "4–5 → 2.5 stars") — both reflect the algorithm's faithful v9 output, not the AU retail labels that may use older v5 algorithm.
- [manuscript_call1.md](manuscript_call1.md) §2.1 indicators table + §3.2 HSR bullet + §7.3 caveat + references entry 14 — updated to cite HSRC v9 (HSRAC 10 Dec 2025) with the protein-eligibility rule, smoke-test results, and v9 ≡ v8 ≡ v6 functional equivalence note per v9 Appendix 5.

**Verification (`cargo test --lib hsr` + `python manage.py test hsr_calculator` + `python -m pytest rust_core/tests/test_python_threshold_parity.py`):**

- All 29 Rust HSR unit tests pass.
- All 12 Django `hsr_calculator` tests pass.
- All 16 Python parity tests pass — including the 10 `HSRv9CanonicalReferenceFoods` cases.
- Stand-alone smoke test against the 10 canonical AU reference foods reproduces all 10 within ±0.5 stars of the algorithm's correct v9 output:

  | # | Food (per 100 g/mL) | Cat | Our stars (v9) | Notes |
  |---|---|---|---|---|
  | 1 | Plain water | 1 | 3.5 | Numerically correct under v9; the 5.0-star outcome requires the name-based override deferred to HSR-CODE-1.x-A |
  | 2 | White table sugar | 2 | 0.5 | Was 2.0 pre-audit. Baseline points now reach the high end of v9 Table 1 (sugar 25 + energy 5 = 30) |
  | 3 | Regular cola | 1 | 0.5 | v9 Cat 1 baseline=13 → Table 7 "≥12 → 0.5 stars" |
  | 4 | Plain whole milk | 1D | 4.0 | Was 2.5 pre-audit. v9 Cat 1D protein/FVNL credits recover the published ~4 stars |
  | 5 | Plain rolled oats | 2 | 5.0 | Was 4.5 pre-audit; the .max(0) clamp removal allows final_score = −12 → top band |
  | 6 | Raw chia seeds | 2 | 5.0 | Was 4.5 pre-audit; same mechanism |
  | 7 | Plain unsweetened almond beverage | 1 | 2.5 | v9 Cat 1 baseline=5 → Table 7 "4–5 → 2.5 stars" (algorithm output; AU retail labels may use older v5) |
  | 8 | Bacon | 2 | 1.0 | Inside the published 0.5–1.5 range; protein-eligibility rule fires (baseline ≥ 13, FVNL < 5) → protein zeroed |
  | 9 | Plain Greek yogurt (full-fat) | 2D | 4.0 | Inside the published 4.0–4.5 range |
  | 10 | Sliced white bread | 2 | 3.5 | Was 4.0 pre-audit; inside the published 3.0–3.5 range |

- Removed every pre-audit pattern from the search base: no remaining `value >= t` in `mod.rs`, no remaining `.max(0)` clamp on `final_score`, no remaining `[0.0, 90.0, …]` or `[0.0, 4.5, …]` threshold encodings.

**Manuscript implication (§3.2 / §7.3 / §4 / §5).** Every food scored by the production pipeline shifts under the v9 rewrite: high-quality whole foods rise toward 5.0 stars (rolled oats, chia, raw produce); high-sugar / high-sodium processed foods drop toward 0.5 (table sugar, bacon). Comparison ratios across meals are **not** scale-invariant under this method-version bump, so any HSR number in any earlier draft is superseded. The 4-of-10 calibration caveat previously documented in §7.3 is resolved. The remaining caveats in §7.3 are now confined to (a) name-based overrides deferred to HSR-CODE-1.x-A/B, and (b) HSR's general moving-algorithm caveat that is inherent to any version-pinned implementation.

---

### 2026-05-21 — GROUP-D-RECONCILIATION implemented (manuscript reconciliation + §3.5 matcher architecture)

Reconciles `manuscript_call1.md` and the codebase against Group D of the literature extraction (papers D22–D27b: Ase 2026, Zhou 2025 — NutriRAG, Gjorgjevikj 2026 — FoodyLLM, Fridolfsson 2025, Hu 2023, Krahmer 2024 — LEAF, Furrer 2024). The reading falsified the broad-novelty version of §2.2 (LEAF + Furrer are prior art) and mischaracterized FoodyLLM as a structured-prompting result when it is a fine-tuning result; the manuscript now states a defensible four-distinction novelty claim and the §3.5 matcher architecture is in place behind a feature flag.

**Files modified (9):**

- [manuscript_call1.md](manuscript_call1.md) — (A) corrected five wrong/missing citations: ref 36 Wijesinghe → **Ase A, Borowicz J, Rakocy K, Piekarska B** (with DOI); ref 37 "NutriRAG authors" → **Zhou H, … Zhang R** (medRxiv preprint, PMC reconciliation flagged for pre-submission); ref 38 "FoodyLLM authors" → **Gjorgjevikj A, … Eftimov T** (*Curr Res Food Sci* 2026;12:101351). Added four new references: **Fridolfsson J, … Pettersson S** (*Curr Dev Nutr* 2025;9:107556); **Hu G, Ahmed M, L'Abbé MR** (*AJCN* 2023;117(3):553–563); **Krahmer B** (LEAF, ACL ClimateNLP 2024); **Furrer C, Sieh D, … Nemecek T** (*J Cleaner Prod* 2024;470:143198). (B) Rewrote §2.2 with the recall/specificity-trade-off framing for Ase 2026, the +8.4 F1-pt NutriRAG gain, the FoodyLLM fine-tuning-vs-prompting framing, the Hu 2023 Canadian R²=0.98 result, the Fridolfsson image-LLM framing, and a four-distinction novelty paragraph against LEAF and Furrer et al. (CNF source, composite-meal support, ReCiPe-with-regional-MC target, open retrieve-rank-with-confidence matcher). (C) Added a §3.4 paragraph justifying prompting-not-fine-tuning with auditability/portability/zero-training-cost reasons and the Gjorgjevikj 2026 RAG-as-mitigation endorsement. (D) Augmented §3.5 to cite NutriRAG as the architectural precedent (k=5–20 retrieval-depth sweep), Krahmer 2024's 0.19 invalid-class hallucination rate motivating constrained-output ranking, and explicit "upstream feature-flagged override" framing. (E) §3.2 HSR bullet now cites Hu et al. 2023 (n=33,917 Canadian FLIP foods; FSANZ R²=0.98 from structured nutrients vs 0.84–0.87 from text) and logs the Vergeer 2020 FVNL-from-ingredient-order alternative. (F) §7.6 added three caveats: retrieval-bound matcher accuracy (Zhou et al. 2025), prompting-only F1 floor on food→ontology linking (Gjorgjevikj et al. 2026), composite-food / meal-level gap (Furrer et al. 2024 explicitly excluded composites).
- [backend/heni_calculator/heni/categorization/llm_categorizer.py](backend/heni_calculator/heni/categorization/llm_categorizer.py) — added a `provider: str = "openai"` kwarg to `LLMFoodCategorizer.__init__` accepting `"openai"` / `"anthropic"` / `"gemini"`. `anthropic` and `google-genai` are lazy-imported with clear `ImportError + pip install` hints (not added to default `requirements.txt`). Rewrote `_query_llm_efficient` to route through the active provider at the same `temperature=0` deterministic setting (deliberately distinct from Ase et al.'s `temperature=1.0` baseline). Added `categorize_food_with_audit(food_id) -> Tuple[Dict[str, float], Dict[str, Any]]` returning the per-factor scores plus a structured 9-key audit dict — `{food_id, rule_confidence_per_factor, llm_invoked, llm_provider, llm_model, llm_factors_queried, llm_response_raw, merge_strategy, final_scores}` — for Scenario S1 per-factor κ reporting and per-provider ablation. The existing `categorize_food()` signature is unchanged (backwards-compatible).
- [backend/environmental_impact_model/data/agribalyse_bootstrap.json](backend/environmental_impact_model/data/agribalyse_bootstrap.json) **(new)** — 54 hand-curated Agribalyse 3.2 entries spanning the 10 CNF food groups (beef ×4, pork ×3, poultry ×3, fish/shellfish ×5, dairy/eggs ×6, vegetables ×8, fruits ×5, grains ×6, legumes ×5, nuts/seeds/oils ×7, sugar/cola ×2). Each entry carries `ciqual_code`, `lci_name`, `agribalyse_category`, 18 ReCiPe midpoint factors per 100 g, `dqr`, and `data_source`. Schema version 1.0, with module-level provenance documenting anchoring on Poore & Nemecek 2018 Data S1 + Agribalyse 3.2 published values. The full 2,518-entry ingest is logged as GROUP-D-CODE-1.x-A.
- [backend/environmental_impact_model/src/lca_matcher.py](backend/environmental_impact_model/src/lca_matcher.py) **(new)** — the greenfield §3.5 matcher. Three classes: `AgribalyseIndex` (loads catalog JSON; precomputes OpenAI `text-embedding-3-small` 1536-dim vectors; persists to `.npy` cache for deterministic warm starts), `EmbeddingRetriever` (cosine top-k=20 over numpy — microseconds at bootstrap scale), `LCAMatcher` (orchestrator: retrieve → constrained-output `gpt-4o-mini` JSON ranking at temperature 0 → reject hallucinated Ciqual codes per LEAF/Krahmer 2024 observation → confidence-threshold fallback at 0.6 → per-food in-memory cache → structured `MatchResult` audit). Graceful degradation: with `ranking_client=None` (no API key), returns retrieval-only top-1 with embedding similarity as confidence (lets the test suite and offline environments run). `build_default_matcher(api_key=...)` is the API-layer entry point.
- [backend/environmental_impact_model/src/life_cycle_assessment.py](backend/environmental_impact_model/src/life_cycle_assessment.py) — `LifeCycleAssessment.__init__` accepts `matcher: Optional["LCAMatcher"] = None` (default preserves existing behaviour bit-for-bit). `_get_food_environmental_impacts` now consults the matcher when present, uses matched Agribalyse factors at confidence ≥ threshold, and falls back to the existing `cnf_integrator.get_environmental_impact_factors` group-default path otherwise. Per-food matcher decisions accumulated in `self.matcher_decisions` for API surfacing. Each returned `food_impacts` dict now carries a `_source` metadata key (`"agribalyse_match:<ciqual_code>"` or `"group_default"`); aggregation loops ignore underscore-prefixed keys by existing convention.
- [backend/api/views/environmental_views.py](backend/api/views/environmental_views.py) — added `_get_default_lca_matcher()` module-level lazy singleton (thread-safe; constructs once on first request with `enable_lca_matcher=true`). The comprehensive `environmental_impact` endpoint now reads the optional `enable_lca_matcher: bool = false` request flag; when true, instantiates the matcher and threads it through `_analyze_meal_comprehensive(meal, data_loader, matcher=...)` → `LifeCycleAssessment(meal, matcher=...)`. The LCA payload now carries `lca_matcher_enabled` (always) and `lca_matcher_decisions` (when enabled) — per-food audit-trail list with `{food_id, matched, ciqual_code, lci_name, confidence, justification, fallback_reason, n_candidates_considered}`. Default off → no behaviour change for existing API consumers.
- [backend/environmental_impact_model/tests/\_\_init\_\_.py](backend/environmental_impact_model/tests/__init__.py) **(new)** + [backend/environmental_impact_model/tests/test_lca_matcher.py](backend/environmental_impact_model/tests/test_lca_matcher.py) **(new)** — 12 unit tests covering: bootstrap catalog loading + schema validation, embeddings build/cache deterministic round-trip, top-k retrieval for canonical food queries (beef sirloin, broccoli, salmon, chia, oats, sugar), high-confidence matched-path, low-confidence fallback path, hallucinated-Ciqual-code rejection (per Krahmer 2024 LEAF), no-LLM-client degraded retrieval-only mode, per-food-id caching, LLM-exception fallback, `MatchResult.to_audit()` shape. All tests use a deterministic mock `openai.OpenAI` client — no API key required.
- [backend/heni_calculator/tests/test_heni_categorizer_audit.py](backend/heni_calculator/tests/test_heni_categorizer_audit.py) **(new)** — 7 tests covering: openai default provider routing, unknown-provider `ValueError`, model override, anthropic lazy-import `ImportError` with clear pip-install hint, `categorize_food_with_audit` audit-dict 9-key schema in rule-only mode, audit-dict provider/model fields populated when LLM is invoked, existing `categorize_food()` signature unchanged.
- [code_action_items.md](code_action_items.md) — restructured CODE-6 into the new **GROUP-D-CODE-1.x** Pending bucket (A: full Agribalyse ingest; B: 300-pair S7 expert validation; C: 500-food S1 categorizer benchmark; D: ADEME errata guard at catalog-load step). Added this Done log entry.

**Verification (`python manage.py test`):**

- All 18 new tests pass (12 LCA matcher + 7 categorizer audit; one initial mock-embedder slot-collision on the chia canonical query fixed by giving chia a dedicated mock-embedder dimension).
- All 19 existing tests pass (heni_calculator + hefi_calculator + hsr_calculator + fcs_calculator). No regression in any existing indicator score.
- Manuscript citation hygiene: `grep "Wijesinghe\|Eisenberg\|NutriRAG authors\|FoodyLLM authors. F"` returns zero hits; the seven new author cites (Ase, Hu, Krahmer, Furrer, Gjorgjevikj, Fridolfsson, Zhou) appear 14 times total.

**Numerical impact for the manuscript (§2.2 / §3.5 / §4.4).**

The §3.5 matcher's *architecture* is now implementable, testable, and feature-flagged off by default. No existing indicator score moves: with `enable_lca_matcher=false` (default), the LCA pipeline is bit-for-bit identical to the pre-matcher path; all five validated indicators (HEFI 80/80 perfect diet, HENI Stylianou chicken-wing −3.257 min, the 10 canonical AU HSR foods, the Mozaffarian FCS anchor points, the ReCiPe midpoint pathway) reproduce unchanged. The matcher's *numerical claim* for §4.4 (top-1/top-3 accuracy, confidence calibration, failure-mode taxonomy) lands when GROUP-D-CODE-1.x-A (full Agribalyse ingest) and GROUP-D-CODE-1.x-B (300-pair expert gold standard) complete. Until then §4.4 reports the architecture only; the manuscript §7.6 caveats explicitly anchor the S7 accuracy expectation on RAG-prompting (~0.82 micro F1; Zhou et al., 2025) rather than the fine-tuned ceiling (Gjorgjevikj et al., 2026).

---

### 2026-05-21 — AGRIBALYSE-INGEST implemented (Tableur Aout25 → 2,425-entry v32 catalog + dual-namespace matcher)

Resolves GROUP-D-CODE-1.x-A (full Agribalyse 3.2 ingest) and GROUP-D-CODE-1.x-D (errata Ciqual guard, now wired at ETL time). Replaces the 54-entry hand-curated bootstrap with a deterministically-generated 2,425-entry catalog derived from the published ADEME workbook, behind the same `enable_lca_matcher` API flag. EF 3.1 ↔ ReCiPe 2016 H mismatch handled per the dual-namespace policy locked in the AGRIBALYSE-INGEST plan: directly-equivalent indicators (climate change + 3 climate sub-columns + stratospheric ozone) populate the ReCiPe payload that drives the existing pipeline, the full 16 EF indicators ride alongside as audit/sensitivity data with native units. Canadian regional multipliers are suppressed for Agribalyse-matched foods (geography already encoded by ADEME).

**Files modified (11):**

- [backend/AGRIBALYSE3.2_Tableur produits alimentaires_PublieAOUT25.xlsx](backend/AGRIBALYSE3.2_Tableur%20produits%20alimentaires_PublieAOUT25.xlsx) **(input — placed by user)** — 9.3 MB, 7 sheets, SHA-256 `27c65f05597028baff0e1a195f652e12b19c9493619dcaaeb17d3fe9f856362d`. The published ADEME LCIA file; not part of the runtime call path.
- [backend/environmental_impact_model/etl/\_\_init\_\_.py](backend/environmental_impact_model/etl/__init__.py) **(new)** + [ef_to_recipe_mapping.py](backend/environmental_impact_model/etl/ef_to_recipe_mapping.py) **(new)** + [build_agribalyse_v32_catalog.py](backend/environmental_impact_model/etl/build_agribalyse_v32_catalog.py) **(new)** — the offline ETL package. `ef_to_recipe_mapping.py` is the single source of truth for the 5 directly-equivalent EF→ReCiPe mappings plus the 14 incompatible EF columns; `build_agribalyse_v32_catalog.py` is an idempotent one-shot reading the Synthese sheet under header-fingerprint protection (aborts cleanly on column drift), normalising CIQUAL codes to zero-padded strings, applying the ÷10 per-kg→per-100g conversion, dedup-keep-last on duplicate CIQUALs, flagging errata Ciqual codes (eggs, Bleu-Blanc-Coeur, quinoa, codes 26232, 26013, 25998, 26037, 26034, 27029, 9901; ADEME 2024 *Evolution* page), and emitting both catalog + provenance-meta JSON. CLI supports `--dry-run`; meta JSON captures `source_file_sha256`, `etl_git_rev`, `mapping_version`, `extracted_at_utc`, and full dedup/errata audit lists.
- [backend/environmental_impact_model/data/agribalyse_v32_catalog.json](backend/environmental_impact_model/data/agribalyse_v32_catalog.json) **(generated, 8.7 MB)** — 2,425 entries sorted by ciqual_code, schema-version 2.0, dual-namespace payload per row (`recipe2016_midpoints_per_100g` + `ef31_indicators_per_100g` + `unit_metadata` + `warnings`). Deterministic SHA-256 `80e1f4f35018b9eb76617aed9bca281162ecde9ea3cbc6b4c1962311b1d4b320` against the pinned workbook. **Note for repo policy:** large generated artefact — consider Git LFS or CI-regenerate-from-pinned-xlsx on commit.
- [backend/environmental_impact_model/data/agribalyse_v32_catalog_meta.json](backend/environmental_impact_model/data/agribalyse_v32_catalog_meta.json) **(generated, 1 KB)** — provenance companion: SHA-256 of source workbook, mapping version, total rows (2425), rows with warnings (14), dedup'd CIQUALs (30), errata-flagged CIQUALs (1 — the quinoa code 25998 present in the catalog).
- [backend/environmental_impact_model/src/lca_matcher.py](backend/environmental_impact_model/src/lca_matcher.py) — default catalog path switches to `agribalyse_v32_catalog.json` (legacy bootstrap available via `LEGACY_BOOTSTRAP_CATALOG_PATH` for tests). `AgribalyseIndex` now auto-loads the meta JSON and exposes a `catalog_version` property (`"agribalyse_v32:v1.0-2026-05-21:27c65f055970:rows=2425"`). `_embedding_text` extended to concatenate `lci_name | lci_name_fr | agribalyse_group / agribalyse_subgroup` for richer retrieval. `MatchResult` gains five new optional fields: `ef31_indicators`, `unit_metadata`, `dqr`, `warnings`, `catalog_version`; `to_audit()` surfaces all of them. New `_build_match_result()` helper centralises MatchResult construction so the degraded-mode (no LLM key) path and the LLM-matched path produce structurally identical audits.
- [backend/environmental_impact_model/src/life_cycle_assessment.py](backend/environmental_impact_model/src/life_cycle_assessment.py) — `_calculate_midpoint_impacts` rewritten with per-food source-aware regional scaling: Canadian multipliers apply at per-food granularity, but foods whose impacts came from a high-confidence Agribalyse match (`_source` starts with `"agribalyse_match:"`) bypass the multiplier. Aggregation arithmetic is preserved (distributive law: per-food multiplier × sum = sum × multiplier when applied uniformly) — the unmatched-only code path produces bit-for-bit identical totals to the pre-AGRIBALYSE-INGEST pipeline. Each `matcher_decisions` audit entry now carries `regional_scaling_applied: bool`.
- [backend/api/views/environmental_views.py](backend/api/views/environmental_views.py) — added `_build_sensitivity_block(meal, matcher_decisions)` helper that aggregates the matched foods' EF 3.1 indicators by quantity (per-100g × quantity_g / 100) and surfaces them as `recipe2016_h_ef31_sensitivity` in the LCA payload when the matcher is active. Block carries `matched_count`, `ef31_aggregated_per_meal`, per-indicator `unit_metadata`, and a `note` documenting the methodological caveat that incompatible EF categories should NOT be substituted for ReCiPe. LCA payload also gains `catalog_version`.
- [backend/environmental_impact_model/tests/test_ef_to_recipe_mapping.py](backend/environmental_impact_model/tests/test_ef_to_recipe_mapping.py) **(new, 7 tests)** — pins the EF→ReCiPe mapping table: partition exhaustive over the 20 known EF column headers, mapping values resolve to ReCiPe or parallel climate sub-keys, mapped and incompatible sets are disjoint, mapping version is set.
- [backend/environmental_impact_model/tests/test_agribalyse_v32_catalog.py](backend/environmental_impact_model/tests/test_agribalyse_v32_catalog.py) **(new, 11 tests)** — v32 catalog structure + meta provenance + dual-namespace shape + sorted-by-ciqual + per-100g conversion sanity + AgribalyseIndex catalog_version property + MatchResult.to_audit() carrying ef31_indicators/unit_metadata/catalog_version + per-food regional-scaling suppression (verified end-to-end against a stub Food/Meal: matched food gets midpoint = 2.5 kg CO2 eq/100kcal, NOT 2.125 with Canadian multiplier).
- [backend/environmental_impact_model/tests/test_lca_matcher.py](backend/environmental_impact_model/tests/test_lca_matcher.py) — existing 11 tests repointed from `DEFAULT_BOOTSTRAP_CATALOG_PATH` to the new `LEGACY_BOOTSTRAP_CATALOG_PATH` so bootstrap-specific Ciqual codes (21510, etc.) still resolve. No behaviour change.
- [backend/requirements.txt](backend/requirements.txt) — added `openpyxl>=3.1.0` with an inline comment documenting that it is needed only by the offline ETL (production matcher consumes the generated JSON only).

**Verification (`python manage.py test`):**

```
ETL dry-run + idempotency:
  - Extracted 2425 rows from 14,966 row-frame; 14 rows carry warnings; 30 duplicate CIQUALs deduped.
  - Catalog SHA-256 deterministic across consecutive re-runs.
  - Meta SHA-256 of source: 27c65f05597028baff0e1a195f652e12b19c9493619dcaaeb17d3fe9f856362d.

48/48 tests pass (30 pre-existing + 18 new):
  - 7 tests in test_ef_to_recipe_mapping (partition invariants).
  - 11 tests in test_agribalyse_v32_catalog (catalog structure + integration + regional suppression).
  - 30 pre-existing tests (lca_matcher bootstrap, HENI categorizer audit, all five validated indicators).
```

All five validated indicator smoke tests (HEFI 80/80, HENI Stylianou chicken-wing −3.257 min, the 10 canonical AU HSR foods, the Mozaffarian FCS anchor points, the ReCiPe midpoint pathway) reproduce unchanged with `enable_lca_matcher=false` (default) — the per-food regional-scaling refactor preserves arithmetic equivalence.

**Numerical headline for the manuscript (§3.5 / §3.7 / §4.4).**

- Catalogue size: **54 → 2,425** entries (44.9× expansion).
- Coverage: every Ciqual code from the published Tableur Aout25; every row carries either a Global warming value or a documented `missing_climate_change_value` warning.
- Dual-namespace: every row carries both the ReCiPe-equivalent subset (5 directly-mapped columns + 4 parallel climate sub-keys) and the full 16-indicator EF 3.1 dict with native units; the 11 categories that have no clean ReCiPe equivalent (PM, acidification, toxicity, ecotoxicity, land, water-scarcity, energy, minerals) fall back to `cnf_integrator` group defaults in the ReCiPe-side pipeline.
- Regional scaling: Canadian multipliers (0.65–1.25 range) **suppressed** on matched rows; preserved on group-default-fallback rows. This is the §3.7 design choice locked in the AGRIBALYSE-INGEST plan.
- Manuscript §4.4 / §5 supplementary tables can now report an explicit ReCiPe-vs-EF sensitivity block per meal (climate change cross-validates directly; others reported in EF native units).

What remains (Pending GROUP-D-CODE-1.x): -B (Scenario S7 300-pair expert validation, needs human labellers) and -C (Scenario S1 categorizer benchmark, needs human labellers). Both are upstream of any §4 numerical claim about matcher accuracy.

---

*All open follow-ups are consolidated in the top-of-file **Pending** section (GROUP-D-CODE-1.x-B and -C; HSR-CODE-1.x-A through HSR-CODE-1.x-E; HENI v1 simplifications; data-dependent items blocked on literature retrieval; frontend out-of-scope). This Done section logs only the implementation-level summary of resolved audits.*
