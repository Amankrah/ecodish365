"""Packaged-food image extraction orchestrator (PKG-IMG-1).

End-to-end flow for one user upload:

  1. Normalise the uploaded bytes via `multimodal_client.normalize_image_bytes`
     (HEIC/AVIF → JPEG, downscale to 1600 px long-edge, SHA-256 hash).
  2. Check Django cache by (sha256, prompt_version, schema_version). Hit
     returns instantly.
  3. Call the multimodal LLM (`build_multimodal_client`) with the system
     + user prompts from `packaged_food_prompts`.
  4. Validate the raw JSON against `NFPanelExtraction`. Validation
     failures become structured `failure_reason` rather than raw exceptions.
  5. Run sanity-range guards (sodium > 5g/serving → reject as misread; etc.).
     Rejections downgrade the affected field's confidence to 0 and append
     to `extraction_warnings`; only catastrophic rejections (nothing usable
     extracted) flip `extraction_succeeded=false`.
  6. Stamp `extraction_metadata` and cache the result for 7 days.

Phase 2 will add `extract_ingredient_list()` to this same module.
"""
from __future__ import annotations

import datetime as _dt
import logging
import time
from dataclasses import dataclass
from typing import Optional

from django.core.cache import cache
from pydantic import ValidationError

from .multimodal_client import (
    build_multimodal_client,
    normalize_image_bytes,
    MultimodalJSONClient,
    ImageDecodeError,
)
from .packaged_food_prompts import (
    NF_PANEL_SYSTEM_PROMPT,
    COMBINED_SYSTEM_PROMPT,
    PROMPT_VERSION,
    build_user_prompt,
    build_combined_user_prompt,
)
from .packaged_food_schema import (
    NFPanelExtraction,
    PackagedFoodExtraction,
    IngredientListExtraction,
    ExtractionMetadata,
    NutrientBlock,
    SCHEMA_VERSION,
)


logger = logging.getLogger(__name__)


# Keys allowed on NFPanelExtraction — strip LLM extras before Pydantic.
_NF_PANEL_CANONICAL_KEYS = frozenset({
    'schema_version', 'language_detected', 'panel_format_detected',
    'product_name_visible', 'brand_visible',
    'serving_size', 'servings_per_container', 'net_weight',
    'per_serving', 'per_100g',
    'hsr_category_hint', 'fopl_on_pack',
    'extraction_succeeded', 'failure_reason',
    'extraction_metadata',
})


# =======================================================================
# Pre-validation normaliser — accept LLM's natural shape, coerce to schema
# =======================================================================
# The combined NF + ingredients prompt is heavy; LLMs often respond with a
# simpler flat structure ('calories': 110 instead of 'per_serving': {
# 'energy_kcal': {'value': 110, 'unit': 'kcal', 'confidence': 0.9}}) even
# when asked for the strict form. Rather than fail validation, this
# normaliser detects flat shapes and coerces them to the schema. Also
# handles common alternate field names (calories→energy_kcal,
# total_fat_g→fat_total_g, etc.) and parses string serving sizes
# ("120 ml", "1/2 cup (120 mL)") into the {value, unit} object.

# Maps LLM-flat keys (lowercased) → canonical per_serving keys.
_FLAT_NUTRIENT_ALIASES: dict[str, str] = {
    # Energy
    'calories':              'energy_kcal',
    'calories_kcal':         'energy_kcal',
    'energy_kcal':           'energy_kcal',
    'kcal':                  'energy_kcal',
    'energy_kj':             'energy_kj',
    'kj':                    'energy_kj',
    # Fats
    'total_fat_g':           'fat_total_g',
    'fat_g':                 'fat_total_g',
    'fat_total_g':           'fat_total_g',
    'fat':                   'fat_total_g',
    'saturated_fat_g':       'fat_sat_g',
    'sat_fat_g':             'fat_sat_g',
    'saturates_g':           'fat_sat_g',
    'fat_sat_g':             'fat_sat_g',
    'trans_fat_g':           'fat_trans_g',
    'trans_g':               'fat_trans_g',
    'fat_trans_g':           'fat_trans_g',
    # Carbs
    'total_carbohydrate_g':   'carbohydrate_total_g',
    'total_carbohydrates_g':  'carbohydrate_total_g',
    'carbohydrate_g':         'carbohydrate_total_g',
    'carbohydrates_g':        'carbohydrate_total_g',
    'carbohydrates_total_g':  'carbohydrate_total_g',  # 2026-05-26: LLM emits this plural-s variant on the combined-prompt path
    'carbs_g':                'carbohydrate_total_g',
    'carbohydrate_total_g':   'carbohydrate_total_g',
    'dietary_fiber_g':       'fibre_g',
    'fiber_g':               'fibre_g',
    'fibre_g':               'fibre_g',
    'fibres_g':              'fibre_g',
    'total_sugars_g':        'sugars_total_g',
    'sugars_g':              'sugars_total_g',
    'sugar_g':               'sugars_total_g',
    'sucres_g':              'sugars_total_g',
    'sugars_total_g':        'sugars_total_g',
    'added_sugars_g':        'sugars_added_g',
    'sugars_added_g':        'sugars_added_g',
    # Protein
    'protein_g':             'protein_g',
    'proteins_g':            'protein_g',
    # Minerals
    'sodium_mg':             'sodium_mg',
    'sodium':                'sodium_mg',
    'potassium_mg':          'potassium_mg',
    'potassium':             'potassium_mg',
    'calcium_mg':            'calcium_mg',
    'calcium':               'calcium_mg',
    'iron_mg':               'iron_mg',
    'iron':                  'iron_mg',
    'fer':                   'iron_mg',  # bilingual FR label shorthand
    'cholesterol_mg':        'cholesterol_mg',
}

# Nested objects the LLM may use for infant-formula vitamin/mineral tables.
_VITAMIN_MINERAL_TABLE_KEYS = (
    'vitamin_mineral_table',
    'vitamins_and_minerals',
    'vitamins_minerals',
    'minerals',
    'micronutrients',
    'nutrition_information',
    'nutrition_info',
)

# Top-level NF panel aliases.
_FLAT_NF_FIELD_ALIASES: dict[str, str] = {
    'product_name':          'product_name_visible',
    'brand':                 'brand_visible',
}

