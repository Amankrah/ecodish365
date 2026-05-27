# `ecodish365` — Validation & Case-Study Scenarios for Call 1 Manuscript

**Companion to** `manuscript_call1.md`.
**Purpose:** Define each runnable scenario, its inputs, methods, outputs, success criteria, and rough effort. Numbers in `[brackets]` are estimates to be confirmed once we begin the run.

---

## Conventions

- **Run ID**: `S<n>` matches the section number in the manuscript.
- **Inputs**: list of code modules, datasets, parameters.
- **Outputs**: tables/figures with manuscript references.
- **Random seed**: fix `seed = 20260520` everywhere unless noted.
- **Hardware target**: single workstation (Linux, 16-core, 64 GB RAM). All scenarios must run in under 24 h on this machine.
- **Reproducibility**: every scenario produces a `results/S<n>/run_manifest.json` capturing git SHA, package versions, CNF version, and prompt/template hashes.

---

## S1 — LLM risk-factor categorizer benchmark *(AI subsystem 1)*

### Goal
Quantify the accuracy of the hybrid rule+LLM categorizer that maps CNF foods to 14 GBD risk factors, against an expert gold standard.

### Inputs
- CNF 2015 (already in repo).
- Code: [`backend/heni_calculator/heni/categorization/rule_based_categorizer.py`](backend/heni_calculator/heni/categorization/rule_based_categorizer.py), [`llm_categorizer.py`](backend/heni_calculator/heni/categorization/llm_categorizer.py).
- LLM: `gpt-4o-mini`, `temperature=0`, `max_tokens=150` (current) **plus** a `claude-haiku-4-5` head-to-head ablation.

### Sample
- Stratified random sample of **n = 500** CNF foods across all food groups, with quota by group proportional to within-group CNF count, capped at 50 per group.
- **Two registered dietitians** independently label each food on all 14 factors using a 0/0.5/1 ordinal scale. Inter-rater Cohen's κ reported per factor; disagreements adjudicated by a third reviewer.

### Conditions compared
1. **Rule-only** baseline.
2. **LLM-only** (skip rule output in prompt).
3. **Rule+LLM hybrid** (current implementation).
4. **Rule+LLM with full-context prompt** (all 14 factors at once, ablation).
5. **Different LLMs**: `gpt-4o-mini` vs `claude-haiku-4-5`.

### Metrics
- Per-factor precision, recall, F1 (binary at score ≥ 0.5).
- Macro- and micro-F1.
- Confusion patterns per food group.
- Cost ($/1 000 foods), tokens, latency p50/p95.
- LLM-invocation rate (fraction of foods triggering an LLM call).

### Outputs
- `results/S1/table1_per_factor.csv` → Table 2 in §4.1.
- `results/S1/fig_cost_accuracy.pdf` → Figure 2.
- `results/S1/error_taxonomy.md` → SI §A.

### Effort
~2 weeks: 3 days labelling logistics, 1 week labelling, 2 days adjudication, 4 days code & figures.

### Success criterion
Hybrid F1 ≥ 0.80 macro on majority of factors *and* cost ≤ $0.50 / 1 000 foods. If not met, refine prompt or escalate model and document in §6.1.

---

## S2 — LCA factor cross-validation *(addresses reviewer concern on hardcoded factors)*

### Goal
Quantify the deviation between `ecodish365`'s per-food-group LCA factors ([`cnf_integrator.py:get_environmental_impact_factors`](backend/environmental_impact_model/src/cnf_integrator.py#L259)) and peer-reviewed inventories.

### Inputs
- `ecodish365` factors (current code).
- Agribalyse 3.2 (acquire via ADEME licence; cite documentation).
- Poore & Nemecek 2018 supplementary dataset (open).
- WFLDB 3.5 group-level statistics where available.

### Method
1. For each of the 10 CNF food groups, identify 3–5 Agribalyse representative entries (vetted by domain expert).
2. Aggregate Agribalyse entries to a group mean weighted by Canadian consumption (CCHS).
3. Compute mean absolute relative error (MARE) per impact category: GWP, land use, water consumption, freshwater eutrophication (P), marine eutrophication (N), terrestrial acidification.
4. Bland–Altman plots per category.
5. Where MARE > 30 %, update factor with documented Agribalyse-derived value; record the change in a `changelog_factors.md`.

### Outputs
- `results/S2/mare_table.csv` → Table 3.
- `results/S2/bland_altman_*.pdf` → SI §B.
- Updated factor table → SI §C.

### Effort
~3 weeks (Agribalyse licence acquisition, mapping, code).

### Success criterion
After updates: median MARE ≤ 25 % across the six headline categories.

---

## S3 — Monte Carlo uncertainty + Sobol sensitivity

### Goal
Quantify confidence intervals on per-meal LCA outputs and identify which factor groups drive output variance.

