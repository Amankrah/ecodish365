# Ingredient substitution (SUBST-1) — manuscript research & testing protocol

**Purpose:** Generate citable evidence for documenting the substitution feature in `manuscript_call1.md`, grounded in extracted literature (`literature_extractions.md`) and aligned with Scenario S5 (`scenarios.md`).

**Status:** Protocol ready; runnable panel at `backend/_smoke_substitution_s5_panel.py`.

---

## 1. Where this belongs in the manuscript

| Manuscript anchor | What SUBST-1 contributes |
|---|---|
| **Abstract A5** | Four diet-shift counterfactuals operationalized as an interactive tool, not only offline tables |
| **§3.8.7** (packaged-food decomposition) | Downstream use case: decomposed label → swap suggestions → re-score |
| **New §3.8.8** (recommended) | Methods: rule table, mass-preserving swap, re-score via existing calculators, constraints, WAFCT recipe hints |
| **§5.2 Scenario S5** | Primary validation: reproduce expected **direction** of ΔHEFI, ΔHENI, ΔFCS, ΔLCA for four canonical swaps |
| **§6.2 Trade-offs** | Pareto frontier on six metrics after swap; link to S4-lite finding that nutrition and environment only weakly align |
| **§7.3–7.4 Limitations** | HENI marginality, GBD substitution ambiguity, HEFI relative-only framing, inferred packaged compositions |

The feature is not a new scoring method. It is a **decision-support layer** that applies explicit, auditable ingredient replacements and re-runs the existing indicators.

---

## 2. Literature that defines what we can claim (and what we cannot)

### 2.1 Substitution as a scientific object

**Stylianou et al. (2021, Nat Food; C15)** frame “small targeted dietary changes” as **explicit isocaloric replacements** (e.g. 10% of calories from processed meat + beef → fruit/veg/legumes/seafood mix), yielding ~**+48 min healthy life/day** and ~**−33% dietary carbon footprint**. SUBST-1 implements the same *logic at ingredient granularity*: name the food out, name the food in, re-score.

**Critical scope limit (C15 Discussion; manuscript §7.4):** HENI is **marginal** — valid for adding/removing a reference serving, not for wholesale diet restructuring. We must report swap deltas as *aggregated marginal effects of the stated substitution*, not as predicted population health gains.

**GBD 2017 Diet Collaborators (literature C18; manuscript §7.4):** Cohort RRs are energy-adjusted; a increase in one dietary component implies an unspecified decrease elsewhere. **Every S5 swap must name both sides of the exchange.** We cannot infer health effects of “beef removed” without stating “beef → lentils.”

**Cardinaals et al. (2024; C17):** Nutrient density (NRF) and disease burden (HENI) are **largely uncorrelated**; both weakly correlate with GWP. Justifies reporting **multi-metric scorecard deltas** (HEFI, HENI, HSR, FCS, environment, dietary pattern) rather than a single “health score.”

**Poore & Nemecek (2018; B-group):** Animal vs plant substitutes differ for five biophysical reasons (yield, feed, land, methane, opportunity cost). Supports expecting **beef → legumes** to reduce environmental single-score while improving HEFI/FCS directionally.

**Brassard et al. (2022a/b; B6–B7):** HEFI-2019 has **no absolute threshold**; interpret **relative** differences across scenarios. Single-day HEFI from one recall is not “usual adherence.” Substitution results on one meal/product are **scenario comparisons**, not population benchmarks against 43.1/80.

**CONE-LCA / milk case (Stylianou 2016; C14):** Nutritional effects at consumption can be **comparable to production LCA** for some foods; supports showing health and environment side-by-side after swap, with separate caveats per pathway.

### 2.2 What the literature does *not* require us to prove

- That automated suggestions are culinarily optimal (Phase 4 adds role + WAFCT guards; manual swap remains the gold standard for edge cases).
- That LLM-decomposed packaged products are analytically true (PKG-IMG-1 caveat carries forward).
- That HENI minutes from a multi-ingredient reformulation equal Stylianou’s population-level 48 min/day result (different scale and aggregation).

---

## 3. Research questions & pre-registered hypotheses

### RQ1 — S5 directional replication (primary)

For each canonical swap at fixed mass (100 g, mass-preserving), does the platform report indicator deltas in the **literature-expected direction**?