# Top-level keys we ignore (LLM might emit; not in schema).
_LLM_NOISE_KEYS = {
    'extraction_warning', 'extraction_warnings',
    'polyunsaturated_fat_g', 'monounsaturated_fat_g',
    'vitamin_d_mcg', 'vitamin_a_mcg', 'vitamin_c_mg',
    'confidence',  # top-level catch-all confidence; we use per-field confidences
    'overall_confidence',
    'front_of_pack_label', 'on_pack_hsr_rating', 'on_pack_nutriscore',
    'front_of_pack',
    'per_container',
}


def _coerce_hsr_category_alternative(raw: object) -> Optional[dict]:
    """Normalise one alternative to {category, reason}. The LLM frequently mirrors
    the parent's `guess` field name into children, but the schema names it
    `category` there; without remapping, extra='forbid' rejects the response."""
    if not isinstance(raw, dict):
        return None
    category = raw.get('category') or raw.get('guess') or raw.get('primary')
    if category is None:
        return None
    return {
        'category': str(category),
        'reason': str(raw.get('reason') or raw.get('rationale') or ''),
    }


def _coerce_hsr_category_hint(raw: object) -> dict:
    """Map alternate LLM shapes (e.g. Opus/Haiku flat hsr_category_*) to schema."""
    if isinstance(raw, str):
        return {'guess': raw, 'confidence': 0.0, 'rationale': '', 'alternatives': []}
    if not isinstance(raw, dict):
        return {}
    guess = raw.get('guess') or raw.get('category') or raw.get('primary')
    if guess is None:
        return {}
    raw_alts = raw.get('alternatives') or []
    alternatives = [
        a for a in (_coerce_hsr_category_alternative(x) for x in raw_alts)
        if a is not None
    ]
    return {
        'guess': str(guess),
        'confidence': float(raw.get('confidence') or 0.0),
        'rationale': str(raw.get('rationale') or raw.get('reason') or ''),
        'alternatives': alternatives,
    }


def _coerce_fopl_on_pack(raw: object) -> dict:
    """Map alternate FoPL key names to fopl_on_pack schema."""
    if not isinstance(raw, dict):
        return {}
    stars = (
        raw.get('hsr_stars_visible') or raw.get('hsr_stars')
        or raw.get('hsr_stars_on_pack')
    )
    nutri = (
        raw.get('nutri_score_visible') or raw.get('nutri_score')
        or raw.get('nutri_score_on_pack')
    )
    return {
        'hsr_stars_visible': stars,
        'nutri_score_visible': nutri,
    }


def _remap_flat_hsr_hint_fields(out: dict) -> dict:
    """Haiku/Opus sometimes flatten hsr_category_hint into sibling keys."""
    if 'hsr_category_hint' not in out and 'hsr_category' in out:
        out['hsr_category_hint'] = _coerce_hsr_category_hint({
            'guess': out.pop('hsr_category'),
            'rationale': out.pop('hsr_category_rationale', ''),
            'alternatives': out.pop('hsr_category_alternatives', []),
            'confidence': out.pop('hsr_category_confidence', 0.0),
        })
    else:
        for stray in (
            'hsr_category', 'hsr_category_rationale',
            'hsr_category_alternatives', 'hsr_category_confidence',
        ):
            out.pop(stray, None)
    return out


# Sub-key aliases inside an ExtractedNumeric dict — the LLM sometimes returns
# nested objects with non-canonical keys ({numeric_value, units, ...} instead
# of {value, unit, ...}). Remap before validation so extra_forbidden doesn't fire.
_NUMERIC_SUBKEY_ALIASES: dict[str, str] = {
    'numeric_value': 'value',
    'quantity':      'value',
    'amount':        'value',
    'number':        'value',
    'val':           'value',
    'qty':           'value',
    'units':         'unit',
    'measure':       'unit',
    'unit_of_measure': 'unit',
    'uom':           'unit',
    'rawtext':       'raw_text',
    'raw':           'raw_text',
    'text':          'raw_text',
    'literal_text':  'raw_text',
    'literal':       'raw_text',
    'source_text':   'raw_text',
}

# Canonical ExtractedNumeric keys — anything outside this gets stripped after
# alias remap (Pydantic's extra="forbid" would otherwise reject them).
_EXTRACTED_NUMERIC_CANONICAL_KEYS = frozenset((
    'value', 'unit', 'confidence', 'raw_text',
    'from_dv_percent', 'from_kcal_conversion',
))

_STRING_SUBKEY_ALIASES: dict[str, str] = {
    'text': 'value',
    'string': 'value',
    'name': 'value',
    'label': 'value',
}

_EXTRACTED_STRING_CANONICAL_KEYS = frozenset(('value', 'confidence'))


def _coerce_extracted_numeric_dict(d: dict) -> dict:
    """Remap LLM sub-key aliases (numeric_value→value, units→unit, ...)
    then strip any extras the schema doesn't allow. Idempotent."""
    if not isinstance(d, dict):
        return d
    out: dict = {}
    for k, v in d.items():
        canonical = _NUMERIC_SUBKEY_ALIASES.get(k, k)
        # Don't overwrite a real value with an alias that ended up empty.
        if canonical in out and (v is None or v == ''):
            continue
        out[canonical] = v
    # Strip non-canonical keys (Pydantic extra="forbid" would reject).
    out = {k: v for k, v in out.items() if k in _EXTRACTED_NUMERIC_CANONICAL_KEYS}
    # Coerce numeric-typed value (LLM sometimes returns strings).
    if 'value' in out and out['value'] is not None and not isinstance(out['value'], (int, float)):
        try:
            out['value'] = float(out['value'])
        except (TypeError, ValueError):
            # If it can't be coerced, leave as raw_text instead
            txt = str(out.pop('value'))
            out.setdefault('raw_text', txt)
    # Confidence must be a number in [0,1]
    if 'confidence' in out and not isinstance(out['confidence'], (int, float)):
        try:
            out['confidence'] = float(out['confidence'])
        except (TypeError, ValueError):
            out['confidence'] = 0.0
    if 'confidence' in out and out['confidence'] is not None:
        out['confidence'] = max(0.0, min(1.0, float(out['confidence'])))
    return out


