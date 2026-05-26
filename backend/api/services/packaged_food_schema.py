"""Strict JSON schema for packaged-food image extraction (PKG-IMG-1).

Defines the Pydantic models that the multimodal extraction LLM must
produce. Used in three places:

  1. `packaged_food_prompts.py` references this schema to construct the
     prompt's "respond with exactly this structure" instruction.
  2. `packaged_food_extractor.py` validates LLM output against these
     models — invalid output is treated as an extraction failure, not
     silently coerced.
  3. `packaged_food_views.py` accepts a validated payload back from the
     frontend after user confirmation, before routing to HSR.

The schema models a generic NF panel covering Canadian (2016 dual-language),
US-FDA (2016 single + dual-column), and EU (Regulation 1169/2011) formats
in a single shape — fields the extracting model couldn't read are nullable.

Per-field confidence is captured as a separate float in [0,1]. LLM-elicited
confidences are known to be miscalibrated; we use them as a relative signal
for visually flagging uncertain fields in the UI, NOT for automatic
acceptance or any computation.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


SCHEMA_VERSION: int = 1
"""Bump when this schema changes in a breaking way. The cache key
(image_sha256, prompt_version, schema_version) invalidates stale cached
extractions on the next pull. Backwards-compatible field additions don't
bump the version."""


# --- Primitive: one numeric field with confidence + raw text -------------


class ExtractedNumeric(BaseModel):
    """A single numeric field the LLM extracted from the panel."""
    model_config = ConfigDict(extra="forbid")

    value: Optional[float] = Field(
        default=None,
        description="The numeric value. Null when the field wasn't on the panel.",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Original unit on the panel (e.g. 'g', 'mg', 'mcg', 'kcal', 'kJ', 'ml'). "
                    "Null only when no unit on label.",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="LLM-self-reported confidence in [0,1]. Treat as relative signal only.",
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="The literal text the LLM read on the panel for this field. "
                    "Used for user cross-check in the prefill form.",
    )
    from_dv_percent: bool = Field(
        default=False,
        description="True if the value was derived from a '% Daily Value' column "
                    "rather than read directly. Flagged because DV-derived values "
                    "carry higher uncertainty (DV reference differs across CA/US/EU).",
    )
    from_kcal_conversion: bool = Field(
        default=False,
        description="True if an energy value is in kJ but was converted from a "
                    "kcal-only label (×4.184). Lower confidence than direct read.",
    )


class ExtractedString(BaseModel):
    """A single text field with confidence."""
    model_config = ConfigDict(extra="forbid")

    value: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# --- Per-serving / per-100g nutrient blocks -----------------------------


class NutrientBlock(BaseModel):
    """A column of the NF panel (either per-serving or per-100g/100ml).

    All fields nullable: not every panel publishes every nutrient. HSR only
    needs energy_kj OR energy_kcal, fat_sat_g, sugars_total_g, sodium_mg,
    protein_g, fibre_g — the rest improve audience-aware reporting but
    don't gate scoring.
    """
    model_config = ConfigDict(extra="forbid")

    energy_kj: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    energy_kcal: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    fat_total_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    fat_sat_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    fat_trans_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    carbohydrate_total_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    fibre_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    sugars_total_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    sugars_added_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    protein_g: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    sodium_mg: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    potassium_mg: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    calcium_mg: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    iron_mg: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    cholesterol_mg: ExtractedNumeric = Field(default_factory=ExtractedNumeric)


# --- HSR category guess --------------------------------------------------


class HSRCategoryAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["1", "1D", "2", "2D", "3", "3D"]
    reason: str


class HSRCategoryHint(BaseModel):
    """LLM's structured guess at the HSR category from the product image.

    The 6 categories follow HSRAC v9:
      - "1"  Beverage (non-dairy)
      - "1D" Dairy beverage
      - "2"  All other foods (default)
      - "2D" Dairy foods (yogurt, cheese, ice cream, …)
      - "3"  Fats / oils / nuts / seed butters
      - "3D" Dairy fats (butter, cream)
    Frontend renders this as a pre-selected dropdown the user confirms or
    overrides. The user's final dropdown choice — NOT the LLM guess — is
    what reaches `/api/hsr/calculate-from-panel/`.
    """
    model_config = ConfigDict(extra="forbid")

    guess: Literal["1", "1D", "2", "2D", "3", "3D"] = Field(
        default="2",
        description="Most likely HSRAC v9 category. Defaults to '2' (safe fallback).",
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = Field(
        default="",
        description="One-sentence justification (e.g. 'Solid food, non-dairy, "
                    "not a fat/oil/nut spread').",
    )
    alternatives: List[HSRCategoryAlternative] = Field(
        default_factory=list,
        description="Up to 2 plausible-but-rejected alternatives, with reasons.",
    )


# --- Top-level extraction result ----------------------------------------


class FoplOnPack(BaseModel):
    """Front-of-pack labels visible on the product, if any. Researcher mode
    surfaces these for comparison against our computed HSR; individual mode
    intentionally does NOT to avoid confusing users with version-drift
    discrepancies between on-pack HSR (potentially older HSRAC version) and
    our v9-pinned compute."""
    model_config = ConfigDict(extra="forbid")
    hsr_stars_visible: Optional[float] = None
    nutri_score_visible: Optional[str] = None  # 'A'..'E'


class ExtractionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str
    provider: str
    prompt_version: int
    schema_version: int
    image_sha256: str
    image_bytes: int
    image_dimensions: List[int]  # [w, h]
    extracted_at: str  # ISO 8601 UTC
    extraction_warnings: List[str] = Field(default_factory=list)
    sanity_guard_rejections: List[str] = Field(default_factory=list)
    cache_hit: bool = False
    latency_ms: Optional[int] = None


class NFPanelExtraction(BaseModel):
    """The full extraction result returned by `/api/packaged-food/extract/`.

    The frontend uses this to prefill the editable confirmation form. After
    user confirmation, the (possibly-edited) payload comes back through to
    `/api/hsr/calculate-from-panel/`.
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: int = SCHEMA_VERSION
    language_detected: Literal["en", "fr", "en-fr", "es", "other", "unknown"] = "unknown"
    panel_format_detected: Literal[
        "canadian_2016", "us_fda_2016", "eu_1169_2011",
        "canadian_infant_formula", "unknown",
    ] = "unknown"

    product_name_visible: ExtractedString = Field(default_factory=ExtractedString)
    brand_visible: ExtractedString = Field(default_factory=ExtractedString)

    serving_size: ExtractedNumeric = Field(
        default_factory=ExtractedNumeric,
        description="Numeric serving size with unit (g or ml).",
    )
    servings_per_container: ExtractedNumeric = Field(default_factory=ExtractedNumeric)
    net_weight: ExtractedNumeric = Field(
        default_factory=ExtractedNumeric,
        description="Total net weight printed on the package (g or ml). "
                    "Often missing; not required for HSR but useful for "
                    "consumed-portion calculations.",
    )

    per_serving: NutrientBlock = Field(default_factory=NutrientBlock)
    per_100g: Optional[NutrientBlock] = Field(
        default=None,
        description="Per-100g (or per-100ml) column when present. Null on "
                    "panels with only the per-serving column.",
    )

    hsr_category_hint: HSRCategoryHint = Field(default_factory=HSRCategoryHint)
    fopl_on_pack: FoplOnPack = Field(default_factory=FoplOnPack)
    extraction_metadata: ExtractionMetadata

    extraction_succeeded: bool = Field(
        default=True,
        description="False when the LLM returned an empty / malformed object "
                    "or sanity guards rejected the extraction. Frontend shows "
                    "a graceful empty state with retry option.",
    )
    failure_reason: Optional[str] = None


