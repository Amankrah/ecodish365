"""Generate Section 5 case-study figures from pinned S4/S5 artefacts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript_figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
    }
)


def fig_s4_pareto_scatter() -> None:
    df = pd.read_csv(ROOT / "results" / "S4" / "meals_panel.csv")
    frontier = json.loads((ROOT / "results" / "S4" / "pareto_frontier.json").read_text(encoding="utf-8"))
    frontier_ids = {d["day_id"] for d in frontier["frontier"]}

    plot = df.dropna(subset=["heni_minutes", "env_gw_per_100kcal"]).copy()
    plot["on_frontier"] = plot["day_id"].isin(frontier_ids)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    off = plot[~plot["on_frontier"]]
    on = plot[plot["on_frontier"]]
    ax.scatter(off["heni_minutes"], off["env_gw_per_100kcal"], alpha=0.55, s=35, c="#abd9e9", label="Other days")
    ax.scatter(on["heni_minutes"], on["env_gw_per_100kcal"], alpha=0.9, s=55, c="#d7191c", edgecolors="white", label="Pareto frontier (n = 6)")
    for _, row in on.iterrows():
        ax.annotate(row["day_id"], (row["heni_minutes"], row["env_gw_per_100kcal"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("HENI (minutes per day)")
    ax.set_ylabel("Global warming (kg CO₂-eq / 100 kcal)")
    ax.set_title("S4-NHANES panel: HENI–footprint trade-off (n = 94 evaluable days)")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "fig5_1_s4_pareto_scatter.png")
    plt.close(fig)


def fig_s5_overlay_exemplars() -> None:
    overlay = json.loads((ROOT / "results" / "S5-subst" / "s4_overlay.json").read_text(encoding="utf-8"))
    days = {d["day_id"]: d for d in overlay["days"] if d["day_id"] in ("D06", "D13")}
    labels = ["D06\nBBQ Western", "D13\nFast-food burger"]
    metrics = [("hefi", "HEFI (/80)"), ("heni_min", "HENI (min)")]
    x = np.arange(len(labels))
    w = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    for ax, (key, ylabel) in zip(axes, metrics):
        baseline = [days["D06"]["baseline"][key], days["D13"]["baseline"][key]]
        modified = [days["D06"]["modified"][key], days["D13"]["modified"][key]]
        ax.bar(x - w / 2, baseline, w, label="Before overlay", color="#fdae61")
        ax.bar(x + w / 2, modified, w, label="After S5 overlay", color="#1a9641")
        ax.set_xticks(x, labels, fontsize=8)
        ax.set_ylabel(ylabel)
    axes[0].set_title("S5 rule overlay on S4-lite Western days")
    axes[1].legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "fig5_2_s5_overlay_exemplars.png")
    plt.close(fig)


def main() -> None:
    fig_s4_pareto_scatter()
    fig_s5_overlay_exemplars()
    print(f"Wrote figures to {OUT}")


if __name__ == "__main__":
    main()
