# Literature Extraction Notes — Call 1 Manuscript

Companion to `literature_wishlist.md` and `manuscript_call1.md`. Entries are organized by the wishlist's lettered groups (A–J) and use the same numbering. Each entry contains: full Vancouver-style citation, page-cited results and formulas, reproducible tables, author-flagged limitations, and a 3-sentence relevance note.

---

## Group A. LCA Methodology

### A1. Huijbregts et al. (2017) — ReCiPe2016 overview [★★★]

**Citation.** Huijbregts MAJ, Steinmann ZJN, Elshout PMF, Stam G, Verones F, Vieira M, Zijp M, Hollander A, van Zelm R. ReCiPe2016: a harmonised life cycle impact assessment method at midpoint and endpoint level. Int J Life Cycle Assess. 2017;22(2):138–147.

**DOI.** 10.1007/s11367-016-1246-y

**Type.** Commentary and Discussion Article (overview paper; the full characterisation factor tables sit in RIVM Report 2016-0104, which is wishlist entry A2).

---

#### Page-cited results and formulas

**Areas of protection (p. 139, §2.1).** Three are defined:
1. Human Health, unit DALYs (disability-adjusted life years).
2. Ecosystem Quality, unit species·yr, aggregated from terrestrial (PDF·m²·yr) and freshwater/marine (PDF·m³·yr) using species densities per Goedkoop et al. 2009.
3. Resource Scarcity, unit USD ($), representing extra future extraction cost.

**Endpoint–midpoint coupling, Eq. (1), p. 139.**
$$\mathrm{CF_{e,x,a}} = \mathrm{CF_{m,x}} \cdot F_{M\to E,a}$$
where `a` = area of protection, `x` = stressor, and `F_{M→E,a}` is the constant midpoint-to-endpoint conversion factor for that area of protection. The authors emphasise the factor is constant per impact category because "environmental mechanisms are considered to be identical for each stressor after the midpoint impact location on the cause-effect pathway" (p. 139).

**Exception:** the mid-to-endpoint factor is NOT constant for fossil resource scarcity (dashed line in Fig. 1, p. 140; restated p. 144 and §3.2.12, p. 144).

**Three-scenario design (p. 140, §2.3) — the I / H / E perspectives.** ReCiPe2016 provides three sets of factors:
| Perspective | Time horizon | Level of evidence | Notes |
|---|---|---|---|
| Individualist (I) | 20 years | Very high evidence only | Short-horizon optimist. |
| Hierarchist (H) | 100 years | Accepted by international bodies (e.g. WHO) | Middle ground, default recommended choice. |
| Egalitarian (E) | 1000 years to infinite | All reported effects | Precautionary; horizon may be < ∞ where models cannot reach steady state. |

Scenario analysis is NOT applied to photochemical ozone formation, terrestrial acidification, freshwater eutrophication, land use, or fossil resource scarcity due to lack of value-choice data in the underlying models (p. 144, §4.1).

---

#### Tables to reproduce or reference in the manuscript

**Table 1 (p. 141) — the 17 midpoint impact categories.** Reproduce this in §3.2 of the draft (the section that introduces our ReCiPe implementation):

| # | Impact category | Midpoint indicator | CFm unit | Key reference |
|---|---|---|---|---|
| 1 | Climate change | Global Warming Potential (GWP) | kg CO₂-eq to air | IPCC 2013; Joos et al. 2013 |
| 2 | Stratospheric ozone depletion | Ozone Depletion Potential (ODP) | kg CFC-11-eq to air | WMO 2011 |
| 3 | Ionising radiation | Ionising Radiation Potential (IRP) | kBq Co-60-eq to air | Frischknecht et al. 2000 |
| 4 | Fine particulate matter formation | Particulate Matter Formation Potential (PMFP) | kg PM2.5-eq to air | Van Zelm et al. 2016 |
| 5 | Photochemical oxidant formation, ecosystems | EOFP | kg NOx-eq to air | Van Zelm et al. 2016 |
| 6 | Photochemical oxidant formation, human health | HOFP | kg NOx-eq to air | Van Zelm et al. 2016 |
| 7 | Terrestrial acidification | Terrestrial Acidification Potential (TAP) | kg SO₂-eq to air | Roy et al. 2014 |
| 8 | Freshwater eutrophication | Freshwater Eutrophication Potential (FEP) | kg P-eq to freshwater | Helmes et al. 2012 |
| 9 | Human toxicity, cancer | HTPc | kg 1,4-DCB-eq to urban air | Van Zelm et al. 2009 |
| 10 | Human toxicity, non-cancer | HTPnc | kg 1,4-DCB-eq to urban air | Van Zelm et al. 2009 |
| 11 | Terrestrial ecotoxicity | TETP | kg 1,4-DCB-eq to industrial soil | Van Zelm et al. 2009 |
| 12 | Freshwater ecotoxicity | FETP | kg 1,4-DCB-eq to freshwater | Van Zelm et al. 2009 |
| 13 | Marine ecotoxicity | METP | kg 1,4-DCB-eq to marine water | Van Zelm et al. 2009 |
| 14 | Land use | Agricultural Land Occupation Potential (LOP) | m²·yr annual cropland-eq | De Baan et al. 2013; Curran et al. 2014 |
| 15 | Water use | Water Consumption Potential (WCP) | m³ water-eq consumed | Döll & Siebert 2002; Hoekstra & Mekonnen 2012 |
| 16 | Mineral resource scarcity | Surplus Ore Potential (SOP) | kg Cu-eq | Vieira et al. 2016a |
| 17 | Fossil resource scarcity | Fossil Fuel Potential (FFP) | kg oil-eq | Jungbluth & Frischknecht 2010 |

**Table 2 (p. 143) — damage pathways for mid-to-endpoint conversion.** Pathways added or refined in ReCiPe2016 (beyond ReCiPe2008):
- Water use → human health (malnutrition via water shortage, Pfister et al. 2009).
- Water use → terrestrial ecosystems (NPP proxy, Pfister et al. 2009).
- Water use → freshwater ecosystems (fish species loss from discharge decline, Hanafiah et al. 2011).
- Climate change → freshwater ecosystems (Hanafiah et al. 2011).
- Tropospheric ozone → terrestrial ecosystems (plant species loss, Van Goethem et al. 2013a,b).

Full pathway-by-pathway descriptions for each of the 17 categories are in §3.2.1 through §3.2.12 (pp. 142–144).

**Numerical characterisation factors** are NOT in the paper itself; they live in the Electronic Supplementary Material spreadsheet and in RIVM Report 2016-0104. Fetch A2 (RIVM 2018) for the actual numbers.

---

#### Methodological choices worth flagging in §3.2 of our draft

1. **USES-LCA 2.0 chosen over USEtox for toxicity (p. 142, §3.1.8).** Two reasons: USEtox lacks terrestrial and marine ecotoxicity factors; USEtox does not easily support time-horizon-dependent characterisation factors. We should cite this if anyone challenges our toxicity numbers.
2. **Ecotoxicological damage factors set to unity (p. 144, §3.2.8).** Justified via Posthuma & De Zwart 2006: acute toxicity data approximate field-condition toxic effects. This is a known sensitivity point.
3. **Country- and continental-scale CFs available for 5 categories (Abstract, p. 138; restated p. 145, §4.2):** fine PM formation, photochemical ozone formation, terrestrial acidification, freshwater eutrophication, and water use. Useful for our Canadian-context layer (wishlist group I).
4. **Phosphorus to agricultural soils:** the paper assumes 10% of all P is transported from agricultural soil to surface water (p. 142, §3.1.7, citing Bouwman et al. 2009). Relevant if we have agricultural inputs in our LCI.

---

#### Author-flagged limitations (for engagement in §7 of our draft)

From §4, pp. 144–145:

1. **§4.1, p. 144 — Scenario analysis gaps.** Time horizon and level of evidence are NOT differentiated for five categories: photochemical ozone formation, terrestrial acidification, freshwater eutrophication, land use, fossil resource scarcity. Authors call for improvement "if more information on value choices becomes available."
2. **§4.2, p. 145 — Regionalisation is incomplete.** Land use (Chaudhary et al. 2015) and toxicity (Kounina et al. 2014; metal ecotoxicity speciation per Dong et al. 2016) are the most prominent gaps. Most other categories have no spatial differentiation in ReCiPe2016.
3. **§4.3, p. 145 — Local vs. global species extinction.** Damage to ecosystem quality is local species loss aggregated over space and time, not global extinction. Verones et al. 2015 and Chaudhary et al. 2015 offer paths to add global decline, currently only for water use and land use.
4. **§4.4, p. 145 — Missing exposure and damage pathways.**
   - Indoor emissions exposure for chemicals and fine PM (Rosenbaum et al. 2015; Hodas et al. 2016).
   - Direct pesticide application to food items (Fantke & Jolliet 2015).
   - Infectious disease incidence changes from climate change (Fan et al. 2015).
   - Mid-to-endpoint factor for fossil resource scarcity is incomplete.
   - Marine impact pathways: marine eutrophication, invasive species, plastic debris (Woods et al. 2016).
   - Noise as a human health impact (Cucurachi & Heijungs 2014).
   - Nanoparticle impacts (Pini et al. 2016).