# =======================================================================
# PKG-IMG-1 Phase 2 (2026-05-26) — ingredient-list extraction + decomposition
# =======================================================================
# Regulation forces ingredient lists into descending-mass-order but does
# NOT require percentages (except EU QUID; rare in North America). We
# model both: positional rank + optional explicit_percentage. The
# decomposer downstream (`ingredient_to_cnf_decomposer.py`) uses the NF
# panel macros as constraints when inferring proportions, with the
# resulting composition explicitly framed as INFERRED, not measured.


class IngredientEntry(BaseModel):
    """One ingredient as read off the label."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Canonical ingredient name as written on the label "
                    "(e.g. 'tomato puree', 'sugar', 'wheat flour'). "
                    "Bilingual labels: prefer the English text.",
    )
    position: int = Field(
        ge=1,
        description="1-indexed position in the descending-mass-order list. "
                    "Position 1 = the dominant ingredient by mass.",
    )
    parenthetical: List[str] = Field(
        default_factory=list,
        description="Sub-ingredients listed in parentheses, e.g. for "
                    "'tomato puree (water, tomato paste)' the parenthetical "
                    "is ['water', 'tomato paste']. Empty when none.",
    )
    explicit_percentage: Optional[float] = Field(
        default=None, ge=0.0, le=100.0,
        description="When the label explicitly discloses a percentage "
                    "(e.g. 'Tomato puree 65%'), record it. Otherwise null — "
                    "the decomposer infers proportions. Rare in North America, "
                    "more common in EU under Regulation 1169/2011 QUID rules.",
    )
    allergen_flag: Optional[str] = Field(
        default=None,
        description="If the ingredient is flagged in a 'Contains: X, Y' "
                    "statement, record the allergen keyword (e.g. 'wheat'). "
                    "Used for downstream warnings; never used in scoring.",
    )


class IngredientListExtraction(BaseModel):
    """An ingredient list as extracted from the back-of-pack."""
    model_config = ConfigDict(extra="forbid")

    ingredients_text: str = Field(
        description="Raw 'Ingredients: ...' string as printed on the label. "
                    "Preserved verbatim for user cross-check.",
    )
    ingredients_parsed: List[IngredientEntry] = Field(
        default_factory=list,
        description="Parsed list in descending mass order. Empty when the LLM "
                    "could read raw text but failed to parse — frontend then "
                    "falls back to a single text-edit field.",
    )
    explicit_percentages_found: bool = Field(
        default=False,
        description="True if at least one ingredient carries an explicit "
                    "percentage. Decomposer uses these as stronger anchors.",
    )
    contains_statement: Optional[str] = Field(
        default=None,
        description="The raw 'Contains: X, Y, Z' allergen statement if present "
                    "(Canadian / US convention; required for the top-9 allergens).",
    )
    language_detected: Literal["en", "fr", "en-fr", "es", "other", "unknown"] = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PackagedFoodExtraction(BaseModel):
    """Unified wrapper returned by /api/packaged-food/extract/ in Phase 2.

    Adaptive: either or both of `nf_panel` and `ingredient_list` may be
    present, depending on what the LLM was able to read from the image.
    The `has_*` booleans let the frontend route the user appropriately
    (straight to score, or prompt for a second photo to fill the gap).
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: int = SCHEMA_VERSION
    nf_panel: Optional[NFPanelExtraction] = None
    ingredient_list: Optional[IngredientListExtraction] = None

    has_nf_panel: bool = False
    has_ingredient_list: bool = False

    extraction_metadata: ExtractionMetadata

    extraction_succeeded: bool = Field(
        default=True,
        description="True when at least one of NF panel or ingredient list "
                    "was extracted. False when neither was found (e.g. cat "
                    "photo, blank front-of-pack).",
    )
    failure_reason: Optional[str] = None


