"""Ingredient-list → CNF FoodID decomposition (PKG-IMG-1 Phase 2).

Given a packaged product's ingredient list (positions, optional %) and its
NF panel macros (per_serving + net_weight), produce a CNF-mapped composition
where each ingredient has a FoodID + inferred mass_g. The composition is then
routable to HEFI / HENI / FCS / dietary-pattern / environmental scorers via
the existing useRecall24hReceiver handoff.

Two-stage pipeline:

  Stage 1: CANDIDATE RETRIEVAL
    For each ingredient text, run the existing CNFMatcher.match() to get
    top-K (default 5) candidate FoodIDs. Aggregate the union → "candidate
    pool" — the LLM is constrained to picking from this pool, preventing
    hallucinated FoodIDs.

  Stage 2: CONSTRAINED MAPPING + MASS INFERENCE
    Single LLM call passes the constrained candidate pool + ingredient
    positions + NF panel macros + net_weight, and asks for per-ingredient
    {food_id, mass_g, confidence}. Constraints in the prompt:
      - Sum of mass_g must reconcile with net_weight ± 5 %.
      - Resulting macro profile (sum across foods, in CNF database) must
        reconcile with the NF panel ± 10 % per macro.
      - Each ingredient's food_id MUST come from its candidate pool.
      - Order MUST respect descending mass (position 1 ≥ position 2 ≥ ...).
      - When an ingredient carries an explicit_percentage, use it as a hard
        anchor (mass_g = explicit_percentage / 100 × net_weight_g) and
        adjust the others around it.

  Stage 3: SERVER-SIDE VALIDATION
    Verify mass-conservation residual ≤ 5 % and macro reconciliation
    ≤ 10 % per macro. Violations lower decomposition_confidence and
    surface as warnings; they don't fail the call (the user can edit
    the composition in the UI).

Honest framing: the output is INFERRED composition, not measured. Regulation
only requires descending-mass-order, not percentages. The decomposition is
a structured guess constrained by the NF panel's macros. Downstream caveats
in the dietary-pattern / HEFI / HENI views surface this.
"""
from __future__ import annotations

import datetime as _dt
import logging
import time
from typing import Any, Dict, List, Optional

from .cnf_matcher import get_default_matcher, CNFMatcher
from .multimodal_client import build_multimodal_client
from .packaged_food_schema import (
    DecomposedIngredient,
    DecompositionResult,
    ExtractionMetadata,
    IngredientListExtraction,
    NFPanelExtraction,
    PackagedFoodExtraction,
    SCHEMA_VERSION,
)
from .packaged_food_prompts import PROMPT_VERSION
from environmental_impact_model.src.llm_client import build_chat_json_client
from api.cnf_cache import get_api_cnf_pipeline


logger = logging.getLogger(__name__)


CANDIDATES_PER_INGREDIENT = 5
"""Top-K candidates per ingredient retrieved from the CNF matcher and passed
to the LLM as the constrained pool. Higher = more flexibility but bigger
prompt; 5 is empirically sufficient for label ingredients (which are usually
generic — 'sugar', 'wheat flour' — not branded)."""


# Macros we round-trip through the NF panel for the reconciliation check.
# Keys are NF panel field names; values are how to read them off a CNF food
# (these CNF nutrient-name keys are the canonical uppercase form).
_MACRO_FIELDS = [
    ("energy_kcal",          "ENERGY (KILOCALORIES)",            5.0),  # tolerance: kcal absolute
    ("fat_total_g",          "FAT (TOTAL LIPIDS)",                1.0),
    ("carbohydrate_total_g", "CARBOHYDRATE, TOTAL (BY DIFFERENCE)", 1.0),
    ("protein_g",            "PROTEIN",                            1.0),
    ("sodium_mg",            "SODIUM",                            50.0),  # mg
]


MACRO_RECONCILIATION_TOLERANCE_PCT = 0.10
MASS_CONSERVATION_TOLERANCE_PCT = 0.05