These limitations are directly usable in our §7 (discussion / methodological limits) to frame why we run scenarios, why we layer Canadian regional factors on top of global CFs, and why uncertainty quantification (wishlist group F) matters.

---

#### Three-sentence relevance note

This is the foundational citation for every ReCiPe-derived number in the manuscript and supplies the constant mid-to-endpoint factor formulation in Eq. (1), p. 139, that our pipeline encodes literally. The 17-category midpoint table (Table 1, p. 141) and the I/H/E scenario design (p. 140) are what our §3.2 implements, and these need to be cited at the page level rather than as a blanket reference. Numerical factor values are NOT in this paper; for those we still need wishlist entry A2 (RIVM Report 2016-0104), and for the 2017 update plus 2024 normalization revision we need to reconcile what ReCiPe2016 says here against the RIVM update document.

---

### A2. RIVM Report 2016-0104a (October 2017) — ReCiPe 2016 v1.1, Report I: Characterization [★★★]

**Citation.** Huijbregts MAJ, Steinmann ZJN, Elshout PMF, Stam G, Verones F, Vieira MDM, Hollander A, Zijp M, van Zelm R. ReCiPe 2016 v1.1. A harmonized life cycle impact assessment method at midpoint and endpoint level. Report I: Characterization. Bilthoven: RIVM (National Institute for Public Health and the Environment); 2017. RIVM Report 2016-0104a.

**URL.** https://www.rivm.nl/sites/default/files/2018-11/Report%20ReCiPe_Update_20171002_0.pdf (201 pp.; revision dated 2 October 2017)

**Scope.** This is the full technical companion to the IJLCA commentary (A1). It contains the numerical characterisation-factor tables, the cultural-perspective operationalisation per category, and the October 2017 v1.1 erratum. The 2024 normalisation revision is NOT in this document. We still need a later RIVM artefact for that.

---

#### Page-cited results and formulas

**Areas of protection, Table 1.2, p. 19.** Reaffirms three endpoints:
| Area of protection | Endpoint name | Abbr. | Unit |
|---|---|---|---|
| Human health | Damage to human health | HH | year (DALY) |
| Natural environment | Damage to ecosystem quality | ED | species·yr |
| Resource scarcity | Damage to resource availability | RA | Dollar ($) |

**Endpoint formulation, §1.5, p. 24.**
$$\mathrm{CF}_{e,c,a,x} = \mathrm{CF}_{m,c,x} \cdot F_{M\to E,c,a,x}$$
Same constant-mid-to-endpoint structure as A1, but now indexed by cultural perspective `c` as well. Fossil resource scarcity remains the sole exception (no constant factor; see Ch. 14 and footnote 3 to Table 1.5).

**Cultural-perspective operationalisation, Table 1.3, pp. 20–22.** Reproduce this in §3.2 when introducing scenarios. Selected rows directly relevant to a food-LCA implementation:

| Choice | Individualist | Hierarchist | Egalitarian |
|---|---|---|---|
| **Climate change** time horizon | 20 yr | 100 yr | 1,000 yr |
| Climate-carbon feedbacks (non-CO₂) | No | Yes | No (data limitation, see footnote 1, p. 28) |
| **Ozone depletion** time horizon / effects | 20 yr / skin cancer | 100 yr / skin cancer | infinite / skin cancer + cataract |
| **Ionising radiation** time horizon / DDREF | 20 yr / 10 | 100 yr / 6 | 100,000 yr / 2 |
| **Fine PM** secondary aerosols included | Primary only | Primary + secondary from SO₂, NH₃, NOx | Primary + secondary from SO₂, NH₃, NOx |
| **Toxicity** time horizon | 20 yr | 100 yr | infinite |
| Carcinogenicity scope | IARC 1, 2A, 2B only | All with reported effects | All with reported effects |
| Min. tested species (ecotox) | 4 | 1 | 1 |
| **Water use** food production requirement | 1000 m³·yr⁻¹·capita⁻¹ | 1350 m³·yr⁻¹·capita⁻¹ | 1350 m³·yr⁻¹·capita⁻¹ |
| Terrestrial impacts considered | No | Yes | Yes |
| **Mineral scarcity** future production | Reserves | Ultimate recoverable resource | Ultimate recoverable resource |

Note (p. 20): value choices were NOT operationalised for photochemical ozone formation, terrestrial acidification, freshwater eutrophication, land use, or fossil resource scarcity. Same gap A1 flagged.

---

#### The October 2017 erratum (p. 7) — what changed from original ReCiPe2016 to v1.1

Reproduce verbatim in §3.2:

| # | Category | Change |
|---|---|---|
| 5 | Fine particulate matter formation | Hierarchist perspective now includes all secondary pollutants. |
| 8 | Freshwater eutrophication | Country- and world-aggregated factors recalculated using updated population data (year 2015). |
| 9 | Marine eutrophication | Added as an impact category now that an endpoint method is available. |
| 10 | Toxicity | Effects on urban soil excluded. Non-carcinogenic toxicity factors updated due to a mistake found in the USES-LCA model. |
| 15 | Sum emissions | Sum emissions for terrestrial and human non-carcinogenic toxicity adapted. |

This delta is what distinguishes "ReCiPe2016 v1.1" (October 2017) from the original "ReCiPe2016" of 2016. If §3.2 says "ReCiPe2016 v1.1", these are the changes we are inheriting.

---

#### Per-category update log, Table 1.1, pp. 16–18 (vs. ReCiPe2008)

Compact summary, in the order the wishlist's group A papers will need cross-referencing:

- **Climate change.** Egalitarian time horizon explicitly set to 1,000 yr (longest horizon in Joos et al. 2013). 207 GHGs from IPCC AR5. Damage factors for HH and terrestrial ecosystems updated. Damage to freshwater (river) ecosystems added.
- **Stratospheric ozone depletion.** New semi-empirical ODPs with detailed CFC speciation. Preliminary ODP for N₂O added. Three consistent time horizons (20 / 100 / infinite).
- **Ionising radiation.** Time horizons 20 / 100 / 100,000 yr. DDREFs differentiated per perspective. DALYs per fatal cancer incidence updated.
- **Fine particulate matter formation.** European factor replaced by world average. Lung cancer and cardiovascular mortality added as critical effects. Value choices added. World-region-specific CFs added.
- **Photochemical ozone formation.** World average replaces European factor. Respiratory mortality included. Most recent POCPs used for VOCs. Damage to terrestrial ecosystems included. World-region CFs added.
- **Terrestrial acidification.** World average replaces European factor. Soil sensitivity now based on H⁺ concentration, not base saturation. All vascular plants included, not only forest. Country-specific CFs added.
- **Freshwater eutrophication.** Global P fate model replaces European. Effect factors based on global analysis. Country-specific CFs added.
- **Marine eutrophication.** Global N fate model replaces European. Endpoint CFs newly added. Continent-specific CFs added.
- **Toxicity.** Cancer and non-cancer effects separated. Fate and exposure for dissociating organics modelled. USEtox organic + inorganic database (3,094 substances). 20-year horizon added for Individualist. Linear effect factors only. Agricultural and urban soil excluded to avoid double counting with land use.
- **Water use.** Consumption/extraction ratios added. Endpoint CFs for HH, terrestrial, and aquatic ecosystems added. Country-specific CFs added.
- **Land use.** Global-scale data replace European. Only local impact modelled (regional considered too uncertain to recommend).
- **Mineral resource scarcity.** Cumulative grade-tonnage and cost-tonnage relationships, mine-specific data, future production without discounting.
- **Fossil resource scarcity.** Cumulative cost-tonnage relationships, future production without discounting.

---

#### Tables to reproduce in the manuscript

**Table 1.5 (p. 25) — global midpoint-to-endpoint factors for I / H / E perspectives.** This is the single most important numerical artefact in the report and the table our §3.2 should cite directly:

