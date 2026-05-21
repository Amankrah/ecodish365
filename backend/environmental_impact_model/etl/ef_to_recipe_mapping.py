"""Single source of truth for the EF 3.1 → ReCiPe 2016 H midpoint mapping.

This module is imported by both the offline ETL (`build_agribalyse_v32_catalog.py`)
and the runtime matcher (`lca_matcher.py`) so the partition stays symmetric
between catalogue construction and inference.

Policy decisions (locked in the AGRIBALYSE-INGEST plan, 2026-05-21):

* **Dual-namespace catalogue.** Each catalogue row carries BOTH
  `recipe2016_midpoints_per_100g` (populated only for the directly equivalent
  EF columns listed in `EF_TO_RECIPE_DIRECT`) AND the full
  `ef31_indicators_per_100g` dict (every EF column with native units).
* **Incompatible categories** (`EF_INCOMPATIBLE_WITH_RECIPE`) are NOT coerced
  into ReCiPe keys. They live in the EF dict only; ReCiPe-side queries for
  those categories fall back to the existing `cnf_integrator` group-default
  values. Manuscript §3.2: "treat any direct PEF-vs-ReCiPe comparison as a
  sensitivity analysis rather than a primary result."

The EF column names below are taken verbatim from row 2 of the `Synthese` tab
of `AGRIBALYSE3.2_Tableur produits alimentaires_PublieAOUT25.xlsx`
(sharedStrings entries [30]–[49]).
"""

from __future__ import annotations

from typing import Dict, FrozenSet


# EF 3.1 column header (row 2 of Synthese tab) → ReCiPe midpoint key.
#
# Only directly equivalent indicators (same physical quantity, same unit
# family, same model boundary) appear here. Cross-method coercions are
# explicitly NOT done — see EF_INCOMPATIBLE_WITH_RECIPE below.
EF_TO_RECIPE_DIRECT: Dict[str, str] = {
    # IPCC AR5 GWP100 — same across EF 3.1 and ReCiPe 2016 H climate change.
    "Changement climatique": "Global warming",
    # Three published climate sub-components from EF 3.1. ReCiPe does not have
    # a parallel three-way decomposition, so we expose them under parallel
    # `Global warming (...)` keys that the matcher can surface but the
    # existing `_calculate_midpoint_impacts` aggregation does not consume
    # (the latter only sums the standard ReCiPe 18 categories).
    "Changement climatique - émissions fossiles": "Global warming (fossil)",
    "Changement climatique - émissions biogéniques": "Global warming (biogenic)",
    "Changement climatique - émissions liées au changement d'affectation des sols": "Global warming (LUC)",
    # CFC-11 eq stratospheric ozone depletion — same indicator both methods.
    "Appauvrissement de la couche d'ozone": "Stratospheric ozone depletion",
}


# EF 3.1 columns that have NO clean ReCiPe equivalent. Reasons documented
# inline below. These columns are still surfaced via the matcher's
# `ef31_indicators_per_100g` payload; the ReCiPe side of the dual-namespace
# catalogue leaves these categories empty (cnf_integrator group-default
# fallback handles them at LCA time).
EF_INCOMPATIBLE_WITH_RECIPE: FrozenSet[str] = frozenset({
    # Different reference isotope: EF uses U-235 eq, ReCiPe uses Co-60 eq.
    "Rayonnements ionisants",
    # EF aggregates HH + Terrestrial; ReCiPe splits them into two midpoints.
    "Formation photochimique d'ozone",
    # EF: disease incidence/kg (DALY-precursor); ReCiPe: kg PM2.5 eq.
    "Particules fines",
    # EF: CTUh; ReCiPe: kg 1,4-DCB eq. Different effect-factor methods.
    "Effets toxicologiques sur la santé humaine : substances non-cancérogènes",
    "Effets toxicologiques sur la santé humaine : substances cancérogènes",
    # EF: mol H+ eq; ReCiPe: kg SO2 eq.
    "Acidification terrestre et eaux douces",
    # Both kg P eq, but EF's flow inventory differs from ReCiPe's; treat as
    # methodologically distinct until a defensible reconciliation exists.
    "Eutrophisation eaux douces",
    # Both kg N eq, but same caveat.
    "Eutrophisation marine",
    # EF dedicated category; ReCiPe rolls into terrestrial acidification.
    "Eutrophisation terrestre",
    # EF: CTUe, freshwater only; ReCiPe: kg 1,4-DCB eq across three
    # compartments (freshwater + terrestrial + marine).
    "Écotoxicité pour écosystèmes aquatiques d'eau douce",
    # EF: Pt/kg (LANCA aggregate score); ReCiPe: m2·a crop eq.
    "Utilisation du sol",
    # EF: m3 deprivation-eq (AWaRe); ReCiPe: m3 water-eq consumption.
    "Épuisement des ressources eau",
    # EF reports as a dedicated MJ midpoint; ReCiPe has no separate energy
    # indicator (fossil resource scarcity is the closest, but kg oil eq).
    "Épuisement des ressources énergétiques",
    # EF: kg Sb eq; ReCiPe: kg Cu eq. Different reference flows.
    "Épuisement des ressources minéraux",
})


# Single-score column — kept separately, not part of the 16-indicator EF
# disaggregated set. Lives in `ef31_indicators_per_100g` under its own key.
EF_SINGLE_SCORE_COLUMN: str = "Score unique EF 3.1"


def all_ef_columns() -> FrozenSet[str]:
    """Return the union of every EF column the ETL knows about (mapped +
    incompatible + single score). Used by the partition-exhaustiveness test."""
    return frozenset(EF_TO_RECIPE_DIRECT) | EF_INCOMPATIBLE_WITH_RECIPE | {EF_SINGLE_SCORE_COLUMN}


# The mapping table is intentionally tiny; bump this string whenever the
# table changes so consumers can record `mapping_version` in audit trails.
MAPPING_VERSION: str = "v1.0-2026-05-21"