# =======================================================================
# Public entry point
# =======================================================================


def decompose_packaged_food(
    panel: NFPanelExtraction,
    ingredients: IngredientListExtraction,
    *,
    matcher: Optional[CNFMatcher] = None,
    chat_client: Optional[Any] = None,
    candidates_per_ingredient: int = CANDIDATES_PER_INGREDIENT,
) -> DecompositionResult:
    """Decompose a packaged product into a CNF-mapped composition.

    Args:
      panel:        the (user-confirmed) NF panel from Phase 1.
      ingredients:  the (user-confirmed) ingredient list from Phase 2.
      matcher:      optional CNFMatcher (defaults to the shared one).
      chat_client:  optional text-only LLM client (gpt-4.1-mini default).
      candidates_per_ingredient: top-K CNF candidates per ingredient.

    Returns:
      DecompositionResult — validated, with per-ingredient food_id + mass_g
      and per-macro reconciliation report. decomposition_confidence is the
      overall trust signal (frontend shows this prominently).

    Raises:
      RuntimeError on LLM unavailable (no API key).
    """
    t_start = time.perf_counter()

    # 0. Validate inputs.
    if not ingredients.ingredients_parsed:
        return _build_failed(
            t_start,
            reason="no_parsed_ingredients: ingredients_text exists but parsed list is empty",
            net_weight=_resolve_net_weight(panel),
        )

    if matcher is None:
        matcher = get_default_matcher()
    if chat_client is None:
        chat_client = build_chat_json_client()
    if chat_client is None:
        raise RuntimeError(
            "ChatJSONClient unavailable: set ANTHROPIC_API_KEY (or OPENAI_API_KEY "
            "when LLM_PROVIDER=openai) and ensure LLM_PROVIDER matches. "
            "For Opus decomposition set CHAT_LLM_MODEL=claude-opus-4-7."
        )

    net_weight_g = _resolve_net_weight(panel)
    if net_weight_g is None or net_weight_g <= 0:
        return _build_failed(
            t_start,
            reason="no_net_weight: cannot decompose without a mass-conservation anchor. "
                   "Either net_weight is missing from the panel or servings × serving_size "
                   "produced 0. Have the user supply net_weight on the form before retrying.",
            net_weight=0.0,
        )

    # 1. Stage 1 — per-ingredient candidate retrieval.
    candidate_pool: Dict[int, Dict[str, Any]] = {}  # food_id → {desc, group, suggested_for: [positions]}
    per_ingredient_candidates: List[List[int]] = []  # [position_idx] → [food_id, ...]

    for ing in ingredients.ingredients_parsed:
        # The CNF matcher accepts free-text and returns top-K candidates
        # ranked by embedding similarity + LLM rerank.
        match_result = matcher.match(ing.name, top_k=candidates_per_ingredient)
        # match() returns a single best result + the candidate pool it
        # considered. Use the alternatives list to expand to top-K.
        food_ids_for_this_ingredient: List[int] = []
        if match_result.matched and match_result.food_id is not None:
            food_ids_for_this_ingredient.append(int(match_result.food_id))
            candidate_pool[int(match_result.food_id)] = {
                "food_id": int(match_result.food_id),
                "food_description": match_result.food_description,
                "food_group": match_result.food_group,
                "macros": _lookup_macros_per_100g(int(match_result.food_id)),
            }
        # Pull additional alternatives if exposed
        alt_ids = getattr(match_result, "alternative_ids", None) or []
        for aid in alt_ids[:candidates_per_ingredient - 1]:
            if aid and aid not in [c["food_id"] for c in candidate_pool.values()]:
                # We don't have descriptions for raw alternatives; look them up.
                desc = _lookup_food_description(aid)
                if desc:
                    food_ids_for_this_ingredient.append(int(aid))
                    candidate_pool[int(aid)] = {
                        "food_id": int(aid),
                        "food_description": desc,
                        "food_group": None,
                        "macros": _lookup_macros_per_100g(int(aid)),
                    }
        per_ingredient_candidates.append(food_ids_for_this_ingredient)

    # If no candidates at all, fail gracefully.
    if not candidate_pool:
        return _build_failed(
            t_start,
            reason="no_cnf_candidates: every ingredient text failed to match any CNF food. "
                   "This is unusual — possibly a foreign-language ingredient list.",
            net_weight=net_weight_g,
        )

    # 2. Stage 2 — constrained mapping + mass inference via LLM.
    llm_result = _call_decomposition_llm(
        panel=panel, ingredients=ingredients,
        per_ingredient_candidates=per_ingredient_candidates,
        candidate_pool=candidate_pool,
        net_weight_g=net_weight_g,
        chat_client=chat_client,
    )
    if llm_result is None:
        return _build_failed(
            t_start,
            reason="llm_decomposition_failed: see logs for details",
            net_weight=net_weight_g,
        )

    decomposed: List[DecomposedIngredient] = []
    for raw_ing in llm_result.get("ingredients", []):
        try:
            fid = int(raw_ing.get("food_id"))
        except (TypeError, ValueError):
            continue
        # Enforce constraint: food_id MUST be in the candidate pool.
        if fid not in candidate_pool:
            logger.warning("LLM picked food_id %s not in candidate pool; skipping", fid)
            continue
        pool = candidate_pool[fid]
        try:
            mass_g = float(raw_ing.get("mass_g", 0.0))
        except (TypeError, ValueError):
            mass_g = 0.0
        if mass_g < 0:
            mass_g = 0.0
        decomposed.append(DecomposedIngredient(
            label_name=str(raw_ing.get("label_name") or pool["food_description"]),
            position=int(raw_ing.get("position", len(decomposed) + 1)),
            food_id=fid,
            food_description=pool["food_description"],
            food_group=pool.get("food_group"),
            mass_g=mass_g,
            confidence=float(raw_ing.get("confidence", 0.0)),
            mass_source=raw_ing.get("mass_source", "position_inferred"),
        ))

    if not decomposed:
        return _build_failed(
            t_start,
            reason="llm_returned_no_valid_ingredients: every mapping was outside the candidate pool",
            net_weight=net_weight_g,
        )

    # 3. Stage 3 — server-side validation: mass conservation + macro reconciliation.
    total_mass = sum(d.mass_g for d in decomposed)
    mass_residual = total_mass - net_weight_g
    warnings: List[str] = []

    if abs(mass_residual) > MASS_CONSERVATION_TOLERANCE_PCT * net_weight_g:
        warnings.append(
            f"mass_conservation: total {total_mass:.0f}g differs from "
            f"net weight {net_weight_g:.0f}g by {mass_residual:+.0f}g "
            f"({abs(mass_residual) / net_weight_g * 100:.1f}% — exceeds "
            f"{MASS_CONSERVATION_TOLERANCE_PCT * 100:.0f}% tolerance)"
        )

    macro_recon = _check_macro_reconciliation(decomposed, panel, total_mass, warnings)

    # Decomposition confidence: starts at 1.0, lowered by violations.
    confidence = float(llm_result.get("decomposition_confidence", 0.7))
    if abs(mass_residual) > MASS_CONSERVATION_TOLERANCE_PCT * net_weight_g:
        confidence = min(confidence, 0.5)
    if any("macro_mismatch" in w for w in warnings):
        confidence = min(confidence, 0.6)

    return DecompositionResult(
        ingredients=decomposed,
        net_weight_g_assumed=net_weight_g,
        mass_conservation_residual_g=mass_residual,
        macro_reconciliation=macro_recon,
        decomposition_confidence=confidence,
        decomposition_warnings=warnings,
        extraction_metadata=_build_metadata(chat_client, t_start),
        decomposition_succeeded=True,
        failure_reason=None,
    )