| Pathway | Unit | I | H | E |
|---|---|---|---|---|
| **Human health** | | | | |
| Climate change | yr / kg CO₂ to air | 8.1×10⁻⁸ | 9.3×10⁻⁷ | 1.3×10⁻⁵ |
| Ozone depletion | yr / kg CFC-11 to air | 2.4×10⁻⁴ | 5.3×10⁻⁴ | 1.3×10⁻³ |
| Ionising radiation | yr / kBq Co-60 to air | 6.8×10⁻⁹ | 8.5×10⁻⁹ | 1.4×10⁻⁸ |
| Fine particulate matter formation | yr / kg PM2.5 to air | 6.3×10⁻⁴ | 6.3×10⁻⁴ | 6.3×10⁻⁴ |
| Photochemical ozone formation | yr / kg NOx to air | 9.1×10⁻⁷ | 9.1×10⁻⁷ | 9.1×10⁻⁷ |
| Cancer toxicity | yr / kg 1,4-DCB to air | 3.3×10⁻⁶ | 3.3×10⁻⁶ | 3.3×10⁻⁶ |
| Non-cancer toxicity | yr / kg 1,4-DCB to air | 6.7×10⁻⁹ | 6.7×10⁻⁹ | 6.7×10⁻⁹ |
| Water use | yr / m³ water | 3.1×10⁻⁶ | 2.2×10⁻⁶ | 2.2×10⁻⁶ |
| **Ecosystem quality: terrestrial** | | | | |
| Climate change | species·yr / kg CO₂ to air | 5.3×10⁻¹⁰ | 2.8×10⁻⁹ | 2.5×10⁻⁸ |
| Photochemical ozone formation | species·yr / kg NOx to air | 1.3×10⁻⁷ | 1.3×10⁻⁷ | 1.3×10⁻⁷ |
| Acidification | species·yr / kg SO₂ to air | 2.1×10⁻⁷ | 2.1×10⁻⁷ | 2.1×10⁻⁷ |
| Toxicity | species·yr / kg 1,4-DCB to industrial soil | 5.4×10⁻⁸ | 5.4×10⁻⁸ | 5.4×10⁻⁸ |
| Water use | species·yr / m³ water consumed | 0 | 1.4×10⁻⁸ | 1.4×10⁻⁸ |
| Land use | species / m² annual crop land | 8.9×10⁻⁹ | 8.9×10⁻⁹ | 8.9×10⁻⁹ |
| **Ecosystem quality: freshwater** | | | | |
| Climate change | species·yr / kg CO₂ | 1.5×10⁻¹⁴ | 7.7×10⁻¹⁴ | 6.8×10⁻¹³ |
| Eutrophication | species·yr / kg P to fresh water | 6.1×10⁻⁷ | 6.1×10⁻⁷ | 6.1×10⁻⁷ |
| Toxicity | species·yr / kg 1,4-DCB to fresh water | 7.0×10⁻¹⁰ | 7.0×10⁻¹⁰ | 7.0×10⁻¹⁰ |
| Water use | species·yr / m³ water consumed | 6.0×10⁻¹³ | 6.0×10⁻¹³ | 6.0×10⁻¹³ |
| **Ecosystem quality: marine** | | | | |
| Toxicity | species·yr / kg 1,4-DCB | 1.1×10⁻¹⁰ | 1.1×10⁻¹⁰ | 1.1×10⁻¹⁰ |
| Eutrophication | species·yr / kg N to marine water | 1.7×10⁻⁹ | 1.7×10⁻⁹ | 1.7×10⁻⁹ |
| **Resource scarcity** | | | | |
| Minerals | US$₂₀₁₃ / kg Cu | 0.16 | 0.23 | 0.23 |
| Fossils (crude oil)¹ | US$₂₀₁₃ / kg crude oil | 0.46 | 0.46 | 0.46 |
| Fossils (hard coal)¹ | US$₂₀₁₃ / kg hard coal | 0.03 | 0.03 | 0.03 |
| Fossils (natural gas)¹ | US$₂₀₁₃ / Nm³ natural gas | 0.30 | 0.30 | 0.30 |

¹ Fossil resource scarcity is the only category for which no constant midpoint-to-endpoint factor exists; the three rows above are the only fossil flows resolved (footnote 3, p. 25).

**Table 2.2 (pp. 29–34) — GWP for 207 GHGs across I (GWP₂₀), H (GWP₁₀₀), E (GWP₁₀₀₀).** Key values for food-system LCA:

| Substance | GWP₂₀ (I) | GWP₁₀₀ (H) | GWP₁₀₀₀ (E) |
|---|---|---|---|
| CO₂ | 1 | 1 | 1 |
| CH₄ (biogenic) | 84 | 34 | 4.8 |
| CH₄ (fossil) | 85 | 36 | 4.9 |
| N₂O | 264 | 298 | 78.8 |

Source: derived from IPCC AR5 (IPCC 2013) and Joos et al. (2013), per §2.3, pp. 28–29. CH₄ fossil vs. biogenic distinction matters for food systems (enteric fermentation is biogenic).

**Climate change endpoint derivation, §2.4, pp. 35–36.** Constants needed if our pipeline rederives or audits the factor table:
- IAGTP for 1 kg CO₂: 9.03×10⁻¹⁵ (20 yr), 4.76×10⁻¹⁴ (100 yr), 4.23×10⁻¹³ (1000 yr) °C·yr·kg⁻¹ CO₂ (Joos et al. 2013).
- Terrestrial effect factor: 0.037 PDF·°C⁻¹, derived from Urban (2015) using ΔPDF / ΔT = (15.7 − 2.8) % / (4.3 − 0.8) °C = 12.9 % / 3.5 °C.
- Total (semi-)natural terrestrial surface: A = 1.08×10¹⁴ m².
- Terrestrial species density: SD_terr = 1.48×10⁻⁸ species·m⁻² (Goedkoop et al. 2008).
- Freshwater species density: SD_fw = 7.89×10⁻¹⁰ species·m⁻³ (Goedkoop et al. 2008).

These constants are referenced by every Ch. 2–11 endpoint derivation and link the species densities used to convert PDF·m²·yr (or PDF·m³·yr) into the common `species·yr` unit (Table 1.2).

**Midpoint indicator units, Table 1.4, pp. 23–24.** This matches A1's Table 1 but with explicit indicator units and CFm units side-by-side. The full midpoint factor lists (Table 2.2 for GWP; equivalents for each impact category) follow in chapters 2–14.

---

#### Author-flagged limitations (for §7 of our draft)

The chapter-level methodology sections flag specific caveats. The most relevant for our manuscript:

1. **Climate change Egalitarian footnote, p. 28.** Climate-carbon feedbacks for non-CO₂ GHGs should ideally be included for the Egalitarian perspective but are not, because GWPs with climate-carbon feedbacks are unavailable for a 1,000-yr time horizon. This is a known inconsistency in our Egalitarian column.
2. **Value-choice gap for 5 categories, §1.3, p. 20.** Restated from A1: photochemical ozone formation, terrestrial acidification, freshwater eutrophication, land use, and fossil resource scarcity do NOT vary by I / H / E. In Table 1.5 these rows are constant across the three columns and our scenario analysis will be silent on them.
3. **Toxicity model adaptations (§S6, p. 169).** USES-LCA 2.0 was patched for dissociating chemicals; USEtox substance database adopted. The October 2017 erratum adds: a USES-LCA bug for non-carcinogenic toxicity factors was corrected. Anyone running pre-v1.1 ReCiPe will get systematically different non-cancer numbers.
4. **Land use modelling restricted to local impact, Ch. 12 / Table 1.1, p. 18.** Regional impacts in earlier ReCiPe were judged "too uncertain to recommend" and were dropped. Global extinction risk is therefore not captured in the land-use CF.
5. **Fossil resource scarcity has no constant mid-to-endpoint factor (footnote 3 to Table 1.5, p. 25; Ch. 14, p. 103).** Endpoint values are supplied per resource (crude oil, hard coal, natural gas) but cannot be derived as `CFm × constant`. Our pipeline needs to special-case fossil resources.

---

#### What this report does NOT contain (still to source)

- **The 2024 normalisation revision** the wishlist mentions. This 2017 v1.1 report has no normalisation factors; normalisation lives in a separate RIVM document. We still need to find that artefact before §3.2 commits to a "2024 normalisation" citation.
- **Country-specific CF tables** for fine PM, photochemical ozone, acidification, freshwater eutrophication, and water use are in supporting information chapters S1–S7 (pp. 129–187). If we are layering Canadian-specific values (wishlist group I), we should pull these supplements.