def _coerce_extracted_string_dict(d: dict) -> dict:
    """Same as _coerce_extracted_numeric_dict but for ExtractedString."""
    if not isinstance(d, dict):
        return d
    out: dict = {}
    for k, v in d.items():
        canonical = _STRING_SUBKEY_ALIASES.get(k, k)
        if canonical in out and (v is None or v == ''):
            continue
        out[canonical] = v
    out = {k: v for k, v in out.items() if k in _EXTRACTED_STRING_CANONICAL_KEYS}
    if 'value' in out and out['value'] is not None and not isinstance(out['value'], str):
        out['value'] = str(out['value'])
    if 'confidence' in out and not isinstance(out['confidence'], (int, float)):
        try:
            out['confidence'] = float(out['confidence'])
        except (TypeError, ValueError):
            out['confidence'] = 0.0
    if 'confidence' in out and out['confidence'] is not None:
        out['confidence'] = max(0.0, min(1.0, float(out['confidence'])))
    return out


def _parse_serving_size_string(raw: object) -> dict:
    """Parse '120 ml', '1/2 cup (120 mL)', '35 g (about 12 chips)' into
    {value, unit, raw_text}. Returns canonical empty object on parse miss.
    When passed a dict, remaps LLM sub-key aliases via
    _coerce_extracted_numeric_dict (handles {numeric_value: 250, ...})."""
    import re
    if isinstance(raw, dict):
        return _coerce_extracted_numeric_dict(raw)
    if raw is None:
        return {}
    s = str(raw).strip()
    if not s:
        return {}
    # Look for the LAST numeric+unit pair (often inside parens: "1 cup (250 mL)").
    # Common units: g, ml, mg, oz, kg, l, L.
    m = re.search(
        r'(\d+(?:\.\d+)?)\s*(g|ml|mg|mL|ML|G|MG|oz|kg|l|L)\b',
        s,
    )
    if m:
        try:
            value = float(m.group(1))
        except ValueError:
            return {'raw_text': s}
        unit = m.group(2).lower()
        if unit == 'l':
            value, unit = value * 1000, 'ml'
        elif unit == 'kg':
            value, unit = value * 1000, 'g'
        return {'value': value, 'unit': unit, 'raw_text': s, 'confidence': 0.85}
    return {'raw_text': s}


def _to_extracted_numeric(raw: object, *, default_unit: str | None = None) -> dict:
    """Coerce a raw LLM value into an ExtractedNumeric dict. Accepts:
       - already-correct {value, unit, ...}
       - dict with sub-key aliases (numeric_value, units, ...) — remapped
         + extras stripped
       - bare scalar (int/float) → {value: x, unit: default_unit}
       - string with number + optional unit
       - None → {} (empty, Pydantic defaults handle the rest)
    """
    if isinstance(raw, dict):
        return _coerce_extracted_numeric_dict(raw)
    if raw is None:
        return {}
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return {'value': float(raw), 'unit': default_unit, 'confidence': 0.85}
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        # Try to extract a number from the string.
        import re
        m = re.search(r'(-?\d+(?:\.\d+)?)', s)
        if m:
            try:
                value = float(m.group(1))
                # Detect unit if present (heuristic: any letters after the number)
                u_match = re.search(r'([a-zA-Z]+)\s*$', s[m.end():].strip())
                unit = u_match.group(1).lower() if u_match else default_unit
                return {'value': value, 'unit': unit, 'raw_text': s, 'confidence': 0.7}
            except ValueError:
                pass
        return {'raw_text': s}
    return {}


def _to_extracted_string(raw: object) -> dict:
    """Coerce raw to ExtractedString dict.
    Dicts go through alias remap + extras strip via _coerce_extracted_string_dict."""
    if isinstance(raw, dict):
        return _coerce_extracted_string_dict(raw)
    if raw is None:
        return {}
    return {'value': str(raw), 'confidence': 0.85}


def _merge_vitamin_mineral_table(block: dict, table: object) -> dict:
    """Merge infant-formula vitamin/mineral table values into a nutrient block.

    The LLM sometimes returns a nested {calcium_mg: 44, ...} or flat
    {calcium: 44, iron: 1, ...} object separate from per_serving. Fill
    per-field gaps without overwriting values already read from the main NF
    rows (existing non-null values win).
    """
    if not isinstance(table, dict):
        return block
    out = dict(block)
    for k, v in table.items():
        if not isinstance(k, str):
            continue
        key = k.lower()
        canonical = _FLAT_NUTRIENT_ALIASES.get(key)
        if canonical is None and key in NutrientBlock.model_fields:
            canonical = key
        if canonical is None or canonical not in NutrientBlock.model_fields:
            continue
        existing = out.get(canonical) or {}
        if isinstance(existing, dict) and existing.get('value') is not None:
            continue
        unit_hint = (
            'mg' if canonical.endswith('_mg')
            else 'g' if canonical.endswith('_g')
            else 'kcal' if 'kcal' in canonical
            else 'kJ' if canonical == 'energy_kj'
            else None
        )
        coerced = _to_extracted_numeric(v, default_unit=unit_hint)
        if coerced.get('value') is not None:
            out[canonical] = coerced
    return out


def _merge_nested_mineral_sources(nf: dict) -> dict:
    """Pull micronutrients from infant-formula nested tables into per_serving."""
    if not isinstance(nf, dict):
        return nf
    per_serving = dict(nf.get('per_serving') or {})
    per_serving = _ensure_nutrient_dicts(per_serving)
    for key in _VITAMIN_MINERAL_TABLE_KEYS:
        if key in nf:
            per_serving = _merge_vitamin_mineral_table(per_serving, nf.pop(key))
    # Some models nest the table inside per_serving under a non-schema key.
    for key in list(per_serving.keys()):
        if key in _VITAMIN_MINERAL_TABLE_KEYS and isinstance(per_serving[key], dict):
            per_serving = _merge_vitamin_mineral_table(
                {k: v for k, v in per_serving.items() if k in NutrientBlock.model_fields},
                per_serving.pop(key),
            )
    nf['per_serving'] = _ensure_nutrient_dicts(per_serving)
    return nf