# =======================================================================
# Stage 2 — LLM call
# =======================================================================


_DECOMPOSITION_SYSTEM_PROMPT = """\
You are a packaged-food ingredient decomposer for ecodish365. Given a \
product's ingredient list (in descending mass order, per regulation) and \
its Nutrition Facts panel macros (per serving + net weight), infer per- \
ingredient masses in grams that:

  1. SUM to the net weight ± 5%.
  2. When MASS-WEIGHTED against the CNF database macros (you'll be told the \
     per-100g macros of each candidate food), reconcile with the NF panel \
     macros ± 10% per macro (energy, fat, carbs, protein, sodium).
  3. RESPECT descending mass order: ingredient at position 1 has the \
     largest mass; position 2 ≤ position 1; and so on.
  4. Use any EXPLICIT PERCENTAGE on the label as a HARD anchor: \
     mass_g = explicit_percentage / 100 × net_weight_g. Adjust the other \
     ingredients to make the sum reconcile.

For each ingredient you must pick ONE food_id from its constrained candidate \
pool. NEVER invent a food_id outside the pool. If no candidate fits well, \
pick the closest match and lower its confidence.

Output as a single JSON object — NO prose, NO markdown fences:

{
  "ingredients": [
    {
      "label_name": "tomato puree",
      "position": 1,
      "food_id": 2756,
      "mass_g": 180.0,
      "confidence": 0.85,
      "mass_source": "macro_constrained" | "explicit_percentage" | "position_inferred"
    },
    ...
  ],
  "decomposition_confidence": 0.0-1.0
}

Honest framing: regulation only requires descending mass order, not \
percentages. Your output is INFERRED composition, not measured. When you're \
uncertain, return a lower decomposition_confidence — the user sees this \
prominently and can edit the masses in the UI before scoring.
"""


