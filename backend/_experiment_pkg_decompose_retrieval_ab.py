"""PKG-DECOMP-LATENCY-AB-1 — retrieval-only vs LLM-rank for packaged-food decompose.

Compares three stage-1 candidate-retrieval strategies before changing production:

  Arm A — Baseline: matcher.match() per ingredient (embed + Opus rank), pool ≈ 1
  Arm B — Fast:      embedding top-1 only, pool = 1
  Arm C — Intended:  embedding top-5, decompose LLM picks food_id

Usage (from backend/):
  set PYTHONIOENCODING=utf-8
  set LLM_PROVIDER=anthropic
  set MULTIMODAL_LLM_MODEL=claude-opus-4-7
  set CHAT_LLM_MODEL=claude-opus-4-7

  python _experiment_pkg_decompose_retrieval_ab.py fixtures
  python _experiment_pkg_decompose_retrieval_ab.py audit
  python _experiment_pkg_decompose_retrieval_ab.py stage1
  python _experiment_pkg_decompose_retrieval_ab.py ab --runs 3
  python _experiment_pkg_decompose_retrieval_ab.py downstream
  python _experiment_pkg_decompose_retrieval_ab.py report
  python _experiment_pkg_decompose_retrieval_ab.py all --runs 3

Fixtures → _experiment_pkg_decompose_fixtures/*.json
Results  → _experiment_pkg_decompose_ab_results.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

_HERE = Path(__file__).resolve().parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")

for line in (_HERE / ".env").read_text(encoding="utf-8").splitlines() if (_HERE / ".env").exists() else []:
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

if not os.environ.get("DJANGO_SECRET_KEY"):
    os.environ["DJANGO_SECRET_KEY"] = "experiment-pkg-decompose-ab"

import django  # noqa: E402

django.setup()

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from api.services.cnf_matcher import CNFMatcher, _normalise_query, get_default_matcher  # noqa: E402
from api.services.ingredient_to_cnf_decomposer import (  # noqa: E402
    CANDIDATES_PER_INGREDIENT,
    MASS_CONSERVATION_TOLERANCE_PCT,
    _build_failed,
    _build_metadata,
    _call_decomposition_llm,
    _check_macro_reconciliation,
    _lookup_food_description,
    _lookup_macros_per_100g,
    _resolve_net_weight,
    decompose_packaged_food,
)
from api.services.packaged_food_extractor import extract_packaged_food  # noqa: E402
from api.services.packaged_food_schema import (  # noqa: E402
    DecomposedIngredient,
    DecompositionResult,
    ExtractedNumeric,
    IngredientListExtraction,
    NFPanelExtraction,
)
from environmental_impact_model.src.llm_client import build_chat_json_client  # noqa: E402

ArmName = Literal["A", "B", "C"]

FIXTURE_DIR = _HERE / "_experiment_pkg_decompose_fixtures"
RESULTS_PATH = _HERE / "_experiment_pkg_decompose_ab_results.json"
IMG_DIR = _HERE / "packeged_foods_images"

# Smoke-panel images (may be absent locally — fixtures command skips missing files).
FIXTURE_SPECS: List[Dict[str, Any]] = [
    {
        "fixture_id": "F1_campbells_nf",
        "filename": "cambell's_nf.jpg",
        "net_weight_override_g": None,
    },
    {
        "fixture_id": "F2_campbells_can",
        "filename": "DSC_08782.webp",
        "net_weight_override_g": None,
    },
    {
        "fixture_id": "F3_stew_dual_column",
        "filename": "large_fe32287d-58b9-470f-bc34-6d13f181f125.jpg",
        "net_weight_override_g": None,
    },
    {
        "fixture_id": "F4_infant_formula",
        "filename": "GS-Plus1-RTF-2.webp",
        "net_weight_override_g": 946.0,
    },
    {
        "fixture_id": "F5_organic_soup",
        "filename": "image-asset.webp",
        "net_weight_override_g": None,
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _warm_matcher() -> CNFMatcher:
    get_default_matcher.cache_clear()
    matcher = get_default_matcher()
    return matcher


def _clear_matcher_runtime_cache(matcher: CNFMatcher) -> None:
    with matcher._cache_lock:  # noqa: SLF001
        matcher._cache.clear()
        matcher._cache_order.clear()


def _load_fixtures() -> List[Dict[str, Any]]:
    if not FIXTURE_DIR.exists():
        return []
    out: List[Dict[str, Any]] = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def _save_fixture(data: Dict[str, Any]) -> Path:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURE_DIR / f"{data['fixture_id']}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _apply_net_weight_override(panel: NFPanelExtraction, override_g: Optional[float]) -> NFPanelExtraction:
    if override_g is None:
        return panel
    panel = panel.model_copy(deep=True)
    panel.net_weight = ExtractedNumeric(value=float(override_g), unit="g", confidence=1.0)
    return panel


def _fixture_to_models(fix: Dict[str, Any]) -> Tuple[NFPanelExtraction, IngredientListExtraction]:
    panel = NFPanelExtraction.model_validate(fix["nf_panel"])
    ingredients = IngredientListExtraction.model_validate(fix["ingredient_list"])
    panel = _apply_net_weight_override(panel, fix.get("net_weight_override_g"))
    return panel, ingredients


def _pool_from_corpus_idx(matcher: CNFMatcher, idx: int) -> Dict[str, Any]:
    fid = int(matcher.corpus.food_ids[idx])
    return {
        "food_id": fid,
        "food_description": matcher.corpus.food_descriptions[idx],
        "food_group": matcher.corpus.food_groups[idx],
        "macros": _lookup_macros_per_100g(fid),
    }


def _jaccard(a: Set[int], b: Set[int]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _food_ids_by_position(dec: DecompositionResult) -> Dict[int, int]:
    return {int(i.position): int(i.food_id) for i in dec.ingredients}


def _macro_warning_count(dec: DecompositionResult) -> int:
    return sum(1 for w in dec.decomposition_warnings if "macro_mismatch" in w)


def _aggregated_from_dec(dec: DecompositionResult) -> List[Dict[str, Any]]:
    return [
        {
            "food_id": int(i.food_id),
            "mass_g": float(i.mass_g),
            "food_description": i.food_description,
            "food_group": i.food_group or "",
        }
        for i in dec.ingredients
    ]


# ---------------------------------------------------------------------------
# Stage 1 — candidate pool builders
# ---------------------------------------------------------------------------


@dataclass
class Stage1Result:
    candidate_pool: Dict[int, Dict[str, Any]]
    per_ingredient_candidates: List[List[int]]
    stage1_ms: float
    embed_calls: int
    llm_rank_calls: int
    pool_sizes: List[int]


def build_stage1_arm_a(
    ingredients: IngredientListExtraction,
    matcher: CNFMatcher,
    *,
    candidates_per_ingredient: int = CANDIDATES_PER_INGREDIENT,
) -> Stage1Result:
    """Production path — matcher.match() per ingredient."""
    t0 = time.perf_counter()
    candidate_pool: Dict[int, Dict[str, Any]] = {}
    per_ingredient_candidates: List[List[int]] = []
    embed_calls = 0
    llm_rank_calls = 0
    pool_sizes: List[int] = []

    for ing in ingredients.ingredients_parsed:
        match_result = matcher.match(ing.name, top_k=candidates_per_ingredient)
        if not match_result.cache_hit:
            embed_calls += 1
        if match_result.used_ai_ranking:
            llm_rank_calls += 1

        food_ids_for_this: List[int] = []
        if match_result.food_id is not None:
            fid = int(match_result.food_id)
            if fid not in food_ids_for_this:
                food_ids_for_this.append(fid)
            if fid not in candidate_pool:
                candidate_pool[fid] = {
                    "food_id": fid,
                    "food_description": match_result.food_description or "",
                    "food_group": match_result.food_group,
                    "macros": _lookup_macros_per_100g(fid),
                }
        for alt in match_result.alternatives[: candidates_per_ingredient - 1]:
            aid = int(alt.food_id)
            if aid in food_ids_for_this:
                continue
            food_ids_for_this.append(aid)
            if aid not in candidate_pool:
                candidate_pool[aid] = {
                    "food_id": aid,
                    "food_description": alt.food_description,
                    "food_group": alt.food_group,
                    "macros": _lookup_macros_per_100g(aid),
                }
        per_ingredient_candidates.append(food_ids_for_this)
        pool_sizes.append(len(food_ids_for_this))

    return Stage1Result(
        candidate_pool=candidate_pool,
        per_ingredient_candidates=per_ingredient_candidates,
        stage1_ms=(time.perf_counter() - t0) * 1000,
        embed_calls=embed_calls,
        llm_rank_calls=llm_rank_calls,
        pool_sizes=pool_sizes,
    )


def build_stage1_retrieve_only(
    ingredients: IngredientListExtraction,
    matcher: CNFMatcher,
    *,
    k: int,
) -> Stage1Result:
    """Embedding retrieval only — top-k per ingredient."""
    t0 = time.perf_counter()
    candidate_pool: Dict[int, Dict[str, Any]] = {}
    per_ingredient_candidates: List[List[int]] = []
    embed_calls = 0
    pool_sizes: List[int] = []

    for ing in ingredients.ingredients_parsed:
        nq = _normalise_query(ing.name)
        with matcher._emb_cache_lock:  # noqa: SLF001
            was_cached = nq in matcher._emb_cache
        pairs = matcher._retrieve(nq, k=k)  # noqa: SLF001
        if not was_cached:
            embed_calls += 1

        food_ids_for_this: List[int] = []
        for idx, _sim in pairs[:k]:
            entry = _pool_from_corpus_idx(matcher, idx)
            fid = entry["food_id"]
            if fid not in candidate_pool:
                candidate_pool[fid] = entry
            if fid not in food_ids_for_this:
                food_ids_for_this.append(fid)
        per_ingredient_candidates.append(food_ids_for_this)
        pool_sizes.append(len(food_ids_for_this))

    return Stage1Result(
        candidate_pool=candidate_pool,
        per_ingredient_candidates=per_ingredient_candidates,
        stage1_ms=(time.perf_counter() - t0) * 1000,
        embed_calls=embed_calls,
        llm_rank_calls=0,
        pool_sizes=pool_sizes,
    )


def build_stage1(arm: ArmName, ingredients: IngredientListExtraction, matcher: CNFMatcher) -> Stage1Result:
    if arm == "A":
        return build_stage1_arm_a(ingredients, matcher)
    if arm == "B":
        return build_stage1_retrieve_only(ingredients, matcher, k=1)
    return build_stage1_retrieve_only(ingredients, matcher, k=CANDIDATES_PER_INGREDIENT)


def decompose_with_arm(
    arm: ArmName,
    panel: NFPanelExtraction,
    ingredients: IngredientListExtraction,
    *,
    matcher: CNFMatcher,
    chat_client: Any,
) -> Tuple[DecompositionResult, Dict[str, Any]]:
    """Run stage-1 (arm-specific) + stage-2/3 (shared). Returns result + timing."""
    t_start = time.perf_counter()
    timing: Dict[str, Any] = {"arm": arm}

    if not ingredients.ingredients_parsed:
        dec = _build_failed(
            t_start,
            reason="no_parsed_ingredients: ingredients_text exists but parsed list is empty",
            net_weight=_resolve_net_weight(panel),
        )
        timing.update(stage1_ms=0.0, decompose_llm_ms=0.0, total_ms=dec.extraction_metadata.latency_ms)
        return dec, timing

    if chat_client is None:
        raise RuntimeError("Chat client unavailable — set ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic")

    net_weight_g = _resolve_net_weight(panel)
    if net_weight_g is None or net_weight_g <= 0:
        dec = _build_failed(
            t_start,
            reason="no_net_weight: cannot decompose without a mass-conservation anchor.",
            net_weight=0.0,
        )
        timing.update(stage1_ms=0.0, decompose_llm_ms=0.0, total_ms=dec.extraction_metadata.latency_ms)
        return dec, timing

    _clear_matcher_runtime_cache(matcher)
    s1 = build_stage1(arm, ingredients, matcher)
    timing["stage1_ms"] = s1.stage1_ms
    timing["embed_calls"] = s1.embed_calls
    timing["llm_rank_calls"] = s1.llm_rank_calls
    timing["pool_sizes"] = s1.pool_sizes
    timing["pool_size_median"] = statistics.median(s1.pool_sizes) if s1.pool_sizes else 0

    if not s1.candidate_pool:
        dec = _build_failed(
            t_start,
            reason="no_cnf_candidates: every ingredient text failed to match any CNF food.",
            net_weight=net_weight_g,
        )
        timing["decompose_llm_ms"] = 0.0
        timing["total_ms"] = (time.perf_counter() - t_start) * 1000
        return dec, timing

    t_llm = time.perf_counter()
    llm_result = _call_decomposition_llm(
        panel=panel,
        ingredients=ingredients,
        per_ingredient_candidates=s1.per_ingredient_candidates,
        candidate_pool=s1.candidate_pool,
        net_weight_g=net_weight_g,
        chat_client=chat_client,
    )
    timing["decompose_llm_ms"] = (time.perf_counter() - t_llm) * 1000
    timing["decompose_opus_calls"] = 1 if llm_result is not None else 0

    if llm_result is None:
        dec = _build_failed(t_start, reason="llm_decomposition_failed: see logs", net_weight=net_weight_g)
        timing["total_ms"] = (time.perf_counter() - t_start) * 1000
        return dec, timing

    decomposed: List[DecomposedIngredient] = []
    for raw_ing in llm_result.get("ingredients", []):
        try:
            fid = int(raw_ing.get("food_id"))
        except (TypeError, ValueError):
            continue
        if fid not in s1.candidate_pool:
            continue
        pool = s1.candidate_pool[fid]
        try:
            mass_g = float(raw_ing.get("mass_g", 0.0))
        except (TypeError, ValueError):
            mass_g = 0.0
        if mass_g < 0:
            mass_g = 0.0
        decomposed.append(
            DecomposedIngredient(
                label_name=str(raw_ing.get("label_name") or pool["food_description"]),
                position=int(raw_ing.get("position", len(decomposed) + 1)),
                food_id=fid,
                food_description=pool["food_description"],
                food_group=pool.get("food_group"),
                mass_g=mass_g,
                confidence=float(raw_ing.get("confidence", 0.0)),
                mass_source=raw_ing.get("mass_source", "position_inferred"),
            )
        )

    if not decomposed:
        dec = _build_failed(
            t_start,
            reason="llm_returned_no_valid_ingredients: every mapping was outside the candidate pool",
            net_weight=net_weight_g,
        )
        timing["total_ms"] = (time.perf_counter() - t_start) * 1000
        return dec, timing

    total_mass = sum(d.mass_g for d in decomposed)
    mass_residual = total_mass - net_weight_g
    warnings: List[str] = []
    if abs(mass_residual) > MASS_CONSERVATION_TOLERANCE_PCT * net_weight_g:
        warnings.append(
            f"mass_conservation: total {total_mass:.0f}g differs from net weight {net_weight_g:.0f}g"
        )
    macro_recon = _check_macro_reconciliation(decomposed, panel, total_mass, warnings)
    confidence = float(llm_result.get("decomposition_confidence", 0.7))
    if abs(mass_residual) > MASS_CONSERVATION_TOLERANCE_PCT * net_weight_g:
        confidence = min(confidence, 0.5)
    if any("macro_mismatch" in w for w in warnings):
        confidence = min(confidence, 0.6)

    dec = DecompositionResult(
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
    timing["total_ms"] = (time.perf_counter() - t_start) * 1000
    timing["macro_warnings"] = _macro_warning_count(dec)
    return dec, timing


# ---------------------------------------------------------------------------
# Downstream scorers (mirrors _smoke_cnf_recall_24h.py)
# ---------------------------------------------------------------------------


def _route_to_hefi(aggregated: List[Dict[str, Any]]) -> Optional[float]:
    try:
        from django.conf import settings
        from hefi_calculator.hefi.algorithm import compute_hefi
        from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
        from hefi_calculator.hefi.models import HEFIInputs

        integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
        food_data = [(int(i["food_id"]), float(i["mass_g"])) for i in aggregated]
        agg = integrator.aggregate_inputs(food_data)
        result = compute_hefi(HEFIInputs(**agg))
        return float(getattr(result, "overall_score", None) or getattr(result, "total_score", None) or 0.0)
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] HEFI: {exc!r}")
        return None


def _route_to_heni(aggregated: List[Dict[str, Any]]) -> Optional[float]:
    try:
        from heni_calculator.heni.models.ingredient import Ingredient
        from heni_calculator.heni.service import calculate_meal_heni_response, get_cnf_integrator

        integrator = get_cnf_integrator()
        ingredients = [
            Ingredient(
                food_id=int(i["food_id"]),
                amount=float(i["mass_g"]),
                unit="g",
                cnf_integrator=integrator,
            )
            for i in aggregated
        ]
        result = calculate_meal_heni_response(ingredients, llm_api_key=None, cnf_integrator=integrator)
        if isinstance(result, dict):
            hp = result.get("health_impact") or {}
            for key in ("health_impact_minutes", "total_health_impact_minutes", "total_impact_minutes", "minutes"):
                v = hp.get(key) if isinstance(hp, dict) else None
                if v is not None and isinstance(v, (int, float)):
                    return float(v)
        return 0.0
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] HENI: {exc!r}")
        return None


def _route_to_fcs(aggregated: List[Dict[str, Any]]) -> Optional[float]:
    """Mass-weighted mean FCS across decomposed ingredients."""
    try:
        from fcs_calculator.fcs.service import extract_and_score

        scores: List[float] = []
        weights: List[float] = []
        for item in aggregated:
            _, result = extract_and_score([int(item["food_id"])], item.get("food_description") or "food")
            scores.append(float(result.get("fcs", 0.0)))
            weights.append(float(item["mass_g"]))
        if not weights or sum(weights) <= 0:
            return None
        return sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] FCS: {exc!r}")
        return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def _write_fixture_from_image(
    mm: Any,
    img_path: Path,
    fixture_id: str,
    *,
    net_weight_override_g: Optional[float] = None,
) -> bool:
    print(f"extracting {fixture_id} from {img_path.name}…")
    raw = img_path.read_bytes()
    ex = extract_packaged_food(raw, use_cache=False, client=mm)
    e = ex.extraction
    if not e.extraction_succeeded:
        print(f"  extraction failed: {e.failure_reason}")
        return False
    if not e.nf_panel or not e.ingredient_list or not e.ingredient_list.ingredients_parsed:
        print("  skip: missing nf_panel or parsed ingredients")
        return False
    nw = _resolve_net_weight(e.nf_panel)
    if nw is None and net_weight_override_g is None:
        print("  skip: no net_weight and no override")
        return False
    data = {
        "fixture_id": fixture_id,
        "source_image": img_path.name,
        "net_weight_override_g": net_weight_override_g,
        "nf_panel": e.nf_panel.model_dump(),
        "ingredient_list": e.ingredient_list.model_dump(),
        "extraction_metadata": e.extraction_metadata.model_dump() if e.extraction_metadata else {},
    }
    out = _save_fixture(data)
    print(f"  wrote {out.name} ({len(e.ingredient_list.ingredients_parsed)} ingredients, nw={nw})")
    return True


def cmd_fixtures(force: bool = False, image_dir: Optional[Path] = None, discover: bool = False) -> int:
    from api.services.multimodal_client import build_multimodal_client

    mm = build_multimodal_client()
    if mm is None:
        print("Multimodal client unavailable — check API keys.")
        return 1

    img_root = image_dir or IMG_DIR
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for spec in FIXTURE_SPECS:
        path = FIXTURE_DIR / f"{spec['fixture_id']}.json"
        if path.exists() and not force:
            print(f"skip {spec['fixture_id']} (exists; use --force)")
            continue
        img_path = img_root / spec["filename"]
        if not img_path.exists():
            print(f"skip {spec['fixture_id']}: {img_path.name} not found")
            continue
        if _write_fixture_from_image(
            mm, img_path, spec["fixture_id"],
            net_weight_override_g=spec.get("net_weight_override_g"),
        ):
            written += 1

    if discover and img_root.exists():
        known_names = {s["filename"] for s in FIXTURE_SPECS}
        for img_path in sorted(img_root.iterdir()):
            if not img_path.is_file():
                continue
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".webp", ".avif", ".png"}:
                continue
            if img_path.name in known_names:
                continue
            fid = "disc_" + img_path.stem.replace(" ", "_").replace("'", "")[:48]
            path = FIXTURE_DIR / f"{fid}.json"
            if path.exists() and not force:
                print(f"skip {fid} (exists; use --force)")
                continue
            if _write_fixture_from_image(mm, img_path, fid):
                written += 1

    print(f"\n{written} fixture(s) written to {FIXTURE_DIR}")
    return 0 if written else 1


def cmd_import_fixture(src: Path) -> int:
    data = json.loads(src.read_text(encoding="utf-8"))
    if "fixture_id" not in data:
        print("JSON must include fixture_id")
        return 1
    out = _save_fixture(data)
    print(f"Imported → {out}")
    return 0


def cmd_audit() -> int:
    fixtures = _load_fixtures()
    if not fixtures:
        print("No fixtures — run: python _experiment_pkg_decompose_retrieval_ab.py fixtures")
        return 1

    matcher = _warm_matcher()
    chat = build_chat_json_client()
    print(f"Matcher chat: {getattr(chat, 'provider', None)}/{getattr(chat, 'model', None)}\n")

    rows: List[Dict[str, Any]] = []
    for fix in fixtures:
        panel, ingredients = _fixture_to_models(fix)
        s1 = build_stage1_arm_a(ingredients, matcher)
        print(f"{fix['fixture_id']}: pool_sizes={s1.pool_sizes} median={statistics.median(s1.pool_sizes):.0f}")

        for ing in ingredients.ingredients_parsed:
            nq = _normalise_query(ing.name)
            pairs = matcher._retrieve(nq, k=5)  # noqa: SLF001
            embed_top5 = [int(matcher.corpus.food_ids[idx]) for idx, _ in pairs]
            mr = matcher.match(ing.name, top_k=5)
            llm_id = int(mr.food_id) if mr.food_id is not None else None
            rank = embed_top5.index(llm_id) + 1 if llm_id in embed_top5 else None
            rows.append({
                "fixture_id": fix["fixture_id"],
                "ingredient": ing.name,
                "position": ing.position,
                "embed_top1": embed_top5[0] if embed_top5 else None,
                "llm_rank_id": llm_id,
                "llm_in_embed_top5": llm_id in embed_top5 if llm_id else False,
                "rank_of_llm_in_embed": rank,
                "used_ai_ranking": mr.used_ai_ranking,
            })

    in_top5 = [r for r in rows if r["llm_in_embed_top5"]]
    top1_match = [r for r in rows if r["embed_top1"] == r["llm_rank_id"]]
    n = len(rows)
    print(f"\n--- stage-1 overlap ({n} ingredients across {len(fixtures)} fixtures) ---")
    print(f"LLM rank ∈ embed top-5: {len(in_top5)}/{n} ({100*len(in_top5)/n:.0f}%)")
    print(f"LLM rank == embed top-1: {len(top1_match)}/{n} ({100*len(top1_match)/n:.0f}%)")

    prod_panel, prod_ing = _fixture_to_models(fixtures[0])
    prod = decompose_packaged_food(
        prod_panel, prod_ing, matcher=matcher, chat_client=chat,
    )
    print(f"\nProduction decompose ({fixtures[0]['fixture_id']}): succeeded={prod.decomposition_succeeded} "
          f"n={len(prod.ingredients)} conf={prod.decomposition_confidence:.2f}")

    payload = {"audit_rows": rows, "summary": {
        "n_ingredients": n,
        "pct_llm_in_embed_top5": round(100 * len(in_top5) / n, 1) if n else 0,
        "pct_embed_top1_match": round(100 * len(top1_match) / n, 1) if n else 0,
        "fixture_pool_medians": {
            fix["fixture_id"]: statistics.median(
                build_stage1_arm_a(_fixture_to_models(fix)[1], matcher).pool_sizes
            )
            for fix in fixtures
        },
    }}
    _merge_results({"audit": payload})
    return 0


def cmd_stage1() -> int:
    fixtures = _load_fixtures()
    if not fixtures:
        print("No fixtures — run fixtures first.")
        return 1
    matcher = _warm_matcher()
    disagreements: List[Dict[str, Any]] = []
    for fix in fixtures:
        _, ingredients = _fixture_to_models(fix)
        for ing in ingredients.ingredients_parsed:
            nq = _normalise_query(ing.name)
            pairs = matcher._retrieve(nq, k=5)  # noqa: SLF001
            embed_top5 = [int(matcher.corpus.food_ids[idx]) for idx, _ in pairs]
            mr = matcher.match(ing.name, top_k=5)
            llm_id = int(mr.food_id) if mr.food_id is not None else None
            if llm_id != embed_top5[0]:
                disagreements.append({
                    "fixture_id": fix["fixture_id"],
                    "ingredient": ing.name,
                    "embed_top1": embed_top5[0],
                    "embed_top1_desc": matcher.corpus.food_descriptions[pairs[0][0]],
                    "llm_id": llm_id,
                    "llm_desc": mr.food_description,
                })
    print(f"Stage-1 disagreements (embed top-1 ≠ LLM rank): {len(disagreements)}")
    for d in disagreements[:15]:
        print(f"  [{d['fixture_id']}] {d['ingredient']!r}")
        print(f"    embed: {d['embed_top1']} {d['embed_top1_desc'][:60]}")
        print(f"    llm:   {d['llm_id']} {(d['llm_desc'] or '')[:60]}")
    _merge_results({"stage1": {"disagreements": disagreements, "count": len(disagreements)}})
    return 0


def cmd_ab(runs: int = 3, arms: Optional[List[ArmName]] = None) -> int:
    fixtures = _load_fixtures()
    if not fixtures:
        print("No fixtures — run fixtures first.")
        return 1
    arms = arms or ["A", "B", "C"]
    matcher = _warm_matcher()
    chat = build_chat_json_client()
    if chat is None:
        print("Chat client unavailable.")
        return 1

    # Warm throwaway
    panel0, ing0 = _fixture_to_models(fixtures[0])
    decompose_with_arm("A", panel0, ing0, matcher=matcher, chat_client=chat)

    all_runs: List[Dict[str, Any]] = []
    for fix in fixtures:
        panel, ingredients = _fixture_to_models(fix)
        print(f"\n=== {fix['fixture_id']} ({len(ingredients.ingredients_parsed)} ingredients) ===")
        for arm in arms:
            arm_times: List[float] = []
            arm_results: List[DecompositionResult] = []
            for run_i in range(runs):
                _clear_matcher_runtime_cache(matcher)
                dec, timing = decompose_with_arm(arm, panel, ingredients, matcher=matcher, chat_client=chat)
                arm_times.append(float(timing["total_ms"]))
                arm_results.append(dec)
                status = "ok" if dec.decomposition_succeeded else dec.failure_reason
                print(
                    f"  {arm} run {run_i+1}: {timing['total_ms']:.0f} ms "
                    f"(s1={timing['stage1_ms']:.0f} llm={timing['decompose_llm_ms']:.0f}) "
                    f"n={len(dec.ingredients)} conf={dec.decomposition_confidence:.2f} {status}"
                )
                all_runs.append({
                    "fixture_id": fix["fixture_id"],
                    "arm": arm,
                    "run": run_i,
                    "timing": timing,
                    "decomposition": dec.model_dump(),
                })
            med = statistics.median(arm_times)
            print(f"  {arm} median total: {med:.0f} ms")

    _merge_results({
        "ab_pool_fix_v2": {
            "runs": all_runs,
            "runs_per_arm": runs,
            "arms": arms,
            "note": "top-5 candidate pool fix (alternatives from matcher)",
        },
    })
    return 0


def _ab_runs_from_results(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "ab_pool_fix_v2" in data:
        return data["ab_pool_fix_v2"].get("runs", [])
    return data.get("ab", {}).get("runs", [])


def cmd_downstream() -> int:
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8")) if RESULTS_PATH.exists() else {}
    ab_runs = _ab_runs_from_results(data)
    if not ab_runs:
        print("No ab results — run ab first.")
        return 1

    # Median run per fixture×arm: pick run with median total_ms
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for row in ab_runs:
        key = (row["fixture_id"], row["arm"])
        grouped.setdefault(key, []).append(row)

    downstream: List[Dict[str, Any]] = []
    for (fixture_id, arm), rows in sorted(grouped.items()):
        rows_sorted = sorted(rows, key=lambda r: r["timing"]["total_ms"])
        mid = rows_sorted[len(rows_sorted) // 2]
        dec = DecompositionResult.model_validate(mid["decomposition"])
        if not dec.decomposition_succeeded:
            downstream.append({"fixture_id": fixture_id, "arm": arm, "skipped": True})
            continue
        agg = _aggregated_from_dec(dec)
        downstream.append({
            "fixture_id": fixture_id,
            "arm": arm,
            "hefi": _route_to_hefi(agg),
            "heni": _route_to_heni(agg),
            "fcs": _route_to_fcs(agg),
        })
        print(f"{fixture_id} arm {arm}: HEFI={downstream[-1]['hefi']} HENI={downstream[-1]['heni']} FCS={downstream[-1]['fcs']}")

    _merge_results({"downstream": downstream})
    return 0


def _merge_results(patch: Dict[str, Any]) -> None:
    data: Dict[str, Any] = {}
    if RESULTS_PATH.exists():
        data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    data.update(patch)
    RESULTS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\nResults → {RESULTS_PATH.name}")


def cmd_report() -> int:
    if not RESULTS_PATH.exists():
        print("No results file — run audit / ab first.")
        return 1
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    audit = data.get("audit", {}).get("summary", {})
    ab_runs = _ab_runs_from_results(data)
    downstream = data.get("downstream", [])

    print("=== PKG-DECOMP-LATENCY-AB-1 REPORT ===\n")

    if audit:
        print("Phase 0 / Stage-1 overlap:")
        print(f"  G2.1 LLM ∈ embed top-5: {audit.get('pct_llm_in_embed_top5')}%  (gate ≥95%)")
        print(f"  G2.2 LLM == embed top-1: {audit.get('pct_embed_top1_match')}%  (gate ≥85%)")
        print(f"  Pool size medians: {audit.get('fixture_pool_medians')}\n")

    if not ab_runs:
        print("No A/B runs in results.")
        return 1

    # Baseline medians for arm A
    baseline: Dict[str, DecompositionResult] = {}
    baseline_times: Dict[str, float] = {}
    for fix_id in {r["fixture_id"] for r in ab_runs}:
        a_rows = [r for r in ab_runs if r["fixture_id"] == fix_id and r["arm"] == "A"]
        if not a_rows:
            continue
        a_rows.sort(key=lambda r: r["timing"]["total_ms"])
        mid = a_rows[len(a_rows) // 2]
        baseline[fix_id] = DecompositionResult.model_validate(mid["decomposition"])
        baseline_times[fix_id] = float(mid["timing"]["total_ms"])

    gates: Dict[str, Any] = {"arms": {}}
    for arm in ("A", "B", "C"):
        arm_rows = [r for r in ab_runs if r["arm"] == arm]
        if not arm_rows:
            continue
        times = [float(r["timing"]["total_ms"]) for r in arm_rows]
        llm_ranks = sum(int(r["timing"].get("llm_rank_calls", 0)) for r in arm_rows)
        jaccards: List[float] = []
        pos_agree: List[float] = []
        success_a = success_b = 0
        for fix_id, base_dec in baseline.items():
            fix_arm = [r for r in arm_rows if r["fixture_id"] == fix_id]
            if not fix_arm:
                continue
            fix_arm.sort(key=lambda r: r["timing"]["total_ms"])
            mid = fix_arm[len(fix_arm) // 2]
            dec = DecompositionResult.model_validate(mid["decomposition"])
            if base_dec.decomposition_succeeded:
                success_a += 1
            if dec.decomposition_succeeded:
                success_b += 1
            if base_dec.decomposition_succeeded and dec.decomposition_succeeded:
                ids_a = _food_ids_by_position(base_dec)
                ids_b = _food_ids_by_position(dec)
                jaccards.append(_jaccard(set(ids_a.values()), set(ids_b.values())))
                common = set(ids_a) & set(ids_b)
                if common:
                    pos_agree.append(sum(1 for p in common if ids_a[p] == ids_b[p]) / len(common))

        med_time = statistics.median(times)
        med_a = statistics.median(baseline_times.values()) if baseline_times else 0
        speedup = (1 - med_time / med_a) if med_a and arm != "A" else 0.0
        gates["arms"][arm] = {
            "median_total_ms": round(med_time, 1),
            "speedup_vs_A": round(speedup, 3),
            "median_jaccard_vs_A": round(statistics.median(jaccards), 3) if jaccards else None,
            "median_position_agreement_vs_A": round(statistics.median(pos_agree), 3) if pos_agree else None,
            "llm_rank_calls_total": llm_ranks,
        }
        print(f"Arm {arm}:")
        print(f"  median total ms: {med_time:.0f}  speedup vs A: {speedup*100:.0f}%")
        if arm != "A" and jaccards:
            print(f"  Jaccard vs A: {statistics.median(jaccards):.2f}  position agree: {statistics.median(pos_agree):.2f}")

    # Downstream deltas vs A
    if downstream:
        print("\nDownstream vs Arm A (median run):")
        by_fix: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for row in downstream:
            by_fix.setdefault(row["fixture_id"], {})[row["arm"]] = row
        for fix_id, arms in by_fix.items():
            a = arms.get("A", {})
            if a.get("skipped"):
                continue
            for arm in ("B", "C"):
                b = arms.get(arm, {})
                if b.get("skipped") or not b:
                    continue
                hefi_d = abs((b.get("hefi") or 0) - (a.get("hefi") or 0))
                heni_d = abs((b.get("heni") or 0) - (a.get("heni") or 0))
                fcs_d = abs((b.get("fcs") or 0) - (a.get("fcs") or 0))
                print(f"  {fix_id} {arm}: ΔHEFI={hefi_d:.3f} ΔHENI={heni_d:.3f} ΔFCS={fcs_d:.3f}")

    # Recommendation
    print("\n--- RECOMMENDATION ---")
    b = gates["arms"].get("B", {})
    c = gates["arms"].get("C", {})
    g21 = audit.get("pct_llm_in_embed_top5", 0) >= 95 if audit else False
    g22 = audit.get("pct_embed_top1_match", 0) >= 85 if audit else False
    b_ok = (
        b.get("median_jaccard_vs_A", 0) >= 0.85
        and b.get("speedup_vs_A", 0) >= 0.5
        and g22
    )
    c_ok = c.get("median_jaccard_vs_A", 0) >= 0.85 and c.get("speedup_vs_A", 0) >= 0.4
    if b_ok:
        print("SHIP: Arm B (embedding top-1, skip per-ingredient Opus rank)")
    elif c_ok:
        print("SHIP: Arm C (embedding top-5 pool + single decompose LLM)")
    elif not g21:
        print("NO-GO: LLM rank often outside embed top-5 — keep ranking or fix corpus")
    else:
        print("INCONCLUSIVE: review disagreements + downstream deltas manually")

    _merge_results({"report": gates})
    return 0


def cmd_all(runs: int) -> int:
    rc = cmd_fixtures(force=False)
    if rc != 0 and not _load_fixtures():
        return rc
    cmd_audit()
    cmd_stage1()
    cmd_ab(runs=runs)
    cmd_downstream()
    return cmd_report()


def main() -> int:
    parser = argparse.ArgumentParser(description="PKG-DECOMP-LATENCY-AB-1 experiment")
    parser.add_argument("command", choices=[
        "fixtures", "import-fixture", "audit", "stage1", "ab", "downstream", "report", "all",
    ])
    parser.add_argument("--runs", type=int, default=3, help="Repetitions per fixture per arm (ab/all)")
    parser.add_argument("--force", action="store_true", help="Re-extract fixtures")
    parser.add_argument("--arms", default="A,B,C", help="Comma-separated arms for ab (default A,B,C)")
    parser.add_argument("--discover", action="store_true", help="Also extract every image in --image-dir")
    parser.add_argument("--image-dir", type=Path, default=None, help="Override packeged_foods_images path")
    parser.add_argument("--path", type=Path, default=None, help="JSON file for import-fixture")
    args = parser.parse_args()

    if args.command == "fixtures":
        return cmd_fixtures(force=args.force, image_dir=args.image_dir, discover=args.discover)
    if args.command == "import-fixture":
        if args.path is None:
            print("--path required for import-fixture")
            return 1
        return cmd_import_fixture(args.path)
    if args.command == "audit":
        return cmd_audit()
    if args.command == "stage1":
        return cmd_stage1()
    if args.command == "ab":
        arms = [a.strip().upper() for a in args.arms.split(",") if a.strip()]  # type: ignore[misc]
        return cmd_ab(runs=args.runs, arms=arms)  # type: ignore[arg-type]
    if args.command == "downstream":
        return cmd_downstream()
    if args.command == "report":
        return cmd_report()
    return cmd_all(runs=args.runs)


if __name__ == "__main__":
    raise SystemExit(main())