def _normalise_nf_panel(nf: dict) -> dict:
    """If the LLM returned a flat NF panel, coerce to the canonical nested shape.
    Idempotent — passes a correctly-nested panel through unchanged."""
    if not isinstance(nf, dict):
        return nf

    # Detect flat-vs-nested by checking for ANY flat nutrient key at top level.
    has_flat_nutrients = any(k in nf for k in _FLAT_NUTRIENT_ALIASES)
    has_proper_per_serving = isinstance(nf.get('per_serving'), dict) and any(
        isinstance(nf['per_serving'].get(k), dict)
        for k in ('energy_kcal', 'sodium_mg', 'protein_g')
    )

    # If both forms are present (mixed), still proceed — the flat keys will
    # overwrite nested ones (assume LLM intent is the flat values).
    if not has_flat_nutrients and has_proper_per_serving:
        # Already correct. Make sure each nutrient field is at least an empty dict
        # (the schema requires sub-objects, not nulls).
        nf['per_serving'] = _ensure_nutrient_dicts(nf['per_serving'])
        if isinstance(nf.get('per_100g'), dict):
            nf['per_100g'] = _ensure_nutrient_dicts(nf['per_100g'])
        return _fix_nf_top_level(_merge_nested_mineral_sources(nf))

    # Build the per_serving block from flat keys.
    per_serving: dict = dict(nf.get('per_serving') or {})  # start with whatever was nested
    for k, canonical in _FLAT_NUTRIENT_ALIASES.items():
        if k in nf:
            # mg vs g unit hint from the alias key itself
            unit_hint = (
                'mg' if k.endswith('_mg')
                else 'g' if k.endswith('_g')
                else 'kcal' if 'kcal' in k or k == 'calories'
                else 'kJ' if k == 'energy_kj' or k == 'kj'
                else None
            )
            per_serving[canonical] = _to_extracted_numeric(nf[k], default_unit=unit_hint)

    per_serving = _ensure_nutrient_dicts(per_serving)

    # Rebuild the NF panel dict with canonical keys.
    out: dict = {}
    # Copy through known schema keys that were present
    for schema_key in (
        'schema_version', 'language_detected', 'panel_format_detected',
        'hsr_category_hint', 'fopl_on_pack',
    ):
        if schema_key in nf:
            out[schema_key] = nf[schema_key]
    # Name / brand aliases
    for alias, canonical in _FLAT_NF_FIELD_ALIASES.items():
        if alias in nf and canonical not in nf:
            out[canonical] = _to_extracted_string(nf[alias])
    if 'product_name_visible' in nf:
        out['product_name_visible'] = _to_extracted_string(nf['product_name_visible'])
    if 'brand_visible' in nf:
        out['brand_visible'] = _to_extracted_string(nf['brand_visible'])
    # Serving size — string or object
    if 'serving_size' in nf:
        out['serving_size'] = _parse_serving_size_string(nf['serving_size'])
    # Servings per container
    if 'servings_per_container' in nf:
        out['servings_per_container'] = _to_extracted_numeric(
            nf['servings_per_container'])
    # Net weight
    if 'net_weight' in nf:
        out['net_weight'] = _parse_serving_size_string(nf['net_weight'])
    # Per-serving block
    out['per_serving'] = per_serving
    # Per-100g if present
    if 'per_100g' in nf and nf['per_100g'] is not None:
        if isinstance(nf['per_100g'], dict):
            # Recursively normalise (may also be flat)
            out['per_100g'] = _ensure_nutrient_dicts(
                _build_nutrient_block_from_flat(nf['per_100g']))
        else:
            out['per_100g'] = None
    return _fix_nf_top_level(_merge_nested_mineral_sources(out))


def _build_nutrient_block_from_flat(block: dict) -> dict:
    """Like _normalise_nf_panel's nutrient logic but for a nutrient block alone."""
    out: dict = {}
    for k, canonical in _FLAT_NUTRIENT_ALIASES.items():
        if k in block:
            unit_hint = (
                'mg' if k.endswith('_mg')
                else 'g' if k.endswith('_g')
                else 'kcal' if 'kcal' in k or k == 'calories'
                else 'kJ' if k == 'energy_kj' or k == 'kj'
                else None
            )
            out[canonical] = _to_extracted_numeric(block[k], default_unit=unit_hint)
    # Preserve any sub-objects already in canonical form
    for k, v in block.items():
        if k in (_FLAT_NUTRIENT_ALIASES.get(k, k) for _ in [0]):
            pass
        if isinstance(v, dict) and 'value' in v:
            out[k] = v
    return out


def _ensure_nutrient_dicts(block: dict) -> dict:
    """Make sure every nutrient key in the block is at least an empty dict
    (Pydantic NutrientBlock requires sub-objects, not None or missing).
    Also runs each sub-dict through _coerce_extracted_numeric_dict so
    sub-key aliases (numeric_value→value) and extras get normalised."""
    from .packaged_food_schema import NutrientBlock
    schema_keys = NutrientBlock.model_fields.keys()
    out = dict(block)
    for k in schema_keys:
        if k not in out or out[k] is None:
            out[k] = {}
        elif isinstance(out[k], dict):
            out[k] = _coerce_extracted_numeric_dict(out[k])
        else:
            # Stray scalar — coerce
            out[k] = _to_extracted_numeric(out[k])
    # Strip extra keys not in the schema (Pydantic will reject otherwise).
    return {k: v for k, v in out.items() if k in schema_keys}


