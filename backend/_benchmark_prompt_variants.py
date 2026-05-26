"""PKG-IMG-1 Phase 2.x — A/B benchmark: prompt engineering vs current normaliser.

Runs 4 pipeline variants against the 5 ground-truth test images, N=3 runs per
(variant, image) cell. Decides whether to integrate the enhanced prompt, the
normaliser, or both.

Variants:
  V1: current COMBINED_SYSTEM_PROMPT v2 + normaliser ON   (production today)
  V2: current COMBINED_SYSTEM_PROMPT v2 + normaliser OFF  (normaliser ablation)
  V3: enhanced prompt (few-shot + schema-as-code + CoVe) + normaliser OFF
  V4: enhanced prompt + normaliser ON                     (belt-and-suspenders)

Per cell metrics:
  - schema_ok_pre_norm: raw LLM JSON validates against PackagedFoodExtraction
  - normaliser_fired:   true if applying the normaliser changed the dict (V1, V4 only)
  - extraction_succeeded_final: final validation + extraction_succeeded flag
  - field_accuracy:     fraction of ground-truth fields within tolerance
  - latency_ms:         wall time of the LLM call
  - tokens_estimated:   input (image + system + user) + output, rough estimate

Per variant aggregate: mean accuracy + min + max + per-image breakdown.

Usage:
  cd backend
  set PYTHONIOENCODING=utf-8 && python _benchmark_prompt_variants.py --runs 3

Requires OPENAI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic).
Without a key the benchmark reports a clear "skipped" status and exits 0.
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Boot Django (the extractor + schema imports need the cache backend even
# though we don't use it in the benchmark — use_cache=False everywhere).
# IMPORTANT: import env_bootstrap BEFORE django.setup() so .env vars
# (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) are loaded before settings
# reads them — mirrors the manage.py / wsgi.py boot order.
import dish_project.env_bootstrap  # noqa: F401  (side-effect import)
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

# Reuse the existing ground-truth + per-field comparison machinery.
from _smoke_packaged_food_panel import (  # type: ignore  # noqa: E402
    GROUND_TRUTH, GroundTruth, _within_tolerance, IMG_DIR,
)
from api.services.multimodal_client import (  # noqa: E402
    build_multimodal_client, normalize_image_bytes, MultimodalJSONClient,
)
from api.services.packaged_food_extractor import (  # noqa: E402
    normalise_llm_extraction, _apply_sanity_guards,
)
from api.services.packaged_food_prompts import (  # noqa: E402
    COMBINED_SYSTEM_PROMPT as PROMPT_V2_SYSTEM,
    build_combined_user_prompt as build_user_v2,
    PROMPT_VERSION as PROMPT_VERSION_V2,
)
from api.services.packaged_food_schema import (  # noqa: E402
    PackagedFoodExtraction, ExtractionMetadata, SCHEMA_VERSION,
)
from pydantic import ValidationError  # noqa: E402


# =======================================================================
# V3 ENHANCED PROMPT — defined inline in this benchmark file.
# Promoted to production (with PROMPT_VERSION bump) only if the results
# justify it per the decision matrix in the plan.
# =======================================================================

# Three modular additions:
#   (A) Schema as a TypeScript interface literal (Code Prompting; Puerto 2024)
#   (B) One complete worked few-shot example (Brown 2020)
#   (C) Chain-of-Verification closing instruction (Dhuliawala 2023)

_V3_ADDITION_A_SCHEMA_TS = """\
=========================================================================
OUTPUT STRUCTURE — TypeScript-style schema (this is your contract; the
field names MUST be EXACTLY as below; the sub-object shape for every
numeric value MUST be EXACTLY {value, unit, confidence, raw_text,
from_dv_percent, from_kcal_conversion} — no aliases such as numeric_value,
quantity, amount, val, units, measure, text):
=========================================================================

interface ExtractedNumeric {
  value: number | null;
  unit: ("g" | "mg" | "mcg" | "kcal" | "kJ" | "ml" | "kBq" | null);
  confidence: number;                   // 0.0-1.0
  raw_text: string | null;
  from_dv_percent: boolean;             // false unless derived from %DV column
  from_kcal_conversion: boolean;        // false unless kJ derived via kcal*4.184
}

interface ExtractedString {
  value: string | null;
  confidence: number;
}

interface NutrientBlock {
  energy_kj:             ExtractedNumeric;
  energy_kcal:           ExtractedNumeric;
  fat_total_g:           ExtractedNumeric;
  fat_sat_g:             ExtractedNumeric;
  fat_trans_g:           ExtractedNumeric;
  carbohydrate_total_g:  ExtractedNumeric;
  fibre_g:               ExtractedNumeric;
  sugars_total_g:        ExtractedNumeric;
  sugars_added_g:        ExtractedNumeric;
  protein_g:             ExtractedNumeric;
  sodium_mg:             ExtractedNumeric;
  potassium_mg:          ExtractedNumeric;
  calcium_mg:            ExtractedNumeric;
  iron_mg:               ExtractedNumeric;
  cholesterol_mg:        ExtractedNumeric;
}