### Inputs
- Updated factor table from S2.
- σ_g (geometric SD) per factor from Poore & Nemecek 10th–90th percentile range; fall back to ecoinvent pedigree-matrix defaults where unavailable.
- 100-meal panel from S4.

### Method
1. Sample N = 10 000 draws per meal from joint factor distribution (independent log-normal, with documented correlations between GWP and land use within ruminants).
2. Report median and 5–95 % CIs per midpoint, per endpoint and single-score.
3. Compute first- and total-order Sobol indices with SALib (`saltelli` sampler, N = 1024, hence 14 × 1024 model evaluations per meal).

### Outputs
- `results/S3/ci_per_meal.csv` → SI §E.
- `results/S3/fig_sobol.pdf` → Figure 3.
- `results/S3/ci_violin.pdf` → Figure 4.

### Effort
~1.5 weeks (engineering + runs).

### Success criterion
Single-score 5–95 % CI width ≤ ±60 % of median for ≥ 80 % of meals; Sobol indices sum within ±0.05 of 1.0.

---

## S4 — 100 representative Canadian meals *(case study)*

### Goal
Score 100 typical Canadian meals across all five indicators + monetised externalities, exposing trade-offs.

### Inputs
- 2015 CCHS–Nutrition 24-hour recall (acquire via Statistics Canada Research Data Centre — confirm McGill RDC access).
- Stratification: meal occasion × age band × sex × deprivation quintile.

### Method
1. Cluster CCHS meal records (k-medoids on nutrient/CNF-foodID composition).
2. Sample 100 medoids covering the full distribution.
3. Score each across HEFI, HENI, HSR, FCS, LCA midpoints+endpoints+single-score, and monetised externalities in CAD.
4. Report mean ± SD, pairwise Spearman correlations, PCA biplot, and a Pareto frontier in (HENI, –LCA single score) space.

### Outputs
- `results/S4/meals_panel.csv` → SI §F.
- `results/S4/fig_corr_heatmap.pdf` → Figure 5.
- `results/S4/fig_pca_biplot.pdf` → Figure 6.
- `results/S4/fig_pareto.pdf` → Figure 7.

### Effort
2–3 weeks pending RDC access. **S4-lite interim (2026-05-26):** 25-day curated panel shipped without RDC — see [`backend/_smoke_s4_lite_panel.py`](backend/_smoke_s4_lite_panel.py) and [`results/S4-lite/`](results/S4-lite/). If RDC is blocked, extend S4-lite or document as primary case study (limitation: not CCHS-representative).

### Success criterion
Reproduce the qualitative weak-correlation finding of Stylianou et al. between nutritional and environmental indicators. **S4-lite partial pass:** nutrition–GW Spearman ρ = −0.42 to −0.59 across 25 days; full Pareto frontier awaits 100-meal panel.

---

## S5 — Diet-shift counterfactual scenarios

### Goal
Quantify per-100-g (or per-serving) Δ across indicators for four substitutions.

### Substitutions
1. Beef (CNF FoodGroupName "Beef Products") → legumes (lentils, beans).
2. Cow's milk → fortified soy beverage.
3. Sugar-sweetened beverage (cola) → tap water.
4. Refined grains (white bread) → whole grains (whole-wheat bread).

### Method
For each substitution and each S4 meal that contains the swapped item:
1. Re-compute all indicators.
2. Report Δ in HEFI, HENI (μDALY), HSR, FCS, LCA single-score, monetised externalities (CAD).
3. Stratify by demographic.

### Outputs
- `results/S5/delta_table.csv` → Table 4.
- `results/S5/fig_radar_substitutions.pdf` → Figure 8.

### Effort
~1 week (after S4).

### Success criterion
All deltas reproducible; substitution 1 (beef→legumes) and 3 (SSB→water) should yield positive HENI and negative LCA single-score (i.e. win-win).

---

## S6 — Canadian regional-adaptation impact

### Goal
Quantify how the documented Canadian regional factors (replacing the current hand-tuned ones) change indicator outputs and meal rankings.

### Method
1. Run S4 panel twice: with Canadian factors, and with European defaults.
2. Report ΔLCA single-score per meal; Kendall's τ between rankings.
3. Identify impact categories where the choice changes the sign of the trade-off.

### Outputs
- `results/S6/regional_delta.csv`.
- `results/S6/fig_ranking_change.pdf` → Figure 9.

### Effort
~3 days.

### Success criterion
Adaptation alters single-score by < 20 % for the median meal but can flip rankings for ~10 % of meals (expected; we report transparently).

---

## S7 — LLM food-to-LCA matcher accuracy *(AI subsystem 2)*

### Goal
Validate the new retrieval-augmented LLM matcher that links CNF foods to Agribalyse entries (replaces hardcoded group means with item-level matches).

### Sample
- n = 300 CNF foods stratified by food group.
- Expert ground-truth Agribalyse mapping by one LCA-trained reviewer.