def _fix_nf_top_level(nf: dict) -> dict:
    """Drop noise keys + coerce top-level structures. Always runs dict
    inputs through the relevant coercer so sub-key aliases (numeric_value,
    text, etc.) are mapped to canonical schema keys."""
    out = {k: v for k, v in nf.items() if k not in _LLM_NOISE_KEYS}
    # Remap top-level NF field name aliases (product_name → product_name_visible, etc.)
    # so the nested-already branch of _normalise_nf_panel doesn't miss them.
    for alias, canonical in _FLAT_NF_FIELD_ALIASES.items():
        if alias in out and canonical not in out:
            out[canonical] = out.pop(alias)
        elif alias in out:
            # Both present — keep canonical, drop alias
            out.pop(alias)
    # ExtractedString fields (product_name_visible, brand_visible)
    for fname in ('product_name_visible', 'brand_visible'):
        v = out.get(fname)
        if v is None:
            out[fname] = {}
        elif isinstance(v, dict):
            out[fname] = _coerce_extracted_string_dict(v)
        else:
            out[fname] = _to_extracted_string(v)
    # ExtractedNumeric fields (serving_size, servings_per_container, net_weight)
    for fname in ('serving_size', 'servings_per_container', 'net_weight'):
        v = out.get(fname)
        if v is None:
            out[fname] = {}
        elif isinstance(v, dict):
            out[fname] = _coerce_extracted_numeric_dict(v)
        else:
            # Scalar or string — apply field-aware coercion
            out[fname] = (_parse_serving_size_string(v)
                          if fname in ('serving_size', 'net_weight')
                          else _to_extracted_numeric(v))
    if not isinstance(out.get('per_serving'), dict):
        out['per_serving'] = {}
    if 'per_serving' in out:
        out['per_serving'] = _ensure_nutrient_dicts(out['per_serving'])
    if isinstance(out.get('per_100g'), dict):
        out['per_100g'] = _ensure_nutrient_dicts(out['per_100g'])
    out = _remap_flat_hsr_hint_fields(out)
    # HSR hint — Opus sometimes emits hsr_category_guess instead.
    if 'hsr_category_guess' in out and 'hsr_category_hint' not in out:
        out['hsr_category_hint'] = _coerce_hsr_category_hint(out.pop('hsr_category_guess'))
    elif 'hsr_category_hint' in out:
        out['hsr_category_hint'] = _coerce_hsr_category_hint(out['hsr_category_hint'])
    if 'hsr_category_hint' not in out or not isinstance(out['hsr_category_hint'], dict):
        out['hsr_category_hint'] = {}
    if 'fopl' in out and 'fopl_on_pack' not in out:
        out['fopl_on_pack'] = _coerce_fopl_on_pack(out.pop('fopl'))
    elif 'front_of_pack' in out and 'fopl_on_pack' not in out:
        out['fopl_on_pack'] = _coerce_fopl_on_pack(out.pop('front_of_pack'))
    elif 'fop_label' in out and 'fopl_on_pack' not in out:
        out['fopl_on_pack'] = _coerce_fopl_on_pack(out.pop('fop_label'))
    elif 'fopl_on_pack' in out:
        out['fopl_on_pack'] = _coerce_fopl_on_pack(out['fopl_on_pack'])
    if 'fopl_on_pack' not in out or not isinstance(out['fopl_on_pack'], dict):
        out['fopl_on_pack'] = {}
    out = _merge_nested_mineral_sources(out)
    return {k: v for k, v in out.items() if k in _NF_PANEL_CANONICAL_KEYS}


def _normalise_ingredient_list(il: object) -> object:
    """Coerce LLM ingredient-list output. LLMs sometimes return just a
    string of ingredients text instead of the full {ingredients_text,
    ingredients_parsed, ...} object; wrap minimally in that case."""
    if il is None:
        return None
    if isinstance(il, str):
        return {'ingredients_text': il}
    if not isinstance(il, dict):
        return None
    # Strip noise + ensure required field exists
    out = {k: v for k, v in il.items() if k not in _LLM_NOISE_KEYS}
    if 'ingredients_text' not in out and 'text' in out:
        out['ingredients_text'] = out.pop('text')
    if 'ingredients_text' not in out:
        # Synthesize from parsed list if possible
        parsed = out.get('ingredients_parsed') or out.get('ingredients') or []
        if isinstance(parsed, list) and parsed:
            names = []
            for p in parsed:
                if isinstance(p, dict) and p.get('name'):
                    names.append(str(p['name']))
                elif isinstance(p, str):
                    names.append(p)
            out['ingredients_text'] = ', '.join(names)
        else:
            out['ingredients_text'] = ''
    # Coerce ingredients list shape
    parsed_raw = out.get('ingredients_parsed') or out.get('ingredients') or []
    parsed_norm = []
    for idx, item in enumerate(parsed_raw):
        if isinstance(item, str):
            parsed_norm.append({'name': item, 'position': idx + 1})
        elif isinstance(item, dict):
            entry = {
                'name': str(item.get('name') or ''),
                'position': int(item.get('position') or (idx + 1)),
                'parenthetical': item.get('parenthetical') or [],
                'explicit_percentage': item.get('explicit_percentage'),
                'allergen_flag': item.get('allergen_flag'),
            }
            if entry['name']:
                parsed_norm.append(entry)
    out['ingredients_parsed'] = parsed_norm
    out.pop('ingredients', None)
    return out


def normalise_llm_extraction(raw: dict) -> dict:
    """Top-level normaliser for the combined-extract LLM output.
    Mutates a defensive copy; returns the normalised dict. Idempotent.
    """
    if not isinstance(raw, dict):
        return raw
    out = dict(raw)
    if isinstance(out.get('nf_panel'), dict):
        out['nf_panel'] = _normalise_nf_panel(out['nf_panel'])
    elif out.get('nf_panel') is None:
        # Already-canonical absence; leave alone
        pass
    if 'ingredient_list' in out:
        out['ingredient_list'] = _normalise_ingredient_list(out['ingredient_list'])
    # Drop wrapper-level noise (extraction_warning, confidence, etc.)
    for k in list(out.keys()):
        if k in _LLM_NOISE_KEYS:
            del out[k]
    return out


CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


# --- Sanity-range thresholds --------------------------------------------
# Each tuple: (field_path_in_per_serving, max_plausible_value, unit, friendly_name)
# When the extracted value exceeds the max, we zero its confidence + append
# a warning. We do NOT flip the whole extraction to failed unless the
# critical-set (energy + sodium) is unusable.

_SANITY_RANGES: tuple[tuple[str, float, str, str], ...] = (
    ("sodium_mg",          5_000.0, "mg",   "sodium per serving"),
    ("energy_kcal",        2_000.0, "kcal", "energy per serving (kcal)"),
    ("energy_kj",          8_368.0, "kJ",   "energy per serving (kJ ~ 2000 kcal)"),
    ("fat_total_g",          150.0, "g",    "total fat per serving"),
    ("fat_sat_g",            100.0, "g",    "saturated fat per serving"),
    ("carbohydrate_total_g", 500.0, "g",    "carbohydrate per serving"),
    ("sugars_total_g",       400.0, "g",    "total sugars per serving"),
    ("protein_g",            200.0, "g",    "protein per serving"),
    ("fibre_g",              100.0, "g",    "fibre per serving"),
)


_CRITICAL_FIELDS_FOR_HSR = ("sodium_mg", "fat_sat_g", "sugars_total_g")


# --- Public result type -------------------------------------------------


