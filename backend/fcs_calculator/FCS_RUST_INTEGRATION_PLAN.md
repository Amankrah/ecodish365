# FCS Rust integration plan (HSR-style)

Goal: **canonical FCS 2.0 numeric scoring in `rust_core`**, same pattern as HSR: Python owns CNF I/O and building inputs; Rust owns deterministic math; **no duplicate Python scoring path** after cutover; **fail fast** if the extension is missing (clear `ImportError`).

---

## 1. Principles (match HSR)

| Concern | HSR pattern | FCS equivalent |
|--------|-------------|----------------|
| Canonical algo | `rust_core.hsr` | `rust_core.fcs` (new submodule) |
| Python role | Load data, call Rust, shape API responses | `cnf_data_integrator` fills `FoodItem`-shaped numbers; thin `FoodAnalyzer` delegates scoring |
| Fallback | None (import fails loudly) | None |
| Parity | `cargo test` + Python tests vs Rust | Golden vectors: same `attributes` + `processing_level` → same `original_score`, `fcs` |
| Config | Thresholds in Rust (`threshold_data.rs`) | `REFERENCE_TARGETS` + attribute class lists + domain weights live in Rust |

---

## 2. What moves to Rust (single source of truth)

From `fcs/analyzers/food_analyzer.py` today:

1. **Attribute classification** — beneficial / harmful / ratio sets (`get_attribute_type`).
2. **Per-attribute scoring** — `score_attribute` using low/high targets (`REFERENCE_TARGETS`).
3. **Domain aggregation** — `calculate_original_score` (means, top‑5, top‑3, food_ingredients sum, processing blend, half‑weights, weighted sum).
4. **1–100 mapping** — `calculate_fcs` (linear map, clamp `MIN_FCS`/`MAX_FCS`).

**Optional in Rust (recommended for one boundary):**

5. **NOVA display mapping** — `processing_level` → category label (today `categorize_nova`). Small; keeps `analyze_food_item` thin.

**Stays in Python:**

- `FoodItem` construction and **`cnf_data_integrator.extract_nutrients_enhanced`** (all CNF/pandas/heuristics).
- Django views (`fcs_views.py`), serializers, meal service glue.
- Any future LLM or rule-based *inputs* to attributes (still outputs floats into the Rust payload).

---

## 3. `rust_core` layout

Add a sibling to HSR:

```text
backend/rust_core/src/
  lib.rs                 # register `fcs` submodule + sys.modules["rust_core.fcs"]
  fcs/
    mod.rs # pyfunctions + register()
    reference_targets.rs # REFERENCE_TARGETS (from reference_targets.py)
    attribute_kind.rs    # Beneficial / Harmful / Ratio + name lists
    scoring.rs           # score_attribute, domain rollups, weighted_sum
    fcs_scale.rs         # original_score → FCS 1–100 + clamp
    nova.rs              # optional: processing_level → enum/name
```

Expose on `rust_core.fcs`, mirroring `rust_core.hsr`:

- `compute_fcs(attributes, processing_level) -> dict`  
  Keys at minimum: `original_score`, `fcs`, `nova_category` (string), optionally `domain_scores` for debugging/API parity.

**FFI input shape:** Prefer **`attributes` as the same nested structure as `FoodItem.attributes`** (`dict[str, dict[str, float]]`) so Python can pass `food_item.attributes` with minimal conversion. PyO3: walk dicts or accept JSON string if iteration cost matters (measure later).

---

## 4. Python integration (post–cutover)

1. **`fcs/providers/fcs_rust.py`** (or **`fcs/rust_backend.py`**)  
   - `try: from rust_core import fcs`  
   - else raise `ImportError` with `maturin develop` message (same wording style as HSR).

2. **`FoodAnalyzer`** becomes a thin façade:
   - `analyze_food_item(food_item)` → call `rust_core.fcs.compute_fcs(food_item.attributes, food_item.get_nova_processing_level())` → build the same response dict as today (`name`, `original_score`, `fcs`, `nova_category`, `processing_details` from Python only).
   - Remove in-Python `REFERENCE_TARGETS` usage for scoring (file can re-export constants for docs/tests only, or delete from Python).

3. **Views** (`api/views/fcs_views.py`): no change to HTTP contract if response shape stays the same.

4. **`meals/services.py`**: still uses `FoodAnalyzer`; no duplicate math.

---

## 5. Phased delivery

| Phase | Work | Exit |
|-------|------|------|
| **A — Lock behavior** | Golden tests in Python: fixed `food_ids` → integrator → snapshot `original_score`, `fcs`, optional domain breakdown. | Done: same test module + food `29` golden vector. |
| **B — Rust port** | Implement `fcs` module; `cargo test` with unit tests for `score_attribute`, each domain rule, clamping. | Done: `rust_core/src/fcs/` + `cargo test` green. |
| **C — PyO3 + parity** | `compute_fcs` exposed; Python test loops golden vectors and asserts `abs(py - rust) < epsilon` (or exact for deterministic floats). | Done: `fcs_calculator/tests/test_fcs_rust.py` (golden food `29`). |
| **D — Cutover** | `FoodAnalyzer` calls Rust only; delete Python scoring implementation; mandatory import. | Done: thin `food_analyzer.py`; fail-fast `ImportError` without `rust_core`. |
| **E — Hardening** | Replace `print` debug with `logging`; optional FCS timing logs in `fcs_views` (like HSR). | Clean logs; optional perf metrics. |

Phase **A** can run **in parallel** with **B** once3–5 representative foods are chosen (single food, mixed `processing_level`, edge clamp).

---

## 6. Parity and numerical notes

- Use **f64** throughout Rust; round `fcs` to2 decimals in Rust to match `round(fcs_clamped, 2)`.
- Division-by-zero: mirror Python’s `(high - low)` guards if any target pair can be equal (today targets look strictly ordered).
- **Processing domain** custom blend (NOVA full weight, fermentation/frying half, etc.) must be line-by-line ported; add a dedicated Rust test with a fixed `processing` dict.

---

## 7. Out of scope (for this integration)

- Changing FCS 2.0 *methodology* (targets/weights) unless tracked separately (see `FCS_PHASE0_SCOPE.md`).
- Moving CNF/pandas into Rust (large effort; not required for parity or speedup of the scoring core).

---

## 8. Reference files (Python, pre–cutover)

| File | Role |
|------|------|
| `fcs/constants/reference_targets.py` | Source for `reference_targets.rs` |
| `fcs/analyzers/food_analyzer.py` | Logic to port |
| `fcs/models/food_item.py` | Schema for `attributes` |
| `rust_core/src/lib.rs`, `rust_core/src/hsr/mod.rs` | Pattern for submodule registration |

---

## 9. Status and next step

Phases **A–D** are implemented; regression coverage lives in `fcs_calculator/tests/test_fcs_rust.py` (run: `python manage.py test fcs_calculator.tests.test_fcs_rust`).

**Remaining:** **Phase E** (logging / optional FCS timing in `fcs_views` like HSR) and occasional smoke checks on `api/views/fcs_views.py` and `meals/services.py` FCS paths after releases.
