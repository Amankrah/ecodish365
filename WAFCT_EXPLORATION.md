# WAFCT 2019 — exploration study + integration recommendation

*Status: WAFCT-EXPLORE 2026-05-24 — read-only inventory + per-100g empirical comparison vs CNF. No integration code yet; recommendation memo only.*

## Executive summary

- **WAFCT 2019** (FAO / Bioversity / CIRAD West African Food Composition Table, [`backend/raw_wafct/WAFCT_2019.xlsx`](backend/raw_wafct/WAFCT_2019.xlsx)) contains **1,028 foods** across **14 food groups** with **39 + 57 nutrient sets per 100 g edible portion**, plus 195 canonical mixed-dish recipes, 440 yield factors, 61 retention-factor combinations, 90.9 % FoodEx2 coverage, and 467 bibliographic sources. Encoding is clean UTF-8.
- **Nutrient axis (WAFCT ↔ CNF):** 47 of 57 INFOODS tagnames map cleanly to CNF NutrientName keys (82.5 % bridge coverage). The 10 unmapped tags are WAFCT-only metadata (`EDIBLE1/2`, `SOP`, `XFA`, `XN`) or anti-nutrients (`PHYTCPP`, `IP3-6`) — none block scoring.
- **Per-100g empirical comparison (9 paired foods):** macronutrients agree well (median |Δ%| ≤ 13 % across Energy / Water / Protein / Fat / Carbs / Fibre — no systematic bias). **Minerals show a consistent WAFCT-higher bias**: Ca +23.5 %, Fe +67.7 %, Mg +15.6 %, K +10.8 %. This is the headline empirical finding.
- **The gap WAFCT closes:** 7 of 7 region-specific WAFCT foods sampled (fonio, baobab leaves, dawadawa, gari, egusi, lafun, pearl millet) have **no CNF equivalent at all**. For users in West Africa scoring jollof rice / baobab-leaf sauce / fonio porridge against HEFI / HENI / FCS, WAFCT goes from "0 % coverage" to "full coverage of staples". The integration's user-value-add is enormous.
- **Recommended integration architecture: Option B — WAFCT-as-extension** with a `source` column added. Pack WAFCT foods into the existing CNF schema using FoodIDs offset by 700 000+, translate INFOODS tags to CNF NutrientName keys at ingest, add a `source ∈ {cnf, wafct}` column for provenance + per-database filtering. Lowest risk to the scoring stack; preserves provenance; lets users opt into either or both databases via a UI filter.

## How this study was run

Two read-only harnesses + this memo:

1. [`backend/_explore_wafct.py`](backend/_explore_wafct.py) — structure inspector. Loads all 12 sheets via `openpyxl`, dumps a 104 KB JSON inventory + console summary. No Django, no LLM, no network. Output: [`backend/_explore_wafct_structure.json`](backend/_explore_wafct_structure.json).
2. [`backend/_explore_wafct_vs_cnf_per100g.py`](backend/_explore_wafct_vs_cnf_per100g.py) — per-100g delta study. Hand-curated 16-food panel across 3 sub-classes. Loads WAFCT + the existing CNF pipeline ([`backend/api/cnf_cache.py`](backend/api/cnf_cache.py) `get_api_cnf_pipeline()`). Output: [`backend/_explore_wafct_vs_cnf_per100g_results.json`](backend/_explore_wafct_vs_cnf_per100g_results.json).

Both harnesses are re-runnable; the comparison panel is hand-curated (deterministic, no LLM matcher) so re-runs are bit-identical.

## 1. WAFCT structural overview

### 12 sheets at a glance

