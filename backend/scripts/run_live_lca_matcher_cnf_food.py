"""Live OpenAI-backed LCA matcher smoke: one CNF food, matcher OFF vs ON.

Loads backend/.env (via dish_project.env_bootstrap). Requires OPENAI_API_KEY.

Usage (from backend/):
    python scripts/run_live_lca_matcher_cnf_food.py [--food-id 7] [--quantity-g 150]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

if not os.environ.get("DJANGO_SECRET_KEY"):
    os.environ["DJANGO_SECRET_KEY"] = "live-lca-smoke-non-production-key"

import dish_project.env_bootstrap  # noqa: E402, F401

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402


def _formatted_section(payload: dict) -> dict:
    """Normalize `environmental_views.environmental_impact` response envelope.

    The view returns `{ "data": { "data": formatted_results, "meal_info", ... }, ... }`
    — i.e. formatted_results are nested **one level** under `data`.
    """

    outer = payload.get("data") or {}
    inner = outer.get("data")
    return inner if isinstance(inner, dict) else outer


def _summarize(payload: dict) -> tuple[dict | None, list | None, bool]:
    """Return (midpoints_summary, matcher_decisions, matcher_enabled_flag)."""

    fr = _formatted_section(payload)
    env = fr.get("environmental_impacts") or {}
    mids = env.get("all_impacts") or {}
    mids = {
        kk: vv
        for kk, vv in mids.items()
        if isinstance(kk, str) and not kk.startswith("_")
    }
    matcher_decisions = env.get("lca_matcher_decisions")
    matcher_flag = bool(env.get("lca_matcher_enabled"))

    summary_score = env.get("summary_score") or {}
    single = summary_score.get("value")
    endpoints = env.get("endpoint_impacts") or {}

    hh = endpoints.get("Human Health")
    ecosystems = endpoints.get("Ecosystems")

    summary = {
        "Global warming": mids.get("Global warming"),
        "Land use": mids.get("Land use"),
        "Water consumption": mids.get("Water consumption"),
        "single_score": single if isinstance(single, (int, float)) else None,
        "endpoint_Human Health": hh,
        "endpoint_Ecosystems": ecosystems,
    }
    # MatchResult.to_audit() keys are flattened on the API envelope.
    if isinstance(matcher_decisions, list):
        matcher_decisions = list(matcher_decisions)

    return summary, matcher_decisions, matcher_flag


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--food-id", type=int, default=7, help="CNF FoodID (default: 7 pot roast)")
    ap.add_argument("--quantity-g", type=float, default=150.0)
    args = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY not set. Add it to backend/.env "
            "(or export in the shell) and re-run.",
            file=sys.stderr,
        )
        return 1

    client = Client()
    foods = [{"food_id": args.food_id, "quantity": args.quantity_g}]

    def post(matcher_on: bool) -> tuple[dict | None, int]:
        resp = client.post(
            "/api/environmental-impact/",
            data=json.dumps({
                "foods": foods,
                "user_type": "researcher",
                "enable_lca_matcher": matcher_on,
            }),
            content_type="application/json",
            secure=True,
        )
        try:
            return resp.json(), resp.status_code
        except Exception:
            return None, resp.status_code

    # Food description from CNF (best-effort, for readable logs)
    from environmental_impact_model.src.cnf_integrator import get_cnf_integrator  # noqa: E402

    ci = get_cnf_integrator()
    ci.initialize("raw_cnf")
    fd = ci.get_food_data(args.food_id) or {}
    desc = ""
    fi = fd.get("food_info") or {}
    if isinstance(fi, dict):
        desc = str(fi.get("FoodDescription", "")).strip()
    label = desc[:72] + ("…" if len(desc) > 72 else "")
    print(f"CNF food_id={args.food_id}" + (f' — "{label}"' if label else "") + f", quantity={args.quantity_g} g")
    print("OPENAI_API_KEY: set from environment (not echoed)\n")

    for matcher_on in (False, True):
        label = "matcher ON " if matcher_on else "matcher OFF"
        payload, status = post(matcher_on)
        print("=" * 72)
        print(f"{label}  HTTP {status}")
        print("=" * 72)
        if payload is None or status != 200:
            print("Response error:", payload or "(no JSON)")
            continue
        summary, decisions, enabled = _summarize(payload)
        print("lca_matcher_enabled:", enabled)
        print("meal midpoints (v1 trimmed, meal functional unit):", summary)
        if matcher_on and isinstance(decisions, list):
            print(f"lca_matcher_decisions ({len(decisions)}):")
            for d in decisions:
                lci = str(d.get("lci_name") or "")
                short = lci[:70] + ("…" if len(lci) > 70 else "")
                line = (
                    f"  food_id={d.get('food_id')} matched={d.get('matched')} "
                    f"ciqual={d.get('ciqual_code')} confidence={d.get('confidence')} "
                    f"name={short!r}"
                )
                if not d.get("matched") and d.get("fallback_reason"):
                    line += f" fallback={d.get('fallback_reason')}"
                print(line)

    print("\nComparison: matcher OFF midpoint values vs matcher ON "
          "(difference shows Agribalyse overlay when matched).")
    off_p, status_off = post(False)
    on_p, status_on = post(True)
    if status_off != 200 or status_on != 200:
        print("Could not compare: HTTP", status_off, status_on)
        return 1 if (status_off != 200 or status_on != 200) else 0

    s_off, _, _ = _summarize(off_p or {})
    s_on, decisions_on, _ = _summarize(on_p or {})
    matched_n = (
        sum(1 for x in decisions_on if x.get("matched"))
        if isinstance(decisions_on, list)
        else 0
    )
    print(f"matched_foods ({matched_n} / {len(decisions_on) if decisions_on else 0}):")
    for k in ("Global warming", "Land use", "Water consumption", "single_score"):
        a, b = s_off.get(k), s_on.get(k)
        pct = ""
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a) > 1e-15:
            pct = f"  ({((b - a) / abs(a)) * 100:+.2f}% rel.)"
        print(f"  {k}: OFF={a!r}  ON={b!r}{pct}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
