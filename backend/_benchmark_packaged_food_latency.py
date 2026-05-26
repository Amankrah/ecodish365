"""Benchmark packaged-food extraction + decomposition latency (live API).

Usage (from backend/):
  python _benchmark_packaged_food_latency.py
  python _benchmark_packaged_food_latency.py --runs 3

Requires OPENAI_API_KEY + ANTHROPIC_API_KEY when LLM_PROVIDER=anthropic.
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")

for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import django

django.setup()

from api.services.ingredient_to_cnf_decomposer import decompose_packaged_food
from api.services.multimodal_client import build_multimodal_client
from api.services.packaged_food_extractor import extract_packaged_food
from environmental_impact_model.src.llm_client import build_chat_json_client

IMAGES = [
    ("soup", Path("packeged_foods_images/image-asset.webp")),
    ("campbells", Path("packeged_foods_images/cambell's_nf.jpg")),
]


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1))))
    return s[idx]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=2, help="Timed runs per image (cache off)")
    args = parser.parse_args()

    mm = build_multimodal_client()
    chat = build_chat_json_client()
    if mm is None or chat is None:
        print("Missing multimodal or chat client (check API keys + LLM_PROVIDER)")
        return 1

    print(f"Provider: multimodal={mm.provider}/{mm.model}  chat={chat.provider}/{chat.model}")
    print(f"Runs per image: {args.runs} (use_cache=False)\n")

    rows: list[dict] = []

    for label, path in IMAGES:
        if not path.exists():
            print(f"Skip {label}: {path} not found")
            continue
        raw = path.read_bytes()
        extract_ms: list[float] = []
        decompose_ms: list[float] = []
        total_ms: list[float] = []

        for run in range(args.runs):
            t0 = time.perf_counter()
            ex = extract_packaged_food(raw, use_cache=False, client=mm)
            t1 = time.perf_counter()
            extract_ms.append((t1 - t0) * 1000)

            if not ex.extraction.extraction_succeeded:
                print(f"{label} run {run + 1}: extraction failed — {ex.extraction.failure_reason}")
                continue
            panel = ex.extraction.nf_panel
            ing = ex.extraction.ingredient_list
            if not panel or not ing or not ing.ingredients_parsed:
                print(f"{label} run {run + 1}: no panel or ingredients for decompose")
                total_ms.append(extract_ms[-1])
                continue

            dec = decompose_packaged_food(panel, ing, chat_client=chat)
            t2 = time.perf_counter()
            decompose_ms.append((t2 - t1) * 1000)
            total_ms.append((t2 - t0) * 1000)

            ok = dec.decomposition_succeeded
            n_ing = len(dec.ingredients) if ok else 0
            reason = "" if ok else f" fail={dec.failure_reason}"
            print(
                f"{label} run {run + 1}: extract {extract_ms[-1]:.0f} ms | "
                f"decompose {decompose_ms[-1]:.0f} ms | total {total_ms[-1]:.0f} ms | "
                f"ingredients={n_ing} conf={dec.decomposition_confidence:.2f}{reason}"
            )

        if extract_ms:
            rows.append({
                "label": label,
                "extract_median_ms": statistics.median(extract_ms),
                "decompose_median_ms": statistics.median(decompose_ms) if decompose_ms else None,
                "total_median_ms": statistics.median(total_ms) if total_ms else None,
                "total_p95_ms": _pct(total_ms, 95) if total_ms else None,
            })

    if rows:
        print("\n--- summary (median ms) ---")
        for r in rows:
            dec = f"{r['decompose_median_ms']:.0f}" if r["decompose_median_ms"] is not None else "n/a"
            tot = f"{r['total_median_ms']:.0f}" if r["total_median_ms"] is not None else "n/a"
            print(
                f"{r['label']:12} extract={r['extract_median_ms']:.0f}  "
                f"decompose={dec}  total={tot}  p95_total={r['total_p95_ms']:.0f}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