---

#### Three-sentence relevance note

This is the operational source for every numerical value our §3.2 pipeline encodes: Table 1.5 (p. 25) supplies the midpoint-to-endpoint factor matrix our code translates literally, and Table 2.2 (pp. 29–34) supplies the GWP values for the 207 GHGs. The October 2017 erratum (p. 7) defines exactly what "ReCiPe2016 v1.1" means and is the version label our manuscript should adopt verbatim. The 2024 normalisation revision the wishlist asks us to cite is NOT in this document, so we cannot yet make that citation page-accurate; everything related to characterisation, however, can now be page-cited from this single source.

---

### A3. Dekker et al. (2019) — A taste of the new ReCiPe for food LCAs [★★★]

**Citation.** Dekker E, Zijp MC, van de Kamp ME, Temme EHM, van Zelm R. A taste of the new ReCiPe for life cycle assessment: consequences of the updated impact assessment method on food product LCAs. Int J Life Cycle Assess. 2019. doi:10.1007/s11367-019-01653-3.

**DOI.** 10.1007/s11367-019-01653-3

**Type.** Empirical methodology-comparison paper. This is the canonical reference showing what happens when you actually run ReCiPe 2008 vs. ReCiPe 2016 v1.1 against a real food LCI.

**Study design (Methods, §2, p. 2).**
- n = 152 foods commonly consumed in the Netherlands, covering an estimated 80 % of food-related GHG emissions, land use, and fossil resource depletion (De Valk et al. 2016).
- Functional unit: 1 kg of food prepared at plate.
- LCI sources: ecoinvent v3.1, Agri-footprint v2.0, ELCD v3.1, EU & DK Input-Output Database, plus Blonk Consultants reports.
- Software: SimaPro 8.3.0. LCIA methods: ReCiPe 2008 V1.12 and ReCiPe 2016 V1.1.
- All three perspectives (I / H / E) tested at midpoint and endpoint level.
- Both global-average CFs and Dutch country-specific CFs applied (the latter for acidification, freshwater eutrophication, particulate matter formation, water use).
- Statistical tests: two-sided t-test (absolute difference), Spearman rank (ranking), RMSE and normalised RMSE (RMSE divided by ReCiPe 2008 mean; pp. 2–3).

---

#### Headline results to cite in §3.2 and §7

**Rankings are preserved across the update.** Spearman's ρ between ReCiPe 2008 and 2016 ranges from 0.85 to 0.99 across all impact categories and perspectives (Abstract; §3.1, p. 3). The default Hierarchist perspective shows no significant ranking change. This is the empirical justification for using H as our default and treating the update as "non-disruptive for ranking purposes."

**Absolute impacts change materially.** Per Abstract and §3.2:
- Larger in ReCiPe 2016: climate change, freshwater eutrophication, water consumption.
- Smaller in ReCiPe 2016: acidification, land use.
- Effect propagates to the average Dutch diet: meat and dairy show significantly larger climate-change impact in 2016 (p < 0.05); acidification is significantly lower across every food category in 2016; freshwater eutrophication is significantly larger across every food category in 2016; marine eutrophication is significantly smaller across every food category.

**Endpoint level is more sensitive than midpoint level (§3.1, pp. 3–5).** From the Hierarchist perspective:

| Pathway | ReCiPe 2016 vs. 2008 change |
|---|---|
| Climate change → human health | × 0.7 (lower) |
| Particulate matter formation → human health | × 1.8 (larger) |
| Human toxicity → human health | × 10.3 (larger), now ≈ 10 % of total HH damage |
| Water consumption → human health | NEW in 2016; ≈ 7 % of total HH damage |
| Ozone depletion → human health | × 55 (driven by N₂O CF newly included in 2016) |
| Photochemical ozone formation → human health | × 15 (chronic mortality replaces acute) |
| Climate change → ecosystems | × 0.4 (lower) |
| Land use → ecosystems | × 0.5 (half) |
| Terrestrial acidification → ecosystems | × 22.2 (larger); jumps from < 0.5 % to 14 % of total ecosystem damage |
| Ecotoxicity → ecosystems | drops from ≈ 4 % to < 0.1 % of total ecosystem damage |
| Water consumption → ecosystems | NEW in 2016; ≈ 5 % of total ecosystem damage |
| Photochemical ozone formation → ecosystems | NEW in 2016; ≈ 0.6 % overall, but ≈ 10 % for fish |

**The Individualist climate-change mid-to-endpoint CF dropped by more than an order of magnitude (§4.1, p. 7).** ReCiPe 2008 used 1.19 × 10⁻⁶ DALY·kg⁻¹ CO₂-eq for the Individualist perspective; ReCiPe 2016 v1.1 uses 8.1 × 10⁻⁸ DALY·kg⁻¹ CO₂-eq (consistent with Table 1.5 in A2). This single change accounts for much of the Individualist endpoint discrepancy.

**Egalitarian climate change and acidification change because the time horizon moved from 500 yr (2008) to 1,000 yr or infinite (2016)** (§4.1, p. 7).

---

#### Regionalisation: Dutch CFs vs. global-average CFs (§3.3, pp. 5–6)

This is the section directly relevant to our Canadian regional context (wishlist group I):

- Terrestrial acidification: significantly larger at midpoint with Dutch CFs (p < 0.05).
- Freshwater eutrophication: significantly smaller at midpoint AND endpoint with Dutch CFs (p < 0.001).
- Water consumption endpoint impact on aquatic ecosystems: Dutch CF = 0, vs. global-average CF = 6.04 × 10⁻¹³ species·yr·m⁻³. (Useful number to cite alongside Table 1.5 in A2.)
- Normalised RMSE for water consumption: 3.5 (human health) and 12.2 (terrestrial ecosystems) between Dutch and global CFs.
- Spearman's ρ = 1 between global and Dutch CF rankings: regionalisation shifts magnitudes but not ranking order for the Dutch case.

The authors caveat (§4.2, p. 8) that they applied Dutch CFs as if all production happened in the Netherlands, even though production sites are global. This oversimplification matters and is the recognised methodological gap in regionalised LCA.

---

#### Substance- and product-specific drivers

- **N₂O newly assigned an ODP in ReCiPe 2016**, accounting for most of the 55× rise in ozone-depletion damage (§4.1, p. 7). The earlier ReCiPe 2008 lacked this CF entirely.
- **PM₁₀ replaced by PM₂.₅** as the included particulate species (§4.1, pp. 7–8). The Individualist perspective in 2016 captures only direct PM₂.₅ emissions; H and E also include secondary aerosols from NH₃, SO₂, NOx. ReCiPe 2008 made no such differentiation.
- **Zinc endpoint CF (ecotoxicity) differs by ~300× between ReCiPe 2008 and 2016 from the Egalitarian perspective** (§4.2, p. 8). Cashew and wine LCIs (which carry heavy Zn emissions in cultivation, Benedetto 2013; Figueiredo et al. 2014) shift the most.
- **Beef example (§4.1, p. 7).** ReCiPe 2016 predicts 23 % more HH damage from beef in the Hierarchist perspective; 10 % of that rise is attributable to the newly added water-consumption pathway.
- **Fruits example.** 70 % of the difference in HH damage between 2008 and 2016 is attributable to water consumption alone.

---

#### Author-flagged limitations (§4.2, p. 8)

1. **LCI gaps prevented thorough comparison** for ozone depletion, pesticide toxicity, ozone formation from individual NMVOCs, and ionising radiation. The LCI database had no pesticide data, "which caused a severe underestimation of the true contribution to human and ecotoxicity of food consumption."
2. **Heavy-metal-only toxicity.** The toxicity comparisons captured only Zn, Cu, and similar metals emitted during cultivation/packaging, not pesticide residues. This limits external validity of the toxicity numbers.
3. **Regionalisation oversimplified.** Dutch CFs were applied uniformly across all life cycle stages even when production occurred abroad. The authors call out the lack of LCI granularity and LCA-software support as the blocker for true regionalised LCA, citing Mutel & Hellweg (2008) and Frischknecht et al. (2019).
4. **Out of scope:** crop rotation, surface albedo change, seasonal emission variability, brand-level differentiation, human waste life cycle stages, post-plate stages.
5. **Diet-level comparison is incomplete.** Predicted Dutch-diet climate-change impact came in lower than prior studies (§4.1, p. 8), attributed to (a) limited number of foods, (b) inclusion of children in the consumption survey, (c) underreporting by consumers.

---

#### Direct quotes worth keeping (paraphrase in §3.2 / §7 of our draft)