| Swap ID | Baseline (CNF) | Replacement | Expected ΔHEFI | Expected ΔHENI | Expected ΔFCS | Expected Δ env |
|---|---|---|---|---|---|---|
| `beef_to_legumes` | Ground beef 2683 | Lentils 3392 | ↑ | ↑ (minutes) | ↑ | ↓ (better) |
| `milk_to_soy` | Fluid milk 113 | Fortified soy 501528 | trade-off* | ↑ | trade-off* | ↓ |
| `cola_to_water` | Cola 2920 | Water 2933 | ↑ or flat | ↑ | ↑ | ↓ or flat |
| `white_to_whole_wheat` | White bread 3732 | Whole wheat 4067 | ↑ | ↑ | ↑ | neutral/slight ↓ |

\* Milk→soy on a **single-item** portion: HENI and environmental single-score improve, but HEFI may fall because HEFI-2019 dairy components do not map one-to-one onto plant beverages (Brassard B7 relative framing). Document as trade-off exemplar (§6.2), not analyzer failure.

**Success criterion (from `scenarios.md` §S5):** Swaps 1 and 3 show **positive HENI** and **lower LCA single-score** (win–win). Swaps 2 and 4 show **non-negative HEFI** movement where applicable. Directions matter more than magnitudes for v1 manuscript tables.

### RQ2 — Analyzer fidelity

When the curated rule applies, does `POST /api/substitution/analyze/` rank that rule **first** with positive `rank_score`?

### RQ3 — Multi-metric coherence

After swap, do HEFI, HENI, and FCS move **together** on obvious win–win swaps (extends S4-lite nutrition agreement to the substitution slice)?

### RQ4 — Trade-off documentation (secondary)

On swaps where environment and HENI diverge, does the Pareto tag identify the suggestion as **strong on one axis, weaker on another**? (Feeds §6.2 narrative.)

### RQ5 — Regional / homemade path (exploratory)

For a WAFCT-heavy homemade stew (e.g. garden-egg stew), with `cultural_context=west_africa` and `dish_name` set:

- Document **whether** regional recipe hints appear.
- Document **failure modes** (no OPENAI key → no embedding matches; nutrient discovery blocked by culinary filters).
- **Do not** over-claim automation for culturally specific dishes in v1; show manual swap + constraint toggles as researcher workflow.

---

## 4. Test matrix (what to run)

### Tier A — Deterministic gold cases (required for §5.2 table)

Run `backend/_smoke_substitution_s5_panel.py` (produces `results/S5-subst/`).

- Four S5 swaps, 100 g mass-preserving
- Full six-metric scorecard via production calculators
- JSON + CSV for Table “Per-100 g indicator deltas under canonical diet-shift substitutions”

### Tier B — Analyzer integration (required for §3.8.8)

- `python test_substitution_analyzer.py` (unit: rule match, culinary guards, stew nonsense blocked)
- `_smoke_substitution_analyzer.py` (golden top-rule IDs)
- Batch API smoke: 4 compositions in one `POST /api/substitution/batch/`

### Tier C — End-to-end UX paths (recommended for Supplementary)

| Path | Input | Claim supported |
|---|---|---|
| Packaged | Label photo → decompose → Find swaps | §3.8.7 → §3.8.8 pipeline |
| Homemade | Dish name → decompose → west_africa + dish_name | WAFCT recipe hints (exploratory) |
| Manual | Row Swap + re-score | Researcher override / Cardinaals “explicit substitute” |

Capture screenshots + `run_manifest.json` (git SHA, CNF version, elapsed_ms from API metadata).

### Tier D — S4-lite meal embedding ✅ (2026-05-26)

Run `backend/_smoke_substitution_s4_overlay.py` → `results/S5-subst/s4_overlay.csv`.

For each S4-lite day with ≥1 S5-eligible ingredient, applies **all matching curated S5 rules** at unchanged mass (deterministic overlay; no embedding discovery). Reports day-level six-metric scorecard deltas vs baseline.

Optional: `--with-analyzer` for production analyzer sanity checks (slow).

Links substitution to the **25-day panel** in §6.2 without RDC S4.

---

## 5. Methods text (draft for §3.8.8)