| # | Sheet | What it is | Rows | Key field |
|---|---|---|---|---|
| 01 | Introduction | Title + author list + licensing URL | ~46 lines | "FAO/INFOODS Food Composition Table for Western Africa (2019)" |
| 02 | Components | **Canonical INFOODS tagname dictionary** | 59 components | tag → (label EN/FR, unit, denominator, method) |
| 03 | NV_sum_39 | **Primary nutrient table per 100g EP** | **1,028 foods × 39 nutrients** | Code, EN/FR names, scientific name, BiblioID, 39 nutrient cols |
| 04 | NV_stat_39 | Statistics (mean/SD/n) for 39-set | 1,028 stat rows | parity with sheet 03 |
| 05 | NV_sum_57 | Extended 57-nutrient table | 1,028 foods × 58 cols | adds ALC, CARTA, CARTB, CRYPXB, EDIBLE2, FOLAC, FOLFD, **IP3-6, PHYTCPP**, SOP, TOCPHA-D, XFA, XN |
| 06 | NV_stat_57 | Statistics for 57-set | 1,028 stat rows | — |
| 07 | Yield factors | Raw → cooked weight change | 440 foods | range [0.57, 7.3], mean 1.76 |
| 08 | Retention factors | % nutrient retained through cooking | 61 combos × 20 nutrients | Ca, Fe, Mg, P, K, Na, Zn, Cu, vits A/D/E/B1-12/C, Phytate, IP6 |
| 09 | **Mixed dishes** | **Canonical composite recipes (ingredient lists)** | **195 recipes, 1,512 ingredient rows, avg 7.75 ings/recipe** | Cross-referenced by WAFCT Code |
| 10 | FoodEx2 codes | EFSA classification mapping | 934 / 1027 = **90.9 % coverage**; 633 = 61.6 % "Exact Match" | Bridge to European food taxonomy |
| 11 | 2012 vs 2019 | Version-mapping table | 491 rows | for cross-citation |
| 12 | Data sources | Bibliography | 467 entries | per-food provenance |

### 14 food groups (sheet 03 banding rows)

| Code | Group (EN) | Foods |
|---|---|---|
| 01 | Cereals and their products | **183** |
| 02 | Starchy roots, tubers and their products | 96 |
| 03 | Legumes and their products | 137 |
| 04 | Vegetables and their products | 132 |
| 05 | Fruits and their products | 53 |
| 06 | Nuts, seeds and their products | 34 |
| 07 | Meat, poultry and their products | 128 |
| 08 | Eggs and their products | 14 |
| 09 | Fish and its products | 106 |
| 10 | Milk and its products | 27 |
| 11 | Fats and oils | 35 |
| 12 | Beverages | 24 |
| 13 | Miscellaneous | 25 |
| 14 | Soups and sauces | 34 |

Cereals + legumes + vegetables + meat together = 580 foods (56 % of the table) — typical of a regional composition table emphasising staples.

### Encoding sanity

All 1,028 food rows scanned for U+FFFD replacement characters in English/French names + group banding labels: **0 mojibake**. The file is clean UTF-8. The cp1252-rendering artefacts seen during initial exploration are a *console-display* issue (Windows cp1252 stdout) and not data corruption.

### Sheet 09 — mixed dishes are STRUCTURED, not free-text

This is the most pleasant surprise of the exploration. Sheet 09 contains 195 canonical West African recipes (`Baling béinré`, `Foutou`, `Fonio porridge`, …) where each ingredient row carries:

```
Observation #  Code      Ingredient name                              Weight
1              01_072    Sorghum, flour, degermed                     56 g
               05_021    Tamarind, fruit, ripe, raw                   24 g
               05_004    Baobab, fruit/monkey bread, raw               5 g
               10_017    Milk, cow, powder, skimmed, unfortified      30 g
               13_002    Sugar, white                                  35 g
```

**Ingredient codes are WAFCT Codes** — i.e. each recipe is a structured graph pointing back into sheet 03's nutrient table. This means after integration, our [`CNFRecipeDecomposer`](backend/api/services/cnf_recipe_decomposer.py) gains **195 free pre-decomposed West African recipes** with no LLM calls required. For dishes covered by sheet 09, decomposition becomes a deterministic lookup.

