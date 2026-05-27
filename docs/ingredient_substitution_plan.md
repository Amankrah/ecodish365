# Ingredient Substitution Engine — Plan & Purpose

**Feature code:** `SUBST-1`  
**Status:** Phase 1 in progress (2026-05-26)  
**Related research:** Scenario S5 (`scenarios.md`), manuscript §3.8.7 (packaged-food decomposition)

---

## Purpose

Help users **improve the modelled nutrition of a packaged product or homemade meal** by suggesting evidence-backed ingredient swaps grounded in the Canadian Nutrient File (CNF) and West African Foods Composition Table (WAFCT).

### Who it serves

| Audience | Use case |
|---|---|
| **Consumers** | “Make this granola bar healthier” — scan label, get 1–3 swaps with plain-language impact |
| **Researchers** | Counterfactual diet shifts (S5), product reformulation modelling, trade-off analysis |
| **Policy / industry** | Directional reformulation scenarios with HEFI / HSR / FCS / environmental deltas |

### Inputs (all phases)

1. **Packaged product** — label photo(s) → NF panel + ingredient list → CNF decomposition (existing PKG-IMG-1 pipeline)
2. **Homemade meal** — free-text dish name + total mass → CNF recipe decomposition (existing AI-MATCH-1)
3. **Manual composition** — user-built `{ food_id, mass_g }[]` from CNF Explorer or recall handoff

### Outputs

- Baseline scores (HEFI, HSR, FCS, HENI, environmental, dietary pattern)
- Ranked substitution suggestions with before/after deltas
- Nutrient deltas (sodium, fibre, protein, sat fat, sugars, energy)
- Trade-off narrative when objectives conflict
- Optional apply → re-score → scorecard handoff

### Honest framing (non-negotiable)

- Packaged compositions are **inferred**, not measured (`packaged_food_inferred` caveat)
- Substitutions improve the **modelled** product, not a guaranteed real-world SKU
- HENI is **marginal** — large multi-ingredient reformulations carry the Stylianou caveat
- CNF ↔ WAFCT cross-swaps may reflect database bias, not true biological difference

---

## Architecture

```text
Input (scan / dish / manual)
        ↓
Existing decomposer → { food_id, mass_g, food_group, label_name }[]
        ↓
Substitution analyzer
  ├── Match ingredients to rule table + nutrient filters
  ├── Generate candidate replacements (same mass, mass-preserving)
  ├── Re-score via existing calculator endpoints (never duplicate nutrition math)
  └── Rank by user purpose
        ↓
UI: suggestions + apply + scorecard
```

### Core backend modules

| Module | Role |
|---|---|
| `api/services/substitution_rules.py` | Curated S5-style rules + purpose metadata |
| `api/services/substitution_analyzer.py` | Match → candidate → score → rank |
| `api/views/substitution_views.py` | `POST /api/substitution/analyze/` |
| `frontend/.../SubstitutionSuggestionsPanel.tsx` | Suggestion UI |
| `frontend/src/app/improve-product/page.tsx` | Primary user surface |

### Design principles

1. **Re-score, don’t reimplement** — HEFI/FCS/HSR/HENI/env math stays in existing calculators
2. **Mass-preserving swaps** — replace ingredient *i* with same `mass_g` unless user opts into reformulation
3. **Functional-role gating** — don’t suggest “sugar → lentils”; rules match food group + description patterns
4. **Purpose-aware ranking** — same candidates, different sort weights per objective
5. **Incremental phases** — each phase ships a usable feature

---

## Phases

### Phase 1 — Rule-based “Suggest 1 swap” (MVP) ✅ in progress

**Goal:** Prove end-to-end flow with curated S5 substitutions.

**Rules (v1):**

| ID | Source | Target | Purpose |
|---|---|---|---|
| `beef_to_legumes` | Beef Products (group 13) | Lentils, raw (3392) | general_health |
| `milk_to_soy` | Fluid cow’s milk (dairy, not plant) | Soy beverage, enriched (501528) | general_health |
| `cola_to_water` | Cola / sweetened soft drinks | Water, municipal (2933) | general_health, lower_sodium |
| `white_to_whole_wheat` | White bread (commercial) | Whole wheat bread, commercial (4067) | general_health, higher_fibre |

**Scoring (Phase 1):** HEFI before/after + nutrient deltas (sodium, fibre, protein, sat fat, sugars, energy).

**UI:** `/improve-product` — scan → decompose → composition table + suggestion panel → apply swap → route to scorecard.

**API:** `POST /api/substitution/analyze/`

```json
{
  "composition": [
    { "food_id": 2683, "mass_g": 50, "food_description": "...", "food_group": "Beef Products" }
  ],
  "purpose": "general_health",
  "max_suggestions": 3
}
```

**Success criterion:** User scans a product containing a rule-matched ingredient, sees ≥1 ranked swap with quantified HEFI delta.

---

### Phase 2 — Nutrient-targeted discovery ✅ shipped (2026-05-26)

**Goal:** Purpose picker drives candidate generation beyond the S5 table.

**Adds:**