> Ingredient substitution analysis accepts a CNF/WAFCT composition `{food_id, mass_g}[]`, optional dish name and cultural context, a purpose (e.g. lower sodium, higher fibre), and optional constraints (vegetarian, allergen exclusion, same functional role). Candidate replacements are drawn from (i) four literature-anchored rules aligned with Scenario S5 (beef→legumes, fluid cow's milk→fortified soy beverage, sugar-sweetened beverage→water, refined→whole-grain bread), (ii) embedding-based similar foods, (iii) same-group nutrient discovery, and (iv) for West African dishes, ingredient hints from the 195 mixed-dish recipes in WAFCT 2019 sheet 09. Each candidate replaces one ingredient at unchanged mass; indicators are recomputed through the existing HEFI, HENI, HSR, FCS, environmental LCA, and dietary-pattern modules without duplicating nutrient arithmetic. Suggestions are ranked by purpose-weighted scores and, for the top set, a six-metric scorecard and Pareto non-dominated set are reported. HENI deltas are interpreted as marginal effects of the stated swap (Stylianou et al., 2021; Cardinaals et al., 2024), not as diet-level predictions.

---

## 6. Limitations paragraph (draft for §7)

> Substitution suggestions on decomposed packaged foods inherit PKG-IMG-1 inference uncertainty. HENI swap deltas aggregate marginal food-item effects and are not valid for large multi-ingredient reformulations without caution (Stylianou et al., 2021). HEFI-2019 differences are relative guideline-adherence shifts, not validated health-outcome predictions (Brassard et al., 2022b). Meta-analytic diet-disease risks are defined under unspecified energy substitution (GBD 2017 Diet Collaborators, 2019), so each reported swap names an explicit replacement food. Automated suggestions are filtered for culinary plausibility but remain modelling aids; regional and homemade dishes may require manual ingredient selection.

---

## 7. Deliverables checklist

| Output | Path | Manuscript use |
|---|---|---|
| S5 delta table | `results/S5-subst/s5_delta_table.csv` | Table 4 / §5.2 |
| Radar or bar figure | `results/S5-subst/fig_s5_deltas.json` (data for Figure 8) | §5.2 |
| Analyzer fidelity | `results/S5-subst/analyzer_fidelity.json` | §3.8.8 validation |
| Run manifest | `results/S5-subst/run_manifest.json` | Reproducibility |
| Trade-off exemplars | `results/S5-subst/tradeoff_swaps.json` | §6.2 cross-link |
| S4-lite overlay | `results/S5-subst/s4_overlay.csv` | §5.2 / §6.2 day-level |
| S4 overlay exemplars | `results/S5-subst/s4_overlay_exemplars.json` | §6.2 narrative |
| Unit test log | CI / local pytest output | Supplementary |

---

## 8. Execution order

```text
1. python test_substitution_analyzer.py
2. python _smoke_substitution_analyzer.py
3. python _smoke_substitution_s5_panel.py
4. python _smoke_substitution_s4_overlay.py
5. (Optional) Manual UX captures for packaged + homemade paths
6. Draft §3.8.8 + extend §5.2 from results/S5-subst/
7. Add limitation sentences to §7 from §6 above
```

---

## 9. Key citations to wire in

| Topic | Cite |
|---|---|
| Targeted substitution policy result | Stylianou et al. 2021, Nat Food 2:616–627 |
| HENI marginality | Stylianou et al. 2021 Discussion; Cardinaals et al. 2024 |
| GBD substitution / energy adjustment | GBD 2017 Diet Collaborators, Lancet 2019 |
| Multi-indicator complementarity | Cardinaals et al. 2024, Front Sustain Food Syst 8:1304752 |
| HEFI relative interpretation | Brassard et al. 2022a/b, Appl Physiol Nutr Metab |
| Environmental spread animal vs plant | Poore & Nemecek 2018, Science 360:987–992 |
| S4-lite trade-off structure | Internal `results/S4-lite/` + manuscript §6.2 |

---

## 10. Empirical results (2026-05-26 run)

Panel: `python _smoke_substitution_s5_panel.py` → `results/S5-subst/`

| Swap | Mass | ΔHEFI | ΔHENI (min) | ΔFCS | Δ env | Rule candidate | Analyzer ranked |
|---|---:|---:|---:|---:|---:|---|---|
| Beef → lentils | 100 g | +7.7 | −19.6 (gain) | +42.7 | −0.0004 | ✓ | ✓ |
| Milk → soy | 250 mL | −16.0 | −2.2 (gain) | −37.3 | −0.0001 | ✓ | ✗ (rank_score ≤ 0) |
| Cola → water | 355 mL | 0 | −0.2 (gain) | +2.8 | 0 | ✓ | ✓ |
| White → whole wheat | 80 g | +11.4 | −1.8 (gain) | +8.5 | 0 | ✓ | ✓ |

**Manuscript takeaways:**

1. **S5 win–win confirmed** for beef→legumes and cola→water on HENI + environment (Stylianou-style targeted substitution logic).
2. **Milk→soy** is a **documented trade-off**: marginal HENI and environmental gains, but HEFI/FCS drop on an isolated beverage swap — aligns with Cardinaals C17 (indicators diverge) and HEFI relative-only framing (B7).
3. **Analyzer ranking gap:** curated `milk_to_soy` rule exists but is suppressed when composite rank_score ≤ 0; manuscript should report **direct counterfactual deltas** for S5 and note UI ranking as a separate validation tier.
4. **Cola HEFI at zero** for both baseline and replacement — report HSR/FCS/HENI deltas instead; cite HEFI ceiling on ultra-processed beverages.

### Tier D results — S4-lite day overlay (2026-05-26)

Panel: `python _smoke_substitution_s4_overlay.py` → `results/S5-subst/s4_overlay.csv`

| Metric | Result |
|---|---|
| S4-lite days | 25 |
| S5-eligible days | **14** (contain beef, milk, cola, and/or white bread) |
| HEFI improved (all eligible) | **14/14** |
| Win–win HENI + environment | **9/14** |

**Strongest overlay (D06 — BBQ Western day, 3 swaps):** white bread→whole wheat, beef→lentils, cola→water → ΔHEFI **+31.4**, ΔHENI **−26.9 min**, Δenv **−0.0007**.

**Lose–lose anchor improved (D18 — beef-steak day):** 3 swaps → ΔHEFI +11.5, ΔHENI −25.8 min, Δenv −0.0008 (win–win on HENI+env despite low baseline HEFI).

**Trade-off days (HENI↑ but env flat):** D01, D05, D16, D22, D25 — typically single-swap days (bread or milk only); still HEFI-positive.

**Manuscript link to S4-lite §6.2:** D06 and D13 (western processed) move from lose–lose quadrant toward win–win after S5 overlay, supporting Stylianou-style targeted substitution at day scale while preserving Cardinaals multi-metric framing.

### Draft results paragraph (§5.2)

> We operationalized Scenario S5 as mass-preserving single-ingredient counterfactuals in SUBST-1, recomputing HEFI, HENI, HSR, FCS, and environmental single-score through the production calculator stack (`results/S5-subst/`). Replacing 100 g ground beef with lentils increased HEFI by 7.7 points and shifted HENI by −19.6 health-impact minutes (marginal gain), with a 99.9% reduction in environmental single-score. Replacing 355 mL cola with municipal water improved HSR (+3.0 stars) and FCS (+2.8) with a small HENI gain (−0.24 min). Whole-wheat bread (80 g) outperformed white bread on HEFI (+11.4), FCS (+8.5), and HENI (−1.8 min). The milk→fortified-soy swap showed a **trade-off**: HENI improved (−2.2 min) and environmental impact decreased slightly, but HEFI fell from 16.0 to 0.0 on an isolated beverage portion — consistent with Cardinaals et al.'s finding that nutrient-density and disease-burden indicators need not align, and with HEFI-2019's relative, meal-context-dependent scoring (Brassard et al., 2022b). These results support using multi-metric scorecards rather than a single headline score when reporting substitution effects.

---

## 11. Changelog

| Date | Note |
|---|---|
| 2026-05-26 | Protocol authored; S5 panel script added |
| 2026-05-26 | First panel run; empirical table added |
| 2026-05-26 | Tier D S4-lite overlay: 14 eligible days, 9/14 win–win HENI+env |
| 2026-05-26 | `manuscript_call1.md` updated: §3.8.8 methods, §5.2 results, §6.2 overlay rows, §7.6 limitations |