@dataclass
class ExtractionResult:
    """What `extract_nf_panel` returns. The view layer renders this to JSON."""
    extraction: NFPanelExtraction
    cache_hit: bool


# --- Internal cache key -------------------------------------------------


def _cache_key(sha256_hex: str) -> str:
    # Cache key includes schema + prompt version so a code change here
    # invalidates the cache automatically on next request.
    return f"pkg_food_nf:v{SCHEMA_VERSION}.{PROMPT_VERSION}:{sha256_hex}"


# --- Sanity-guard helper -------------------------------------------------


def _apply_sanity_guards(panel: NFPanelExtraction) -> tuple[NFPanelExtraction, list[str]]:
    """Walk the per_serving block and zero confidence on values that
    exceed plausible bounds. Returns (panel, warnings)."""
    warnings: list[str] = []
    if panel.per_serving is None:
        return panel, warnings

    for field_name, max_val, unit, friendly in _SANITY_RANGES:
        field = getattr(panel.per_serving, field_name, None)
        if field is None or field.value is None:
            continue
        if field.value > max_val:
            warnings.append(
                f"sanity_guard:{field_name}={field.value}{unit} exceeds "
                f"plausible max {max_val}{unit} for {friendly} — confidence "
                f"zeroed, value preserved for user review"
            )
            # Preserve the value (the user might rescue it if our threshold
            # is wrong for their product) but mark it untrustworthy.
            field.confidence = 0.0
            field.from_dv_percent = field.from_dv_percent or False

    return panel, warnings


def _critical_fields_usable(panel: NFPanelExtraction) -> bool:
    """True when at least the HSR-critical fields have plausible values."""
    if panel.per_serving is None:
        return False
    # Energy (either kJ or kcal) must be present.
    energy_ok = (
        (panel.per_serving.energy_kj.value not in (None, 0)
         and panel.per_serving.energy_kj.confidence > 0)
        or (panel.per_serving.energy_kcal.value not in (None, 0)
            and panel.per_serving.energy_kcal.confidence > 0)
    )
    if not energy_ok:
        return False
    for fname in _CRITICAL_FIELDS_FOR_HSR:
        f = getattr(panel.per_serving, fname)
        # Sodium / sat-fat / sugars can legitimately be 0; we only require
        # that they were extracted with some confidence (the user might
        # also see 0 on the label).
        if f.value is None or f.confidence == 0:
            return False
    return True


# --- Main entry point ---------------------------------------------------


def extract_nf_panel(
    image_bytes,
    *,
    target: str = "hsr",
    client: Optional[MultimodalJSONClient] = None,
    use_cache: bool = True,
) -> ExtractionResult:
    """Extract a packaged-food NF panel from one or more images.

    Args:
      image_bytes: EITHER a single `bytes` (one photo — backward-compatible),
        OR a `list[bytes]` of 1-`MAX_IMAGES_PER_EXTRACTION` photos of the
        SAME product from different faces. Multi-image flows merge per
        Rule U so the NF face + net-weight face can be supplied separately.
      target: downstream consumer hint, currently 'hsr' only.
      client: optional pre-built MultimodalJSONClient (for tests).
      use_cache: set False in smoke tests to force fresh extraction.

    Returns:
      ExtractionResult with the validated NFPanelExtraction and cache flag.

    Raises:
      ImageDecodeError: if the bytes don't parse as a supported image.
      RuntimeError: if no multimodal LLM client is available (no API key).
    """
    t_start = time.perf_counter()

    # 1. Normalise image(s). Same polymorphic shape as `extract_packaged_food`.
    raw_list: list[bytes] = (
        [image_bytes] if isinstance(image_bytes, (bytes, bytearray))
        else list(image_bytes)
    )
    if not raw_list:
        raise ValueError("extract_nf_panel: no image bytes provided")
    if len(raw_list) > MAX_IMAGES_PER_EXTRACTION:
        raise ValueError(
            f"extract_nf_panel: at most {MAX_IMAGES_PER_EXTRACTION} images "
            f"per call (got {len(raw_list)})"
        )
    normalised: list[tuple[bytes, dict]] = [normalize_image_bytes(b) for b in raw_list]
    jpeg_list = [n[0] for n in normalised]
    per_image_meta = [n[1] for n in normalised]
    img_meta = dict(per_image_meta[0])
    img_meta["images"] = per_image_meta
    img_meta["image_count"] = len(per_image_meta)
    sha = _combined_sha_for_images([m["sha256"] for m in per_image_meta])
    img_meta["sha256"] = sha

    # 2. Cache check.
    if use_cache:
        cached = cache.get(_cache_key(sha))
        if cached is not None:
            try:
                ex = NFPanelExtraction.model_validate(cached)
                ex.extraction_metadata.cache_hit = True
                ex.extraction_metadata.latency_ms = int(
                    (time.perf_counter() - t_start) * 1000
                )
                return ExtractionResult(extraction=ex, cache_hit=True)
            except ValidationError as exc:
                # Bad cache entry (schema migration mid-flight, etc.) — fall through.
                logger.warning("pkg-food cache validation failed; refetching: %s", exc)

    # 3. LLM client.
    if client is None:
        client = build_multimodal_client()
    if client is None:
        raise RuntimeError(
            "MultimodalJSONClient unavailable: set OPENAI_API_KEY or "
            "ANTHROPIC_API_KEY and ensure LLM_PROVIDER matches. "
            "For Opus extraction set MULTIMODAL_LLM_MODEL=claude-opus-4-7."
        )

    # 4. Call (single multimodal call, 1-3 image blocks).
    try:
        raw = client.extract_with_images(
            system=NF_PANEL_SYSTEM_PROMPT,
            user=build_user_prompt(target=target),
            images_jpeg_bytes=jpeg_list,
            temperature=0.0,
            max_tokens=2048,
        )
    except Exception as exc:  # noqa: BLE001 — surface as structured failure
        logger.exception("pkg-food LLM call failed")
        return _build_failed_result(
            img_meta, client, t_start, reason=f"llm_call_failed: {exc!r}",
        )

    # 5. Validate against schema.
    if not isinstance(raw, dict) or not raw:
        return _build_failed_result(
            img_meta, client, t_start,
            reason="empty_or_non_object_llm_response",
        )

    # Defensive: same normaliser as the combined endpoint. LLMs sometimes
    # flatten the schema even on the simpler NF-only prompt.
    raw = _normalise_nf_panel(raw)

    # The model never includes extraction_metadata; we stamp it server-side.
    raw.pop("extraction_metadata", None)
    raw["extraction_metadata"] = _build_metadata(img_meta, client, t_start)

    try:
        panel = NFPanelExtraction.model_validate(raw)
    except ValidationError as exc:
        logger.warning("pkg-food schema validation failed AFTER normalisation: %s", exc)
        return _build_failed_result(
            img_meta, client, t_start,
            reason=f"schema_validation_failed: {exc.errors()[:3]!r}",
        )

    # If the model self-flagged failure, skip sanity guards + cache the
    # negative result (so a "this is a cat" upload doesn't re-bill).
    if not panel.extraction_succeeded:
        if use_cache:
            cache.set(_cache_key(sha), panel.model_dump(), timeout=CACHE_TTL_SECONDS)
        return ExtractionResult(extraction=panel, cache_hit=False)

    # 6. Sanity guards.
    panel, sanity_warnings = _apply_sanity_guards(panel)
    panel.extraction_metadata.sanity_guard_rejections.extend(sanity_warnings)

    # If the critical HSR fields didn't survive, mark failed.
    if not _critical_fields_usable(panel):
        panel.extraction_succeeded = False
        panel.failure_reason = (
            "critical_fields_unusable: HSR requires at minimum "
            "energy + sodium + saturated fat + total sugars, "
            "and one or more was missing or zero-confidence "
            "(possibly due to sanity-guard rejection)."
        )

    panel.extraction_metadata.latency_ms = int(
        (time.perf_counter() - t_start) * 1000
    )

    # 7. Cache.
    if use_cache:
        cache.set(_cache_key(sha), panel.model_dump(), timeout=CACHE_TTL_SECONDS)

    return ExtractionResult(extraction=panel, cache_hit=False)


