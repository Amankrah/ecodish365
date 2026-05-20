# An AI-Augmented Multi-Indicator Framework for Sustainability Assessment of Food Production–Consumption Systems: The `ecodish365` Platform with a Canadian Case Study

**Target journal:** *Sustainable Production and Consumption* (Elsevier)
**Special Issue:** Artificial Intelligence for Sustainability Assessment in Production and Consumption Systems
**Guest editors:** José María Ponce-Ortega, César Ramírez-Márquez
**Submission deadline:** 30 September 2026
**Manuscript status:** Working draft — empirical sections (§4–§5) to be filled after Scenarios S1–S8 are executed.

---

## Authors (placeholder)

A. Author¹\*, B. Author¹, C. Author²

¹ Affiliation 1
² Affiliation 2
\* Corresponding author: `dishdevinfo@gmail.com`

## Highlights

- **A1.** Unified open-source platform integrating five food-system indicators (HEFI-2019, HENI, HSR, FCS, ReCiPe 2016 LCA) with monetary valuation of externalities, computed reproducibly from the Canadian Nutrient File.
- **A2.** Two AI subsystems: (i) a rule-augmented LLM categorizer that maps ~5 000 CNF food entries to GBD dietary risk factors; (ii) an LLM-assisted food-to-LCA matcher that links CNF foods to peer-reviewed inventory data (Agribalyse 3.2 / Poore & Nemecek 2018).
- **A3.** Benchmark of LLM categorization against an expert-labelled subset (n = 500) reporting precision, recall, F1, latency, and cost per call.
- **A4.** Monte Carlo uncertainty propagation (10 000 iterations) and Sobol sensitivity analysis identifying which characterization factors drive variance in single-score outputs.
- **A5.** Multi-indicator case study on 100 typical Canadian meals and four diet-shift counterfactuals (beef→legumes; dairy→soy; SSB→water; refined→whole grain) reporting health/environment/cost trade-offs.
- **A6.** Transparent reporting of the "sustainability of AI" footprint of the pipeline itself (compute, water, dollar cost of LLM calls), in line with Green AI principles.

## Abstract (~250 words, draft)

Sustainability assessment of food production–consumption systems requires integrating nutritional, epidemiological, environmental and economic evidence at the granularity of individual food items: the food supply chain emits ~26 % of anthropogenic greenhouse gases, drives ~78 % of eutrophication and varies up to 50-fold among producers of the same product (Poore & Nemecek, 2018), and single-indicator proxies are demonstrably weak (cross-indicator R² = 0–30 % in 26 of 32 impact-impact pairs). Existing platforms either optimise for one dimension or treat the dominant European LCA reference database (AGRIBALYSE 3.2) as numerically interchangeable with the diet-health LCA standard (ReCiPe 2016 v1.1), which it is not. We present `ecodish365`, an open-source decision-support platform that operationalises five complementary indicators — the Healthy Eating Food Index 2019 (HEFI-2019), the Health Nutritional Index (HENI, in disability-adjusted life years), the Health Star Rating (HSR), the Food Compass Score (FCS), and a ReCiPe 2016 v1.1 (Hierarchist) life-cycle assessment with monetary valuation — over the Canadian Nutrient File. Artificial intelligence is incorporated in two well-bounded roles: (i) a hybrid rule + Large Language Model (LLM) categorizer that maps food items to Global Burden of Disease dietary risk factors when rule coverage is incomplete; and (ii) an LLM-assisted matcher that links CNF entries to peer-reviewed life-cycle inventories (AGRIBALYSE 3.2 supplemented by Poore & Nemecek (2018)). We report a benchmark of categorization accuracy against an expert-labelled gold standard (n = 500 foods), cross-validate the platform's life-cycle factors against AGRIBALYSE 3.2 LCIs re-scored under ReCiPe, and propagate per-factor uncertainty via Monte Carlo (10 000 iterations) with σ_g fitted from Poore & Nemecek's (2018) deposited archive. A Sobol-index sensitivity analysis quantifies the contribution of each factor group. We illustrate the framework with 100 representative Canadian meals drawn from the 2015 Canadian Community Health Survey–Nutrition and four diet-shift counterfactual scenarios, quantifying health-vs-environment trade-offs and monetised externalities. The platform is released as a reproducible Python/Rust toolchain (Apache 2.0) with all factors, prompts, and benchmarks open.

**Keywords:** sustainability assessment; life-cycle assessment; large language models; food systems; diet quality; DALY; Canadian Nutrient File; decision support; uncertainty quantification.

---

## 1. Introduction

### 1.1 Why integrate AI with sustainability assessment of food systems?

The food supply chain emits ~13.7 Gt CO₂-eq yr⁻¹ — 26 % of anthropogenic greenhouse gases — and is responsible for ~32 % of global terrestrial acidification, ~78 % of eutrophication, ~43 % of ice- and desert-free land occupation, and roughly two-thirds of freshwater withdrawals (Poore & Nemecek, 2018, p. 2). Farm-stage operations dominate that burden (61 % of food GHGs, 79 % of acidification, 95 % of eutrophication; Poore & Nemecek, 2018, p. 2, table S17), and impacts vary up to **50-fold among producers of the same product** (Poore & Nemecek, 2018, p. 1) — meaning that the choice of supplier, processing route, and consumption pattern is as material as the choice of food item itself. Demand-side measures are now explicit in the IPCC AR6 mitigation pathways (IPCC, 2022, ch. 5), and the 2025 EAT–Lancet update reaffirms that dietary transitions remain the single largest demand-side lever (Rockström et al., 2025). Translating that ambition into operational decision support at the granularity of meals, products and supply chains requires simultaneously evaluating multiple, heterogeneous indicators — nutritional adequacy, disease-burden, environmental footprint and economic externalities — over very large food-item catalogues, because single-indicator proxies are demonstrably weak: cross-indicator R² is 0–30 % in 26 of 32 impact-impact pairs (Poore & Nemecek, 2018, p. 3, fig. S4).