# --- Decomposition result (Phase 2 — ingredient_to_cnf_decomposer output) ---


class DecomposedIngredient(BaseModel):
    """One ingredient mapped to a CNF FoodID with an inferred mass."""
    model_config = ConfigDict(extra="forbid")

    label_name: str = Field(
        description="Original ingredient name from the label (e.g. 'tomato puree')."
    )
    position: int = Field(
        ge=1, description="1-indexed position from the ingredient list."
    )
    food_id: int = Field(
        description="CNF (or WAFCT, when >= 700_000) FoodID the matcher selected."
    )
    food_description: str = Field(
        description="CNF FoodDescription for the matched food."
    )
    food_group: Optional[str] = Field(default=None)
    mass_g: float = Field(
        ge=0.0,
        description="Inferred mass in grams. Sum across all ingredients should "
                    "reconcile to the net weight ± 5 % (see "
                    "DecompositionResult.mass_conservation_residual_g).",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="LLM self-reported confidence in this single mapping.",
    )
    mass_source: Literal[
        "explicit_percentage",   # extracted from "Tomato 65%" on the label
        "macro_constrained",     # inferred to reconcile NF macros + position rank
        "position_inferred",     # inferred from position rank only (no macro anchor)
    ] = "position_inferred"


class DecompositionResult(BaseModel):
    """Output of /api/packaged-food/decompose-ingredients/."""
    model_config = ConfigDict(extra="forbid")

    schema_version: int = SCHEMA_VERSION
    ingredients: List[DecomposedIngredient] = Field(default_factory=list)

    net_weight_g_assumed: float = Field(
        description="The net weight used as the mass-conservation anchor. "
                    "Sourced from the NF panel's net_weight when present, "
                    "or imputed from servings_per_container × serving_size.",
    )
    mass_conservation_residual_g: float = Field(
        description="(sum of mass_g) − net_weight_g_assumed. Within ± 5 % "
                    "of net weight = good. Larger residuals lower the "
                    "overall decomposition_confidence.",
    )

    macro_reconciliation: dict = Field(
        default_factory=dict,
        description="Macro check: each panel macro vs the macro the decomposed "
                    "CNF foods sum to. Within ± 10 % per macro = good.",
    )

    decomposition_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall confidence — lowered by mass-conservation violations, "
                    "low individual-ingredient confidences, low explicit_percentage "
                    "coverage, or large macro-reconciliation residuals.",
    )

    decomposition_warnings: List[str] = Field(default_factory=list)
    extraction_metadata: ExtractionMetadata

    decomposition_succeeded: bool = True
    failure_reason: Optional[str] = None