From the Conclusions (§5, p. 8):
- The update preserves rankings across food items but changes absolute values; hotspots and category-level interpretation are robust to the switch.
- Endpoint-level LCAs done with ReCiPe 2008 should be updated, particularly for products that emit large amounts of PM₂.₅ or its precursors, or that consume large amounts of water.
- Products with large toxicant emissions should be re-evaluated under 2016 because predicted impacts will be larger.
- "It is therefore recommended to include insights on practical consequences of old studies when updates are released" (§5, p. 9), and "the comparison of LCA results with absolute boundaries or goals should be approached with care" (§5, p. 9).

These quotes legitimise three claims our manuscript can make: (a) always use the latest ReCiPe, (b) ranking-based conclusions in legacy literature usually still hold, (c) absolute-magnitude claims do not transfer between method versions.

---

#### Three-sentence relevance note

Dekker et al. 2019 is the empirical bridge between A1 (the methodology commentary) and A2 (the factor-table report): it demonstrates with n = 152 food items what the numerical differences actually look like, which is exactly what our §3.2 and §7 need to cite. The Spearman ρ = 0.85–0.99 result is the single most important number from this paper for our manuscript, because it underwrites the claim that ranking-based food-system conclusions from legacy ReCiPe 2008 LCAs largely survive the update. The Dutch-CF regionalisation section (§3.3) is the closest published precedent for the Canadian-CF layer we plan to add in §3.2, and the specific quantitative shifts they document (water-use CF = 0 in NL vs. 6.04 × 10⁻¹³ globally) give us a template for how to present our own regional values.

---

### A4. Poore & Nemecek (2018) — Reducing food's environmental impacts through producers and consumers [★★★]

**Citation.** Poore J, Nemecek T. Reducing food's environmental impacts through producers and consumers. Science. 2018;360(6392):987–992. doi:10.1126/science.aaq0216. [Erratum 22 February 2019.]

**DOI.** 10.1126/science.aaq0216

**Type.** Globally reconciled, methodologically harmonised meta-analysis of farm- and supply-chain–stage LCA data. This is the single most-cited reference in the food-LCA literature and is the primary source the wishlist designates for our group-level factors and σ_g in S3.

**Data archive.** Microsoft Excel file allowing full replication (all original and recalculated data, including Data S1 and S2) deposited at the Oxford University Research Archive: doi.org/10.5287/bodleian:0z9MYbMyZ. **Fetch this archive before finalising S3** — the printed Fig. 1 gives only GHG and land-use values numerically; acidification, eutrophication, and scarcity-weighted water values are bars without printed numbers and must be read from Data S1.

**Study design (Building the multi-indicator global database, pp. 1–2).**
- 1,530 candidate studies screened; supplemented with data from 139 authors.
- 11 standardisation criteria applied → 570 suitable studies, median reference year 2010.
- Coverage: ~38,700 commercially viable farms in 119 countries (fig. S2).
- 40 products representing ~90 % of global protein and calorie consumption.
- Five impact indicators (p. 1): land use, freshwater withdrawals weighted by local water scarcity, GHG emissions, terrestrial acidification, freshwater eutrophication.
- Postfarm: ~1,050 observations from the original studies, plus 153 supplementary studies contributing 550 observations on processing, packaging, retail.
- Weighting: each observation weighted by share of national production it represents; each country by its share of global production. Randomisation used to capture variance at all stages (p. 2).
- For GHG emissions, farm stage further disaggregated into 20 emission sources.
- New models built for this study: nitrate leaching and aquaculture (p. 2).
- Validation: average and 90th-percentile yields reconcile to FAO data within ±10 % for most crops; total arable land and freshwater withdrawals reconcile to FAO estimates; deforestation and agricultural-methane emissions fall within independent model ranges (p. 2).

---

#### Headline food-system aggregates (p. 2 — directly usable in our §1, §3, §7)

These are the canonical "what fraction of global X comes from food" numbers; cite at page level.

| Metric | Value | Source location |
|---|---|---|
| Food supply chain GHG emissions | ~13.7 Gt CO₂-eq/yr (26 % of anthropogenic GHGs) | p. 2 §"Environmental impacts of the entire food supply chain" |
| Non-food agriculture + other deforestation drivers | ~2.8 Gt CO₂-eq/yr (5 % of anthropogenic GHGs) | p. 2, same section |
| Food share of global terrestrial acidification | ~32 % | p. 2 |
| Food share of global eutrophication | ~78 % | p. 2 |
| Farm stage share of food's GHG emissions | 61 % (81 % including deforestation) | p. 2, table S17 |
| Farm stage share of food's acidification | 79 % | p. 2, table S17 |
| Farm stage share of food's eutrophication | 95 % | p. 2, table S17 |
| Agriculture's share of ice- and desert-free land | ~43 % (87 % for food, 13 % for biofuels / textile / non-food) | p. 2 |
| Irrigation share of freshwater withdrawals | ~⅔ | p. 2 |
| Irrigation share of scarcity-weighted water use | 90–95 % | p. 2 |

---

#### Fig. 1 (p. 2) — global variation in five impacts across 40 foods

**This is the table the wishlist designates as the primary reference for our group-level factors and σ_g in S3.** Reproduced in full below as printed. Values are mean and 10th-percentile for GHG (kg CO₂-eq) and land use (m²·yr); acidification, eutrophication, and scarcity-weighted water are shown as bars in the printed figure (numerical values must be pulled from Data S1).

**Panel A — protein-rich products (per 100 g protein):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Beef (beef herd) | 724 | 20 | 50 | 42 | 164 |
| Lamb & Mutton | 757 | 12 | 20 | 30 | 185 |
| Beef (dairy herd) | 490 | 9.1 | 17 | 7.3 | 22 |
| Crustaceans (farmed) | 1,000 | 5.4 | 18 | 0.4 | 2.0 |
| Cheese | 1,900 | 5.1 | 11 | 4.4 | 41 |
| Pig Meat | 116 | 4.6 | 7.6 | 4.8 | 11 |
| Fish (farmed) | 612 | 2.5 | 6.0 | 0.4 | 3.7 |
| Poultry Meat | 326 | 2.4 | 5.7 | 3.8 | 7.1 |
| Eggs | 100 | 2.6 | 4.2 | 4.0 | 5.7 |
| Tofu | 354 | 1.0 | 2.0 | 1.1 | 2.2 |
| Groundnuts | 100 | 0.6 | 1.2 | 1.8 | 3.5 |
| Other Pulses | 115 | 0.5 | 0.8 | 4.6 | 7.3 |
| Peas | 438 | 0.3 | 0.4 | 1.2 | 3.4 |
| Nuts | 199 | −2.2 | 0.3 | 2.7 | 7.9 |
| Grains | 23,000 | 1.0 | 2.7 | 1.7 | 4.6 |

Nuts have a negative 10th-percentile GHG value because tree crops can sequester carbon on what was previously cropland or pasture (Fig. 3 caption, p. 4).

**Panel B — milks (per 1 L):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Milk | 1,800 | 1.7 | 3.2 | 1.1 | 8.9 |
| Soymilk | 354 | 0.6 | 1.0 | 0.3 | 0.7 |

**Panel C — starch-rich products (per 1,000 kcal):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Cassava | 288 | 0.4 | 1.4 | 0.8 | 1.9 |
| Rice (flooded) | 7,800 | 0.4 | 1.2 | 0.3 | 0.8 |
| Oatmeal | 139 | 0.3 | 0.9 | 1.1 | 2.9 |
| Potatoes | 604 | 0.2 | 0.6 | 0.6 | 1.2 |
| Wheat & Rye (Bread) | 8,800 | 0.3 | 0.6 | 0.4 | 1.4 |
| Maize (Meal) | 6,200 | 0.2 | 0.4 | 0.3 | 0.7 |

**Panel D — oils (per 1 L):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Palm Oil | 220 | 3.6 | 7.3 | 1.7 | 2.4 |
| Soybean Oil | 497 | 2.4 | 6.3 | 5.3 | 11 |
| Olive Oil | 411 | 2.9 | 5.4 | 7.9 | 26 |
| Rapeseed Oil | 1,800 | 2.5 | 3.8 | 5.2 | 11 |
| Sunflower Oil | 519 | 2.5 | 3.6 | 8.4 | 18 |

**Panel E — vegetables (per 1 kg):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Tomatoes | 855 | 0.4 | 2.1 | 0.1 | 0.8 |
| Brassicas | 40 | 0.2 | 0.5 | 0.2 | 0.6 |
| Onions & Leeks | 37 | 0.3 | 0.5 | 0.1 | 0.4 |
| Root Vegetables | 43 | 0.2 | 0.4 | 0.2 | 0.3 |

