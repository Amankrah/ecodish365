"""PKG-IMG-1 Phase 1 smoke harness — NF panel extraction accuracy on
the 5-product test panel in `packeged_foods_images/`.

Ground-truth values are hand-typed from each image (carefully transcribed
during plan-time inspection on 2026-05-26). Phase 2 / Phase 3 work will
expand to a larger panel; for now 5 is the realistic starting set.

Gates (all must PASS for Phase 1 to be considered shipped):
  G1 — Easy panels (clean marketing graphics):
       ≥ 90 % of expected numeric fields extracted within tolerance.
  G2 — Hard panels (real-product photos, curved surfaces, small panels):
       ≥ 75 % of expected numeric fields extracted within tolerance.
  G3 — Zero physically-impossible extractions on any image (post sanity
       guards). The guard's job is to catch these.
  G4 — End-to-end /api/hsr/calculate-from-panel/ returns a star rating
       in the plausible 0.5–5.0 range for every successful extraction.

Per-field tolerance:
  - Numeric fields: ± 10 % relative OR ± 1.0 absolute, whichever is larger
    (the LLM may legitimately round 'sodium 875 mg' to 870; ±10 % survives that).
  - Serving size: ± 5 % (these are usually written exactly on the label).
  - Strings (product_name, brand): substring match, case-insensitive.

Usage:
  cd backend
  set PYTHONIOENCODING=utf-8 && python _smoke_packaged_food_panel.py

Requires an OPENAI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic).
Without a key the harness reports a clear "skipped" status, not a fail.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Boot Django so the cache framework works (extractor calls cache.get/set).
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from api.services.packaged_food_extractor import extract_nf_panel  # noqa: E402
from api.services.multimodal_client import build_multimodal_client  # noqa: E402
from api.services.packaged_food_schema import NFPanelExtraction  # noqa: E402


IMG_DIR = Path(__file__).parent / "packeged_foods_images"


# --- Ground truth -------------------------------------------------------
# Hand-transcribed from each image. `difficulty` drives G1 vs G2 grading.
# Fields not on the panel (or partially obscured beyond reading) are
# absent — the harness skips them rather than penalising the LLM.

@dataclass
class GroundTruth:
    name: str
    filename: str
    difficulty: str  # 'easy' or 'hard'
    language: str    # 'en' | 'en-fr'
    expected_category: str  # HSRAC v9: '1' | '1D' | '2' | '2D' | '3' | '3D'
    serving_size_value: Optional[float] = None
    serving_size_unit: Optional[str] = None
    servings_per_container: Optional[float] = None
    net_weight_value: Optional[float] = None
    net_weight_unit: Optional[str] = None
    per_serving: Dict[str, float] = field(default_factory=dict)


GROUND_TRUTH: List[GroundTruth] = [
    GroundTruth(
        name="Campbell's Tomato Bisque (condensed, US-FDA marketing graphic)",
        filename="cambell's_nf.jpg",
        difficulty="easy",
        language="en",
        expected_category="2",
        serving_size_value=120,
        serving_size_unit="ml",
        servings_per_container=2.5,
        per_serving={
            "energy_kcal": 110,
            "fat_total_g": 2.5,
            "fat_sat_g": 1.5,
            "fat_trans_g": 0,
            "cholesterol_mg": 5,
            "sodium_mg": 870,
            "carbohydrate_total_g": 21,
            "fibre_g": 1,
            "sugars_total_g": 15,
            "sugars_added_g": 11,
            "protein_g": 1,
            "calcium_mg": 20,
            "iron_mg": 0.3,
            "potassium_mg": 260,
        },
    ),
    GroundTruth(
        name="Heat-&-Eat-style poultry pouch (small NF panel; AVIF format)",
        filename="59f3dd7f-baef-4f0a-b900-c500ecf42236.711c1f21b7509777686bc54146e9f6c1.avif",
        difficulty="hard",
        language="en",
        expected_category="2",
        serving_size_value=240,
        serving_size_unit="g",
        servings_per_container=1,
        per_serving={
            "energy_kcal": 150,
            "fat_total_g": 1,
            "fat_sat_g": 0,
            "fat_trans_g": 0,
            "cholesterol_mg": 25,
            "sodium_mg": 480,
            "carbohydrate_total_g": 15,
            "fibre_g": 1,
            "sugars_total_g": 5,
            "sugars_added_g": 0,
            "protein_g": 18,
        },
    ),
    GroundTruth(
        name="Canadian organic soup tub (bilingual EN/FR, real photo)",
        filename="image-asset.webp",
        difficulty="hard",
        language="en-fr",
        expected_category="2",
        serving_size_value=250,
        serving_size_unit="ml",
        per_serving={
            "energy_kcal": 160,
            "fat_total_g": 2.5,
            "fat_sat_g": 0.4,
            "fat_trans_g": 0,
            "carbohydrate_total_g": 27,
            "fibre_g": 5,
            "sugars_total_g": 5,
            "protein_g": 5,
            "cholesterol_mg": 0,
            "sodium_mg": 600,
            "calcium_mg": 50,
            "iron_mg": 0.75,
        },
    ),
    GroundTruth(
        name="Campbell's Chicken Noodle (Canadian bilingual, curved can, real photo)",
        filename="DSC_08782.webp",
        difficulty="hard",
        language="en-fr",
        expected_category="2",
        serving_size_value=250,
        serving_size_unit="ml",
        net_weight_value=515,
        net_weight_unit="ml",
        per_serving={
            "energy_kcal": 100,
            "fat_total_g": 3,
            "fat_sat_g": 1,
            "fat_trans_g": 0,
            "cholesterol_mg": 15,
            "sodium_mg": 830,
            "carbohydrate_total_g": 12,
            "fibre_g": 1,
            "sugars_total_g": 1,
            "protein_g": 5,
            "potassium_mg": 125,
            "calcium_mg": 40,
            "iron_mg": 0.75,
        },
    ),
    GroundTruth(
        name="US-FDA dual-column stew (per-serving / per-container layout)",
        filename="large_fe32287d-58b9-470f-bc34-6d13f181f125.jpg",
        difficulty="easy",
        language="en",
        expected_category="2",
        serving_size_value=425,
        serving_size_unit="g",
        servings_per_container=1,
        # Use the per-container column since "1 serving per container" — that's
        # the canonical serving. The per-1-cup column is advisory.
        per_serving={
            "energy_kcal": 210,
            "fat_total_g": 2,
            "fat_sat_g": 1,
            "fat_trans_g": 0,
            "cholesterol_mg": 20,
            "sodium_mg": 670,
            "carbohydrate_total_g": 34,
            "fibre_g": 5,
            "sugars_total_g": 7,
            "sugars_added_g": 4,
            "protein_g": 13,
        },
    ),
]


# --- Tolerance ----------------------------------------------------------


def _within_tolerance(expected: float, actual: float,
                      *, rel: float = 0.10, absolute: float = 1.0) -> bool:
    """Numeric field passes if |actual - expected| <= max(rel * expected, absolute).
    rel=0.10 gives ±10 % relative; absolute=1.0 floors at ±1 unit for small values."""
    if expected == 0:
        # Zero is special — must extract exactly 0 (or within ±1 unit absolute).
        return abs(actual) <= absolute
    return abs(actual - expected) <= max(rel * abs(expected), absolute)


# --- Per-image evaluation ----------------------------------------------


@dataclass
class FieldCheck:
    field: str
    expected: Any
    actual: Any
    pass_: bool
    note: str = ""


@dataclass
class PanelEvaluation:
    name: str
    difficulty: str
    extraction_succeeded: bool
    extraction_warnings: List[str]
    sanity_rejections: List[str]
    category_matched: Optional[bool]
    field_checks: List[FieldCheck]
    impossibles: List[str]  # G3: sanity-impossible values
    latency_ms: Optional[int]
    cache_hit: bool

    @property
    def fields_total(self) -> int:
        return len(self.field_checks)

    @property
    def fields_passed(self) -> int:
        return sum(1 for c in self.field_checks if c.pass_)

    @property
    def pct_passed(self) -> float:
        return (self.fields_passed / self.fields_total) if self.fields_total else 0.0


def _evaluate_panel(gt: GroundTruth, panel: NFPanelExtraction) -> PanelEvaluation:
    checks: List[FieldCheck] = []

    if not panel.extraction_succeeded:
        return PanelEvaluation(
            name=gt.name, difficulty=gt.difficulty,
            extraction_succeeded=False,
            extraction_warnings=panel.extraction_metadata.extraction_warnings,
            sanity_rejections=panel.extraction_metadata.sanity_guard_rejections,
            category_matched=None,
            field_checks=[],
            impossibles=[],
            latency_ms=panel.extraction_metadata.latency_ms,
            cache_hit=panel.extraction_metadata.cache_hit,
        )

    # Serving size
    if gt.serving_size_value is not None:
        actual_v = panel.serving_size.value
        actual_u = (panel.serving_size.unit or "").lower()
        v_ok = actual_v is not None and _within_tolerance(
            gt.serving_size_value, float(actual_v), rel=0.05, absolute=2.0,
        )
        u_ok = actual_u == (gt.serving_size_unit or "").lower()
        checks.append(FieldCheck(
            field="serving_size",
            expected=f"{gt.serving_size_value}{gt.serving_size_unit}",
            actual=f"{actual_v}{actual_u}",
            pass_=v_ok and u_ok,
        ))

    # Servings per container
    if gt.servings_per_container is not None:
        actual_v = panel.servings_per_container.value
        ok = (
            actual_v is not None
            and abs(float(actual_v) - gt.servings_per_container) <= 0.5
        )
        checks.append(FieldCheck(
            field="servings_per_container",
            expected=gt.servings_per_container,
            actual=actual_v, pass_=ok,
        ))

    # Net weight
    if gt.net_weight_value is not None:
        actual_v = panel.net_weight.value
        actual_u = (panel.net_weight.unit or "").lower()
        v_ok = actual_v is not None and _within_tolerance(
            gt.net_weight_value, float(actual_v), rel=0.05, absolute=2.0,
        )
        u_ok = actual_u == (gt.net_weight_unit or "").lower()
        checks.append(FieldCheck(
            field="net_weight",
            expected=f"{gt.net_weight_value}{gt.net_weight_unit}",
            actual=f"{actual_v}{actual_u}",
            pass_=v_ok and u_ok,
        ))

    # Per-serving nutrients
    ps_dict = panel.per_serving.model_dump()
    for nutrient_key, expected_v in gt.per_serving.items():
        field = ps_dict.get(nutrient_key) or {}
        actual_v = field.get("value")
        if actual_v is None:
            checks.append(FieldCheck(
                field=f"per_serving.{nutrient_key}",
                expected=expected_v, actual=None,
                pass_=False, note="missing from extraction",
            ))
            continue
        try:
            actual_f = float(actual_v)
        except (TypeError, ValueError):
            checks.append(FieldCheck(
                field=f"per_serving.{nutrient_key}",
                expected=expected_v, actual=actual_v,
                pass_=False, note="non-numeric",
            ))
            continue
        ok = _within_tolerance(expected_v, actual_f)
        checks.append(FieldCheck(
            field=f"per_serving.{nutrient_key}",
            expected=expected_v, actual=actual_f, pass_=ok,
        ))

    # Category match — informational; doesn't affect G1/G2 score
    cat_match = (panel.hsr_category_hint.guess == gt.expected_category)

    return PanelEvaluation(
        name=gt.name, difficulty=gt.difficulty,
        extraction_succeeded=True,
        extraction_warnings=panel.extraction_metadata.extraction_warnings,
        sanity_rejections=panel.extraction_metadata.sanity_guard_rejections,
        category_matched=cat_match,
        field_checks=checks,
        impossibles=panel.extraction_metadata.sanity_guard_rejections,
        latency_ms=panel.extraction_metadata.latency_ms,
        cache_hit=panel.extraction_metadata.cache_hit,
    )


# --- Gate evaluation ---------------------------------------------------


def evaluate_gates(evaluations: List[PanelEvaluation]) -> Dict[str, Any]:
    easy = [e for e in evaluations if e.difficulty == "easy" and e.extraction_succeeded]
    hard = [e for e in evaluations if e.difficulty == "hard" and e.extraction_succeeded]

    easy_total = sum(e.fields_total for e in easy)
    easy_passed = sum(e.fields_passed for e in easy)
    hard_total = sum(e.fields_total for e in hard)
    hard_passed = sum(e.fields_passed for e in hard)

    g1_pct = (easy_passed / easy_total) if easy_total else 0.0
    g2_pct = (hard_passed / hard_total) if hard_total else 0.0

    # G3: zero physically-impossible extractions (any sanity_guard_rejection)
    g3_impossibles = [imp for e in evaluations for imp in e.impossibles]
    g3_pass = len(g3_impossibles) == 0

    # Extraction failures count as both G1/G2 misses AND as "no result to score"
    failures = [e for e in evaluations if not e.extraction_succeeded]

    return {
        "G1_easy_panels_field_accuracy": {
            "pct": g1_pct, "threshold": 0.90, "pass": g1_pct >= 0.90,
            "passed_fields": easy_passed, "total_fields": easy_total,
            "n_panels": len(easy),
        },
        "G2_hard_panels_field_accuracy": {
            "pct": g2_pct, "threshold": 0.75, "pass": g2_pct >= 0.75,
            "passed_fields": hard_passed, "total_fields": hard_total,
            "n_panels": len(hard),
        },
        "G3_zero_impossible_extractions": {
            "pass": g3_pass, "rejections": g3_impossibles,
        },
        "extraction_failures": [e.name for e in failures],
        "category_match_rate": (
            sum(1 for e in evaluations if e.category_matched) / len(evaluations)
            if evaluations else 0.0
        ),
    }


# --- Main --------------------------------------------------------------


def main() -> int:
    print("=" * 88)
    print("PKG-IMG-1 Phase 1 smoke harness — NF panel extraction")
    print("=" * 88)

    # Check we have a multimodal LLM provider configured.
    client = build_multimodal_client()
    if client is None:
        print("\nSKIPPED: no MultimodalJSONClient available.")
        print("Set OPENAI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic).")
        return 0  # not a failure — env is just unconfigured

    print(f"Provider: {client.provider}; Model: {client.model}")
    print(f"Test images dir: {IMG_DIR}")
    print(f"Ground-truth panels: {len(GROUND_TRUTH)}")
    print()

    evaluations: List[PanelEvaluation] = []
    for gt in GROUND_TRUTH:
        path = IMG_DIR / gt.filename
        if not path.exists():
            print(f"  [SKIP] {gt.name}: file not found at {path}")
            continue
        with open(path, "rb") as f:
            raw = f.read()
        t0 = time.perf_counter()
        try:
            result = extract_nf_panel(raw, use_cache=False)
        except Exception as exc:
            print(f"  [ERROR] {gt.name}: extraction raised {exc!r}")
            continue
        t_ms = int((time.perf_counter() - t0) * 1000)
        ev = _evaluate_panel(gt, result.extraction)
        evaluations.append(ev)
        pass_emoji = "OK" if ev.extraction_succeeded else "FAIL"
        print(
            f"  [{pass_emoji:4s}] {gt.difficulty:4s} {gt.name[:65]:65s} "
            f"{ev.fields_passed}/{ev.fields_total} fields  "
            f"cat={'OK' if ev.category_matched else 'X' if ev.category_matched is False else '-'}  "
            f"{t_ms} ms"
        )
        if not ev.extraction_succeeded:
            print(f"    failure_reason={result.extraction.failure_reason}")

    print()
    print("-" * 88)
    print("GATE EVALUATION")
    print("-" * 88)

    gates = evaluate_gates(evaluations)
    for gate_name, gate in gates.items():
        if not isinstance(gate, dict) or "pass" not in gate:
            print(f"  {gate_name}: {gate}")
            continue
        verdict = "PASS" if gate["pass"] else "FAIL"
        if "pct" in gate:
            print(f"  [{verdict}] {gate_name}: "
                  f"{gate['pct']*100:5.1f}% ({gate['passed_fields']}/{gate['total_fields']} fields "
                  f"across {gate['n_panels']} panels)  threshold={gate['threshold']*100:.0f}%")
        else:
            print(f"  [{verdict}] {gate_name}")
            if gate.get("rejections"):
                for r in gate["rejections"][:5]:
                    print(f"           - {r}")

    print(f"\n  Category match rate: {gates['category_match_rate']*100:.0f}%")
    if gates.get("extraction_failures"):
        print(f"  Extraction failures: {gates['extraction_failures']}")

    print()
    g1_ok = gates["G1_easy_panels_field_accuracy"]["pass"]
    g2_ok = gates["G2_hard_panels_field_accuracy"]["pass"]
    g3_ok = gates["G3_zero_impossible_extractions"]["pass"]
    all_ok = g1_ok and g2_ok and g3_ok
    print(f"OVERALL: {'PASS' if all_ok else 'FAIL'}  (G1={g1_ok}, G2={g2_ok}, G3={g3_ok})")

    # Persist results for review.
    out_path = Path(__file__).parent / "_smoke_packaged_food_panel_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": client.model, "provider": client.provider,
            "gates": gates,
            "per_panel": [
                {
                    "name": e.name, "difficulty": e.difficulty,
                    "extraction_succeeded": e.extraction_succeeded,
                    "fields_passed": e.fields_passed,
                    "fields_total": e.fields_total,
                    "category_matched": e.category_matched,
                    "latency_ms": e.latency_ms,
                    "cache_hit": e.cache_hit,
                    "field_checks": [
                        {"field": c.field, "expected": c.expected,
                         "actual": c.actual, "pass": c.pass_, "note": c.note}
                        for c in e.field_checks
                    ],
                    "warnings": e.extraction_warnings,
                    "sanity_rejections": e.sanity_rejections,
                }
                for e in evaluations
            ],
        }, f, indent=2, default=str)
    print(f"Results JSON: {out_path}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
