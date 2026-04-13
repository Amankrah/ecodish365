# FCS update — Phase 0: scope and decisions

**Rust integration (HSR-style):** see [`FCS_RUST_INTEGRATION_PLAN.md`](FCS_RUST_INTEGRATION_PLAN.md).

Phase 0 locks **what** we are changing before touching code (Phase 1+).

**Exit criterion:** this document has **explicit choices** for each section below (no "TBD" in critical paths).

---

## 1. Primary goal (pick one lead; others can be secondary)

| Track | Description | Lead? (check one column) |
|-------|-------------|-------------------------|
| **A. Science / methodology** | Change FCS 2.0 rules: reference targets, domain weights, attribute lists, NOVA handling, 1–100 mapping. | [ ] |
| **B. Engineering** | Keep current methodology; improve tests, logging, structure, optional Rust for numeric core, performance. | [ ] |
| **C. Product / API** | Response shape, versioning field, batch/compare UX, errors, documentation for clients. | [ ] |

**Lead track for this effort:** _______________________

**Secondary tracks:** _______________________

---

## 2. Science / methodology (only if Track A is in scope)

- **Reference document:** (paper, internal spec, spreadsheet — link or path):  
  _______________________

- **Frozen behaviors to verify or change:**
  - [ ] `REFERENCE_TARGETS` in `fcs/constants/reference_targets.py`
  - [ ] Beneficial / harmful / ratio attribute lists in `FoodAnalyzer.get_attribute_type`
  - [ ] Domain aggregation in `FoodAnalyzer.calculate_original_score` (means, top-5, half-weights)
  - [ ] Final mapping in `FoodAnalyzer.calculate_fcs` (current linear map using -70 / +70)
  - [ ] NOVA / processing scoring alignment with integrator outputs

- **Acceptable drift:** e.g. "±1 FCS points vs current for regression set" — define:  
  _______________________

---

## 3. Engineering (only if Track B is in scope)

- [ ] Golden regression tests (food IDs + expected FCS / domains)
- [ ] Replace `print` debug in `calculate_fcs` with `logging`
- [ ] Request timing logs (CNF/integrator vs analyzer), similar to HSR
- [ ] Optional: port pure scoring to `rust_core` after tests exist

**Non-goals (explicitly out of scope):** _______________________

---

## 4. Product / API (only if Track C is in scope)

- [ ] Expose `fcs_model_version` (or `algorithm_version`) on responses
- [ ] Standardize error JSON across `fcs_calculate`, batch, compare
- [ ] Document breaking changes (if any) for frontend

**Consumers:** (web app only / public API / both):  
_______________________

---

## 5. Constraints and dependencies

- **Data:** CNF under `backend/raw_cnf` — same as today? [ ] yes [ ] no — changes: ___________

- **Python:** min version aligned with `backend/requirements.txt`

- **Timeline / milestone:** _______________________

- **Owner / reviewers:** _______________________

---

## 6. Phase 0 sign-off

When the tables above are filled and stakeholders agree:

| Name | Role | Date | Approved |
|------|------|------|----------|
| | | | [ ] |

**Next step:** Phase 1 — baseline tests + logging cleanup (unless Track A requires a methodology doc first).

---

## 7. Quick default if you want to move fast

If there is **no new FCS paper** driving changes:

- Set **Track B (Engineering)** as lead.
- **Track C** light: version field + errors.
- **Track A:** verify only; no target changes until a written spec exists.

Then proceed to Phase 1.