- Purposes: `lower_sodium`, `higher_fibre`, `higher_protein`, `lower_sat_fat`, `diabetes_friendly`, `sustainability`
- Candidate pool from nutrient-range search + CNFMatcher alternatives (`substitution_discovery.py`)
- Per-row CNF swap via `AIEnhancedSearch` in composition forms
- Multi-swap suggestions (up to 2 ingredients via `constraints.max_swaps`)
- FCS before/after + group-level sustainability proxy for ranking

**API extensions:** `constraints` (`exclude_food_ids`, `source_filter`, `max_swaps`, `vegetarian`, `exclude_allergens`, `same_functional_role`); `include_scorecard`; `pareto_frontier` in response.

---

### Phase 3 — Product-level optimization ✅ (shipped)

**Goal:** Full scorecard delta + Pareto trade-offs.

**Adds:**

- All 6 scorers in before/after diff (`substitution_scorecard.py`)
- Pareto frontier (`substitution_pareto.py`) with UI badges
- Constraint engine: vegetarian, allergen exclude, same functional role (`substitution_constraints.py`)
- `POST /api/substitution/apply/` — re-score modified composition
- `POST /api/substitution/batch/` — researcher batch analyze
- `/scan-product` secondary tab “Improve nutrition” (`ImproveProductFlow`)

**Status:** Phase 3 complete.

---

### Phase 4 — Research-grade reformulation ✅ (shipped)

**Goal:** Multi-ingredient optimization and regional depth.

**Adds:**

- Functional role classification (oil stays oil, protein stays protein) when "Keep the same role" is checked
- WAFCT mixed-dish recipe hints for West African meals (`wafct_recipes.py`, 195 traditional recipes)
- Greedy multi-step reformulation plans (`reformulation_mode: greedy`, up to 4 swaps)
- `dish_name` + `cultural_context` on analyze API for regional matching
- User-facing copy refresh on `/improve-product` and `/scan-product`

**Remaining future work:** phytate/bioavailability, barcode/Open Food Facts, recall-history personalization, full LLM cultural classifier.

---

## API contract (stable across phases)

### `POST /api/substitution/analyze/`

**Request:**

| Field | Type | Required | Description |
|---|---|---|---|
| `composition` | `{food_id, mass_g, food_description?, food_group?, label_name?, position?}[]` | yes | Baseline CNF-mapped list |
| `purpose` | string | no | Default `general_health` |
| `max_suggestions` | int | no | Default 3, max 10 |
| `constraints` | object | no | Phase 2+: exclude_ids, source, max_swaps |

**Response:**

| Field | Description |
|---|---|
| `baseline.hefi` | HEFI total score + components |
| `baseline.nutrients` | Aggregated per-serving nutrients |
| `suggestions[]` | Ranked swaps with `rule_id`, ingredient index, target food, deltas |
| `purpose` | Echo |
| `metadata` | Rule version, foods evaluated, timing |

### `POST /api/substitution/apply/` (Phase 3)

Accept `modified_composition` → return full re-score + six-metric scorecard.

### `POST /api/substitution/batch/` (Phase 3)

Accept `items[]` with per-item `composition`, optional `label` / `purpose` → batch analyze results.

---

## Frontend surfaces

| Route | Phase | Description |
|---|---|---|
| `/improve-product` | 1 | Primary: scan or describe → suggest → apply |
| `/scan-product` | 3 | Add “Improve nutrition” tab alongside HSR |
| `/recall-24h` | 3 | “Suggest swap” on packaged occasion |
| `/cnf/compare` | 2 | Link from discover → substitution context |
| `/scorecard` | 1 | Handoff after apply |

---

## Testing strategy

| Layer | Phase 1 |
|---|---|
| Unit | Rule matching, mass-preserving replace, HEFI delta sign (beef→legumes improves HEFI) |
| Smoke | `_smoke_substitution_analyzer.py` on S5 canonical compositions |
| Integration | improve-product page → analyze API → apply → scorecard |
| Research | Reproduce S5 delta directions (beef→legumes: HENI↑, env↓) |

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| False confidence on inferred labels | Mandatory caveat banner; edit-before-suggest |
| Culinary nonsense swaps | Group + description gating; Phase 4 LLM role filter |
| HENI marginal misuse | Cap swap magnitude; existing HENI disclaimer |
| Performance (N×scorers) | Phase 1: HEFI + nutrients only; cache baseline |
| WAFCT/CNF bias | Prefer same `source`; flag cross-DB swaps (Phase 2) |

---

## File index (Phase 1)

```
docs/ingredient_substitution_plan.md          ← this document
backend/api/services/substitution_rules.py
backend/api/services/substitution_discovery.py
backend/api/services/substitution_analyzer.py
backend/api/views/substitution_views.py
backend/test_substitution_analyzer.py
backend/_smoke_substitution_analyzer.py
frontend/src/app/improve-product/page.tsx
frontend/src/components/shared/SubstitutionSuggestionsPanel.tsx
frontend/src/components/shared/ImproveProductFlow.tsx
frontend/src/lib/api.ts                       ← SubstitutionApiService types
```

---

## Changelog

| Date | Phase | Change |
|---|---|---|
| 2026-05-26 | 1 | Plan authored; Phase 1 implementation started |
| 2026-05-26 | 2 | Nutrient discovery, FCS scoring, multi-swap, manual row swap, constraints |