interface NFPanelExtraction {
  schema_version: 1;
  language_detected: "en" | "fr" | "en-fr" | "es" | "other" | "unknown";
  panel_format_detected: "canadian_2016" | "us_fda_2016" | "eu_1169_2011" | "unknown";
  product_name_visible: ExtractedString;
  brand_visible:        ExtractedString;
  serving_size:           ExtractedNumeric;  // value+unit (g or ml)
  servings_per_container: ExtractedNumeric;
  net_weight:             ExtractedNumeric;
  per_serving: NutrientBlock;
  per_100g:    NutrientBlock | null;
  hsr_category_hint: {
    guess: "1"|"1D"|"2"|"2D"|"3"|"3D";
    confidence: number;
    rationale: string;
    alternatives: Array<{category: "1"|"1D"|"2"|"2D"|"3"|"3D", reason: string}>;
  };
  fopl_on_pack: {hsr_stars_visible: number | null, nutri_score_visible: string | null};
  extraction_succeeded: boolean;
  failure_reason: string | null;
}

interface IngredientListExtraction {
  ingredients_text: string;
  ingredients_parsed: Array<{
    name: string,
    position: number,
    parenthetical: string[],
    explicit_percentage: number | null,
    allergen_flag: string | null
  }>;
  explicit_percentages_found: boolean;
  contains_statement: string | null;
  language_detected: "en" | "fr" | "en-fr" | "es" | "other" | "unknown";
  confidence: number;
}

interface PackagedFoodExtraction {
  schema_version: 1;
  nf_panel: NFPanelExtraction | null;
  ingredient_list: IngredientListExtraction | null;
  has_nf_panel: boolean;
  has_ingredient_list: boolean;
  extraction_succeeded: boolean;
  failure_reason: string | null;
}

CRITICAL: every nutrient sub-field is itself an ExtractedNumeric OBJECT —
NEVER a bare number. When the label doesn't list a nutrient, return
{"value": null, "unit": null, "confidence": 0, "raw_text": null,
 "from_dv_percent": false, "from_kcal_conversion": false}. Do not flatten.
"""


_V3_ADDITION_B_FEW_SHOT = """\
=========================================================================
WORKED EXAMPLE — a generic granola bar (Canadian bilingual). Use this to
mirror the EXACT output shape; the field names + nesting are non-negotiable.
=========================================================================

If the image shows a granola-bar wrapper with:
  Nutrition Facts / Valeur nutritive
  Per 1 bar (35 g) / pour 1 barre (35 g)
  Calories  150
  Fat / Lipides 5 g  (7 % DV)
    Saturated / saturés 1 g + Trans / trans 0 g  (5 %)
  Carbohydrate / Glucides 23 g  (8 %)
    Fibre / Fibres 2 g  (7 %)
    Sugars / Sucres 11 g  (11 %)
  Protein / Protéines 3 g
  Cholesterol / Cholestérol 0 mg
  Sodium 75 mg  (3 %)
  Calcium 20 mg  (2 %)
  Iron / Fer 1 mg  (6 %)
  8 bars per box / 8 barres par boîte
  Ingredients: Whole grain oats, sugar, vegetable oil (canola), …

Your output MUST be:

{
  "schema_version": 1,
  "nf_panel": {
    "schema_version": 1,
    "language_detected": "en-fr",
    "panel_format_detected": "canadian_2016",
    "product_name_visible": {"value": "Granola Bar", "confidence": 0.9},
    "brand_visible": {"value": null, "confidence": 0},
    "serving_size":           {"value": 35, "unit": "g",  "confidence": 0.97, "raw_text": "Per 1 bar (35 g) / pour 1 barre (35 g)", "from_dv_percent": false, "from_kcal_conversion": false},
    "servings_per_container": {"value": 8,  "unit": null, "confidence": 0.92, "raw_text": "8 bars per box", "from_dv_percent": false, "from_kcal_conversion": false},
    "net_weight":             {"value": 280,"unit": "g",  "confidence": 0.85, "raw_text": "280 g (8 × 35 g)", "from_dv_percent": false, "from_kcal_conversion": false},
    "per_serving": {
      "energy_kj":            {"value": 628,"unit": "kJ",   "confidence": 0.7,  "raw_text": null, "from_dv_percent": false, "from_kcal_conversion": true},
      "energy_kcal":          {"value": 150,"unit": "kcal", "confidence": 0.95, "raw_text": "Calories 150", "from_dv_percent": false, "from_kcal_conversion": false},
      "fat_total_g":          {"value": 5,  "unit": "g",    "confidence": 0.95, "raw_text": "Fat / Lipides 5 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "fat_sat_g":            {"value": 1,  "unit": "g",    "confidence": 0.95, "raw_text": "Saturated 1 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "fat_trans_g":          {"value": 0,  "unit": "g",    "confidence": 0.95, "raw_text": "Trans 0 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "carbohydrate_total_g": {"value": 23, "unit": "g",    "confidence": 0.95, "raw_text": "Carbohydrate 23 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "fibre_g":              {"value": 2,  "unit": "g",    "confidence": 0.93, "raw_text": "Fibre 2 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "sugars_total_g":       {"value": 11, "unit": "g",    "confidence": 0.95, "raw_text": "Sugars 11 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "sugars_added_g":       {"value": null, "unit": null, "confidence": 0, "raw_text": null, "from_dv_percent": false, "from_kcal_conversion": false},
      "protein_g":            {"value": 3,  "unit": "g",    "confidence": 0.95, "raw_text": "Protein 3 g", "from_dv_percent": false, "from_kcal_conversion": false},
      "sodium_mg":            {"value": 75, "unit": "mg",   "confidence": 0.96, "raw_text": "Sodium 75 mg", "from_dv_percent": false, "from_kcal_conversion": false},
      "potassium_mg":         {"value": null, "unit": null, "confidence": 0, "raw_text": null, "from_dv_percent": false, "from_kcal_conversion": false},
      "calcium_mg":           {"value": 20, "unit": "mg",   "confidence": 0.85, "raw_text": "Calcium 20 mg", "from_dv_percent": false, "from_kcal_conversion": false},
      "iron_mg":              {"value": 1,  "unit": "mg",   "confidence": 0.85, "raw_text": "Iron 1 mg", "from_dv_percent": false, "from_kcal_conversion": false},
      "cholesterol_mg":       {"value": 0,  "unit": "mg",   "confidence": 0.95, "raw_text": "Cholesterol 0 mg", "from_dv_percent": false, "from_kcal_conversion": false}
    },
    "per_100g": null,
    "hsr_category_hint": {
      "guess": "2",
      "confidence": 0.9,
      "rationale": "Solid packaged food (bar), non-dairy, not a fat/oil/nut spread.",
      "alternatives": [{"category": "3", "reason": "Possible if predominantly nuts/seeds — unlikely for a granola bar."}]
    },
    "fopl_on_pack": {"hsr_stars_visible": null, "nutri_score_visible": null},
    "extraction_succeeded": true,
    "failure_reason": null
  },
  "ingredient_list": {
    "ingredients_text": "Ingredients: Whole grain oats, sugar, vegetable oil (canola), ...",
    "ingredients_parsed": [
      {"name": "whole grain oats", "position": 1, "parenthetical": [], "explicit_percentage": null, "allergen_flag": null},
      {"name": "sugar",            "position": 2, "parenthetical": [], "explicit_percentage": null, "allergen_flag": null},
      {"name": "vegetable oil",    "position": 3, "parenthetical": ["canola"], "explicit_percentage": null, "allergen_flag": null}
    ],
    "explicit_percentages_found": false,
    "contains_statement": null,
    "language_detected": "en",
    "confidence": 0.85
  },
  "has_nf_panel": true,
  "has_ingredient_list": true,
  "extraction_succeeded": true,
  "failure_reason": null
}

Notice especially:
- EVERY nutrient field is an OBJECT with the six canonical keys.
- Absent nutrients are NOT omitted; they get value=null, confidence=0.
- The kcal-only label still populates energy_kj via ×4.184 with from_kcal_conversion=true.
- Position is 1-indexed in the ingredient list.
"""


_V3_ADDITION_C_COVE = """\
=========================================================================
SELF-VERIFICATION (Chain-of-Verification) — apply BEFORE returning JSON.
Walk through this checklist mentally; if any item fails, REVISE your draft
output, THEN return the corrected JSON.
=========================================================================

(1) Field-name check. Open every nutrient sub-object. Does it use EXACTLY
    these keys: {value, unit, confidence, raw_text, from_dv_percent,
    from_kcal_conversion}? If you wrote numeric_value, quantity, amount,
    val, units, measure, or text — rewrite using the canonical names.

(2) Nesting check. Are nutrient values under per_serving (or per_100g
    when published)? If you have keys like calories, total_fat_g, sodium_mg
    at the TOP LEVEL of nf_panel — move them under per_serving.

(3) Sanity check. Is per-serving energy in the typical 5-800 kcal range?
    Is sodium in the typical 0-5000 mg range? If a value is wildly out
    of range you misread the label — re-examine and lower confidence.

(4) Object-not-scalar check. Are serving_size, servings_per_container,
    and net_weight all OBJECTS (with value+unit+confidence)? They must
    NOT be bare numbers or bare strings.

(5) Completeness check. Did you include EVERY nutrient field of
    NutrientBlock, even when the label doesn't have it (value=null,
    confidence=0)? Missing fields cause validation errors.

If all five checks pass, return the JSON. Otherwise revise first.
"""


COMBINED_SYSTEM_PROMPT_V3_ENHANCED: str = (
    PROMPT_V2_SYSTEM
    + "\n\n"
    + _V3_ADDITION_A_SCHEMA_TS
    + "\n\n"
    + _V3_ADDITION_B_FEW_SHOT
    + "\n\n"
    + _V3_ADDITION_C_COVE
)


def build_user_v3() -> str:
    """User prompt for the enhanced variant. Same body as v2 but with a
    short reminder to follow the worked example."""
    return build_user_v2() + (
        "\n\nIMPORTANT: follow the WORKED EXAMPLE shape EXACTLY — every "
        "nutrient is an ExtractedNumeric object with the six canonical keys. "
        "Apply the self-verification checklist before returning."
    )


# =======================================================================
# Variant definitions
# =======================================================================


@dataclass
class Variant:
    id: str                       # 'V1' .. 'V4'
    system_prompt: str
    user_prompt: str
    normaliser_enabled: bool
    description: str


def get_variants() -> List[Variant]:
    return [
        Variant(
            id='V1',
            system_prompt=PROMPT_V2_SYSTEM,
            user_prompt=build_user_v2(),
            normaliser_enabled=True,
            description='Current prompt v2 + normaliser ON  (production today)',
        ),
        Variant(
            id='V2',
            system_prompt=PROMPT_V2_SYSTEM,
            user_prompt=build_user_v2(),
            normaliser_enabled=False,
            description='Current prompt v2 + normaliser OFF  (normaliser ablation)',
        ),
        Variant(
            id='V3',
            system_prompt=COMBINED_SYSTEM_PROMPT_V3_ENHANCED,
            user_prompt=build_user_v3(),
            normaliser_enabled=False,
            description='Enhanced prompt (few-shot+schema-as-code+CoVe) + normaliser OFF',
        ),
        Variant(
            id='V4',
            system_prompt=COMBINED_SYSTEM_PROMPT_V3_ENHANCED,
            user_prompt=build_user_v3(),
            normaliser_enabled=True,
            description='Enhanced prompt + normaliser ON  (belt-and-suspenders)',
        ),
    ]


# =======================================================================
# Per-cell measurement
# =======================================================================


@dataclass
class CellResult:
    variant_id: str
    image_filename: str
    image_difficulty: str
    run_index: int

    # Pipeline outcomes
    schema_ok_pre_norm: bool
    normaliser_fired: Optional[bool]    # None when variant has normaliser off
    extraction_succeeded_final: bool
    failure_reason: Optional[str]

    # Field-level accuracy (only meaningful when extraction succeeded)
    fields_passed: int
    fields_total: int
    field_accuracy: float               # passed / total; 0.0 when extraction failed

    # Resource cost
    latency_ms: int
    est_input_tokens: int
    est_output_tokens: int

    # Per-field diff (sample of failures for diagnostics)
    sample_field_failures: List[Dict[str, Any]] = field(default_factory=list)


def _estimate_tokens(text: str) -> int:
    """OpenAI heuristic: ~4 chars per token. Good enough for relative comparison."""
    return max(1, len(text) // 4)


# Image at detail='high' in OpenAI vision API costs ~765 tokens for the
# canonical 1024x1024 input (per OpenAI docs, October 2024). We downscale
# to 1600px long-edge so this is an upper estimate.
_IMAGE_TOKEN_COST_HIGH_DETAIL: int = 765


def _make_metadata_stub() -> Dict[str, Any]:
    """Metadata field the schema requires. Filled with placeholders; we
    don't care about its exact contents for the benchmark."""
    return {
        'model': 'benchmark', 'provider': 'benchmark',
        'prompt_version': 0, 'schema_version': SCHEMA_VERSION,
        'image_sha256': 'bench', 'image_bytes': 1,
        'image_dimensions': [1, 1],
        'extracted_at': _dt.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'extraction_warnings': [], 'sanity_guard_rejections': [],
        'cache_hit': False, 'latency_ms': 0,
    }


def _validate_with_metadata(raw: Dict[str, Any]) -> Optional[PackagedFoodExtraction]:
    """Try to validate raw LLM output against PackagedFoodExtraction.
    Strips/replaces extraction_metadata first since the LLM never produces it."""
    if not isinstance(raw, dict):
        return None
    stub = _make_metadata_stub()
    payload = dict(raw)
    payload.pop('extraction_metadata', None)
    payload['extraction_metadata'] = stub
    if isinstance(payload.get('nf_panel'), dict):
        payload['nf_panel']['extraction_metadata'] = stub
    try:
        return PackagedFoodExtraction.model_validate(payload)
    except ValidationError:
        return None


def _evaluate_panel_vs_ground_truth(
    pfe: PackagedFoodExtraction, gt: GroundTruth,
) -> tuple[int, int, List[Dict[str, Any]]]:
    """Compare extracted panel to ground truth, return (passed, total, sample_failures)."""
    if pfe.nf_panel is None or not pfe.extraction_succeeded:
        return 0, 0, []

    passed = 0
    total = 0
    failures: List[Dict[str, Any]] = []
    panel = pfe.nf_panel

    # Serving size (value + unit; tighter tolerance per smoke harness convention)
    if gt.serving_size_value is not None:
        total += 1
        v = panel.serving_size.value
        u = (panel.serving_size.unit or '').lower()
        ok = (v is not None and _within_tolerance(
            gt.serving_size_value, float(v), rel=0.05, absolute=2.0,
        ) and u == (gt.serving_size_unit or '').lower())
        if ok:
            passed += 1
        else:
            failures.append({'field': 'serving_size',
                             'expected': f'{gt.serving_size_value}{gt.serving_size_unit}',
                             'actual':   f'{v}{u}'})

    # Servings per container (loose tolerance)
    if gt.servings_per_container is not None:
        total += 1
        v = panel.servings_per_container.value
        ok = v is not None and abs(float(v) - gt.servings_per_container) <= 0.5
        if ok:
            passed += 1
        else:
            failures.append({'field': 'servings_per_container',
                             'expected': gt.servings_per_container, 'actual': v})

    # Net weight
    if gt.net_weight_value is not None:
        total += 1
        v = panel.net_weight.value
        u = (panel.net_weight.unit or '').lower()
        ok = (v is not None and _within_tolerance(
            gt.net_weight_value, float(v), rel=0.05, absolute=2.0,
        ) and u == (gt.net_weight_unit or '').lower())
        if ok:
            passed += 1
        else:
            failures.append({'field': 'net_weight',
                             'expected': f'{gt.net_weight_value}{gt.net_weight_unit}',
                             'actual':   f'{v}{u}'})

    # Per-serving nutrients
    ps = panel.per_serving.model_dump()
    for nkey, expected in gt.per_serving.items():
        total += 1
        sub = ps.get(nkey) or {}
        v = sub.get('value')
        if v is None:
            failures.append({'field': f'per_serving.{nkey}', 'expected': expected, 'actual': None})
            continue
        try:
            actual_f = float(v)
        except (TypeError, ValueError):
            failures.append({'field': f'per_serving.{nkey}', 'expected': expected, 'actual': v})
            continue
        if _within_tolerance(expected, actual_f):
            passed += 1
        else:
            failures.append({'field': f'per_serving.{nkey}', 'expected': expected, 'actual': actual_f})

    return passed, total, failures[:5]   # cap noise in result JSON


# =======================================================================
# Per-cell execution
# =======================================================================


def run_one_cell(
    *, variant: Variant, image_bytes: bytes, gt: GroundTruth,
    run_index: int, client: MultimodalJSONClient,
) -> CellResult:
    """Run one (variant × image × run) cell — single LLM call + scoring."""
    jpeg, _img_meta = normalize_image_bytes(image_bytes)
    t0 = time.perf_counter()
    raw: Dict[str, Any]
    try:
        raw = client.extract_with_image(
            system=variant.system_prompt,
            user=variant.user_prompt,
            image_jpeg_bytes=jpeg,
            temperature=0.0,
            max_tokens=3500,
        )
    except Exception as exc:  # noqa: BLE001
        latency = int((time.perf_counter() - t0) * 1000)
        return CellResult(
            variant_id=variant.id,
            image_filename=gt.filename,
            image_difficulty=gt.difficulty,
            run_index=run_index,
            schema_ok_pre_norm=False, normaliser_fired=None,
            extraction_succeeded_final=False,
            failure_reason=f'llm_call_failed: {exc!r}',
            fields_passed=0, fields_total=0, field_accuracy=0.0,
            latency_ms=latency, est_input_tokens=0, est_output_tokens=0,
        )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    # Cost estimates
    est_input = (
        _IMAGE_TOKEN_COST_HIGH_DETAIL
        + _estimate_tokens(variant.system_prompt)
        + _estimate_tokens(variant.user_prompt)
    )
    est_output = _estimate_tokens(json.dumps(raw, default=str))

    # Schema compliance check on the RAW output (pre-normaliser)
    raw_copy_for_pre_check = copy.deepcopy(raw)
    pre_norm_validation = _validate_with_metadata(raw_copy_for_pre_check)
    schema_ok_pre = pre_norm_validation is not None

    # Apply normaliser if the variant says so
    normaliser_fired: Optional[bool] = None
    if variant.normaliser_enabled:
        pre_state = json.dumps(raw, sort_keys=True, default=str)
        raw = normalise_llm_extraction(raw)
        post_state = json.dumps(raw, sort_keys=True, default=str)
        normaliser_fired = (pre_state != post_state)

    # Final validation
    final = _validate_with_metadata(raw)
    if final is None:
        return CellResult(
            variant_id=variant.id,
            image_filename=gt.filename,
            image_difficulty=gt.difficulty,
            run_index=run_index,
            schema_ok_pre_norm=schema_ok_pre,
            normaliser_fired=normaliser_fired,
            extraction_succeeded_final=False,
            failure_reason='schema_validation_failed_post_pipeline',
            fields_passed=0, fields_total=0, field_accuracy=0.0,
            latency_ms=latency_ms,
            est_input_tokens=est_input, est_output_tokens=est_output,
        )

    # Sanity guards (mirrors production extractor)
    if final.nf_panel is not None:
        nf, warns = _apply_sanity_guards(final.nf_panel)
        final.nf_panel = nf
        final.nf_panel.extraction_metadata.sanity_guard_rejections.extend(warns)

    # Field accuracy vs ground truth
    passed, total, failures = _evaluate_panel_vs_ground_truth(final, gt)
    field_accuracy = (passed / total) if total > 0 else 0.0

    return CellResult(
        variant_id=variant.id,
        image_filename=gt.filename,
        image_difficulty=gt.difficulty,
        run_index=run_index,
        schema_ok_pre_norm=schema_ok_pre,
        normaliser_fired=normaliser_fired,
        extraction_succeeded_final=final.extraction_succeeded,
        failure_reason=final.failure_reason,
        fields_passed=passed,
        fields_total=total,
        field_accuracy=field_accuracy,
        latency_ms=latency_ms,
        est_input_tokens=est_input, est_output_tokens=est_output,
        sample_field_failures=failures,
    )


# =======================================================================
# Aggregation + reporting
# =======================================================================


def aggregate_variant(cells: List[CellResult]) -> Dict[str, Any]:
    """Aggregate cell results for one variant. Returns the dict that goes
    into the per-variant summary table + JSON."""
    if not cells:
        return {}
    total_cells = len(cells)
    schema_ok = sum(1 for c in cells if c.schema_ok_pre_norm)
    final_ok = sum(1 for c in cells if c.extraction_succeeded_final)
    fired = sum(1 for c in cells if c.normaliser_fired)
    # net accuracy: cells that failed validation/extraction get 0
    accs = [c.field_accuracy for c in cells]
    latencies = [c.latency_ms for c in cells]
    in_toks = [c.est_input_tokens for c in cells]
    out_toks = [c.est_output_tokens for c in cells]

    def _safe_mean(xs: List[float]) -> float:
        return statistics.mean(xs) if xs else 0.0

    return {
        'n_cells': total_cells,
        'schema_ok_pre_norm': {'count': schema_ok, 'rate': schema_ok / total_cells},
        'extraction_succeeded_final': {'count': final_ok, 'rate': final_ok / total_cells},
        'normaliser_fired': {'count': fired, 'rate': fired / total_cells},
        'field_accuracy': {
            'mean': _safe_mean(accs),
            'min':  min(accs) if accs else 0.0,
            'max':  max(accs) if accs else 0.0,
        },
        'latency_ms': {
            'mean': int(_safe_mean(latencies)),
            'min':  min(latencies) if latencies else 0,
            'max':  max(latencies) if latencies else 0,
        },
        'est_input_tokens':  {'mean': int(_safe_mean(in_toks))},
        'est_output_tokens': {'mean': int(_safe_mean(out_toks))},
        # Per-image breakdown for diagnostics
        'per_image': _per_image_breakdown(cells),
    }


def _per_image_breakdown(cells: List[CellResult]) -> Dict[str, Dict[str, Any]]:
    by_image: Dict[str, List[CellResult]] = {}
    for c in cells:
        by_image.setdefault(c.image_filename, []).append(c)
    out: Dict[str, Dict[str, Any]] = {}
    for fname, runs in by_image.items():
        accs = [r.field_accuracy for r in runs]
        out[fname] = {
            'difficulty': runs[0].image_difficulty,
            'n_runs': len(runs),
            'accuracy_mean': statistics.mean(accs) if accs else 0.0,
            'accuracy_min':  min(accs) if accs else 0.0,
            'accuracy_max':  max(accs) if accs else 0.0,
            'final_ok_count': sum(1 for r in runs if r.extraction_succeeded_final),
            'schema_ok_pre_norm_count': sum(1 for r in runs if r.schema_ok_pre_norm),
            'unstable': (max(accs) - min(accs)) > 0.0 if accs else False,
        }
    return out


def print_markdown_table(per_variant: Dict[str, Dict[str, Any]],
                         variants: List[Variant]) -> None:
    """Print the decision-ready comparison table to stdout."""
    print()
    print('=' * 100)
    print('A/B BENCHMARK — PROMPT ENGINEERING vs NORMALISER')
    print('=' * 100)
    print()
    print(f'{"Variant":<6} | {"Description":<58} | {"Schema-OK":>10} | {"Field acc":>9} | '
          f'{"Latency":>8} | {"In/Out tok":>11} | {"Norm fired":>10}')
    print('-' * 6 + ' | ' + '-' * 58 + ' | ' + '-' * 10 + ' | ' + '-' * 9
          + ' | ' + '-' * 8 + ' | ' + '-' * 11 + ' | ' + '-' * 10)
    for v in variants:
        agg = per_variant.get(v.id) or {}
        if not agg:
            continue
        schema_pct = f'{agg["schema_ok_pre_norm"]["rate"]*100:5.1f}%'
        acc_pct = (f'{agg["field_accuracy"]["mean"]*100:5.1f}% '
                   f'[{agg["field_accuracy"]["min"]*100:.0f}-{agg["field_accuracy"]["max"]*100:.0f}]')
        lat = f'{agg["latency_ms"]["mean"]/1000:5.2f}s'
        toks = f'{agg["est_input_tokens"]["mean"]}/{agg["est_output_tokens"]["mean"]}'
        fired = (f'{agg["normaliser_fired"]["count"]}/{agg["n_cells"]}'
                 if v.normaliser_enabled else 'n/a')
        # Truncate description to fit the column
        desc = v.description if len(v.description) <= 58 else v.description[:55] + '...'
        print(f'{v.id:<6} | {desc:<58} | {schema_pct:>10} | {acc_pct:>9} | '
              f'{lat:>8} | {toks:>11} | {fired:>10}')

    print()
    print('Per-image accuracy breakdown:')
    print('-' * 100)
    # Get image list (assume all variants saw the same images)
    sample = next(iter(per_variant.values()), {}).get('per_image', {})
    images = list(sample.keys())
    if images:
        print(f'{"Image":<55} | ' + ' | '.join(f'{v.id:<8}' for v in variants))
        for img in images:
            row = f'{img[:55]:<55} | '
            cells = []
            for v in variants:
                agg = per_variant.get(v.id) or {}
                imgs = agg.get('per_image') or {}
                row_data = imgs.get(img, {})
                acc = row_data.get('accuracy_mean', 0.0)
                ok_count = row_data.get('final_ok_count', 0)
                n = row_data.get('n_runs', 0)
                cells.append(f'{acc*100:5.1f}% ({ok_count}/{n})')
            row += ' | '.join(f'{c:<8}' for c in cells)
            print(row)
    print()


def apply_decision_matrix(per_variant: Dict[str, Dict[str, Any]]) -> str:
    """Apply the decision matrix from the plan. Returns a human-readable verdict."""
    v1 = per_variant.get('V1') or {}
    v2 = per_variant.get('V2') or {}
    v3 = per_variant.get('V3') or {}
    v4 = per_variant.get('V4') or {}
    if not all((v1, v2, v3, v4)):
        return 'Incomplete results — re-run the benchmark.'

    v1_acc = v1['field_accuracy']['mean']
    v2_acc = v2['field_accuracy']['mean']
    v3_acc = v3['field_accuracy']['mean']
    v4_acc = v4['field_accuracy']['mean']
    v3_schema = v3['schema_ok_pre_norm']['rate']
    v1_in_toks = v1['est_input_tokens']['mean']
    v3_in_toks = v3['est_input_tokens']['mean']
    cost_premium = (v3_in_toks - v1_in_toks) / v1_in_toks if v1_in_toks > 0 else 0.0

    lines: List[str] = []
    lines.append('=' * 100)
    lines.append('DECISION MATRIX (per the plan)')
    lines.append('=' * 100)
    lines.append(f'  V1 baseline accuracy:           {v1_acc*100:.1f}%')
    lines.append(f'  V2 (normaliser ablation):       {v2_acc*100:.1f}%')
    lines.append(f'  V3 (enhanced prompt, no norm):  {v3_acc*100:.1f}%  '
                 f'(schema-OK pre-norm: {v3_schema*100:.1f}%)')
    lines.append(f'  V4 (enhanced prompt + norm):    {v4_acc*100:.1f}%')
    lines.append(f'  Prompt cost premium (V3/V1):    +{cost_premium*100:.1f}% input tokens')
    lines.append('')

    if v3_acc >= v1_acc and v3_schema >= 0.90 and cost_premium <= 0.20:
        lines.append('VERDICT: Ship V3 (drop normaliser). Enhanced prompt achieves')
        lines.append('  ≥ baseline accuracy AND ≥ 90% raw schema compliance AND')
        lines.append('  ≤ 20% cost premium. The normaliser layer can be retired.')
    elif v4_acc - v1_acc >= 0.05 and cost_premium <= 0.25:
        lines.append('VERDICT: Ship V4 (enhanced prompt + normaliser). Belt-and-suspenders')
        lines.append('  beats baseline by ≥ 5pp without burning the cost budget.')
    elif v2_acc >= v1_acc:
        lines.append('VERDICT: Normaliser is overkill — V2 (no normaliser, current prompt)')
        lines.append('  matches V1. Consider removing the normaliser without prompt changes.')
    elif max(v1_acc, v2_acc, v3_acc, v4_acc) < 0.75:
        lines.append('VERDICT: ALL VARIANTS UNDER 75% — investigate. Possible causes:')
        lines.append('  image quality, ground-truth typos, or LLM model regression.')
    else:
        lines.append('VERDICT: Keep V1 (current production). Prompt enhancements add no value;')
        lines.append('  the current normaliser-only approach is the right architecture.')
    return '\n'.join(lines)


# =======================================================================
# Main
# =======================================================================


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=3,
                        help='Runs per (variant, image) cell. Default 3.')
    parser.add_argument('--variants', type=str, default='V1,V2,V3,V4',
                        help='Comma-separated variant IDs to run.')
    parser.add_argument('--images', type=str, default='',
                        help='Comma-separated image filenames to limit to '
                             '(default: all 5 ground-truth images).')
    args = parser.parse_args()

    print('=' * 100)
    print('PKG-IMG-1 Phase 2.x A/B benchmark — prompt engineering vs normaliser')
    print('=' * 100)

    client = build_multimodal_client()
    if client is None:
        print()
        print('SKIPPED: no MultimodalJSONClient available.')
        print('Set OPENAI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic).')
        return 0

    print(f'Provider: {client.provider}; Model: {client.model}')
    print(f'Image dir: {IMG_DIR}')

    # Filter variants
    requested = [v.strip() for v in args.variants.split(',') if v.strip()]
    variants = [v for v in get_variants() if v.id in requested]
    if not variants:
        print(f'ERROR: no matching variants in {args.variants!r}')
        return 1

    # Filter images
    images_filter = {s.strip() for s in args.images.split(',') if s.strip()}
    ground_truth = [g for g in GROUND_TRUTH
                    if not images_filter or g.filename in images_filter]

    n_cells = len(variants) * len(ground_truth) * args.runs
    est_cost_cents = n_cells * 1
    print(f'Variants: {[v.id for v in variants]}')
    print(f'Images:   {len(ground_truth)}')
    print(f'Runs/cell: {args.runs}')
    print(f'Total LLM calls: {n_cells}  (estimated cost: ~{est_cost_cents}¢)')
    print()

    # Pre-load image bytes once
    images_bytes: Dict[str, bytes] = {}
    for gt in ground_truth:
        p = IMG_DIR / gt.filename
        if not p.exists():
            print(f'  [SKIP] {gt.filename}: not found at {p}')
            continue
        with open(p, 'rb') as f:
            images_bytes[gt.filename] = f.read()
    ground_truth = [g for g in ground_truth if g.filename in images_bytes]

    # Run all cells
    cells_by_variant: Dict[str, List[CellResult]] = {v.id: [] for v in variants}
    cell_index = 0
    for v in variants:
        print(f'--- Variant {v.id}: {v.description} ---')
        for gt in ground_truth:
            for run_idx in range(args.runs):
                cell_index += 1
                t0 = time.perf_counter()
                cell = run_one_cell(
                    variant=v, image_bytes=images_bytes[gt.filename],
                    gt=gt, run_index=run_idx, client=client,
                )
                cells_by_variant[v.id].append(cell)
                elapsed = time.perf_counter() - t0
                acc_pct = cell.field_accuracy * 100
                final_status = 'OK' if cell.extraction_succeeded_final else 'FAIL'
                schema_status = 'OK' if cell.schema_ok_pre_norm else 'X '
                norm_status = ('-' if cell.normaliser_fired is None
                               else 'fired' if cell.normaliser_fired
                               else 'noop')
                print(f'  [{cell_index:3d}/{n_cells}] {v.id} {gt.filename[:38]:<38} '
                      f'run={run_idx + 1}  '
                      f'schema={schema_status}  final={final_status:<4}  '
                      f'acc={acc_pct:5.1f}%  norm={norm_status:<5}  '
                      f'{elapsed:.1f}s')
        print()

    # Aggregate
    per_variant: Dict[str, Dict[str, Any]] = {
        v.id: aggregate_variant(cells_by_variant[v.id]) for v in variants
    }

    # Print decision-ready table + verdict
    print_markdown_table(per_variant, variants)
    verdict = apply_decision_matrix(per_variant)
    print(verdict)
    print()

    # Persist results
    out_path = Path(__file__).parent / '_benchmark_prompt_variants_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model': client.model, 'provider': client.provider,
            'runs_per_cell': args.runs,
            'variants_evaluated': [v.id for v in variants],
            'images_evaluated':  [g.filename for g in ground_truth],
            'per_variant_aggregate': per_variant,
            'per_cell_detail': [
                {
                    'variant': c.variant_id, 'image': c.image_filename,
                    'difficulty': c.image_difficulty, 'run_index': c.run_index,
                    'schema_ok_pre_norm': c.schema_ok_pre_norm,
                    'normaliser_fired': c.normaliser_fired,
                    'extraction_succeeded_final': c.extraction_succeeded_final,
                    'failure_reason': c.failure_reason,
                    'fields_passed': c.fields_passed, 'fields_total': c.fields_total,
                    'field_accuracy': c.field_accuracy,
                    'latency_ms': c.latency_ms,
                    'est_input_tokens': c.est_input_tokens,
                    'est_output_tokens': c.est_output_tokens,
                    'sample_field_failures': c.sample_field_failures,
                }
                for cells in cells_by_variant.values() for c in cells
            ],
            'verdict': verdict,
        }, f, indent=2, default=str)
    print(f'Results JSON: {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