**Panel F — fruits (per 1 kg):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Berries | 183 | 0.8 | 1.5 | 0.3 | 2.4 |
| Bananas | 246 | 0.6 | 0.9 | 0.3 | 1.9 |
| Apples | 125 | 0.3 | 0.4 | 0.3 | 0.6 |
| Citrus | 377 | 0.1 | 0.4 | 0.4 | 0.9 |

**Panel G — sugars (per 1 kg):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Cane Sugar | 116 | 0.9 | 3.2 | 1.2 | 2.0 |
| Beet Sugar | 209 | 1.2 | 1.8 | 1.2 | 1.8 |

**Panel H — alcoholic beverages (per 1 unit = 10 mL alcohol):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Beer (5 % ABV) | 695 | 0.14 | 0.24 | 0.05 | 0.22 |
| Wine (12.5 % ABV) | 154 | 0.07 | 0.14 | 0.07 | 0.14 |

**Panel I — stimulants (per 1 serving):**

| Product | n | GHG 10th | GHG Mean | Land 10th | Land Mean |
|---|---|---|---|---|---|
| Dark Chocolate (50 g) | 162 | −0.01 | 2.3 | 1.7 | 3.4 |
| Coffee (15 g, 1 cup) | 346 | 0.08 | 0.4 | 0.13 | 0.3 |

**Implication for S3 σ_g derivation.** A first-pass estimate of within-product variance can be derived from the (mean − 10th-percentile) gap, which, for many products, is comparable in magnitude to the mean itself (suggesting log-skewed distributions). For finer σ_g (e.g. distinguishing CV by group: ruminant meat vs. legumes vs. cereals), pull the full per-product distribution from Data S1 rather than rebuilding from the printed table.

---

#### Variability and skew of impact (pp. 1–2, "Highly variable and skewed environmental impacts")

Quotable claims for §1 and §7 of our draft:

1. **Up to 50-fold variation in impact among producers of the same product** (abstract; p. 1).
2. **90th-percentile beef GHG and land use** (beef herd): 105 kg CO₂-eq/100 g protein and 370 m²·yr — 12× and 50× greater than 10th-percentile dairy-beef impacts (p. 2).
3. **10th-percentile dairy-beef vs. peas:** 36× higher GHG and 6× higher land use (p. 2).
4. **Major staples** (wheat, maize, rice): 90th-percentile impacts > 3× 10th-percentile impacts on all five indicators (p. 2).
5. **Producer skew, beef herd:** highest-impact 25 % of producers account for 56 % of beef-herd GHG emissions and 61 % of land use (~1.3 Gt CO₂-eq and 950 Mha of land — primarily pasture) (p. 2).
6. **Producer skew across all products:** highest-impact 25 % of producers contribute on average 53 % of each product's environmental impact (p. 2, fig. S3).
7. **Water-scarcity skew is most extreme:** just 5 % of world's food calories create ~40 % of the scarcity-weighted water burden (p. 2).

---

#### Proxies and cross-indicator predictability (pp. 2–3, "Enable producers to monitor multiple impacts")

Directly relevant to our §3 (why we predict ALL five categories per dish, not just GHG):

- **Single-proxy farm-stage prediction is weak.** Crop yield, N-use efficiency, milk yield per cow, liveweight gain, pasture area, feed conversion ratios: R² = 0–27 % in 47 of 48 proxy-impact combinations (fig. S4; text p. 2).
- **Cross-indicator prediction is weak.** R² = 0–30 % in 26 of 32 impact-impact combinations (fig. S4; text p. 3).
- **One exception:** pork, poultry, and milk show R² ≤ 54 % between acidification and eutrophication (p. 3), driven by manure dominance.
- **Conclusion the authors draw (p. 3):** "Monitoring multiple impacts and avoiding proxies supports far better decisions and helps prevent harmful, unintended consequences."

This validates our multi-indicator design and gives an empirical basis for refusing to extrapolate from GHG-only data.

---

#### Animal vs. vegetable substitutes — the five biophysical reasons (p. 5, Fig. 3 p. 4)

For §7 of our draft on why dietary shifts dominate producer-side mitigation:

1. **Feed–to–edible-protein conversion ratios > 2 for most animals** (cites Tilman & Clark 2014; Mottet et al. 2017). High by-product use is offset by low digestibility and growth; additional transport required to take feed to livestock.
2. **Deforestation is feed-dominated:** 67 % of agriculture-driven deforestation is for feed (soy, maize, pasture) → loss of above- and belowground carbon. Improved pasture management can temporarily sequester carbon but cuts ruminant life-cycle emissions by at most 22 %.
3. **Animal-only emission sources:** enteric fermentation, manure, aquaculture ponds. 10th-percentile values alone for these sources are 0.4–15 kg CO₂-eq/100 g protein.
4. **Slaughterhouse effluent processing:** 0.3–1.1 kg CO₂-eq/100 g protein — greater than processing emissions for most other products.
5. **High wastage of fresh animal products** (spoilage-prone).

**The headline imbalance (p. 4):** "Meat, aquaculture, eggs, and dairy use ~83 % of the world's farmland and contribute 56–58 % of food's different emissions, despite providing only 37 % of our protein and 18 % of our calories." This sentence is quotable verbatim under the 15-word rule if broken up; otherwise paraphrase.

---

#### Dietary-change scenarios (p. 5, "Mitigation through consumers") — for our §7 and S3 calibration

**Scenario 1 — plant-only diet (table S13, citing Springmann et al. 2016):** moving from current diets to a diet that excludes animal products, for a 2010 reference year:

| Indicator | Reduction | Range |
|---|---|---|
| Land use | −3.1 (2.8 – 3.3) Gha | −76 % (includes −19 % arable land) |
| GHG emissions | −6.6 (5.5 – 7.4) Gt CO₂-eq | −49 % |
| Acidification | −50 % | (45 – 54 %) |
| Eutrophication | −49 % | (37 – 56 %) |
| Scarcity-weighted freshwater withdrawals | −19 % | (−5 to 32 %) |

Plus **~8.1 Gt CO₂/yr atmospheric removal over 100 yr** as natural vegetation re-establishes and soil carbon re-accumulates on released land (IMAGE integrated assessment model; p. 5).

**Scenario 1, US-only:** dietary change has potential for 61–73 % reduction in food's emissions (US per-capita meat consumption is 3× global average; p. 5).

**Scenario 2 — halve animal-product consumption by replacing above-median GHG producers with vegetable equivalents:** achieves 71 % of Scenario 1's GHG reduction (~10.4 Gt CO₂-eq/yr including atmospheric CO₂ removal), and 67 %, 64 %, 55 % of land-use, acidification, eutrophication reductions respectively (p. 5).

**Scenario for discretionary products:** lowering oils, sugar, alcohol, stimulants consumption by 20 % by avoiding highest-land-use production reduces land use of those products by 39 % on average; emissions reductions 31–46 %; scarcity-weighted water reductions 87 % (p. 5).

These numbers calibrate the upper bound on what consumer-side mitigation can buy us and are directly comparable to the AGRIBALYSE-derived diet-change scenarios we will run in S2.

---

#### Methodological cautions and author-flagged limitations (for §7)

1. **Geography influences trade-offs and limits proxy generalisation (p. 3).** Practices like conservation agriculture, organic farming, and integrated best-practice systems all have highly variable outcomes. Practice choice should not be conflated with environmental targets.
2. **Variable sources of impact even within product (Fig. 2, p. 3; figs. S7–S10).** For all crop calorie production globally, 40 % of land-use variance comes from differences in fallow duration and multiple cropping — yet most strategies focus on increasing single-crop yields.
3. **Site-condition dependence.** ~40 % of variation in reactive-N loss is explained by soil pH, temperature, and drainage; freshwater aquaculture ponds emit 0–450 g CH₄/kg liveweight, ⅓ explained by temperature (p. 3).
4. **Deforestation + cultivated organic soils dominate variance:** 42 % of each product's agricultural GHG variance comes from these two sources, and they dominate the highest-impact producers (p. 4, figs. S10–S11). Curbing forest loss and limiting peatland cultivation should remain priority interventions.
5. **Procurement traceability limits.** RSPO palm-oil case (p. 4): one-fifth of 2017 production certified but virtually no demand in China, India, Indonesia. Procurement-only strategies leak unless globally enforced; this is the limitation our supply-chain framing in §7 must engage with.
6. **Standards as a safety net.** The paper recommends pairing flexible producer-driven mitigation with strict standards on hardest-to-quantify impacts (deforestation, harmful pesticides, biodiversity); our framework should make the same distinction.