### Method
1. Build embedding index of Agribalyse descriptions (`text-embedding-3-small` baseline; `bge-large` ablation).
2. Retrieve top-10 candidates per CNF food.
3. LLM ranks candidates with reasoning + 0–1 confidence.
4. Report top-1 and top-3 accuracy; calibration curve of confidence vs accuracy; failure-mode taxonomy.

### Outputs
- `results/S7/match_eval.csv` → Table 5.
- `results/S7/fig_calibration.pdf` → Figure 10.
- `results/S7/failure_modes.md` → SI §G.

### Effort
~3 weeks (build + benchmark).

### Success criterion
Top-3 accuracy ≥ 0.80; calibration ECE ≤ 0.10.

---

## S8 — Sustainability of the AI pipeline itself

### Goal
Report the per-meal AI inference footprint (compute, energy, water, CAD cost) to satisfy "AI as part of the system under evaluation".

### Method
1. Instrument the categorizer and matcher to log tokens (input/output) and wall-clock latency.
2. Convert tokens → kWh via published model energy intensities (e.g. ~3 Wh / 1 k tokens for GPT-4-class as of 2025; cite McGill paper TBD).
3. kWh → CO₂e via Quebec / Ontario / Alberta grid intensities (sensitivity).
4. kWh → water via hyperscaler PUE+WUE figures.
5. Cost in CAD at current per-token list price.

### Outputs
- `results/S8/ai_footprint.csv` → Table 6.
- `results/S8/fig_ai_vs_meal.pdf` → Figure 11 (AI footprint as a fraction of the meal's own LCA).

### Effort
~1 week.

### Success criterion
Pipeline AI footprint per meal < 0.1 % of the meal's LCA single-score (expected; documents the bounded role of AI).

---

## Cross-scenario summary table

| Scenario | Depends on | Wall-clock | Manuscript section | Output figures/tables |
|---|---|---|---|---|
| S1 LLM categorizer benchmark | – | 2 wk | §4.1 | T2, F2 |
| S2 LCA cross-validation | Agribalyse licence | 3 wk | §4.2 | T3 |
| S3 MC + Sobol | S2 + S4 | 1.5 wk | §4.3 | F3, F4 |
| S4 Meal panel | RDC access | 2–3 wk | §5.1 | F5, F6, F7 |
| S5 Diet shifts | S4 | 1 wk | §5.2 | T4, F8 |
| S6 Regional adaptation | S4 | 3 d | §5.3 | F9 |
| S7 Food-to-LCA matcher | – | 3 wk | §4.4 | T5, F10 |
| S8 AI footprint | S1, S7 | 1 wk | §5.5 | T6, F11 |

**Critical path:** Agribalyse licence (S2) and RDC access (S4) — both should be initiated within week 1. Total realistic duration assuming licences arrive on time and one researcher full-time + one part-time: **~10–12 weeks**. With a deadline of 30 September 2026, starting now (May 2026) gives ample buffer.

---

## Risk register

| Risk | Mitigation |
|---|---|
| Agribalyse licence delay | Fall back to Poore & Nemecek 2018 supplementary dataset (open); document the licence gap. |
| RDC access delay | Synthetic meal panel from CFG-2019 + CNF; clearly framed as illustrative. |
| Expert labelling capacity | Pre-train labelling rubric; use third dietitian only for tie-breaks. |
| LLM model deprecation | Pin model version; archive prompts and example I/O; ablation across two providers (OpenAI + Anthropic). |
| Monetary factor sources weak | Replace `consultation` references with citable values; mark surviving low-confidence factors. |

---

## Required Canadian data dependencies (Group B surfaced)

The HEFI-2019 scoring algorithm (Brassard et al., 2022a) needs **two external Canadian databases that are NOT in the base CNF 2015**:

1. **Health Canada Table of Reference Amounts for Food (2016).** Required because all five food-based HEFI-2019 components (V&F, whole grains, grain-foods ratio, protein, plant-based protein) are scored in Reference Amounts (RAs), not grams or volumes. **Action:** confirm acquisition; placeholder reference Health Canada (2016).
2. **Rana et al. 2021 free-sugars supplement to CNF 2015.** Required because the base CNF carries total sugars but not free sugars; HEFI-2019 component 9 (free sugars / energy %) cannot be computed without it. Reference: Rana H, Mallet M-C, Gonzalez A, Verreault M-F, St-Pierre S. *Free sugars consumption in Canada.* Nutrients. 2021;13(5):1471. doi:10.3390/nu13051471. **Action:** verify the supplementary dataset is publicly downloadable; if not, contact corresponding author or Health Canada.

Both dependencies block any HEFI-2019 results in S4/S5. If Rana 2021 cannot be acquired in time, fall back to total sugars with a documented warning, and report HEFI-2019 component 9 as an approximation only.
