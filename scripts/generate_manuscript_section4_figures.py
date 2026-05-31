"""Generate Section 4 validation figures from pinned benchmark artefacts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

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


def fig_s4_spearman_heatmap() -> None:
    df = pd.read_csv(ROOT / "results" / "S4" / "spearman_matrix.csv")
    labels = ["HEFI", "HENI", "HSR", "FCS", "GW"]
    mat = np.eye(5)
    pairs = list(zip(df["pair_a"], df["pair_b"], df["rho"]))
    idx = {l: i for i, l in enumerate(labels)}
    for a, b, rho in pairs:
        i, j = idx[a], idx[b]
        mat[i, j] = mat[j, i] = rho

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(5), labels, rotation=45, ha="right")
    ax.set_yticks(range(5), labels)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", color="black", fontsize=8)
    ax.set_title("S4-NHANES medoid panel (n = 91 complete days): Spearman rho")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Spearman rho")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_1_s4_spearman_heatmap.png")
    plt.close(fig)


def fig_s4lite_spearman_heatmap() -> None:
    df = pd.read_csv(ROOT / "results" / "S4-lite" / "meals_panel.csv")
    cols = ["hefi_score", "heni_minutes", "hsr_stars", "fcs_score", "env_gw_per_100kcal"]
    labels = ["HEFI", "HENI", "HSR", "FCS", "GW"]
    n = len(labels)
    data = np.eye(n)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            data[i, j] = stats.spearmanr(df[cols[i]], df[cols[j]]).statistic

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(data, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center", color="black", fontsize=8)
    ax.set_title("S4-lite day panel (n = 25): Spearman rank correlations")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Spearman rho")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_9_s4lite_spearman_heatmap.png")
    plt.close(fig)


def fig_matcher_ece() -> None:
    runs = [
        ("gpt-4o-mini\n(pre-upgrade)", 0.215, 0.297),
        ("gpt-4.1-mini\n(post-upgrade)", 0.143, 0.216),
        ("gpt-4.1-mini\n(Hyp B)", 0.125, 0.213),
        ("gpt-4.1-mini\n(latest, n=200)", 0.098, 0.199),
    ]
    names = [r[0] for r in runs]
    ece = [r[1] for r in runs]
    brier = [r[2] for r in runs]

    x = np.arange(len(names))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - w / 2, ece, w, label="ECE", color="#2c7bb6")
    ax.bar(x + w / 2, brier, w, label="Brier score", color="#abd9e9")
    ax.set_xticks(x, names)
    ax.set_ylabel("Calibration error (lower is better)")
    ax.set_title("Matcher verbalised-confidence calibration (Table 4.4a)")
    ax.legend()
    ax.set_ylim(0, 0.35)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_2_matcher_calibration_ece_brier.png")
    plt.close(fig)


def fig_matcher_verdict_distribution() -> None:
    path = ROOT / "backend" / "environmental_impact_model" / "data" / "matcher_benchmark_6e2a999_20260528T165427Z.json"
    summary = json.loads(path.read_text(encoding="utf-8"))["summary"]["overall"]
    labels = ["Clean", "Borderline", "Flagged"]
    counts = [summary["clean"], summary["borderline"], summary["flagged"]]
    colors = ["#1a9641", "#fdae61", "#d7191c"]

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, counts, color=colors)
    ax.set_ylabel("Foods (n = 200)")
    ax.set_title("Matcher automated verdicts (gpt-4.1-mini, latest run)")
    for i, v in enumerate(counts):
        ax.text(i, v + 2, f"{v} ({100*v/sum(counts):.0f}%)", ha="center")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_3_matcher_verdict_distribution.png")
    plt.close(fig)


def fig_decomposition_fidelity() -> None:
    stages = [
        "Before fix\n(raw decompose)",
        "Prompt only\n(force decompose)",
        "Full pipeline\n(catalog preference)",
    ]
    pass_rates = [16, 20.8, 99.2]
    flagged = [55, 50.8, 0]

    x = np.arange(len(stages))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - w / 2, pass_rates, w, label="Pass rate (%)", color="#1a9641")
    ax.bar(x + w / 2, flagged, w, label="Flagged (%)", color="#d7191c")
    ax.set_xticks(x, stages)
    ax.set_ylabel("Percent of 240 composite foods")
    ax.set_title("Recipe decomposition nutrient fidelity (Table 4.7)")
    ax.legend()
    ax.set_ylim(0, 110)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_4_decomposition_fidelity.png")
    plt.close(fig)


def fig_sobol_top_contributors() -> None:
    path = ROOT / "backend" / "_smoke_lca_sobol_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    top = payload["by_category"]["Global warming"]["top_contributors"][:8]
    labels = [f"Food {t['food_id']}" for t in top]
    st = [t["ST"] for t in top]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(labels[::-1], st[::-1], color="#4575b4")
    ax.set_xlabel("Total-order Sobol index (ST)")
    ax.set_title("Global warming variance drivers on representative S4 day")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_5_sobol_global_warming.png")
    plt.close(fig)


def fig_bland_altman_heni_hefi() -> None:
    df = pd.read_csv(ROOT / "results" / "S4-lite" / "meals_panel.csv")
    n = len(df)

    def pct_rank(x: np.ndarray) -> np.ndarray:
        r = stats.rankdata(x, method="average")
        return (r - 1) / (n - 1) * 100

    hefi = pct_rank(df["hefi_score"].values)
    heni = pct_rank(df["heni_minutes"].values)
    mean = (hefi + heni) / 2
    diff = heni - hefi
    bias = np.mean(diff)
    loa = 1.96 * np.std(diff, ddof=1)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.scatter(mean, diff, alpha=0.75, edgecolors="white", linewidth=0.5)
    ax.axhline(bias, color="#d7191c", linestyle="-", linewidth=1, label=f"Bias = {bias:.1f} pp")
    ax.axhline(bias + loa, color="#4575b4", linestyle="--", label=f"+LoA = {bias + loa:.1f}")
    ax.axhline(bias - loa, color="#4575b4", linestyle="--", label=f"-LoA = {bias - loa:.1f}")
    ax.set_xlabel("Mean percentile rank (HENI, HEFI)")
    ax.set_ylabel("Difference (HENI minus HEFI, percentile points)")
    ax.set_title("Bland-Altman agreement on S4-lite panel (n = 25)")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_6_bland_altman_heni_hefi.png")
    plt.close(fig)


def fig_s4_pca_biplot() -> None:
    path = ROOT / "results" / "S4" / "pca_biplot.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    loadings = payload["loadings"]
    indicators = payload["indicators"]
    pc1 = [loadings["PC1"][k] for k in indicators]
    pc2 = [loadings["PC2"][k] for k in indicators]
    var = payload["variance_explained_ratio"]

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.axhline(0, color="grey", linewidth=0.5)
    ax.axvline(0, color="grey", linewidth=0.5)
    for i, label in enumerate(indicators):
        ax.arrow(0, 0, pc1[i], pc2[i], head_width=0.03, head_length=0.02, fc="#d7191c", ec="#d7191c")
        ax.text(pc1[i] * 1.08, pc2[i] * 1.08, label, fontsize=10)
    ax.set_xlabel(f"PC1 ({var[0]*100:.1f} % variance)")
    ax.set_ylabel(f"PC2 ({var[1]*100:.1f} % variance)")
    ax.set_title("PCA loadings on S4-NHANES panel (n = 91)")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_7_s4_pca_biplot.png")
    plt.close(fig)


def fig_s5_swap_deltas() -> None:
    path = ROOT / "results" / "S5-subst" / "s5_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload["cases"]
    labels = [c["label"].replace(" → ", "\n→ ") for c in cases]
    hefi = [c["delta"]["hefi"] for c in cases]
    heni = [c["delta"]["heni_min"] for c in cases]

    x = np.arange(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - w / 2, hefi, w, label="ΔHEFI (pts)", color="#2c7bb6")
    ax.bar(x + w / 2, heni, w, label="ΔHENI (min)", color="#fdae61")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylabel("Change after swap (positive HENI = loss)")
    ax.set_title("Canonical S5 single-ingredient swaps (Table 4.8a)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_8_s5_swap_deltas.png")
    plt.close(fig)


def fig_monte_carlo_envelope() -> None:
    path = ROOT / "backend" / "_smoke_lca_monte_carlo_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    cats = payload["by_category"]
    labels = [c["category"].replace(" ", "\n") for c in cats]
    central = [c["central"] for c in cats]
    p5 = [c["mc_p5"] for c in cats]
    p95 = [c["mc_p95"] for c in cats]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.errorbar(x, central, yerr=[np.array(central) - np.array(p5), np.array(p95) - np.array(central)],
                fmt="o", color="#4575b4", capsize=6, label="MC p5–p95")
    ax.scatter(x, central, s=60, c="#d7191c", zorder=3, label="Central estimate")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Meal-level impact (per S4-038 day)")
    ax.set_title("Monte Carlo uncertainty bands (N = 1 000, seed 42)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_10_monte_carlo_envelope.png")
    plt.close(fig)


def main() -> None:
    fig_s4_spearman_heatmap()
    fig_s4lite_spearman_heatmap()
    fig_monte_carlo_envelope()
    fig_matcher_ece()
    fig_matcher_verdict_distribution()
    fig_decomposition_fidelity()
    fig_sobol_top_contributors()
    fig_bland_altman_heni_hefi()
    fig_s4_pca_biplot()
    fig_s5_swap_deltas()
    print(f"Wrote figures to {OUT}")


if __name__ == "__main__":
    main()
