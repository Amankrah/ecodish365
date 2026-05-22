# Environmental impact model — data artefacts

**Runtime:** The Django API / LCA matcher load only the **`*.json`** (and embeddings where used) artefacts built from official sources. Offline **reference documents** below are for validation, manuscript provenance, and future ETL—**they are not imported by application code.**

## Offline reference literature (pinned copies)

| File | Description |
|------|-------------|
| `s11367-019-01653-3.pdf` | Open-access article PDF: Dekker et al., *Int J Life Cycle Assess* **25**, 2315–2324 (2020); [doi:10.1007/s11367-019-01653-3](https://doi.org/10.1007/s11367-019-01653-3). |
| `11367_2019_1653_MOESM1_ESM.docx` | Publisher **electronic supplementary material (ESM 1)** for the same article (Springer Nature MOESM1); GloboDiet grouping table and midpoint/endpoint supporting figures/data referenced in the paper. |

Licence for the Springer article/supplement follows the publisher’s OA terms (article: CC BY 4.0 as stated on the publisher page).

## Curated Dekker classification (structured)

| File | Description |
|------|-------------|
| `dekker_2020_ijlca_esm_table_s1_globodiet_mapping.json` | Machine-readable **`ESM Table S1`**: Dekker's nine aggregated categories, GloboDiet source groups where applicable, and the **152** product labels. See `note` in JSON: numeric midpoint/endpoint results are **only** in ESM figures S2–S13, not tabulated per food in Table S1. |

## Generated / curated JSON (summary)

| File | Role |
|------|------|
| `agribalyse_bootstrap.json` | Small hand-curated bootstrap set for matcher development (see repo `code_action_items.md`). |
| `agribalyse_v32_catalog.json` | Full catalog extracted from pinned ADEME workbook (generated; large). |
| `agribalyse_v32_catalog_meta.json` | Provenance checksums and counts for the catalog build. |
| `agribalyse_v32_embeddings.npy` | Optional embedding artefact used by offline tooling. |

Rebuild catalogue from ADEME workbooks with `environmental_impact_model/etl/build_agribalyse_v32_catalog.py`.
