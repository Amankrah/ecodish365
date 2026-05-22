# Environmental impact model — data artefacts

**Runtime:** The Django API / LCA matcher load only the **`*.json`** (and embeddings where used) artefacts built from official sources. Offline **reference documents** below are for validation, manuscript provenance, and future ETL—**they are not imported by application code.**

## ReCiPe 2016 v1.1 factor packs (multi-country, perspective-aware)

| File | Description |
|------|-------------|
| `ReCiPe2016_CFs_v1.1_20180117.xlsx` | Source RIVM workbook — per-substance midpoint CFs for all 18 ReCiPe 2016 categories AND midpoint-to-endpoint conversion factors for all 26 endpoint pathways at all three cultural perspectives (Individualist / Hierarchist / Egalitarian). |
| `Normalization scores ReCiPe2016v1.1_20190514.xlsx` | World 2010 per-person-per-year normalisation scores at midpoint AND endpoint, all three perspectives. |
| `ReCiPe2016_country factors_v1.1_20171221.xlsx` | Country-specific CFs for the 5 spatially-explicit categories (Water consumption: 288 country rows; Terrestrial acidification: 224; Freshwater eutrophication: 159; Photochemical ozone formation: 70; Particulate matter formation: 66). |
| `recipe2016_endpoint_factors.json` | **Generated**: midpoint→endpoint CFs for I/H/E perspectives, 26 pathways each. |
| `recipe2016_normalization.json` | **Generated**: per-midpoint + per-endpoint + per-AoP World 2010 norm scores. |
| `recipe2016_country_factors.json` | **Generated**: per-country, per-category midpoint and endpoint CFs (246 ISO-3 codes covered after name normalisation). |
| `recipe2016_factor_packs_meta.json` | **Generated**: provenance, SHA-256s of source workbooks and output packs, ETL git rev, extraction timestamp. |
| `country_iso3_map.json` | **Generated**: workbook country string -> ISO 3166-1 alpha-3 code (embedded inline in the ETL script for reviewability). |

**Rebuild** the four generated files with:

```bash
python -m environmental_impact_model.etl.build_recipe2016_factor_packs
```

The runtime loader is `environmental_impact_model.src.methodology_factors.get_methodology_pack('recipe2016')`. It validates SHA-256 against meta on load and exposes country / perspective / endpoint-factor-source accessors to `LifeCycleAssessment`.

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