def _call_decomposition_llm(
    *,
    panel: NFPanelExtraction,
    ingredients: IngredientListExtraction,
    per_ingredient_candidates: List[List[int]],
    candidate_pool: Dict[int, Dict[str, Any]],
    net_weight_g: float,
    chat_client: Any,
) -> Optional[Dict[str, Any]]:
    """Build the constrained prompt and call the chat client."""
    # Build per-ingredient candidate block.
    ing_lines: List[str] = []
    for idx, ing in enumerate(ingredients.ingredients_parsed):
        cands_ids = per_ingredient_candidates[idx] if idx < len(per_ingredient_candidates) else []
        cand_strs = []
        for fid in cands_ids:
            pool = candidate_pool.get(fid, {})
            macros = pool.get("macros") or {}
            kcal = macros.get("energy_kcal", 0)
            cand_strs.append(
                f"      food_id={fid}: \"{pool.get('food_description', '?')}\" "
                f"(per-100g: {kcal:.0f}kcal, {macros.get('fat_total_g', 0):.1f}g fat, "
                f"{macros.get('carbohydrate_total_g', 0):.1f}g carb, "
                f"{macros.get('protein_g', 0):.1f}g protein, "
                f"{macros.get('sodium_mg', 0):.0f}mg sodium)"
            )
        explicit = (f", EXPLICIT {ing.explicit_percentage:.1f}%"
                    if ing.explicit_percentage is not None else "")
        parens = (f", sub-ingredients: {ing.parenthetical}"
                  if ing.parenthetical else "")
        ing_lines.append(
            f"  Position {ing.position}: \"{ing.name}\"{explicit}{parens}\n"
            f"    Candidates (pick ONE food_id):\n" + "\n".join(cand_strs)
        )

    panel_macros = panel.per_serving.model_dump() if panel.per_serving else {}
    serving_g = panel.serving_size.value if panel.serving_size and panel.serving_size.value else 0
    servings_per = panel.servings_per_container.value if panel.servings_per_container and panel.servings_per_container.value else 1

    # Build macro context lines — only include macros we actually have.
    macro_ctx = []
    for panel_key, _cnf_key, _tol in _MACRO_FIELDS:
        v = (panel_macros.get(panel_key) or {}).get("value")
        if v is not None:
            macro_ctx.append(f"    {panel_key}: {v} per serving ({serving_g}g) — "
                             f"per-100g target ≈ {(v * 100 / serving_g) if serving_g else 0:.1f}")

    user_msg = f"""\
Product: {panel.product_name_visible.value or 'unknown'} \
({panel.brand_visible.value or 'unknown brand'})

Net weight: {net_weight_g:.0f} g (mass-conservation target)
Servings per container: {servings_per}
Serving size: {serving_g} g

NF panel macros per serving:
{chr(10).join(macro_ctx) if macro_ctx else '    (none extracted)'}

Ingredient list (descending mass order):
{chr(10).join(ing_lines)}

Decompose. Return the JSON object as described in your system instructions.
"""

    try:
        result = chat_client.chat_completion_json(
            system=_DECOMPOSITION_SYSTEM_PROMPT,
            user=user_msg,
            temperature=0.0,
            max_tokens=2048,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("ingredient decomposition LLM call failed: %s", exc)
        return None

    if not isinstance(result, dict):
        return None
    return result


# =======================================================================
# Helpers
# =======================================================================


def _resolve_net_weight(panel: NFPanelExtraction) -> Optional[float]:
    """Resolve net weight in grams from the panel, with sensible fallbacks."""
    nw = panel.net_weight
    if nw and nw.value is not None and nw.value > 0:
        # ml treated as g (density assumption); same as the HSR path.
        return float(nw.value)
    # Fallback: servings_per_container × serving_size
    serv = panel.serving_size
    spc = panel.servings_per_container
    if serv and serv.value and spc and spc.value:
        return float(serv.value) * float(spc.value)
    return None


def _lookup_food_description(food_id: int) -> Optional[str]:
    """Lookup CNF food description by FoodID via the shared pipeline."""
    try:
        pipeline = get_api_cnf_pipeline()
        details = pipeline.get_food_details(int(food_id))
        if details:
            return details.get("FoodDescription")
    except Exception:  # noqa: BLE001
        pass
    return None


def _lookup_macros_per_100g(food_id: int) -> Dict[str, float]:
    """Lookup per-100g macros for a CNF food. Returns empty dict on miss."""
    try:
        pipeline = get_api_cnf_pipeline()
        details = pipeline.get_food_details(int(food_id))
        if not details:
            return {}
        nv = {n["NutrientName"]: n["NutrientValue"] for n in details.get("NutrientValues", [])}
        return {
            "energy_kcal":          float(nv.get("ENERGY (KILOCALORIES)", 0) or 0),
            "fat_total_g":          float(nv.get("FAT (TOTAL LIPIDS)", 0) or 0),
            "carbohydrate_total_g": float(nv.get("CARBOHYDRATE, TOTAL (BY DIFFERENCE)", 0) or 0),
            "protein_g":            float(nv.get("PROTEIN", 0) or 0),
            "sodium_mg":            float(nv.get("SODIUM", 0) or 0),
        }
    except Exception:  # noqa: BLE001
        return {}


def _check_macro_reconciliation(
    decomposed: List[DecomposedIngredient],
    panel: NFPanelExtraction,
    total_mass_g: float,
    warnings: List[str],
) -> Dict[str, Any]:
    """Sum CNF per-100g macros weighted by decomposed mass; compare to NF panel.
    Adds warnings for any macro outside the tolerance band."""
    if total_mass_g <= 0 or not panel.per_serving:
        return {}
    # Compute the inferred-composition per-100g macros.
    inferred_per_100g: Dict[str, float] = {k: 0.0 for k, _, _ in _MACRO_FIELDS}
    for ing in decomposed:
        macros = _lookup_macros_per_100g(ing.food_id)
        for key in inferred_per_100g:
            inferred_per_100g[key] += macros.get(key, 0.0) * (ing.mass_g / 100.0)
    # Convert sum to per-100g of total product.
    for key in inferred_per_100g:
        inferred_per_100g[key] = inferred_per_100g[key] * 100.0 / total_mass_g

    # NF panel per-100g target.
    panel_macros = panel.per_serving.model_dump()
    serving_g = panel.serving_size.value if panel.serving_size and panel.serving_size.value else 0
    if not serving_g:
        return {"warning": "no_serving_size_for_reconciliation"}

    report: Dict[str, Any] = {}
    for panel_key, _cnf_key, abs_tol in _MACRO_FIELDS:
        panel_v = (panel_macros.get(panel_key) or {}).get("value")
        if panel_v is None:
            continue
        panel_per_100g = panel_v * 100.0 / serving_g
        inferred_v = inferred_per_100g.get(panel_key, 0.0)
        diff = inferred_v - panel_per_100g
        rel_diff = abs(diff) / panel_per_100g if panel_per_100g > 0 else 0.0
        report[panel_key] = {
            "panel_per_100g": round(panel_per_100g, 2),
            "inferred_per_100g": round(inferred_v, 2),
            "diff": round(diff, 2),
            "rel_diff_pct": round(rel_diff * 100, 1),
            "within_tolerance": rel_diff <= MACRO_RECONCILIATION_TOLERANCE_PCT,
        }
        if rel_diff > MACRO_RECONCILIATION_TOLERANCE_PCT and abs(diff) > abs_tol:
            warnings.append(
                f"macro_mismatch: {panel_key} panel says {panel_per_100g:.1f} "
                f"per-100g but decomposition implies {inferred_v:.1f} "
                f"({rel_diff * 100:.0f}% off)"
            )
    return report


def _build_metadata(client: Any, t_start: float) -> ExtractionMetadata:
    return ExtractionMetadata(
        model=getattr(client, "model", "unknown"),
        provider=getattr(client, "provider", "unknown"),
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        image_sha256="",  # decomposition is text-only; no image hash
        image_bytes=0,
        image_dimensions=[0, 0],
        extracted_at=_dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        extraction_warnings=[],
        sanity_guard_rejections=[],
        cache_hit=False,
        latency_ms=int((time.perf_counter() - t_start) * 1000),
    )


def _build_failed(t_start: float, *, reason: str,
                  net_weight: Optional[float]) -> DecompositionResult:
    meta = ExtractionMetadata(
        model="unknown", provider="unknown",
        prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION,
        image_sha256="", image_bytes=0, image_dimensions=[0, 0],
        extracted_at=_dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        latency_ms=int((time.perf_counter() - t_start) * 1000),
    )
    return DecompositionResult(
        ingredients=[],
        net_weight_g_assumed=net_weight or 0.0,
        mass_conservation_residual_g=0.0,
        macro_reconciliation={},
        decomposition_confidence=0.0,
        decomposition_warnings=[reason],
        extraction_metadata=meta,
        decomposition_succeeded=False,
        failure_reason=reason,
    )


def decompose_packaged_food_from_wrapper(
    wrapped: PackagedFoodExtraction,
    *, matcher: Optional[CNFMatcher] = None, chat_client: Optional[Any] = None,
) -> DecompositionResult:
    """Convenience: decompose from a PackagedFoodExtraction wrapper. Requires
    both NF panel AND ingredient list to be populated; otherwise returns a
    failed result with a clear reason."""
    if wrapped.nf_panel is None:
        return _build_failed(
            time.perf_counter(),
            reason="missing_nf_panel: decomposition requires NF panel for "
                   "macro-reconciliation anchoring. Capture a second photo "
                   "of the Nutrition Facts panel.",
            net_weight=None,
        )
    if wrapped.ingredient_list is None:
        return _build_failed(
            time.perf_counter(),
            reason="missing_ingredient_list: decomposition needs the "
                   "ingredient list. Capture a second photo of the back-of-pack "
                   "ingredient line.",
            net_weight=_resolve_net_weight(wrapped.nf_panel),
        )
    return decompose_packaged_food(
        panel=wrapped.nf_panel,
        ingredients=wrapped.ingredient_list,
        matcher=matcher, chat_client=chat_client,
    )
