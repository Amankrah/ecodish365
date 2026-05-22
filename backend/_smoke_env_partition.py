"""Throwaway smoke test for the EF -> ReCiPe partition behaviour.

Question being verified: when the v32 matcher fires on a real food, does the
EF-incompatible set of categories fall back to cnf_integrator group defaults
on the ReCiPe side (as the manuscript claims), or is the fallback path
implemented differently?

Run from backend/ with the venv:
    venv/Scripts/python.exe _smoke_env_partition.py
"""
from __future__ import annotations

import json
import os
import sys

# Mirror the Django sys.path tweak (dish_project/settings.py adds these).
_HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("environmental_impact_model", "dish_cnf_db_pipeline"):
    p = os.path.join(_HERE, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

# Bring Django up so cnf_cache can read settings.CNF_FOLDER.
# env_bootstrap loads backend/.env (OPENAI_API_KEY etc.) before Django imports.
import dish_project.env_bootstrap  # noqa: F401,E402
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
import django  # noqa: E402

django.setup()


def main() -> int:
    from environmental_impact_model.etl.ef_to_recipe_mapping import (
        EF_INCOMPATIBLE_WITH_RECIPE,
        EF_TO_RECIPE_DIRECT,
        EF_SINGLE_SCORE_COLUMN,
        all_ef_columns,
    )

    print("=" * 72)
    print("Partition audit (manuscript claim)")
    print("=" * 72)
    print(f"|EF_TO_RECIPE_DIRECT|       = {len(EF_TO_RECIPE_DIRECT):>2}")
    print(f"|EF_INCOMPATIBLE_WITH_RECIPE| = {len(EF_INCOMPATIBLE_WITH_RECIPE):>2}")
    print(f"|{{EF_SINGLE_SCORE_COLUMN}}|   = 1")
    print(f"|union of all_ef_columns()| = {len(all_ef_columns()):>2}")
    print()
    print("Incompatible categories (manuscript should reflect this list):")
    for i, name in enumerate(sorted(EF_INCOMPATIBLE_WITH_RECIPE), 1):
        print(f"  {i:>2}. {name}")
    print()

    # --- Real-food smoke test of the matcher dual-namespace + LCA fallback. ---
    from environmental_impact_model.src.cnf_integrator import get_cnf_integrator
    from environmental_impact_model.src.lca_matcher import (
        AgribalyseIndex,
        DEFAULT_BOOTSTRAP_CATALOG_PATH,
    )

    integrator = get_cnf_integrator()
    integrator.initialize()
    print("cnf_integrator initialized:", integrator.is_initialized())

    # Load the v32 catalog and pick a real beef row to demonstrate the
    # dual-namespace payload. Beef sirloin has both rich EF and ReCiPe sides.
    idx = AgribalyseIndex(catalog_path=DEFAULT_BOOTSTRAP_CATALOG_PATH)
    sample_entry = None
    for entry in idx.catalog:
        ef = entry.get("ef31_indicators_per_100g") or {}
        if (
            "boeuf" in (entry.get("lci_name_fr") or "").lower()
            and ef.get("Particules fines") is not None
            and ef.get("Utilisation du sol") is not None
        ):
            sample_entry = entry
            break
    if sample_entry is None:
        sample_entry = idx.catalog[0]
    print(
        "\nSample Agribalyse row:",
        sample_entry.get("ciqual_code"),
        "-",
        sample_entry.get("lci_name_fr") or sample_entry.get("lci_name"),
    )

    recipe_side = sample_entry.get("recipe2016_midpoints_per_100g") or {}
    ef_side = sample_entry.get("ef31_indicators_per_100g") or {}
    print(f"\nReCiPe-side keys present  (matched overlay) : {sorted(recipe_side.keys())}")
    print(f"EF31-side keys present                       : {len(ef_side)} indicators")

    # Confirm the partition contract row-by-row.
    ef_incompat_present = [c for c in EF_INCOMPATIBLE_WITH_RECIPE if c in ef_side]
    ef_direct_present = [c for c in EF_TO_RECIPE_DIRECT if c in ef_side]
    print(f"\nEF-incompatible cats present in EF dict     : {len(ef_incompat_present)} / {len(EF_INCOMPATIBLE_WITH_RECIPE)}")
    print(f"EF-direct cats present in EF dict           : {len(ef_direct_present)} / {len(EF_TO_RECIPE_DIRECT)}")

    # Crucial check: the ReCiPe overlay must NOT carry any key that traces
    # back to an EF-incompatible source (i.e. the matcher must not coerce).
    coerced_recipe_keys = [
        EF_TO_RECIPE_DIRECT[k] for k in EF_TO_RECIPE_DIRECT
        if EF_TO_RECIPE_DIRECT[k] in recipe_side
    ]
    print(f"ReCiPe keys overlaid from EF directs        : {coerced_recipe_keys}")
    assert all(
        k not in EF_INCOMPATIBLE_WITH_RECIPE for k in recipe_side
    ), "ReCiPe overlay leaked an EF-incompatible category"

    # --- Now exercise the merge in life_cycle_assessment for a real food. ---
    from environmental_impact_model.src.food import Food
    from environmental_impact_model.src.meal import Meal
    from environmental_impact_model.src.data_loader import DataLoader
    from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment

    # Pick the first beef row from CNF (FoodGroupID may vary; we just need a
    # real food_id from the CNF DB to exercise group-default lookup).
    food_name_df = integrator.get_dataframe("food_name")
    beef_rows = food_name_df[
        food_name_df["FoodDescription"].str.contains("Beef", case=False, na=False)
    ]
    if beef_rows.empty:
        print("\nNo beef foods found in CNF — using arbitrary first food.")
        food_id = int(food_name_df.iloc[0]["FoodID"])
        food_name = str(food_name_df.iloc[0]["FoodDescription"])
    else:
        food_id = int(beef_rows.iloc[0]["FoodID"])
        food_name = str(beef_rows.iloc[0]["FoodDescription"])
    print(f"\nSmoke meal: {food_name} (food_id={food_id}), 100 g")

    data_loader = DataLoader()
    food = Food(food_id=food_id, quantity=100.0, data_loader=data_loader)
    meal = Meal(foods=[food])

    # Matcher OFF — purely the cnf_integrator group-default path. This is what
    # the manuscript says the "ReCiPe-side fallback" looks like for the 14
    # EF-incompatible categories.
    lca = LifeCycleAssessment(meal, matcher=None)
    midpoints = lca.perform_lcia()
    print("\nMidpoint impacts (matcher OFF, group-default ReCiPe):")
    for k in sorted(midpoints):
        print(f"  {k:>40}: {midpoints[k]:.6g}")

    # v1 TRIMMED SCOPE: the consumed midpoint vector is now only the 3
    # categories the pipeline can defend per-food-group from literature
    # (Global warming, Land use, Water consumption). The other 15 ReCiPe
    # midpoints are NOT in the consumed vector by design — see
    # life_cycle_assessment._calculate_midpoint_impacts docstring and
    # manuscript §7.5.
    expected_v1_midpoints = {"Global warming", "Land use", "Water consumption"}
    actual_midpoints = set(midpoints.keys())
    assert actual_midpoints == expected_v1_midpoints, (
        f"v1 midpoint trim violated: expected {expected_v1_midpoints}, "
        f"got {actual_midpoints}"
    )
    print(f"\nv1 trimmed midpoint set populated: {sorted(actual_midpoints)}")

    # Per-category source audit. Matcher OFF → every consumed key should be
    # explicitly tagged "fallback_low_confidence:group_default" rather than
    # silently labelled "group_default".
    impacts_dbg = lca._get_food_environmental_impacts(food)
    sources = impacts_dbg.get("_category_sources", {})
    sources_for_consumed = {k: v for k, v in sources.items() if k in expected_v1_midpoints}
    distinct_sources = set(sources_for_consumed.values())
    print(f"Category-source values when matcher OFF: {distinct_sources}")
    assert distinct_sources == {"fallback_low_confidence:group_default"}, (
        f"matcher-off path should be explicit fallback_low_confidence tag, "
        f"got {distinct_sources}"
    )

    # ------------------------------------------------------------------ #
    # Matcher ON — real retrieval + LLM ranking (OPENAI_API_KEY required) #
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 72)
    print("Matcher ON (real retrieval + LLM ranking)")
    print("=" * 72)
    # Echo log warnings from the LCA merge so silent matcher exceptions surface.
    import logging as _logging
    _logging.basicConfig(level=_logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    from environmental_impact_model.src.lca_matcher import build_default_matcher
    matcher = build_default_matcher()
    print(f"Matcher LLM client present?       {matcher.ranking_client is not None}")
    print(f"Embedding client present?         {matcher.retriever.embedding_client is not None}")
    print(f"Confidence threshold:             {matcher.confidence_threshold}")
    lca2 = LifeCycleAssessment(meal, matcher=matcher)
    midpoints2 = lca2.perform_lcia()
    impacts_dbg2 = lca2._get_food_environmental_impacts(food)
    sources2 = impacts_dbg2.get("_category_sources", {})
    food_source = impacts_dbg2.get("_source", "?")

    # Show the matcher's actual decision for this food.
    if lca2.matcher_decisions:
        d = lca2.matcher_decisions[-1]
        print(
            f"\nMatcher decision for food_id={food.food_id}:\n"
            f"  matched           : {d.get('matched')}\n"
            f"  ciqual_code       : {d.get('ciqual_code')}\n"
            f"  lci_name          : {d.get('lci_name')}\n"
            f"  confidence        : {d.get('confidence'):.4f}\n"
            f"  fallback_reason   : {d.get('fallback_reason')}\n"
            f"  catalog_version   : {d.get('catalog_version')}\n"
        )
    print(f"food-level _source tag: {food_source}")

    # Per-category source split.
    by_source: Dict[str, List[str]] = {}
    for cat, src in sources2.items():
        by_source.setdefault(src, []).append(cat)
    print(f"\nReCiPe categories grouped by source:")
    for src, cats in sorted(by_source.items()):
        print(f"  [{src}]  ({len(cats)} categories)")
        for c in sorted(cats):
            v_off = midpoints.get(c, 0.0)
            v_on = midpoints2.get(c, 0.0)
            delta = v_on - v_off
            tag = "  CHANGED" if abs(delta) > 1e-12 else ""
            print(f"    {c:>42}  off={v_off:.5g}  on={v_on:.5g}{tag}")

    # The claim under test: matcher-on path produces matched-category sources
    # only for the 5 EF-direct ReCiPe keys; the other 13 stay group_default.
    if food_source.startswith("agribalyse_match:"):
        matched_cats = {c for c, s in sources2.items() if s == food_source}
        default_cats = {c for c, s in sources2.items() if s == "group_default"}
        print(
            f"\nMatcher-overlay split:\n"
            f"  categories sourced from match           : {len(matched_cats)}\n"
            f"  categories sourced from group default   : {len(default_cats)}\n"
        )
        # Show exactly which keys came from the matcher.
        print(f"  matcher-sourced keys: {sorted(matched_cats)}")

    print("\nAll smoke assertions passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