---

#### Direct supply-chain numbers (Communicate impacts up the supply chain, p. 4)

Worth keeping for the postfarm-stage discussion in our §3 / §7:

- **Postfarm emissions variability:** 90th-percentile postfarm emissions are 2–140× larger than 10th-percentile postfarm emissions across products (p. 4, fig. S12).
- **Beer packaging example:** returnable stainless-steel kegs = 20 g CO₂-eq/L; recycled glass bottles = 300–750 g; bottles to landfill = 450–2,500 g.
- **Beef distribution and retail losses** contribute 12–15 % of total emissions; the sum of packaging + transport + retail contributes just 1–9 % (p. 4, fig. S13). Loss-reduction priority is clear for beef.
- **Processed vs. fresh wastage:** processed fruit & veg wastage is ~14 % lower than fresh; processed fish/seafood ~8 % lower.
- **Retail concentration:** 10 retailers represent 52 % of US grocery sales and 15 % of global sales (Euromonitor, ref. 32; p. 4) — enabling market transformation through procurement standards.

---

#### Five-point integrated mitigation framework (Fig. 4, p. 5)

For citation in our §7 / discussion if framing our system as a "monitor-incentivise-mitigate-communicate" pipeline:

1. **Producers monitor their impacts** using digital tools, validated against known input-output ranges and certified independently.
2. **Policy-makers set targets** on environmental indicators and incentivise them via credits, tax breaks, or reallocated subsidies (>USD 500 B/yr worldwide, OECD 2017, ref. 38).
3. **Assessment tools provide multiple mitigation and productivity-enhancement options**, consolidating research and producer best-practice.
4. **Impacts communicated up the supply chain and through to consumers** via labels, taxes/subsidies reflecting environmental cost, and education.
5. **Stringent traceability** for animal products (already legally required in many countries; cites EU Regulation 1308/2013) makes producer-impact communication most feasible where it matters most.

---

#### Three-sentence relevance note