# --- Helpers ------------------------------------------------------------


def _build_metadata(img_meta: dict, client: MultimodalJSONClient,
                    t_start: float) -> dict:
    return {
        "model": client.model,
        "provider": client.provider,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "image_sha256": img_meta["sha256"],
        "image_bytes": img_meta["normalised_bytes"],
        "image_dimensions": img_meta["normalised_dimensions"],
        "extracted_at": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "extraction_warnings": [],
        "sanity_guard_rejections": [],
        "cache_hit": False,
        "latency_ms": int((time.perf_counter() - t_start) * 1000),
    }


def _build_failed_result(img_meta: dict, client: Optional[MultimodalJSONClient],
                         t_start: float, *, reason: str) -> ExtractionResult:
    """Return a minimal extraction marked failed, so the frontend can
    render a graceful empty state with a retry option."""
    meta_dict = {
        "model": client.model if client else "unknown",
        "provider": client.provider if client else "unknown",
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "image_sha256": img_meta["sha256"],
        "image_bytes": img_meta["normalised_bytes"],
        "image_dimensions": img_meta["normalised_dimensions"],
        "extracted_at": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "extraction_warnings": [],
        "sanity_guard_rejections": [],
        "cache_hit": False,
        "latency_ms": int((time.perf_counter() - t_start) * 1000),
    }
    panel = NFPanelExtraction(
        extraction_succeeded=False,
        failure_reason=reason,
        extraction_metadata=ExtractionMetadata(**meta_dict),
    )
    return ExtractionResult(extraction=panel, cache_hit=False)


# =======================================================================
# PKG-IMG-1 Phase 2 (2026-05-26) — adaptive entry point
# =======================================================================
# Single multimodal call that extracts NF panel + ingredient list (either
# or both, depending on what's visible) and returns a unified wrapper.
# Reuses the same cache + sanity-guard machinery as Phase 1.


@dataclass
class CombinedExtractionResult:
    """What `extract_packaged_food` returns. Frontend renders this as
    one or two confirmation steps depending on what was found."""
    extraction: PackagedFoodExtraction
    cache_hit: bool


MAX_IMAGES_PER_EXTRACTION = 3
"""Hard cap on photos per combined extraction. Three covers
front + back + side, which is typically enough to surface the NF panel,
ingredient list, AND net weight (often on different faces). Higher
counts push token costs disproportionately without raising accuracy."""


def _combined_cache_key(sha256_hex: str) -> str:
    """Distinct from Phase 1's NF-only key so Phase 1 and Phase 2 caches
    don't collide on the same image. For multi-image uploads, pass the
    concatenated-and-rehashed SHA from `_combined_sha_for_images`."""
    return f"pkg_food_combined:v{SCHEMA_VERSION}.{PROMPT_VERSION}:{sha256_hex}"


def _combined_sha_for_images(per_image_sha: list[str]) -> str:
    """Stable cache key for a multi-image upload. Order matters (different
    face-order = different LLM input = different result), so we don't sort.
    Single-image case returns the original SHA unchanged so existing
    cache entries continue to hit."""
    import hashlib
    if len(per_image_sha) == 1:
        return per_image_sha[0]
    return hashlib.sha256("|".join(per_image_sha).encode("ascii")).hexdigest()