AI is a natural mediator here, for three reasons. First, modern food databases (CNF, FNDDS/FPED, USDA SR, Agribalyse, ecoinvent) are heterogeneous in coverage, granularity and labelling, and require fuzzy linkage; Large Language Models (LLMs) have recently been shown to perform near-expert classification of food items against NOVA/WHO criteria ([Nutrients, 2026](https://www.mdpi.com/2072-6643/18/1/23)) and to support retrieval-augmented classification of recipes ([NutriRAG, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11957177/)). Second, the volume of relevant epidemiological and life-cycle evidence has grown beyond what manual review can keep current. Third, AI itself is increasingly subject to sustainability scrutiny ([NTT DATA, 2025](https://www.nttdata.com/global/en/news/press-release/2025/october/102800)), making it imperative to design AI-augmented sustainability tools that account for their own footprint.

### 1.2 The gap in current tools

Existing platforms either (a) optimise for a single dimension — diet quality (HEFI-2019, HEI-2015, NRF), nutrient profiling (HSR, Nutri-Score, FCS), carbon footprint, or DALYs — or (b) integrate two dimensions but treat the others as fixed (e.g. nutritional LCA with carbon only). Multi-indicator tools that combine epidemiological DALY-weighted health burden with ReCiPe-style LCA and monetary externalities at the level of individual food items, with explicit uncertainty quantification and open AI augmentation, are rare. The complementarity of nutrient density and disease burden in nutritional LCA was articulated by [Stylianou and colleagues](https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1304752/full) but the implementation pipelines and prompts have not been openly released.

Critically, the *authors of the dominant validated nutrient-profiling system themselves* set out the integration this paper performs. O'Hearn et al. (2022, Discussion p. 10) write that "the long-term vision of Food Compass is to score additional features... such as environmental sustainability, social justice, and animal welfare — one for each direction of the compass," yet no openly-released implementation links Food Compass to a peer-reviewed LCIA framework. Likewise the FCS-10 authors (Barrett et al., 2025, Discussion pp. 14–15) state that "use of artificial intelligence large language models could also facilitate the recognition and interpretation of ingredients lists" — an authoritative call for exactly the LLM-based food classification that our pipeline supplies (§3.4).

Two further methodological gaps compound this. First, the dominant European reference databases — AGRIBALYSE 3.2 and ecoinvent — apply the European Commission's Product Environmental Footprint (PEF) method, which uses 16 indicators with fixed weights, rather than the 17-midpoint / 3-endpoint ReCiPe 2016 family used by most diet-health LCA studies (ADEME, 2024; Huijbregts et al., 2017, p. 141, Table 1). PEF and ReCiPe outputs are **not** numerically interchangeable. Second, no large reference database publishes quantitative uncertainty (e.g. standard deviations) per impact factor: AGRIBALYSE explicitly notes that estimating these would require data not currently available, providing only a qualitative 1–5 Data Quality Rating (DQR), with 67 % of products rated at DQR ≤ 3 (ADEME, 2024, *Méthodologie ACV* page). Any tool aspiring to decision-support credibility therefore has to wrap point-estimate factors in propagated uncertainty bands and cross-database harmonisation logic — which is what we build in §3.6 and §3.5 respectively.

A practical motivation also runs through this paper: producing HEFI-2019 variables manually from 24-hour recalls cost **> 75 hours of registered-dietitian time** in the Canadian Food Intake Screener validation study (Hutchinson et al., 2023, Discussion p. 630). Automated, recipe-level scoring is not an academic luxury — it is the prerequisite for running multi-indicator assessment at population scale.

### 1.3 Contributions

This paper makes the following contributions:

1. **A unified, open-source assessment framework** integrating five complementary indicators on top of the Canadian Nutrient File (§3).
2. **Two AI subsystems with clearly delimited roles** — risk-factor categorization (§3.4) and food-to-LCA matching (§3.5) — each accompanied by a controlled benchmark against expert labels (§4.1–§4.2).
3. **Uncertainty quantification** via Monte Carlo propagation and Sobol sensitivity over LCA characterization factors (§3.6, §4.3), addressing a recurring critique of food LCA tools.
4. **A Canadian case study** linking the framework to the 2015 Canadian Community Health Survey–Nutrition and four counterfactual diet shifts (§5).
5. **A "sustainability of AI" audit** of the pipeline's own compute, energy and dollar footprint (§5.5).
6. **A fully reproducible release** (Python/Rust, Apache 2.0) including all factors, prompts, benchmark labels and notebooks.

---

## 2. Background and Related Work

### 2.1 Indicators

| Indicator | Domain | Unit | Reference (page-cited) |
|---|---|---|---|
| HEFI-2019 | CFG-2019 adherence (10 components) | / 80 | Brassard et al., 2022a (Dev., APNM 47:595–610, Table 2 p. 600); Brassard et al., 2022b (Eval., APNM 47:582–594, Table A2 p. 591) |
| HENI | Disease-burden of food / diet | μDALY ⁄ serving | Stylianou et al., 2021 (Nat. Food 2:616–627) |
| HSR | Nutrient profiling (AU/NZ) | 0.5–5 stars (half-step) | Australian HSRAC, HSRC v5 Guide for Industry, 2016 (canonical algorithm); algorithm structure described in Shahid et al., 2020 (Nutrients 12:1791, §2.4 p. 4) |
| FCS-10 (label-readable Food Compass) | Nutrient profiling, 18 label attributes + ingredient list | 1–10 | Barrett et al., 2025 (AJCN, Methods pp. 7–9; cut-offs ≥7/4–6/≤3) |
| Full FCS / i.FCS (per-diet) | 54 attributes × 9 domains; energy-weighted diet score | 1–100 | Mozaffarian et al., 2021 (Nat. Food 2:809–818, Table S3 pp. 9–12); Barrett et al., 2024 (Nat. Food 5:911–915, Methods p. 914); O'Hearn et al., 2022 (Nat. Commun. 13:7066, Methods p. 11) |
| ReCiPe 2016 v1.1 LCA | Environmental impact | 17 midpoint, 3 endpoint, single-score | Huijbregts et al., 2017 (Int J LCA 22:138–147, Table 1 p. 141); RIVM Report 2016-0104a, 2017 (Table 1.5 p. 25) |

**FCS choice.** Our pipeline implements **FCS-10** (Barrett et al., 2025) rather than the full 54-attribute FCS because (a) FCS-10 is fully reproducible — every component is published in the Methods and Supplementary Tables 1–4, whereas the full-FCS *code* is withheld by Tufts pending commercial licensing (Barrett et al., 2024, Data availability; O'Hearn et al., 2022, Data/Code availability); (b) FCS-10 validates against the full FCS at Spearman r = 0.93 (89 % within ±1 unit) with 87 % recommendation-category classification accuracy (Barrett et al., 2025, Results pp. 11–12); (c) FCS-10's inputs match what our recipe-level pipeline actually has — the Nutrition Facts panel plus the ingredient list. We retain the full-FCS framework for diet-level (i.FCS) reporting whenever inputs are complete. Where appropriate, the food-level FCS-10 score is mapped back to the FCS 1–100 scale (≥70 / 31–69 / ≤30 ↔ ≥7 / 4–6 / ≤3) for comparability.

### 2.2 AI for food classification and LCA matching

Recent work demonstrates that LLMs can classify food items at near-expert accuracy when prompted with structured criteria and validated by domain experts ([Nutrients 2026](https://www.mdpi.com/2072-6643/18/1/23); [FoodyLLM, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12927182/)). Retrieval-augmented approaches reach F1 ≈ 0.82 on food identification and classification tasks ([NutriRAG, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11957177/)). For images, GPT-class models approach but do not yet meet expert nutritional content estimation ([ScienceDirect 2025](https://www.sciencedirect.com/science/article/pii/S2475299125030185)). To our knowledge, no published system uses LLMs to bridge nutrition databases (CNF, FNDDS) with environmental LCA inventories (Agribalyse, ecoinvent).

### 2.3 Uncertainty in food LCA

Monte Carlo propagation remains the dominant approach for LCA uncertainty ([Heijungs review; MDPI 2022](https://www.mdpi.com/2673-4060/3/3/39); [2D-MC, 2022](https://link.springer.com/article/10.1007/s11367-022-02041-0)). Global sensitivity analysis with correlated inputs has been formalised recently ([Kim, 2025, JIE](https://onlinelibrary.wiley.com/doi/10.1111/jiec.70036)). We adopt log-normal characterization-factor distributions parameterised from Poore & Nemecek's reported between-producer variability.

### 2.4 Sustainability of AI

The pipeline's own footprint matters: training GPT-3 was reported at 1 287 MWh / 552 t CO₂e, and hyperscaler water withdrawals have grown sharply since 2016 ([NTT DATA, 2025](https://www.nttdata.com/global/en/news/press-release/2025/october/102800); [E3S, 2025](https://www.e3s-conferences.org/articles/e3sconf/abs/2025/75/e3sconf_geome2025_03007/e3sconf_geome2025_03007.html)). We therefore audit the per-meal AI inference cost and footprint (§5.5).

---

## 3. Methods

### 3.1 Platform architecture

`ecodish365` is a monorepo with three layers (Figure 1, *to draw*):

- **Frontend**: Next.js 15 (TypeScript), accessible at the page level via [`frontend/src/app/`](frontend/src/app/), exposing per-indicator and per-meal views.
- **Backend**: Django 5 with REST endpoints in [`backend/api/`](backend/api/) and module-specific services in [`backend/{hefi,heni,hsr,fcs,environmental_impact_model,meals}/`](backend/).
- **Numerical core**: a Rust crate (`rust_core`, PyO3 bindings) implementing the HSR, FCS and HENI scoring kernels for deterministic, performance-critical paths (see [`backend/rust_core/`](backend/rust_core/)).

The Canadian Nutrient File (CNF) is the canonical food catalogue. Foods are referenced by `FoodID`; quantities flow through the pipeline as grams or Reference Amounts as appropriate per indicator.

### 3.2 Indicators

All five indicators are implemented exactly per their published definitions (see [`hefi_technical_report.md`](hefi_technical_report.md) and [`heni_technical_report.md`](heni_technical_report.md) for the detailed component-by-component algorithms). For brevity we omit equations here and report only the salient design decisions:

- **HEFI-2019** uses the 10 components and the scoring standards of Brassard et al. (2022a, Table 2 p. 600), with linear interpolation between minimum and maximum standards (Brassard et al., 2022a, Results p. 599). Food classification follows the inclusion/exclusion list of Table A1 of that paper (pp. 606–609) literally — including the choices that fruit juice is *excluded* from V&F, all potatoes (any preparation) count as vegetables, processed meats appear only in the denominator of the Protein component, and regular-fat (3.25 %) milk counts in the Beverages numerator. We retain HEFI-2019's published interpretive guidance: a single one-day score is *not* interpretable as usual adherence (Brassard et al., 2022b, Discussion p. 588), there is no absolute "aligned-diet" threshold (Brassard et al., 2022a, Discussion p. 603), and total and component scores are always reported together (Brassard et al., 2022b, Conclusion p. 589). Two external databases are mandatory: Health Canada's Table of Reference Amounts (2016) and the Rana et al. (2021) free-sugars supplement to CNF 2015 — the CNF itself does not carry a free-sugars field. See [`backend/hefi_calculator/hefi/algorithm.py`](backend/hefi_calculator/hefi/algorithm.py).
- **HENI** is computed as Σ (gᵣᵢₛₖ₋ᶠᵃᶜᵗᵒʳ × μDALY ⁄ gᵣᵢₛₖ₋ᶠᵃᶜᵗᵒʳ) over 14 GBD risk factors; factor values are taken from the published HENI specification (Stylianou et al., 2021; canonical 14-factor table pending Group C extraction).
- **HSR** is implemented per the Australian/NZ HSR Calculator v5 (HSRAC, 2016) with the algorithmic structure documented in Shahid et al. (2020, §2.4 p. 4): six category-specific scoring matrices, baseline points from energy, saturated fat, total sugars and sodium minus modifying points from FVNL %, concentrated FVNL %, protein and fibre; output 0.5–5.0 stars in half-star increments. FVNL content is computed from CNF ingredient lists; where ingredient-level proportions are unavailable we apply the geometric ingredient-order weighting of Barrett et al. (2025, Equation 1 p. 9; see FCS-10 below).
- **FCS-10** (Barrett et al., 2025, Methods pp. 7–9) is our primary item-level FCS implementation. 18 attributes are scored directly from the Nutrition Facts panel (Nutrient Ratios, Vitamins, Minerals, Additives, Specific Lipids, Fibre/Protein); the Food Ingredients domain is scored from the first five non-trace ingredients mapped to one of 168 ingredient categories (Supplementary Table 4 of B12), weighted by Eq. 1 (first ingredient ≈ 42 %, then ×2/3 decay across five ingredients). Missing vitamin / mineral / lipid / phytochemical attributes are imputed from the 168-category reference scores (Supplementary Table 3 of B12). NOVA, nitrites, fermented and fried flags use the keyword rules of B12 Methods p. 9. Final FCS-10 ∈ [1,10] with cut-offs ≥ 7 / 4–6 / ≤ 3 (Barrett et al., 2025, Methods p. 7), mapping to the FCS 1–100 bands ≥ 70 / 31–69 / ≤ 30. Diet-level scoring uses **i.FCS**, the energy-weighted mean of per-item FCS, with alcohol excluded and entered as a covariate (O'Hearn et al., 2022, Methods p. 11).
- **LCA** uses ReCiPe 2016 v1.1 Hierarchist midpoint and endpoint factors, taken from the October 2017 RIVM v1.1 release (Huijbregts et al., 2017; RIVM Report 2016-0104a, 2017, *Report I: Characterization*). The Hierarchist 100-yr global-warming potentials we encode are CO₂ = 1, CH₄ (biogenic) = 34, CH₄ (fossil) = 36, N₂O = 298 (RIVM 2017, pp. 29–34, Table 2.2), with the constant midpoint-to-endpoint factor structure of Eq. (1) on p. 139 of Huijbregts et al. 2017 (fossil resource scarcity excepted; RIVM 2017, p. 25, Table 1.5, footnote 3). We use the global default characterization factors and report country-specific results from the chapter S1–S7 supplements where Canadian values are available (water use, fine PM, photochemical ozone, terrestrial acidification, freshwater eutrophication). See [`backend/environmental_impact_model/src/life_cycle_assessment.py`](backend/environmental_impact_model/src/life_cycle_assessment.py).

**Choice of method: ReCiPe vs PEF.** Our pipeline uses ReCiPe 2016 v1.1 Hierarchist rather than the European Commission's PEF method (the LCIA framework underlying AGRIBALYSE 3.2; ADEME, 2024). This choice is principled but consequential: PEF and ReCiPe diverge in (i) category list (PEF has 16 indicators, ReCiPe 17 midpoint + 3 endpoint), (ii) eutrophication treatment (PEF splits into terrestrial / marine / freshwater; ReCiPe keeps freshwater and marine), (iii) weighting (PEF imposes a single fixed weight set; ReCiPe offers I/H/E cultural perspectives), and (iv) value-choice operationalisation (PEF embeds one set; ReCiPe makes the choice transparent). We adopt ReCiPe because the diet-health LCA literature is built on it (Stylianou et al., 2016, 2021; Dekker et al., 2019; Heller et al., 2013), because the Hierarchist perspective aligns with WHO and intergovernmental conventions (Huijbregts et al., 2017, p. 140), and because the published v1.1 update preserves food-product rankings against ReCiPe 2008 with Spearman ρ between 0.85 and 0.99 across all impact categories and perspectives (Dekker et al., 2019, §3.1, p. 3) — making the method choice low-risk for ranking-based conclusions even where absolute magnitudes change. We use AGRIBALYSE 3.2 only as a source of LCI data (not LCIA), re-applying ReCiPe characterisation factors to the underlying inventories where ecoinvent licensing permits, and treat any direct PEF-vs-ReCiPe comparison as a sensitivity analysis rather than a primary result.

### 3.3 Monetary valuation

Monetised externalities use ECCC's Social Cost of GHG (2023 update, CAD constant 2021), Canadian municipal water tariffs, and Canadian Environmental Prices for non-GHG categories where available, otherwise European Environmental Prices Handbook values adjusted via PPP. See [`backend/environmental_impact_model/src/monetization.py`](backend/environmental_impact_model/src/monetization.py) and the table in §C of the Supplementary Information. *We replace personal-communication references in the source code with citable equivalents prior to submission.*

### 3.4 AI subsystem 1 — Hybrid rule + LLM categorization to GBD risk factors

The HENI risk-factor categorizer ([`backend/heni_calculator/heni/categorization/`](backend/heni_calculator/heni/categorization/)) is a two-stage hybrid:

1. **Rule-based first**: a deterministic categorizer maps CNF food-group, NutrientName, and description tokens to risk-factor scores ∈ [0, 1] for each of 14 GBD risk factors.
2. **LLM augmentation only when needed**: an LLM (default `gpt-4o-mini`, temperature 0, max 150 tokens) is invoked *only* for foods whose rule output is incomplete or low-confidence (any factor with rule-confidence < 0.3). The prompt is restricted to ≤ 5 factors at a time, includes the rule output as context, and requests JSON.

This design constrains LLM usage to the long-tail of ambiguous foods, keeping the pipeline cheap and auditable. The choice is endorsed by the FCS-10 authors themselves, who state that "use of artificial intelligence large language models could also facilitate the recognition and interpretation of ingredients lists" (Barrett et al., 2025, Discussion pp. 14–15), and consistent with the contemporaneous evidence that retrieval-augmented LLMs reach F1 ≈ 0.82 on food identification (NutriRAG, 2025) and near-expert classification with structured prompts (Wijesinghe et al., 2026, *Nutrients*).

### 3.5 AI subsystem 2 — LLM-assisted food-to-LCA matching *(new capability for this paper)*

A central reviewer concern with food LCA tools is hardcoded per-food-group impact factors. We therefore add an LLM-assisted matcher that, for each CNF food, returns its best-matching entry in Agribalyse 3.2 (and falls back to Poore & Nemecek 2018 group means). The matcher uses retrieval-augmented prompting: candidate Agribalyse entries are first retrieved by embedding similarity over food descriptions, then ranked by an LLM with explicit reasoning over food composition, processing and provenance. Outputs include the matched ID, a 0–1 confidence score, and a short justification. Confidence below a threshold (default 0.6) triggers fallback to the food-group default, with the decision logged for auditing.

### 3.6 Uncertainty quantification

The dominant European reference databases publish point estimates only: AGRIBALYSE provides a 1–5 Data Quality Rating but explicitly notes that quantitative standard deviations would require data not currently available (ADEME, 2024). We therefore build the uncertainty layer from primary-data variability. Each ReCiPe midpoint characterization factor (CF_m) and each upstream LCI factor is wrapped in a log-normal distribution with geometric standard deviation σ_g derived as follows: (a) for LCI factors covered by Poore & Nemecek (2018), σ_g is fitted from the published 10th-percentile-to-mean gap of Fig. 1 (p. 2) for each of the 40 product groups, with full distributions pulled from the deposited archive (doi.org/10.5287/bodleian:0z9MYbMyZ, Data S1) since acidification, eutrophication, and scarcity-weighted water values are bar-only in the printed figure; (b) for characterisation factors where ReCiPe publishes I/H/E factors, the I–E spread is used as a lower-bound on uncertainty; (c) all remaining factors fall back to ecoinvent pedigree-matrix defaults. This approach is principled: Poore & Nemecek (2018) report up to 50-fold producer-level variation within a single product (p. 1), and the 90th-percentile-to-10th-percentile ratio exceeds 3× across all five indicators for major staples (p. 2). We propagate uncertainty via Monte Carlo (N = 10 000) per meal, reporting medians and 5th–95th percentile intervals for each midpoint, each endpoint and the single score. Sobol first-order and total-order indices are computed (SALib; Saltelli, 2008) to attribute output variance to factor groups (energy/feed; manure & enteric; land-use change; transport & retail; characterization to endpoint; normalization). The Egalitarian–Hierarchist climate-CF gap of ~14× at endpoint (e.g. 1.3 × 10⁻⁵ vs 9.3 × 10⁻⁷ DALY kg⁻¹ CO₂; RIVM 2017, p. 25, Table 1.5) is the largest single uncertainty driver and is reported separately as a sensitivity.

### 3.7 Canadian regional adaptation

ReCiPe 2016 v1.1 publishes country-specific factors for only five categories (fine PM formation, photochemical ozone formation, terrestrial acidification, freshwater eutrophication, water use; Huijbregts et al., 2017, Abstract and §4.2, p. 145), reflecting both data limitations and a deliberate choice not to introduce regionalisation where the underlying models are too uncertain (Land use, Ch. 12 / Table 1.1 of RIVM 2017, p. 18). We follow the Dutch precedent of Dekker et al. (2019, §3.3, pp. 5–6) by applying Canadian-specific characterisation factors layered on top of global defaults, drawn from: (a) GHG grid intensity from the ECCC National Inventory Report 1990–2022 (ECCC, 2024); (b) blue-water scarcity from the AWaRe consensus model regionalised to Canada (Boulay et al., 2018); (c) land-use intensity from the Statistics Canada Census of Agriculture (Statistics Canada, 2024); (d) for impact categories without a defensible Canadian factor we default to 1.0 (no adjustment). We report both the regionalised and unadjusted runs in §5.3 (Scenario S6) so that the contribution of regionalisation to any individual conclusion is transparent — this is the same protocol Dekker et al. (2019) used to show that Dutch regionalisation shifts magnitudes but preserves ranking (Spearman ρ = 1 in their case study). The mapping is in Supplementary §D.

*Note on normalisation.* Our pipeline applies ReCiPe global normalisation factors as published in Huijbregts et al. 2017 / RIVM 2016-0104a. Earlier drafts referred to a "2024 RIVM normalisation revision"; we have removed that claim because no RIVM artefact post-dating the October 2017 v1.1 release was retrievable for this study. We will reinstate the citation if and when the corresponding RIVM document is identified.

### 3.8 Reproducibility

All factors, prompts, retrieval indices, benchmark labels, notebooks and figures are released in the `paper_v1` branch of the repository under Apache 2.0. Results are reproducible from CNF 2015 with one command (`make figures`).

---

## 4. Validation Results *(to be filled after Scenarios S1–S3, S7)*

### 4.1 Scenario S1 — LLM risk-factor categorizer benchmark
*Stratified sample of 500 CNF foods labelled by two registered dietitians; Cohen's κ for inter-rater agreement; per-factor precision/recall/F1 for rule-only, LLM-only, and rule+LLM hybrid; cost ($/1 000 foods) and latency.*

### 4.2 Scenario S2 — LCA factor cross-validation
*Per-food-group mean absolute relative error (MARE) of `ecodish365` factors vs. Agribalyse 3.2 and Poore & Nemecek 2018 for GWP, land use, water consumption, eutrophication (P, N), and acidification. Bland–Altman plots in SI.*

### 4.3 Scenario S3 — Monte Carlo uncertainty and Sobol sensitivity
*5th–95th percentile bands on single-score for the 100-meal panel; bar chart of total-order Sobol indices.*

### 4.4 Scenario S7 — LLM food-to-LCA matcher accuracy
*Top-1 / top-3 match accuracy vs. expert-labelled mapping on 300 CNF–Agribalyse pairs; calibration of confidence scores; failure-mode taxonomy.*

---

## 5. Case Study: Canadian Meals and Counterfactual Diet Shifts *(to be filled after Scenarios S4–S6, S8)*

### 5.1 Scenario S4 — 100 representative Canadian meals

*Source.* 2015 Canadian Community Health Survey–Nutrition Public-Use Microdata File (Statistics Canada, 2017), the same dataset and exclusion logic used by Brassard et al. (2022b, Methods p. 583): nationally representative of Canadians aged ≥ 1 y in private dwellings in the 10 provinces (excludes Territories, Forces members, reserves, remote areas, institutions), data collected 1 Jan – 31 Dec 2015, 24-hour recall via the Automated Multiple Pass Method, second recall obtained for ~37 % of respondents. We apply the same analytic exclusions as B7 (< 2 y; zero-energy reporters) for a national-comparable analytic frame of n = 20,103 respondents.

*Stratification and sampling.* 100 meal medoids drawn via k-medoids on nutrient/CNF-FoodID composition, stratified by meal occasion (breakfast/lunch/dinner/snack), three age-sex groups (2–18 y; males ≥ 19 y; females ≥ 19 y — matching the B7 stratification used to fit usual-intake models), and deprivation quintile.

*Usual-intake modelling.* For diet-level (i.FCS, HEFI-2019) reporting we apply the **NCI multivariate Markov-Chain Monte Carlo method** (Zhang et al., 2011) with 500 pseudo-individuals per respondent, episodically-consumed categories flagged at the ≥ 5 % zero-recall threshold (Krebs-Smith et al., 2010), and Balanced Repeated Replication on 500 Statistics Canada bootstrap weights — the exact machinery of Brassard et al. (2022b, Methods pp. 583–585).

*Benchmarks.* National HEFI-2019 distributions from Brassard et al. (2022b, Table A2 p. 591) are the comparison set. Reproducing the national mean of 43.1 / 80 (95 % CI 42.7–43.6) and the by-stratum means (2–18 y = 39.5; males ≥ 19 = 43.3; females ≥ 19 = 46.0) on our panel is the pre-registered sanity check before reporting any new finding. Indicators are reported as mean ± SD with pairwise Spearman correlation, a PCA biplot, and a Pareto frontier in (HENI gained, LCA single-score avoided) space.

### 5.2 Scenario S5 — Diet-shift counterfactuals
*Per-100 g (or per serving) Δ across HEFI, HENI, FCS, HSR, LCA single-score and monetised externalities for:*
1. *Beef → legumes*
2. *Dairy → fortified soy beverage*
3. *Sugar-sweetened beverages → water*
4. *Refined grains → whole grains*

### 5.3 Scenario S6 — Regional adaptation impact
*With- vs. without-Canadian-factors comparison on the meal panel; identification of categories where regional adaptation changes the ranking of meals.*

### 5.4 Trade-off frontier
*Pareto frontier in (HENI gained, LCA single-score avoided) space; identification of "best-on-both" foods.*

### 5.5 Scenario S8 — Sustainability of the AI pipeline
*Tokens, energy (estimated per token), water (per token) and dollar cost per meal scored; comparison of "rule-only" vs. "rule + LLM" hybrid in cost-accuracy space.*

---

## 6. Discussion

### 6.1 What AI adds — and what it doesn't

Constraining LLM calls to ambiguous foods (§3.4) and to retrieval-ranked candidates (§3.5) keeps the pipeline cheap, deterministic at the cache level, and auditable. We do not advocate end-to-end LLM scoring of sustainability outcomes: epidemiological factors (HENI), LCA characterization (ReCiPe), and indicator algorithms (HEFI/HSR/FCS) are deterministic computations whose values must remain peer-reviewed and traceable. AI is bounded to classification and linkage — exactly the tasks where the literature shows LLMs are competitive with expert work.

### 6.2 Trade-offs across indicators

[Empirical placeholder — to be filled from §5.1.]

### 6.3 Decision-support and policy implications

Demand-side measures in IPCC AR6 require operational tooling at the granularity of meals and product categories. Open multi-indicator platforms reduce the cost of policy modelling, EAT–Lancet implementation studies, and dietary guideline revision.

### 6.4 Methodological contributions for AI-for-sustainability

We argue that AI in sustainability assessment is best deployed as: (i) a *linker* between heterogeneous data sources, (ii) a *fallback* when rule coverage is incomplete, and (iii) an *explainability layer* for decision support. Each role admits a clean benchmark.

### 6.5 The cost of the AI itself

[Empirical placeholder — §5.5.]

---

## 7. Limitations

### 7.1 LCIA method limits inherited from ReCiPe 2016 v1.1

We inherit the documented gaps of ReCiPe 2016 v1.1 (Huijbregts et al., 2017, §4, pp. 144–145; RIVM 2017, §1.3, p. 20). The most consequential for food LCA:

- **No scenario differentiation** (I/H/E) for five categories — photochemical ozone formation, terrestrial acidification, freshwater eutrophication, land use, fossil resource scarcity — because value-choice data are not available in the underlying models.
- **Fossil resource scarcity** has no constant midpoint-to-endpoint factor; the endpoint must be resolved per resource (crude oil, hard coal, natural gas) and our pipeline treats this category as an exception (RIVM 2017, p. 25, Table 1.5, footnote 3).
- **Toxicity factors with restricted scope.** Cancer and non-cancer effects are linearised; agricultural and urban soil pathways are excluded to avoid double-counting with land use (Table 1.1, p. 18). Pesticide-residue ingestion is not modelled (Dekker et al., 2019, §4.2, p. 8 — and confirmed in AGRIBALYSE; ADEME, 2024).
- **Land use** is local-impact only; global extinction risk is not captured (Huijbregts et al., 2017, p. 145).
- **Egalitarian climate factors omit climate-carbon feedbacks** for non-CO₂ GHGs (RIVM 2017, footnote 1, p. 28).
- **Missing pathways**: indoor exposure, marine debris/invasive species, noise, nanoparticles, infectious-disease impacts of climate change (Huijbregts et al., 2017, §4.4, p. 145).

We explicitly flag the toxicity numbers in our outputs as low-confidence per the source documentation.

### 7.2 Reference-database limits

- AGRIBALYSE 3.2 carries known errata on egg-containing products, Bleu-Blanc-Coeur labelled products, quinoa, and seven Ciqual codes (ADEME, 2024, *Evolution* page); our pipeline either skips affected codes or applies the corrected values, with a complete log in the SI.
- AGRIBALYSE publishes only qualitative DQR (1–5); 67 % of products are at DQR ≤ 3 (ADEME, 2024). Our S3 uncertainty quantification therefore comes from Poore & Nemecek's deposited distributions rather than AGRIBALYSE itself.
- Using disaggregated AGRIBALYSE LCIs (vs. its open aggregated factor tables) requires an ecoinvent licence (ADEME, 2024, *Liens avec ecoinvent* page). Our open-source release uses the open factor tables; the licensed runs are noted in §3.5.

### 7.3 Nutritional-indicator limits inherited from the source instruments

- **HEFI-2019 has no absolute "aligned-diet" threshold** (Brassard et al., 2022a, Discussion p. 603; Brassard et al., 2022b, Discussion p. 588). The 99th percentile of Canadians ≥ 2 y is 62.9 / 80; full adherence is rare. We report HEFI-2019 only as relative differences across our diet scenarios — never as a pass/fail nutritional verdict.
- **HEFI-2019 component-level floor/ceiling effects** compress dynamic range on Protein foods (ceiling), Saturated fats, and Free sugars (Brassard et al., 2022a, Results p. 601; Brassard et al., 2022b, Discussion p. 588). Diet-shift signals will concentrate in V&F, Plant-based protein, Whole-grain foods, Grain-ratio and Beverages.
- **HEFI-2019 is NOT validated against health outcomes.** Brassard et al. (2022b, Discussion p. 589) state explicitly that the link between HEFI-2019 and disease endpoints is undetermined. HEFI-2019 is therefore reported as a *guideline-adherence* index, distinct from the disease-burden HENI score (which uses GBD epidemiology) and from the i.FCS score (which is mortality-validated).
- **Single one-day HEFI-2019 scores are not interpretable** as usual adherence (Brassard et al., 2022b, Discussion p. 588) — only the usual-intake NCI machinery (§5.1) supports inference at the meal-occasion level.
- **HEFI-2019 inherits the random and systematic error of 24-h recall data** (Brassard et al., 2022b, Discussion pp. 588–589); its validity for pregnant women, special-diet populations and clinical settings is undemonstrated.
- **Cronbach's α = 0.66** (95 % CI 0.63–0.69; Brassard et al., 2022b, Results p. 587) — comparable to HEI-2015 α = 0.67 but below the conventional 0.70 reliability threshold. Authors attribute this to multidimensionality (≥ 4 PCA dimensions); we follow their convention of reporting total *and* component scores together.
- **HSR is a moving algorithm.** The point tables and star cut-offs are version-dependent and recommendations to better align with the Australian Dietary Guidelines will change product HSRs over time (Shahid et al., 2020, §4 p. 10). Our implementation pins HSRC v5 (HSRAC, 2016) — the version current at the time of the B13 uptake study.
- **HSR FVNL inputs are commonly missing** on real packages (Shahid et al., 2020, §2.3 p. 3); our pipeline imputes them either from ingredient-list category-analogy (a precedent the HSR authors themselves use across ~700 subcategories) or via the FCS-10 ingredient-order weighting. This is a documented but unavoidable source of HSR variability.
- **Food Compass / i.FCS is built and validated on US data only** (NHANES/FNDDS/FPED), with thresholds anchored to the 5th/95th percentile of NHANES 2015–16 (Mozaffarian et al., 2021, Table S3 footnote †; Barrett et al., 2024, Methods p. 914). Direct transfer to CNF requires explicit category re-mapping; in practice the original FCS used 47 of 54 attributes in FNDDS because 7 (iodine, trans fat, 5 artificial additives) were unscorable.
- **FCS-10 has not been validated against health outcomes directly** (Barrett et al., 2025, Discussion p. 16). Health-outcome validation flows from i.FCS (O'Hearn et al., 2022; full FCS, n = 47 999 NHANES adults, all-cause mortality HR 0.93 per 1 SD) and FCS-10 inherits it only by proxy via Spearman r = 0.93 against full FCS.
- **i.FCS energy-weighting under-weights low-calorie foods** like fruits and vegetables — a design trade-off to avoid the water-content bias of per-kg weighting (O'Hearn et al., 2022, Discussion pp. 9–10).
- **Conflict-of-interest disclosure.** Senior authors of the Food Compass series (Mozaffarian, Blumberg) report extensive food-industry advisory and equity relationships (Barrett et al., 2024, Competing interests; O'Hearn et al., 2022, Competing interests; Barrett et al., 2025, Competing interests). We disclose this because Food Compass is part of our framework. Tufts is also considering commercial licensing of the full FCS implementation code, which is why our pipeline uses the openly-published FCS-10 (Barrett et al., 2025) and not full-FCS code.

### 7.4 Benchmark and cohort limits

- The S1 benchmark cohort is drawn from CNF; transferability to FNDDS / FoodData Central foods requires re-labelling.
- LCA factors remain group-level after fallback when the AI matcher's confidence is below threshold (§3.5); item-level refinement on the long tail awaits a wider Agribalyse mapping.
- HENI factor values rest on GBD epidemiology (currently GBD 2019); revisions of GBD will require re-running.
- The 2015 CCHS–Nutrition is the most recent open Canadian 24-hour recall dataset; results are presentational, not forecasts. The B7 validation sample (n = 20 103) excludes Canadians on full-time military service, residents of the Territories, on-reserve Indigenous populations, residents of remote areas, and institutionalised individuals (Brassard et al., 2022b, Methods p. 583) — a limit to external validity our manuscript must repeat verbatim.

### 7.5 AI-system limits

- Inference cost will change as model prices change; we report tokens to allow extrapolation.
- LLM outputs are non-deterministic above zero temperature; we hold temperature at 0 for the categorizer and matcher and cache outputs by SHA-256 of the prompt to make runs reproducible.
- Provider-specific behaviour: we run the same prompts against `gpt-4o-mini` and `claude-haiku-4-5` (S1 ablation) so that no single vendor's idiosyncrasies dominate results.

---

## 8. Conclusion

[Two-paragraph summary; emphasise the open-source release, the bounded role of AI, and the multi-indicator integration.]

---

## CRediT author statement

Conceptualization: …; Methodology: …; Software: …; Validation: …; Investigation: …; Data curation: …; Writing — original draft: …; Writing — review & editing: …; Visualization: …

## Funding and Acknowledgements

[Placeholder.]

## Data and code availability

All code, prompts, characterization factors, benchmark labels and notebooks are available at the project repository under Apache 2.0. The CNF 2015 dataset is publicly distributed by Health Canada; Agribalyse 3.2 is available under its licence terms.

## Conflicts of Interest

None declared.

---

## References (Group A confirmed from PDF; Groups B–J pending retrieval)

**Confirmed (Groups A + B — page-cited in body):**

1. Poore J, Nemecek T. Reducing food's environmental impacts through producers and consumers. *Science.* 2018;360(6392):987–992. doi:10.1126/science.aaq0216. Data archive: doi.org/10.5287/bodleian:0z9MYbMyZ.
2. Huijbregts MAJ, Steinmann ZJN, Elshout PMF, Stam G, Verones F, Vieira M, Zijp M, Hollander A, van Zelm R. ReCiPe2016: a harmonised life cycle impact assessment method at midpoint and endpoint level. *Int J Life Cycle Assess.* 2017;22(2):138–147. doi:10.1007/s11367-016-1246-y.
3. Huijbregts MAJ, Steinmann ZJN, Elshout PMF, Stam G, Verones F, Vieira MDM, Hollander A, Zijp M, van Zelm R. *ReCiPe 2016 v1.1. A harmonized life cycle impact assessment method at midpoint and endpoint level. Report I: Characterization.* RIVM Report 2016-0104a. Bilthoven: RIVM; 2017.
4. Dekker E, Zijp MC, van de Kamp ME, Temme EHM, van Zelm R. A taste of the new ReCiPe for life cycle assessment: consequences of the updated impact assessment method on food product LCAs. *Int J Life Cycle Assess.* 2019. doi:10.1007/s11367-019-01653-3.
5. ADEME. *AGRIBALYSE® 3.2 — Programme de référence sur les indicateurs d'impacts environnementaux des produits agricoles et alimentaires.* Angers: ADEME; November 2024. Dataverse: doi:10.57745/XTENSJ.
6. Brassard D, Elvidge Munene LA, St-Pierre S, Guenther PM, Kirkpatrick SI, Slater J, Lemieux S, Jessri M, Haines J, Prowse R, Olstad DL, Garriguet D, Vena J, Vatanparast H, L'Abbe MR, Lamarche B. Development of the Healthy Eating Food Index (HEFI)-2019 measuring adherence to Canada's Food Guide 2019 recommendations on healthy food choices. *Appl Physiol Nutr Metab.* 2022;47(5):595–610. doi:10.1139/apnm-2021-0415.
7. Brassard D, Elvidge Munene LA, St-Pierre S, Gonzalez A, Guenther PM, Jessri M, Vena J, Olstad DL, Vatanparast H, Prowse R, Lemieux S, L'Abbe MR, Garriguet D, Kirkpatrick SI, Lamarche B. Evaluation of the Healthy Eating Food Index (HEFI)-2019 measuring adherence to Canada's Food Guide 2019 recommendations on healthy food choices. *Appl Physiol Nutr Metab.* 2022;47(5):582–594. doi:10.1139/apnm-2021-0416.
8. Hutchinson JM, Dodd KW, Guenther PM, Lamarche B, Haines J, Wallace A, Perreault M, Williams TE, da Costa Louzada ML, Jessri M, Lemieux S, Olstad DL, Prowse R, Randall Simpson J, Vena JE, Szajbely K, Kirkpatrick SI. The Canadian Food Intake Screener for assessing alignment of adults' dietary intake with the 2019 Canada's Food Guide healthy food choices recommendations: scoring system and construct validity. *Appl Physiol Nutr Metab.* 2023;48(5):620–633. doi:10.1139/apnm-2023-0018.
9. Mozaffarian D, El-Abbadi NH, O'Hearn M, Marino J, Masters WA, Jacques P, Shi P, Blumberg J, Micha R. Food Compass is a nutrient profiling system using expanded characteristics for assessing healthfulness of foods. *Nature Food.* 2021;2(10):809–818. doi:10.1038/s43016-021-00381-y.
10. Barrett EM, Shi P, Blumberg JB, O'Hearn M, Micha R, Mozaffarian D. Food Compass 2.0 is an improved nutrient profiling system to characterize healthfulness of foods and beverages. *Nature Food.* 2024;5(11):911–915. doi:10.1038/s43016-024-01053-3.
11. O'Hearn M, Erndt-Marino J, Gerber S, Lauren BN, Economos C, Wong JB, Blumberg JB, Mozaffarian D. Validation of Food Compass with a healthy diet, cardiometabolic health, and mortality among U.S. adults, 1999–2018. *Nature Communications.* 2022;13:7066. doi:10.1038/s41467-022-34195-8.
12. Barrett EM, Cudhea F, Washbon E, Levitan Z, Reedy Sharib J, Blumberg JB, Micha R, Mozaffarian D. Food Compass Score-10: validation of a method for evaluating the healthfulness of foods and beverages using ingredient list information. *Am J Clin Nutr.* 2025. doi:10.1016/j.ajcnut.2025.01.014.
13. Shahid M, Neal B, Jones A. Uptake of Australia's Health Star Rating System 2014–2019. *Nutrients.* 2020;12(6):1791. doi:10.3390/nu12061791.
14. Health Star Rating Advisory Committee. *Guide for Industry to the Health Star Rating Calculator (HSRC) v5.* Canberra: Australian Government Department of Health; 2016. (Style Guide v5, HSRAC, 2017, companion specification.)
15. Health Canada. *Table of Reference Amounts for Food.* Ottawa: Health Canada; 2016.
16. Rana H, Mallet M-C, Gonzalez A, Verreault M-F, St-Pierre S. Free sugars consumption in Canada. *Nutrients.* 2021;13(5):1471. doi:10.3390/nu13051471.
17. Statistics Canada. *Canadian Community Health Survey – Nutrition, 2015: Public-Use Microdata File User Guide.* Catalogue 82M0024X. Ottawa: Statistics Canada; 2017.
18. Zhang S, Krebs-Smith SM, Midthune D, Perez A, Buckman DW, Kipnis V, et al. Fitting a bivariate measurement error model for episodically consumed dietary components. *Int J Biostat.* 2011;7(1):Article 1. doi:10.2202/1557-4679.1267.
19. Krebs-Smith SM, Pannucci TE, Subar AF, et al. Update of the Healthy Eating Index: HEI-2015. *J Acad Nutr Diet.* 2018;118(9):1591–1602. (Cited via NCI MCMC episodically-consumed threshold; B7 Methods p. 583.)

**Pending retrieval (★ — Groups C / D / E / F / G / H / I):**

20. ★ Stylianou KS, Heller MC, Fulgoni VL, Ernstoff AS, Keoleian GA, Jolliet O. A life cycle assessment framework combining nutritional and environmental health impacts of diet: a case study on milk. *Int J Life Cycle Assess.* 2016;21:734–746.
21. ★ Stylianou KS, et al. Small targeted dietary changes can yield substantial gains for human health and the environment. *Nature Food.* 2021;2:616–627. doi:10.1038/s43016-021-00343-4.
22. ★ Stylianou KS, et al. The complementarity of nutrient density and disease burden for Nutritional Life Cycle Assessment. *Front Sustain Food Syst.* 2024;8:1304752.
23. ★ Heller MC, Keoleian GA, Willett WC. Toward a life cycle–based, diet-level framework for food environmental impact and nutritional quality assessment. *Environ Sci Technol.* 2013;47(22):12632–12647.
24. EAT–Lancet Commission 2.0 (Rockström J, et al.). The EAT–Lancet Commission on healthy, sustainable, and just food systems. *Lancet.* 2025. doi:10.1016/S0140-6736(25)01201-2.
25. ★ Heijungs R. On the number of Monte Carlo runs needed to compare the impacts of alternatives in LCA. *Int J Life Cycle Assess.* 2020;25:394–402.
26. ★ Kim A. Global sensitivity analysis of correlated uncertainties in life cycle assessment. *J Ind Ecol.* 2025. doi:10.1111/jiec.70036.
27. ★ Lo Piano S, Saltelli A. Two-dimensional Monte Carlo simulations in LCA. *Int J Life Cycle Assess.* 2022. doi:10.1007/s11367-022-02041-0.
28. Saltelli A, et al. *Global Sensitivity Analysis: The Primer.* Chichester: Wiley; 2008.
29. ★ Wijesinghe DGNG, et al. Large Language Models for Real-World Nutrition Assessment: Structured Prompts, Multi-Model Validation and Expert Oversight. *Nutrients.* 2026;18(1):23.
30. ★ NutriRAG authors. NutriRAG: Unleashing the Power of Large Language Models for Food Identification and Classification through Retrieval Methods. 2025. PMC PMC11957177.
31. ★ FoodyLLM authors. FoodyLLM. 2025. PMC PMC12927182.
32. ★ Boulay AM, et al. The WULCA consensus characterization model for water scarcity footprints: AWaRe. *Int J Life Cycle Assess.* 2018;23:368–378.
33. ★ ECCC. *Guidance on the social cost of greenhouse gas emissions.* Ottawa: Government of Canada; 2023.
34. ★ ECCC. *National Inventory Report 1990–2022: Canada's GHG sources and sinks.* Ottawa: Government of Canada; 2024.
35. ★ Statistics Canada. *Census of Agriculture.* Ottawa: StatCan; 2024.
36. IPCC. *Climate Change 2022: Mitigation of Climate Change. Contribution of Working Group III to the Sixth Assessment Report.* Ch. 5: Demand, services and social aspects of mitigation. Geneva: IPCC; 2022.
37. Strubell E, Ganesh A, McCallum A. Energy and Policy Considerations for Modern Deep Learning Research. *Proc AAAI Conf Artif Intell.* 2020;34(09):13693–13696.
38. Patterson D, Gonzalez J, Le Q, et al. Carbon Emissions and Large Neural Network Training. arXiv:2104.10350; 2021.
39. Li P, Yang J, Islam MA, Ren S. Making AI Less "Thirsty". arXiv:2304.03271; 2023.

*Three wishlist corrections discovered during Group B extraction: (a) B7 pagination is 582–594, not 611–624; (b) the Canadian Food Intake Screener paper is led by Hutchinson, not Lamarche; (c) Food Compass 2.0, FCS-10 and the i.FCS validation paper are led by Barrett, Barrett, and O'Hearn respectively, not Mozaffarian. References 20–39 will receive page-cited specificity as the remaining PDFs arrive (see `literature_extractions.md`).*

---

*End of working draft v0.1 — sections §4 and §5 to be filled after Scenarios S1–S8 (see `scenarios.md`); reference list to be expanded once McGill PDFs are retrieved (see `literature_wishlist.md`).*