This is the canonical empirical reference for our group-level environmental factors and within-group variability (σ_g) in S3 — Fig. 1 (p. 2) gives means and 10th percentiles for 40 products across five indicators, and the underlying archive (doi.org/10.5287/bodleian:0z9MYbMyZ) supplies the full distributions and acidification/eutrophication/water values we cannot read off the printed figure. The headline aggregates (food = 26 % of anthropogenic GHGs, 32 % of acidification, 78 % of eutrophication; farm stage = 61–95 % of food's burden, pp. 1–2) and the producer-variability claims (50-fold producer-level variation; 25 % of producers contribute 53 % of impact; p. 2) anchor §1 and §7 and need page-accurate citation. The dietary-change scenario block (p. 5) — plant-only diet cutting GHGs 49 %, land use 76 %, plus 8.1 Gt CO₂/yr atmospheric removal — calibrates the upper bound on what our consumer-side modeling can quantify and is the result we benchmark our own dietary-shift scenarios against.

---

### A5. AGRIBALYSE 3.2 documentation (ADEME, November 2024) [★★★]

**Citation.** ADEME (Agence de l'environnement et de la maîtrise de l'énergie). AGRIBALYSE® 3.2 — Programme de référence sur les indicateurs d'impacts environnementaux des produits agricoles et alimentaires. Angers: ADEME; November 2024.

**Primary URL.** https://doc.agribalyse.fr/documentation-en (English landing page; substantive documentation pages are in French at https://doc.agribalyse.fr/documentation/).

**Dataverse DOI.** doi:10.57745/XTENSJ — https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/XTENSJ

**Software availability.** OpenLCA and SimaPro implementations of v3.2 were in progress at the time of release; the dataverse package contains the raw impact factors usable without an LCA software stack.

**Type.** Reference LCI/LCIA database for agricultural and food products consumed in France. Public-domain factor tables built collectively under the GIS REVALIM partnership (ADEME + INRAE + LCA consultancies).

---

#### Scope and coverage (Introduction page)

- **>200 agricultural raw products** (carrots, wheat, milk, etc.) modelled at farm gate.
- **>2,500 ready-to-eat food products** — both raw (an apple) and processed (applesauce, a muffin). Covers all main categories of products consumed in France including imported foods (coffee, chocolate).
- **Functional unit:** 1 kg of food product at plate (or per kg of agricultural product at farm gate for raw-products tables).
- **Food-product list aligned 1:1 with the Ciqual nutritional composition table** maintained by ANSES (~2,800 foods, expanding to 3,000). Same food items in both, enabling joint nutritional × environmental analysis — directly relevant to our Call 1 manuscript's diet-quality × environment fusion (§3.3, §4 of our draft).
- **"Standard / average" representative products only** in the simplified version — one indicator set per Ciqual code, no brand or sub-variant declensions. Limited season/air-transport variants (tomato, strawberry, Kenyan green beans).
- **"Consumption mix" weighting** for imported ingredients: e.g. tomato used in pizza = 18 % French + 46 % Italian + 36 % Spanish (Périmètre page). We should use the same logic for any Canadian consumption-mix layer we build in S2.

---

#### LCIA method — Product Environmental Footprint (PEF)

**16 impact categories** following the European Commission's PEF method (Méthodologie ACV page). Reproduce this table in our §3.2:

| Indicator | Unit | Notes |
|---|---|---|
| Climate change | kg CO₂-eq | Most familiar indicator; global ecosystem-level effect. |
| Fine particulate matter | disease incidence | Human-health endpoint already aggregated. |
| Water scarcity (depletion) | m³ world-eq | Scarcity-weighted (AWARE); 1 L in Morocco ≠ 1 L in Brittany. |
| Fossil resource depletion (energy) | MJ | Non-renewable energy: coal, gas, oil, uranium. |
| Land use | point | Reference is "natural state"; reflects degradation. |
| Mineral resource depletion | kg Sb-eq | Copper, potash, rare earths, sand, etc. |
| Stratospheric ozone depletion | kg CFC-11-eq | UV protection layer; carcinogenicity link. |
| Acidification | mol H⁺-eq | Acid rain pathway. |
| Ionising radiation, human health | kBq U-235-eq | Radioactive waste, principally from nuclear electricity. |
| Photochemical ozone formation | kg NMVOC-eq | Low-altitude smog → respiratory health. |
| Terrestrial eutrophication | mol N-eq | Mainly agricultural soils. |
| Marine eutrophication | kg N-eq | Algal bloom / dead-zone driver. |
| Freshwater eutrophication | kg P-eq | River/lake equivalent. |
| Freshwater ecotoxicity | CTUe | Flagged by ADEME as "encore peu robuste" — fragile; only available in LCA software, not the Excel files. |
| Human toxicity, non-cancer | CTUh | Environmental exposure (air, water, soil) only; ingestion of pesticide residues NOT modelled. |
| Human toxicity, cancer | CTUh | Same exposure caveat. |

**Note for §3.2 of our draft:** AGRIBALYSE uses PEF, not ReCiPe. Our pipeline must distinguish: ReCiPe2016 v1.1 (A1, A2, A3) gives 17 midpoint categories with I/H/E perspective; PEF gives 16 indicators with one fixed weighting set. The category lists are similar but not identical (PEF splits eutrophication into 3 sub-categories; ReCiPe keeps freshwater and marine separate). The mapping between PEF and ReCiPe must be made explicit in §3.2.

---

#### Single-score aggregation — EF single score

- **Single EF score** recommended by the European Commission combines all 16 indicators using fixed weighting factors that account for both indicator robustness and environmental stakes.
- Unit: **Eco-indicator Point (Pt)** or millipoint (mPt; 500 mPt = 0.5 Pt). Scale chosen such that 1 Pt ≈ the annual environmental impact of one European inhabitant.
- Reference for weights: JRC Technical Reports 2018 (Sala et al.) — https://publications.jrc.ec.europa.eu/repository/bitstream/JRC106545/jrc106545_weighting__on_line-1.pdf
- Authoritative method spec: JRC Technical Reports — Suggestions for updating the Product Environmental Footprint (PEF) method (Zampori L, Pant R, 2019), p. 105 — https://eplca.jrc.ec.europa.eu/permalink/PEF_method.pdf
- ADEME caveat (Méthodologie ACV page, verbatim): "Ce score est un score moyen, qui comprend un arbitraire certain concernant la pondération entre les différents indicateurs." Translation: weighting between indicators carries unavoidable subjectivity. This is the caveat our §7 needs to acknowledge.

---

#### Data quality framework

**Data Quality Ratio (DQR), scale 1–5.** Each agricultural and food product has a DQR computed using the European Commission's recommended method. Lower is better (1 = very good, 5 = very poor). The Commission recommends caution for any data with DQR > 3.

**ADEME's own reported DQR distribution:** 67 % of AGRIBALYSE data have DQR rated good or very good (1 to 3).

**No quantitative uncertainty (e.g. standard deviations) is published.** ADEME states explicitly that estimating these would require data not currently available. Implication for our S3 σ_g and uncertainty quantification: we cannot pull per-product CVs from AGRIBALYSE, but we can use DQR as a coarse weighting flag.

---

#### Version history (Evolution de la base de données page)

| Version | Release | Background data |
|---|---|---|
| 3.0 | June 2020 | ecoinvent 3.5 + WFLDB 3.1 |
| 3.0.1 | October 2020 | ecoinvent 3.5 + WFLDB 3.1 |
| 3.1 | October 2022 | ecoinvent 3.8 + WFLDB 3.5 |
| 3.1.1 | June 2023 | ecoinvent 3.8 + WFLDB 3.5 |
| **3.2** | **November 2024** | **ecoinvent 3.9.1 + WFLDB 3.5** |
| 3.3 (planned) | Mid-to-late 2026 | ecoinvent 3.11 |

**Update cadence:** new versions published every 18–24 months.

---

#### What changed in v3.2 (vs. v3.1.1) — Evolution de la base de données page

For §3.2 of our draft, distinguish v3.2 from earlier releases:

1. **New and updated inventories** from the InCyVie project (technical institutes of agriculture/agri-food) and from external contributors including Alliance 7.
2. **Packaging modelling overhauled** via the PACK_AGB project.
3. **Cooking modes and recipes refined.**
4. **Trace metallic elements in organic fertilisers revised.**
5. **Allocation rule for organic residual products (PRO) updated.**
6. **Water flow geographic correction.**
7. **Background data upgraded** to ecoinvent 3.9.1 (from 3.8) and WFLDB stays at 3.5.

**Known errata in v3.2** (Evolution page, top alert box):
- **Eggs** at farm gate: impacts judged underestimated; farm-gate egg factors temporarily withdrawn from the agricultural-product spreadsheet. Foods containing eggs in v3.2 are similarly under-estimated.
- **Bleu-Blanc-Coeur labelled products** (pork, eggs, poultry) withdrawn pending update.
- **Quinoa** LCI error under correction.
- **Packaging error** on Ciqual codes 26232, 26013, 25998, 26037, 26034, 27029, 9901: corrected values appear as duplicated rows (red = uncorrected/software-aligned; black = corrected/not-yet-software-aligned).

These errata should be flagged in our §3.2 and (if we use any of those Ciqual codes) handled explicitly in our pipeline.

---

#### Upstream dependencies — ecoinvent and WFLDB linkage (Liens avec ecoinvent page)

- AGRIBALYSE uses **ecoinvent for non-agricultural background processes** (electricity, transport) and for many imported productions (e.g. pineapple, Moroccan tomato).
- AGRIBALYSE uses **WFLDB (World Food LCA Database, Quantis-developed)** for international food-product LCAs.
- **Licensing.** Using AGRIBALYSE in LCA software (where it appears in disaggregated form) requires an ecoinvent licence (Academic, Commercial, or Enterprise). Integrating AGRIBALYSE's ecoinvent background processes into a derived tool requires a Developer licence.
- For our manuscript: the licensing dependency on ecoinvent is a non-trivial barrier for any open-source pipeline. The dataverse-deposited impact factors (DOI 10.57745/XTENSJ) ARE open, but the disaggregated upstream processes are NOT. We need to clarify in §3.2 whether our S2 runs use the open factor tables only, or also dip into licensed background data.

---

#### Companion tool — MEANS-InOut (INRAE-Cirad)

Mentioned in the Périmètre page. INRAE-Cirad's MEANS-InOut software is the upstream tool for describing agricultural itineraries before piping into SimaPro for AGRIBALYSE calculation. Available online by service subscription: https://www.inrae.fr/means. **Not required** for using AGRIBALYSE factor tables — only for building new agricultural inventories.

---

#### Methodological scope and stage breakdown

**Agricultural products (per Périmètre page):** all upstream processes (input manufacture) and on-field operations included, ending at field exit. Transformation, logistics, transport, packaging, and use phases are NOT included in the agricultural tables.

**Food products:** five life-cycle stages broken out for each of the 2,500 Ciqual products in the simplified file:
1. Agricultural production
2. Transport
3. Packaging
4. Distribution
5. Use (cooking, defrosting)

For composite products, impacts are additionally broken out **by ingredient**. Useful for our recipe-level decomposition.

**On agricultural-stage dominance** (Introduction page, verbatim translation): "50 to 80 % of the environmental impacts of a food product occur during the agricultural production phase," with high variability at that stage from diversity of production modes and contexts. Quotable in our §1 and §3.

---

#### Author-flagged limitations (Périmètre page — directly usable in our §7)

ADEME lists current limits and required improvements:

1. **Biodiversity not well represented** by current LCA indicators; supplementary indicators (e.g. Surfaces d'Intérêt Écologique) recommended for context.
2. **Soil carbon storage/release not yet properly modelled.**
3. **Transformation processes and co-product use in agri-food industries** need better description.
4. **Pesticide degradation in the environment and its effect on human and ecosystem health** insufficiently modelled. Direct ingestion exposure to pesticide residues is NOT in PEF/AGRIBALYSE.
5. **Water consumption spatialisation** needs improvement.
6. **Ecotoxicity and toxicity indicators** flagged as "encore peu robustes" — fragile and difficult to interpret; available only in LCA software, not in Excel exports.
7. **No biodynamic / organic variants for some products.** Notable example: cannot today compare environmental impact of conventional vs. organic average French cow milk because the ACV BIO project could not model an average organic product for bovine sectors (insufficient statistics on organic production diversity).
8. **No quantitative uncertainty (standard deviations)** — DQR is qualitative.

These align with what we need for §7 of the manuscript and explicitly justify (a) running uncertainty scenarios (wishlist group F) on top of AGRIBALYSE point estimates, (b) supplementing with biodiversity / soil-carbon proxies if the manuscript discusses them, (c) being cautious with toxicity rankings.

---

#### Coming in v3.3 (Evolution de la base de données page — for context only, not citation)

- Background data upgrade to ecoinvent 3.11.
- DQR methodology revision.
- New organic-production inventories.
- Methodological updates: land-use change and practice change accounting; agricultural water balance closure; enteric methane mitigation levers.
- Methodological reports updated.

If our manuscript is published after mid-2026, we may need to re-run S2 with v3.3 — flag this in the version-dependency note.

---

#### Three-sentence relevance note

AGRIBALYSE 3.2 is the primary LCI / LCIA reference our S2 will draw on to score French and European consumption-mix-weighted foods, and the 1:1 alignment between AGRIBALYSE food items and the Ciqual nutritional composition table is precisely what makes the diet-quality × environment fusion in our §3.3 / §4 feasible at scale. The 16-indicator PEF method used here differs from the ReCiPe2016 v1.1 method documented in A1–A3 (different category list, different weighting, different cultural-perspective handling), so §3.2 must make the method choice explicit and the manuscript should not present PEF and ReCiPe results as interchangeable. Author-flagged limits (no quantitative uncertainty, only qualitative DQR; fragile toxicity indicators; no biodiversity or soil-carbon mechanism; pesticide-residue ingestion not modelled) directly motivate our wishlist-group-F uncertainty work and our §7 caveats, and the 67 % "DQR ≤ 3" headline figure is the single most useful quality indicator to cite alongside any specific AGRIBALYSE-derived number.

---

## Group B. Diet quality and nutritional indices

*Pending: papers B6 through B13.*

## Group C. Health-burden and DALY food scoring

*Pending: papers C14 through C21.*

## Group D. AI / LLMs for food classification and LCA

*Pending: papers D22 through D27.*

## Group E. Sustainability assessment frameworks

*Pending: papers E28 through E32.*

## Group F. Uncertainty quantification in LCA

*Pending: papers F33 through F38.*

## Group G. Sustainability of AI

*Pending: papers G39 through G46.*

## Group H. Monetary valuation and externalities

*Pending: papers H47 through H50.*

## Group I. Canadian regional context

*Pending: papers I51 through I54.*

## Group J. Data and study cohorts

*Pending: papers J55 through J57.*