## 2. Nutrient-axis bridge (INFOODS ↔ CNF)

WAFCT uses the **FAO INFOODS tagname standard** ([fao.org/infoods](https://www.fao.org/infoods/infoods/standards-guidelines/food-component-identifiers-tagnames/en/)) — a controlled vocabulary of ~250+ nutrient identifiers used by every modern composition table. CNF uses Health Canada's `NutrientName` convention, which is descriptive English text. The two are not byte-equal but are conceptually 1:1 for ~82 % of nutrients.

### Curated bridge table (47 mappings)

| INFOODS tag | CNF NutrientName | Unit | Class |
|---|---|---|---|
| `ENERC` (kJ)    | `ENERGY (KILOJOULES)`   | kJ | macro |
| `ENERC` (kcal)  | `ENERGY (KILOCALORIES)` | kcal | macro |
| `WATER`         | `MOISTURE` | g | macro |
| `PROTCNT`       | `PROTEIN`  | g | macro |
| `FAT` / `FATCE` | `FAT (TOTAL LIPIDS)` | g | macro |
| `CHOAVLDF`      | `CARBOHYDRATE, TOTAL (BY DIFFERENCE)` | g | macro |
| `FIBTG` / `FIBC` | `FIBRE, TOTAL DIETARY` / `FIBRE, CRUDE` | g | macro |
| `ALC`, `ASH`    | `ALCOHOL`, `ASH, TOTAL` | g | macro |
| `CA / FE / MG / P / K / NA / ZN / CU` | direct minerals | mg | mineral |
| `VITA / VITA_RAE / RETOL / CARTBEQ / CARTA / CARTB / CRYPXB` | vitamin A family | mcg | vitamin |
| `VITD / VITE / TOCPHA-D` | vitamin D/E family | mcg / mg | vitamin |
| `THIA / RIBF / NIA / NIAEQ / TRP / VITB6C / VITB12 / VITC` | B-vitamins + C | mg / mcg | vitamin |
| `FOL / FOLSUM / FOLAC / FOLFD / FOLDFE` | folate family | mcg | vitamin |
| `CHOLE` | `CHOLESTEROL` | mg | lipid |
| `FASAT / FAMS / FAPU / F18D2CN6 / F18D3CN3` | fatty-acid totals + 18:2n6 + 18:3n3 | g | lipid |

Full machine-readable table is in `_explore_wafct_structure.json` under `infoods_cnf_bridge.bridge`.

### WAFCT-only nutrients (10 orphans — by design)

| Tag | What it is | Why CNF lacks it | Useful for? |
|---|---|---|---|
| `EDIBLE1`, `EDIBLE2` | Edible-portion coefficients | CNF stores YIELD / REFUSE in separate tables | Pre-conversion to edible-mass basis (we'd compute this from CNF's REFUSE_AMOUNT if needed) |
| `SOP` | Sum of proximate components | CNF doesn't carry the check column | Internal QC, not for scoring |
| `XFA`, `XN` | Atwater conversion factors | CNF embeds these in the energy calc | Internal QC |
| `PHYTCPP` (or `PHYTCP`) | Phytate, total | CNF doesn't analyse phytate | **Anti-nutrient — clinically relevant for iron / zinc bioavailability in cereal-heavy diets**. Regional staples (sorghum, millet) have high phytate. |
| `IP3 / IP4 / IP5 / IP6` | Inositol mono-phosphate isomers | CNF doesn't analyse | Phytate degradation products; biomarker for fermentation processing |

**Take-home**: WAFCT's anti-nutrient (phytate / inositol-P) panel is a genuine *advantage* for West African nutritional research where mineral bioavailability is a clinical concern. If we ever extend HENI to model bioavailability discount factors, these columns become first-class inputs.

### CNF-only nutrients (not in WAFCT 39-set or 57-set)

CNF carries ~150 nutrients per food; WAFCT carries 57. CNF nutrients with no WAFCT counterpart:
- Granular fatty-acid profile (30+ individual fatty acids: 16:0, 18:1, 20:5n3, 22:6n3 etc.)
- Sugar partitioning (TOTAL SUGARS, GLUCOSE, FRUCTOSE, SUCROSE, LACTOSE, MALTOSE)
- Vitamin K, biotin, pantothenic acid, choline
- Several amino acids (CNF carries 18 individual AAs; WAFCT only tryptophan via `TRP`)

This matters for **HEFI's free-sugars component** — WAFCT doesn't carry a `SUGARS_FREE` equivalent, so HEFI's `RATIO_SUG_PERC` would silently degrade for any WAFCT food unless we either (a) compute free sugars from WAFCT's `CHOAVLDF` minus fibre + an estimated added-sugar fraction, or (b) flag WAFCT-only foods as unsupported for HEFI's sugar component. Recommend **(b) with a clear caveat banner** until a dedicated WAFCT sugars panel is sourced.

## 3. Per-100g empirical findings

### Panel A — universal raw commodities (calibration baseline)

| WAFCT food | CNF counterpart | Median \|Δ%\| | Verdict |
|---|---|---|---|
| 01_037 Rice, white, raw | CNF 4471 long-grain regular dry | 27.1 % | MODERATE |
| 01_043 Wheat flour, white, unfortified | CNF 4501 white all-purpose bleached | 13.7 % | STRONG |
| 08_001 Egg, chicken, raw | CNF 125 whole, fresh, raw | 18.5 % | MODERATE |
| 10_001 Milk, cow, whole 3.5 % fat | CNF 113 whole 3.25 % M.F. | **5.0 %** | **STRONG** |
| 05_028 Banana, yellow, ripe, raw | CNF 1704 raw | 18.8 % | MODERATE |
| 01_039 Sorghum, whole grains, raw | CNF 4432 grains, sorghum | 16.9 % | MODERATE |
| 09_018 Catfish, fillet, raw | CNF 5966 tilapia, raw (different species!) | **6.4 %** | **STRONG** |

### Panel B — cooking / preparation variants

| WAFCT food | CNF counterpart | Median \|Δ%\| | Verdict |
|---|---|---|---|
| 01_069 Rice, white, polished, boiled | CNF 4475 white medium-grain cooked | **8.0 %** | **STRONG** |
| 09_020 Catfish, fillet, grilled | CNF 5966 tilapia raw (not cooked — only available) | 18.9 % | MODERATE |

### Panel C — region-specific WAFCT foods with NO CNF equivalent

These 7 staples are the *real* user-value-add of integrating WAFCT — without it, scoring any West African meal containing them is structurally impossible:

| WAFCT food | Energy (kcal) | Protein (g) | Fat (g) | Ca (mg) | Fe (mg) | Notes |
|---|---|---|---|---|---|---|
| 01_002 Fonio, black, whole grains, raw | 332 | 8.3 | 3.0 | 51.0 | 8.3 | West African cereal |
| 04_002 Baobab, leaves, dried | 241 | 13.7 | 2.3 | **1244** | **13.7** | Calcium-dense leafy green |
| 03_042 Soumbala / dawadawa (fermented locust bean) | 375 | **33.1** | 15.6 | 435 | 15.2 | Fermented seasoning; high-Na |
| 02_039 Gari (fermented + toasted cassava) | 351 | 1.2 | 0.5 | 42 | 1.6 | Cassava staple |
| 06_013 Egusi (melon seed kernel, dried) | **574** | 27.6 | **45.0** | 118 | 6.3 | Oilseed for soups |
| 02_038 Cassava flour, fermented (lafun) | 344 | 1.5 | 0.6 | 68 | 3.4 | Cassava staple |
| 01_018 Pearl millet (IKMV 8201) | 375 | 9.5 | 6.8 | 23 | **15.2** | West African Sahel cereal |

### Aggregate per-nutrient bias (Panel A + B, n=9 paired foods)

| Nutrient | n | Median Δ% (WAFCT − CNF) | Median \|Δ%\| | Direction |
|---|---|---|---|---|
| Energy  | 9 | +3.4 %  | 4.8 %  | no systematic bias |
| Water   | 9 | -0.7 %  | 2.4 %  | no systematic bias |
| Protein | 9 | +4.7 %  | 13.4 % | no systematic bias |
| Fat     | 9 | +1.1 %  | 9.5 %  | no systematic bias |
| Carbs   | 9 | -5.2 %  | 6.1 %  | CNF marginally higher |
| Fibre   | 8 | +1.8 %  | 1.8 %  | no systematic bias |
| **Ca**  | 9 | **+23.5 %** | **57.1 %** | **WAFCT higher** |
| **Fe**  | 9 | **+67.7 %** | **81.5 %** | **WAFCT higher** |
| **Mg**  | 9 | **+15.6 %** | **36.7 %** | **WAFCT higher** |
| **K**   | 9 | **+10.8 %** | 17.4 % | WAFCT higher |

### Headline findings

1. **Macronutrients agree well.** Energy, Water, Protein, Fat, Carbs, Fibre all show median |Δ%| ≤ 13.4 % with no systematic bias direction. The two databases are nutritionally equivalent on macros, which means **HEFI / FCS / HSR scoring on macro-dominated components should produce comparable results from either source**.
2. **Minerals show a consistent WAFCT-higher bias.** Iron especially: +67.7 % WAFCT − CNF median across 9 paired foods. Likely causes (informed speculation, not measured here):
   - **Soil mineralisation differences** — West African soils carry different mineral profiles than Canadian/US soils, propagating to plant minerals at source.
   - **Cooking-vessel iron leaching** — traditional West African cookware (iron pots, cast iron) demonstrably elevates iron content of cooked foods.
   - **Analytical-method variance** — WAFCT often uses ICP-MS / AAS to FAO INFOODS protocols, CNF uses Health Canada methods; method-of-analysis differences for trace minerals are well-documented in the food-composition literature.
   - **Cultivar / varietal effects** — WAFCT samples are West African cultivars; CNF samples are North American cultivars of the "same" species.
3. **No food in Panel A or B fell into "WEAK" agreement.** Every paired food landed STRONG (5 % - 14 % |Δ%|) or MODERATE (15 % - 30 % |Δ%|). This means **the bridge is reliable enough for macro-level scoring** but mineral-level scoring (HEFI's sodium component, HENI's iron / zinc downstream) requires care.
4. **The gap WAFCT closes is enormous.** Of 7 deliberately region-specific WAFCT foods sampled, 7 / 7 have no CNF counterpart. A user in Lagos scoring a fonio breakfast against HEFI today gets nothing useful; with WAFCT integrated, every staple in Panel C becomes scoreable.

## 4. Integration-path recommendation

### Three options analyzed

**Option A — Source-tagged unification (most architecturally pure).** Every food gets a `(source, source_id)` tuple; FoodID becomes namespaced (`cnf:125`, `wafct:01_172`). Pros: clean separation, no ID collision, source provenance always explicit. Cons: **every downstream caller** ([`CNFMatcher`](backend/api/services/cnf_matcher.py), [`CNFRecipeDecomposer`](backend/api/services/cnf_recipe_decomposer.py), [`CNFRecall24h`](backend/api/services/cnf_recall_24h.py), the 5 scoring endpoints HEFI/HENI/HSR/FCS/Environmental) becomes source-aware. Substantial blast radius — every TypeScript interface that touches `food_id: number` becomes `food_id: { source: string; id: string }` or similar.

**Option B — WAFCT-as-extension (lowest blast radius, recommended).** WAFCT foods get FoodIDs offset by a constant (e.g. 700 000+; CNF tops out at ~6 500, leaving safe headroom). Packed into the same `food_name_df` / `nutrient_amount_df` schema as CNF. The Phase 2 INFOODS-to-CNF bridge translates WAFCT INFOODS tags to CNF NutrientName keys at ingest. A `source ∈ {cnf, wafct}` column is added to `food_name_df` for provenance + per-database filtering. Pros: **zero changes to scoring pipelines** — HEFI's existing `nutrients_for(food_id)['ENERGY (KILOCALORIES)']` works for both sources. The matcher's corpus expansion is a single `pd.concat`. The decomposer's lookup is unchanged. Cons: WAFCT's `PHYTCPP / IP3-6` orphan tags need a "WAFCT-only" namespace inside `nutrient_amount_df` (or get dropped at ingest — recommended for v1).

**Option C — Bridge table only (least committal, but functionally weakest).** Keep WAFCT independent; build a CNF↔WAFCT mapping table for equivalent foods only; let users pick a "preferred" database with bridge-fallback. Pros: zero risk to existing data; no schema changes. Cons: **Panel C foods become unreachable** — a user picking "CNF" gets no fonio, no baobab leaves, no gari. The bridge is incomplete by construction (only ~9 foods in Panel A+B map deterministically; thousands of WAFCT foods have no CNF equivalent). Defeats the point of the integration.

### Recommendation: Option B with a `source` column

**Why:** the per-100g empirical findings make this concrete. Macronutrient agreement is good enough (median |Δ%| ≤ 13 %) that translating WAFCT INFOODS values into CNF NutrientName-keyed cells is *defensible* — the downstream scorers don't need to know the source to produce reasonable results. The mineral bias is real but applies as a known caveat to be flagged in the audience-aware explanations panel ("WAFCT food: iron content is on average 68 % higher than CNF equivalent — reflects analytical-method and soil-source differences"), not a blocker. The 7-of-7 Panel C coverage gap means we *must* integrate, not just bridge.

The `source` column lets us:
- Filter food search to CNF-only, WAFCT-only, or both (UI database-picker)
- Surface "this food came from WAFCT" provenance badge in researcher / policy modes
- Apply different unit / method caveats per source in the explanations panel
- Run smoke tests that exercise both sources independently

### What this would look like at file level (deferred to integration plan)

- `backend/api/cnf_data_pipeline.py` adds a `source` column to `food_name_df` after WAFCT ingest. `nutrients_for(food_id)` works unchanged.
- New `backend/api/wafct_ingest.py` — one-time ETL that reads `raw_wafct/WAFCT_2019.xlsx`, normalises via the bridge, appends to the in-memory DataFrames with offset FoodIDs.
- `backend/api/cnf_cache.py` `get_api_cnf_pipeline()` calls the new ingest once on first access.
- [`CNFMatcher`](backend/api/services/cnf_matcher.py) re-embeds with the expanded corpus (~5,691 + 1,028 = ~6,719 foods; +18 % corpus). One-time cost.
- Frontend [food-search components](frontend/src/components/shared/AIEnhancedSearch.tsx) gain a `?source=cnf|wafct|both` filter.
- Each calculator page surfaces a per-food provenance badge.

### UI database-picker — quick decision

Three UI patterns considered:
- **Explicit per-session toggle** in the global header (like the AudienceToggle) — clean but heavy. Recommended only if usage data shows users staying within a single source per session.
- **Auto-pick based on locale** (browser language → defaults to WAFCT for French-WA locales) — magical, hard to override, recommend against.
- **Inline filter in food search** (`Source: ○ Both ○ CNF only ○ WAFCT only`) — minimal, opt-in, discoverable. **Recommended for v1.**

Default to **"Both"** — users see all foods unless they actively narrow. Researcher-mode users get a "source = WAFCT" pill on each result for provenance traceability.

## 5. Out-of-scope follow-ups (integration plan to come)

- **Actual integration code.** This memo stops at the architectural recommendation. The implementation plan is a separate document and will cover: ETL inscription, FoodID offset choice, schema migration, matcher corpus rebuild, audience-aware provenance surfacing, per-source caveat banners, smoke + golden harness extensions.
- **License / attribution / republication review.** WAFCT 2019 is freely available from FAO under the CC BY-NC-SA 3.0 IGO licence (verified in the `01 Introduction` sheet). Before shipping WAFCT data through public endpoints we should confirm attribution requirements with the user / legal — at minimum, a citation block in the documentation + a per-API-response source attribution field.
- **Manuscript update.** A new §3.x WAFCT subsection will document: rationale, structural overview, integration architecture, the per-100g empirical finding (mineral bias), the Panel-C coverage gap WAFCT closes. Recommend this follows the integration build (so the §3.x can cite the smoke-harness pass counts).
- **WAFCT mixed-dish integration with [`CNFRecipeDecomposer`](backend/api/services/cnf_recipe_decomposer.py).** Sheet 09's 195 canonical recipes are cross-referenced by WAFCT Code, meaning the decomposer could lookup pre-decomposed canonical recipes (no LLM call) for known West African dishes — a substantial latency + cost + reproducibility win. Worth a dedicated mini-plan post-integration.
- **FoodEx2 as a deterministic CNF↔WAFCT bridge.** 90.9 % of WAFCT foods carry FoodEx2 codes; if CNF foods can be FoodEx2-coded (Health Canada has internal mappings — needs verification), we get a deterministic source-agnostic bridge independent of the LLM matcher. Could complement Option B's offset-FoodID approach for cross-source "equivalent food" lookups.
- **Bioavailability / phytate-aware HENI / FCS extensions.** WAFCT's `PHYTCPP / IP3-6` columns enable iron + zinc bioavailability discounting that's clinically meaningful for cereal-heavy West African diets. Out of scope for v1 integration; a future research extension.
- **24-h recall wizard WAFCT support.** Once the matcher + decomposer handle WAFCT foods, the [Recall24hWizard](frontend/src/components/shared/Recall24hWizard.tsx) gets WAFCT support for free (it composes the decomposer). One end-to-end smoke test against a canonical West African day (fonio breakfast / jollof rice lunch / baobab-leaf-sauce dinner) confirms the integration.
- **Full-corpus auto-matching CNF↔WAFCT via the LLM matcher.** A one-time pass building a `bridge_table.json` between every WAFCT food and its best CNF equivalent (with confidence) would (a) make the per-food provenance UI smarter, (b) flag potential duplicate-entry concerns ("user is scoring CNF banana but the wizard also has WAFCT banana — disambiguate"), and (c) feed a research deliverable comparing the two databases at full scale. Cost ~$2-3 in OpenAI calls. Out of scope for exploration.

## Verification

```bash
cd backend

# Phase 1 + 2: structure inspector + INFOODS-to-CNF bridge (no Django, no LLM, ~5 s)
set PYTHONIOENCODING=utf-8 && python _explore_wafct.py
# expected: console summary of all 12 sheets + ~100 KB JSON written

# Phase 3: per-100g delta panel (loads CNF pipeline; deterministic; ~10 s; no LLM)
set PYTHONIOENCODING=utf-8 && python _explore_wafct_vs_cnf_per100g.py
# expected: 3 panel tables + aggregate bias table + per-food agreement verdict + ~47 KB JSON

# Regression sanity (no production code is touched in this exploration)
python _smoke_cnf_matcher.py                  # 36/40
python _smoke_cnf_recipe_decomposer_golden.py # 3/3
python _smoke_cnf_recall_24h_golden.py        # 1/1
cd ../frontend && npx tsc --noEmit            # clean
```

The exploration adds two harness files and this memo. Nothing in the production code path is modified.