def extract_packaged_food(
    image_bytes,
    *,
    client: Optional[MultimodalJSONClient] = None,
    use_cache: bool = True,
) -> CombinedExtractionResult:
    """Adaptive extractor — returns NF panel + ingredient list, either or both.

    `image_bytes` is either:
      - a single `bytes` (one photo — backward-compatible), OR
      - a `list[bytes]` of 1-`MAX_IMAGES_PER_EXTRACTION` photos of the SAME
        product taken from different faces. The LLM is instructed (Rule U)
        to merge across faces so net weight from the front face can complete
        an NF panel read from the back face.

    Single multimodal call using COMBINED_SYSTEM_PROMPT. The LLM is told to
    populate whichever pieces are visible and to set has_nf_panel /
    has_ingredient_list booleans accordingly. extraction_succeeded=false
    only when neither is found.

    Phase 1's `extract_nf_panel()` remains valid for NF-only callers (the
    HSR-only path doesn't need the heavier prompt); Phase 2 callers
    (the dietary-pattern / HEFI / HENI / FCS / env scoring paths) use this.
    """
    t_start = time.perf_counter()

    raw_list: list[bytes] = [image_bytes] if isinstance(image_bytes, (bytes, bytearray)) else list(image_bytes)
    if not raw_list:
        raise ValueError("extract_packaged_food: no image bytes provided")
    if len(raw_list) > MAX_IMAGES_PER_EXTRACTION:
        raise ValueError(
            f"extract_packaged_food: at most {MAX_IMAGES_PER_EXTRACTION} images "
            f"per call (got {len(raw_list)})"
        )

    normalised: list[tuple[bytes, dict]] = [normalize_image_bytes(b) for b in raw_list]
    jpeg_list = [n[0] for n in normalised]
    per_image_meta = [n[1] for n in normalised]
    # Compose a single image-metadata dict for the wrapper. The first image
    # is the "primary" for source_format / dimensions reporting; we keep
    # an `images` array with per-image metadata so callers can audit.
    img_meta = dict(per_image_meta[0])
    img_meta["images"] = per_image_meta
    img_meta["image_count"] = len(per_image_meta)
    sha = _combined_sha_for_images([m["sha256"] for m in per_image_meta])
    img_meta["sha256"] = sha

    if use_cache:
        cached = cache.get(_combined_cache_key(sha))
        if cached is not None:
            try:
                ex = PackagedFoodExtraction.model_validate(cached)
                ex.extraction_metadata.cache_hit = True
                ex.extraction_metadata.latency_ms = int(
                    (time.perf_counter() - t_start) * 1000
                )
                return CombinedExtractionResult(extraction=ex, cache_hit=True)
            except ValidationError as exc:
                logger.warning("combined pkg-food cache validation failed; refetching: %s", exc)

    if client is None:
        client = build_multimodal_client()
    if client is None:
        raise RuntimeError(
            "MultimodalJSONClient unavailable: set OPENAI_API_KEY or "
            "ANTHROPIC_API_KEY and ensure LLM_PROVIDER matches. "
            "For Opus extraction set MULTIMODAL_LLM_MODEL=claude-opus-4-7."
        )

    try:
        raw = client.extract_with_images(
            system=COMBINED_SYSTEM_PROMPT,
            user=build_combined_user_prompt(),
            images_jpeg_bytes=jpeg_list,
            temperature=0.0,
            max_tokens=3500,  # combined NF + ingredients can be larger
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("combined pkg-food LLM call failed")
        return _build_failed_combined(
            img_meta, client, t_start, reason=f"llm_call_failed: {exc!r}",
        )

    if not isinstance(raw, dict) or not raw:
        return _build_failed_combined(
            img_meta, client, t_start,
            reason="empty_or_non_object_llm_response",
        )

    # Normalise the LLM output BEFORE stamping metadata + validating.
    # LLMs often return a flat shape (calories: 110) when the prompt is
    # heavy with multiple sections; the normaliser coerces flat-vs-nested
    # into the schema's canonical form and remaps alternate field names.
    raw = normalise_llm_extraction(raw)

    # Stamp server-side metadata onto the WRAPPER (not the inner panel — the
    # nested panel's `extraction_metadata` is the same object).
    raw.pop("extraction_metadata", None)
    server_meta = _build_metadata(img_meta, client, t_start)
    raw["extraction_metadata"] = server_meta
    # Inner nf_panel object also needs extraction_metadata since its schema
    # requires it; mirror the same dict.
    if isinstance(raw.get("nf_panel"), dict):
        raw["nf_panel"]["extraction_metadata"] = server_meta

    try:
        wrapped = PackagedFoodExtraction.model_validate(raw)
    except ValidationError as exc:
        logger.warning(
            "combined pkg-food schema validation failed AFTER normalisation: %s",
            exc,
        )
        return _build_failed_combined(
            img_meta, client, t_start,
            reason=f"schema_validation_failed: {exc.errors()[:3]!r}",
        )

    # Mirror the boolean flags from what's actually populated. Don't trust
    # the LLM's self-reported has_* flags — derive them ourselves.
    wrapped.has_nf_panel = wrapped.nf_panel is not None
    wrapped.has_ingredient_list = (
        wrapped.ingredient_list is not None
        and bool(wrapped.ingredient_list.ingredients_text.strip())
    )

    # If absolutely nothing was extracted, mark failed.
    if not wrapped.has_nf_panel and not wrapped.has_ingredient_list:
        wrapped.extraction_succeeded = False
        wrapped.failure_reason = wrapped.failure_reason or "no_panel_or_ingredients_detected"
        if use_cache:
            cache.set(_combined_cache_key(sha), wrapped.model_dump(), timeout=CACHE_TTL_SECONDS)
        return CombinedExtractionResult(extraction=wrapped, cache_hit=False)

    # Sanity-guard the NF panel piece (the ingredient list is text-only
    # and has no numeric thresholds to check).
    if wrapped.nf_panel is not None:
        nf, sanity_warnings = _apply_sanity_guards(wrapped.nf_panel)
        nf.extraction_metadata.sanity_guard_rejections.extend(sanity_warnings)
        wrapped.nf_panel = nf

    wrapped.extraction_metadata.latency_ms = int(
        (time.perf_counter() - t_start) * 1000
    )

    if use_cache:
        cache.set(_combined_cache_key(sha), wrapped.model_dump(), timeout=CACHE_TTL_SECONDS)

    return CombinedExtractionResult(extraction=wrapped, cache_hit=False)


def _build_failed_combined(
    img_meta: dict, client: Optional[MultimodalJSONClient],
    t_start: float, *, reason: str,
) -> CombinedExtractionResult:
    meta = ExtractionMetadata(**_build_metadata_for_failure(img_meta, client, t_start))
    wrapped = PackagedFoodExtraction(
        extraction_succeeded=False,
        failure_reason=reason,
        extraction_metadata=meta,
    )
    return CombinedExtractionResult(extraction=wrapped, cache_hit=False)


def _build_metadata_for_failure(img_meta: dict, client: Optional[MultimodalJSONClient],
                                t_start: float) -> dict:
    return {
        "model": client.model if client else "unknown",
        "provider": client.provider if client else "unknown",
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "image_sha256": img_meta["sha256"],
        "image_bytes": img_meta["normalised_bytes"],
        "image_dimensions": img_meta["normalised_dimensions"],
        "extracted_at": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "extraction_warnings": [],
        "sanity_guard_rejections": [],
        "cache_hit": False,
        "latency_ms": int((time.perf_counter() - t_start) * 1000),
    }
