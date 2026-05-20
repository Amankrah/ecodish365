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

### B6. Brassard et al. (2022) — Development of the HEFI-2019 [★★★]

**Citation.** Brassard D, Elvidge Munene LA, St-Pierre S, Guenther PM, Kirkpatrick SI, Slater J, Lemieux S, Jessri M, Haines J, Prowse R, Olstad DL, Garriguet D, Vena J, Vatanparast H, L'Abbe MR, Lamarche B. Development of the Healthy Eating Food Index (HEFI)-2019 measuring adherence to Canada's Food Guide 2019 recommendations on healthy food choices. Appl Physiol Nutr Metab. 2022;47(5):595–610.

**DOI.** 10.1139/apnm-2021-0415

**Type.** Technical Note describing the construction and scoring standards of the HEFI-2019. This is the development paper; construct validity and Cronbach's α live in the companion evaluation paper (B7, apnm-2021-0416) — those numbers are NOT in this document.

**License.** CC BY 4.0 (open access). Scoring algorithm code is in Supplementary File S1 (https://doi.org/10.1139/apnm-2021-0415).

**Provenance.** Built for 24-hour dietary recall data, calibrated against the 2015 Canadian Community Health Survey (CCHS)-Nutrition (our J55 data source). Funded partly by Health Canada via a contract with Laval University; Health Canada had final authority on each component's scoring standard (Box 1, p. 597).

---

#### The index in one paragraph (Abstract; §"Identification of the HEFI-2019 components", p. 597)

The HEFI-2019 measures alignment of eating patterns with the "Healthy Food Choices" / "What to Eat" recommendations of Canada's Food Guide 2019 (CFG-2019), for Canadians aged ≥2 years. It has **10 components — 5 food-based, 1 beverage-based, 4 nutrient-based — summing to a maximum of 80 points.** Seven components are "adequacy" (more is better); 3 are "moderation" components for nutrients of concern (saturated fats, free sugars, sodium; less is better). All components are expressed as ratios (proportions of total foods, total beverages, or total energy), so the score reflects diet *quality* rather than *quantity*.

---

#### Table 2 (p. 600) — the scoring standards. Reproduce verbatim in our §3.2 / nutrition module

This is the single most important artefact in the paper and the exact specification our pipeline must encode:

| # | Component | Measurement (ratio) | Max pts | Unit | Min-score standard | Max-score standard |
|---|---|---|---|---|---|---|
| 1 | Vegetables and fruits | total veg & fruit / total foods | 20 | RA/RA | no veg and no fruit | ≥ 0.50 |
| 2 | Whole-grain foods | total whole-grain foods / total foods | 5 | RA/RA | no whole-grain foods | ≥ 0.25 |
| 3 | Grain foods ratio | total whole-grain foods / total grain foods | 5 | RA/RA | no whole-grain foods | 1.0 |
| 4 | Protein foods | total protein foods / total foods | 5 | RA/RA | no protein foods | ≥ 0.25 |
| 5 | Plant-based protein foods | plant-based protein foods / total protein foods | 5 | RA/RA | no plant-based protein foods | > 0.50 |
| 6 | Beverages | (plain water + unsweetened beverages) / total beverages | 10 | g/g | no water and no unsweetened beverages | 1.0 |
| 7 | Fatty acids ratio | (MUFA + PUFA) / saturated fat | 5 | g/g | ≤ 1.1 | ≥ 2.6 |
| 8 | Saturated fats | saturated fat / energy | 5 | %E (kcal/kcal) | ≥ 15 %E | < 10 %E |
| 9 | Free sugars | free sugars / energy | 10 | %E (kcal/kcal) | ≥ 20 %E | < 10 %E |
| 10 | Sodium | sodium / energy | 10 | mg/kcal | ≥ 2.0 | < 0.9 |

**Points between min and max are attributed proportionately (linearly) for all components** (Results, p. 599).

**Threshold provenance (Table 2 footnotes, p. 600 + Results pp. 599–602):**
- Fatty-acids max (≥ 2.6) = 1st percentile of unsat/sat ratio in simulated CFG-2019-consistent diets; matches HEI-2015. Min (1.1) = 15th percentile of the ratio in 2015 CCHS-Nutrition (single 24-h recall, ≥2 y).
- Saturated-fat min-score (≥ 15 %E) = 85th percentile of intake in 2015 CCHS-Nutrition.
- Free-sugars min-score (≥ 20 %E) = 85th percentile of intake in 2015 CCHS-Nutrition.
- Sodium max-score (< 0.9 mg/kcal) = NASEM 2300 mg/day CDRR threshold ÷ 2600 kcal (the 90th percentile of usual energy intake, ≥2 y, 2015 CCHS-Nutrition). Min-score (≥ 2.0) = 85th percentile of the sodium-to-energy ratio.

---

#### Weighting logic (§"Weighting of components", pp. 598–599) — needed to justify the 80-point scale

- Three sets of *complementary* recommendations each split 5 + 5 so the pair weighs the same as a single 10-point component: grains (#2 + #3), protein (#4 + #5), fats (#7 + #8).
- **Vegetables and fruits is the sole over-weighted component (20 pts)** because the evidence base is strong and uncontested.
- Net: every recommendation (or complementary set) carries 10 points except vegetables-and-fruits at 20, totalling 80.

This rationale is what we cite if a reviewer asks why our nutrition module weights V&F double.

---

#### Reference metric: Reference Amounts (RAs), not grams or volumes (pp. 597–598)

- All five food-based components use **Reference Amounts (RAs)** — the amount of a food typically eaten at one sitting (g for solids, mL for liquids), from Health Canada's Table of Reference Amounts (2016). Beverages use grams directly to avoid an unnecessary RA conversion.
- Volumes rejected (solids like muffins don't convert cleanly); weights rejected (can't compare leafy greens vs. nuts fairly). RAs chosen to sidestep CFG-2019's deliberate lack of numeric portion guidance.
- **Total foods** = sum of RAs of all foods + protein-containing beverages (unsweetened milk and unsweetened plant beverages > 2.5 g protein/100 mL). **Excludes** culinary ingredients (spices, baking soda), non-protein beverages (water, coffee, tea, almond/cashew/rice/coconut), and oils/spreads (those route to the fat components). This exact inclusion/exclusion list is in Table A1 (Appendix A, pp. 606–609) and must be encoded faithfully.

---

#### Density (energy-adjusted) approach for nutrient components (pp. 598, 602)

Sodium, saturated fats, and free sugars are scored as ratios to energy (not absolute intake) to (a) decouple the score from total energy / amount eaten, (b) reduce ceiling/floor effects, and (c) keep all components dimensionally consistent as ratios. This is the methodological reason our pipeline must carry per-dish energy alongside nutrient masses.

---

#### Data inputs required to compute HEFI-2019 (Discussion, p. 603) — checklist for our nutrition module

Three pre-steps before scoring:
1. Classify each food/beverage into the numerator/denominator categories (Table A1).
2. Quantify each category — RAs for foods, grams for beverages.
3. Total nutrient intakes (MUFA, PUFA, saturated fat, free sugars in g; sodium in mg) and energy (kcal).

Two external databases are mandatory:
- **Reference Amounts** table (Health Canada 2016).
- **Free sugars content** of Canadian Nutrient File 2015 foods — the CNF itself does NOT contain free sugars; Health Canada built a separate free-sugars database (Rana et al. 2021, Nutrients 13(5):1471). **Flag for our J56 (CNF) extraction:** we need the Rana et al. 2021 free-sugars supplement, not just the base CNF.

---

#### Statistical methodology (§"Statistical analyses", p. 599)

- Scoring standards lacking a CFG benchmark (fatty-acids, free sugars, saturated fats, sodium) were derived from **first-24-h-recall intake distributions** in 2015 CCHS-Nutrition.
- Standards were then compared against **usual-intake** distributions estimated with the **National Cancer Institute (NCI) bivariate method** (Freedman et al. 2010; Kipnis et al. 2016), using repeated recalls available for ~37 % of respondents.
- Models stratified into 3 groups: children/adolescents 2–18 y, males ≥19 y, females ≥19 y. Covariates: age (DRI groups), sex (only for 2–18 y), recall-sequence indicator, weekend indicator. All survey-weighted.

This is the same NCI bivariate machinery our S4 meal panel will likely need; cite alongside J55.

---

#### Ceiling / floor effects — critical for our sensitivity analysis (Results p. 601; Discussion p. 603)

The authors explicitly flag three components with non-trivial floor/ceiling effects, meaning these are **less sensitive to detecting subgroup or temporal differences:**
- **Protein foods (#4):** strong ceiling — ~50 % of Canadians ≥2 y received the maximum score in 2015.
- **Saturated fats (#8):** floor/ceiling.
- **Free sugars (#9):** floor/ceiling — a "perfect" score only means intake is below 10 %E; any variation below that cutoff is invisible.

Implication for us: if our manuscript reports HEFI-2019 component scores across dietary scenarios, we should expect compressed dynamic range on these three components and say so in §7.

---

#### Author-flagged limitations (Discussion, "Strengths and limitations", p. 603) — for our §7

1. **Floor/ceiling effects** limit sensitivity beyond CFG-2019 recommendations (see above).
2. **No absolute "good diet" threshold** — there is no known HEFI-2019 cut-off above which a pattern is "fully aligned." Authors recommend interpreting **relative** differences (between groups / over time) only. We must not present an absolute HEFI-2019 pass/fail line.
3. **Developed for 24-h recalls only** — application to FFQ or other instruments needs further research.
4. **Does not cover CFG-2019 "healthy eating habits" (the "how to eat" dimension, Guideline #3)** — only the "what to eat" food-choices dimension. A separate tool was under development for habits.

---

#### Scope notes worth keeping (for accurate implementation)

- **Fruit juice is excluded from Vegetables and fruits** (treated as a sugary drink in CFG-2019).
- **All potatoes (any preparation, including fried) count as vegetables** — a notable classification choice.
- **Processed meats** are NOT protein foods; they appear only in the *denominator* (total foods) of component #4.
- **Regular-fat (3.25 %) milk counts in the Beverages numerator** because the intent is reducing sugary drinks, and saturated fat is captured elsewhere.
- **Artificially sweetened beverages are excluded from the Beverages numerator** (no evidence of health benefit) and sit in the denominator.
- Whole-grain = "first ingredient is whole grain or whole wheat."

---

#### Three-sentence relevance note

B6 is the authoritative specification for the HEFI-2019 our nutrition module implements, and Table 2 (p. 600) plus Table A1 (pp. 606–609) together give the exact component ratios, point allocations, scoring thresholds, and food-classification rules our pipeline must encode literally. The construct-validity and Cronbach's α figures the wishlist asks for are NOT in this paper; they are in the companion evaluation paper (B7, apnm-2021-0416), which we still need to extract. Two implementation dependencies surface here that affect our data plan: HEFI-2019 requires Health Canada's Reference Amounts table and the Rana et al. 2021 free-sugars supplement to the CNF (J56), and the authors' explicit warning that there is no absolute "aligned-diet" threshold means our manuscript must frame HEFI-2019 results as relative comparisons across scenarios, never as a pass/fail nutritional verdict.

---

### B7. Brassard et al. (2022) — Evaluation of the HEFI-2019 [★★★]

**Citation.** Brassard D, Elvidge Munene LA, St-Pierre S, Gonzalez A, Guenther PM, Jessri M, Vena J, Olstad DL, Vatanparast H, Prowse R, Lemieux S, L'Abbe MR, Garriguet D, Kirkpatrick SI, Lamarche B. Evaluation of the Healthy Eating Food Index (HEFI)-2019 measuring adherence to Canada's Food Guide 2019 recommendations on healthy food choices. Appl Physiol Nutr Metab. 2022;47(5):582–594.

**DOI.** 10.1139/apnm-2021-0416

**⚠ Wishlist correction.** The wishlist lists B7 as "APNM 47(5), 611–624." The actual pagination is **582–594** (the evaluation paper precedes the development paper in the print issue; the development paper B6 is 595–610). Use 582–594 in the reference list. Note also an erratum was applied to the e-First version on 28 April 2022; the current online and print versions are identical and corrected.

**Type.** Companion evaluation paper to B6. This is the source of the construct-validity and reliability numbers the wishlist asks for. License CC BY 4.0.

---

#### The headline psychometrics (Abstract; Results pp. 585–589) — these are the numbers to cite

| Property | Value | Location |
|---|---|---|
| **Mean HEFI-2019 score** (Canadians ≥2 y, usual intake) | **43.1 / 80** (95 % CI 42.7–43.6) ≈ **53.9 %** | Abstract; p. 586; Discussion p. 588 |
| Median | 43.4 (95 % CI 42.9–43.9) | p. 586 |
| 1st percentile | 22.1 | p. 586; Table A2 |
| 99th percentile | 62.9 (= 78.6 %) | p. 586; Discussion p. 588 |
| **Cronbach's α (standardised)** | **0.66** (95 % CI 0.63–0.69) | Abstract; p. 587 |
| **Correlation with US HEI-2015** | **r = 0.79, r² = 0.62** | p. 586, Fig. 3 |
| Correlation with energy intake | **r = −0.13** (95 % CI −0.20 to −0.06) — weak, inverse | Abstract; p. 588, Table 4 |
| Dimensionality (PCA) | **at least 4 dimensions**; first 4 PCs explain 69 % of variance (PC1 = 27 %) | p. 586–587, Figs. A2–A3 |

**Interpretive framing the authors insist on (Conclusion p. 589):** the total score must always be reported alongside component scores, because the index is multidimensional. Our manuscript should do the same.

---

#### Validation dataset (Methods, "Study design and participants", p. 583) — pins down our J55 sample

- **2015 CCHS-Nutrition**, nationally representative of Canadians ≥1 y in private dwellings in the 10 provinces. **Excludes** full-time Canadian Forces members, Territories, reserves, remote areas, institutions.
- Data collected 1 Jan – 31 Dec 2015.
- Exclusions for this analysis: <2 y (n = 367) and zero-energy reporters (n = 8).
- **Final analytic sample: n = 20,103.** (Pregnant/lactating women, <1.5 % of participants, retained.)
- Public Use Microdata Files (PUMF). 24-h recall following Automated Multiple Pass Method; 96 % of first recalls in person, second recall (37 % of respondents) by phone. Proxy for ≤6 y, parent-assisted 6–11 y, direct ≥12 y.
- **This is the exact sample frame and exclusion logic our S4 meal panel must replicate** if we benchmark against national HEFI distributions. Cite n = 20,103 and the 2015 collection year.

---

#### Table A2 (p. 591) — national HEFI-2019 component and total score distribution. Reproduce as our benchmark

Means and percentiles, Canadians ≥2 y, usual intake (NCI multivariate method). This is the table our S4 panel scores should be compared against.

| Component (max) | Mean (SE) | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|---|---|---|
| Vegetables & fruits (20) | 9.3 (0.1) | 2.5 | 3.9 | 4.9 | 6.6 | 9.0 | 11.7 | 14.3 | 16.0 | 19.0 |
| Whole-grain foods (5) | 1.2 (0.0) | 0.0 | 0.1 | 0.3 | 0.6 | 1.1 | 1.6 | 2.2 | 2.6 | 3.5 |
| Grain foods ratio (5) | 1.3 (0.0) | 0.0 | 0.2 | 0.3 | 0.7 | 1.3 | 1.9 | 2.4 | 2.7 | 3.3 |
| Protein foods (5) | 4.5 (0.0) | 2.4 | 3.0 | 3.4 | 4.1 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| Plant-based protein (5) | 1.4 (0.0) | 0.0 | 0.1 | 0.2 | 0.5 | 1.2 | 2.0 | 3.0 | 3.5 | 4.6 |
| Beverages (10) | 7.5 (0.0) | 2.8 | 4.2 | 5.1 | 6.5 | 7.8 | 8.9 | 9.6 | 9.8 | 10.0 |
| Fatty acids ratio (5) | 2.2 (0.0) | 0.0 | 0.4 | 0.7 | 1.3 | 2.1 | 3.0 | 4.0 | 4.7 | 5.0 |
| Saturated fats (5) | 3.7 (0.0) | 0.0 | 0.5 | 1.4 | 2.7 | 4.1 | 5.0 | 5.0 | 5.0 | 5.0 |
| Free sugars (10) | 7.0 (0.1) | 0.0 | 0.0 | 0.6 | 4.6 | 8.4 | 10.0 | 10.0 | 10.0 | 10.0 |
| Sodium (10) | 5.0 (0.1) | 0.0 | 0.9 | 2.0 | 3.6 | 5.2 | 6.5 | 7.7 | 8.3 | 9.5 |
| **Total (80)** | **43.1 (0.2)** | 22.1 | 27.6 | 30.9 | 36.7 | 43.4 | 49.7 | 55.0 | 57.9 | 62.9 |

(The paper also provides Table A3 — by sex × age stratum, and Table A4 — by 14 DRI age-sex groups. Mean totals by stratum: 2–18 y = 39.5; males ≥19 y = 43.3; females ≥19 y = 46.0. If we stratify our panel by age-sex, those tables are the comparators; flag if needed and I can reproduce them in full.)

---

#### Construct-validity evidence (Results pp. 586–587)

1. **Discriminates known subgroups (Table 3, ≥19 y, population-ratio method):**
   - Females vs. males: **+3.1** points (95 % CI 2.0–4.1), driven mainly by Vegetables-and-fruits and Beverages.
   - 50–70 y vs. 19–30 y: **+6.5** points (95 % CI 5.0–8.1).
   - **Smokers vs. non-smokers: −7.2** points (95 % CI −8.5 to −5.9) — the largest contrast; total smoker mean 40.9 vs. non-smoker 48.1.
2. **Convergent validity with US HEI-2015:** r = 0.79, r² = 0.62 (Fig. 3); the 1st–99th percentile spread (22.1–62.9) mirrors the US HEI-2015 distribution.
3. **Independence from energy intake:** weak inverse r = −0.13. Component-level energy correlations (Table 4): strongest positive = Sodium (r = 0.23); strongest inverse = Beverages (r = −0.28), then Vegetables-and-fruits (r = −0.24). Authors recommend considering energy intake when comparing groups/trends.
4. **Multidimensionality (PCA, Figs. A2–A3):** ≥4 meaningful dimensions; PC1 (27 % variance) loads most on Vegetables-and-fruits, Grain foods ratio, Plant-based protein foods.
5. **A posteriori recipe check:** 3 days of CFG-2019 website recipes (standardised to 1800 kcal) scored **67.1 / 80** — 4.2 points above the population 99th percentile. Lowest component scores in those "ideal" menus: Plant-based protein (0.7/5), Fatty acids ratio (1.7/5), Whole-grain foods (4/5); perfect on Grain foods ratio, Protein foods, Beverages, Saturated fats, Free sugars.

---

#### Reliability / internal consistency (Results p. 587; Discussion p. 588)

- **Standardised Cronbach's α = 0.66** (95 % CI 0.63–0.69), just below the conventional 0.70 threshold. Authors argue this is expected given multidimensionality, only 10 components, a heterogeneous population (≥2 y), and a priori component inclusion regardless of statistical contribution. They note the **US HEI-2015 α is also 0.67** (NHANES 2011–2012) — i.e., comparable.
- **Component-to-residual-score correlations (Table 5):** range 0.02 (Sodium) to 0.51 (Vegetables-and-fruits). Protein foods (0.14) and Sodium (0.02) are the weakest contributors to internal consistency.
- Inter-component correlations of note (Table 5): Whole-grain foods ↔ Grain foods ratio = 0.83 (highest); Fatty acids ratio ↔ Saturated fats = 0.60; Beverages ↔ Free sugars = 0.49.

---

#### Score-distribution shape — confirms B6's ceiling/floor warning (Results p. 586; Discussion p. 588)

- **Skewed toward maximum (ceiling):** Protein foods, Saturated fats, Free sugars — because much of the population already meets these recommendations.
- **Skewed toward low scores (floor):** Whole-grain foods, Grain foods ratio, Plant-based protein foods.
- **Children (2–18 y) lowest overall (mean 39.5),** with particularly low Fatty acids ratio, Plant-based protein, and Free sugars components.

For our manuscript: when reporting HEFI-2019 across dietary scenarios, expect these three ceiling components to show little movement and these three floor components to carry most of the discriminating signal.

---

#### Statistical machinery (Methods pp. 583–585) — what our S4 pipeline must implement

- **Usual-intake modelling: NCI multivariate Markov-Chain Monte-Carlo method** (Zhang et al. 2011) — handles skewed, correlated, error-laden, zero-inflated dietary data; 500 simulated pseudo-individuals per respondent. Stratified into 3 groups (2–18 y both sexes; males ≥19 y; females ≥19 y), with DRI age-group covariates, recall-sequence and weekend indicators.
- **Episodically-consumed categories** (need zero-inflated handling): whole-grain foods, plant-based protein foods, and several beverage categories (sugary drinks, ASBs, juices, sweetened milk/plant beverages, alcohol, unsweetened milk, unsweetened soy). All other foods/nutrients treated as daily.
- **Subgroup means: population-ratio method** (Freedman et al. 2008) — less computationally intensive, valid for group means even with a single 24-h recall.
- **Variance: Balanced Repeated Replication** with 500 Statistics Canada bootstrap weights. Software: SAS Studio v3.8 + R v3.6.2.
- **Critical caveat (Discussion p. 588):** a single individual HEFI-2019 from one 24-h recall does NOT reflect usual adherence and must be interpreted with great caution; usual-intake or population-ratio methods are required for "usual" or population scores. Individual-level assessment needs ≥2 recall days.

---

#### Author-flagged limitations (Discussion pp. 588–589) — for our §7

1. **Input-data dependence:** HEFI-2019 inherits the random and systematic error of the dietary intake data (though 24-h recalls are less biased than FFQs/screeners).
2. **Sensitivity to change over time not assessed** — CCHS-Nutrition 2015 is cross-sectional.
3. **Validity for pregnant women, special-diet populations, and clinical settings not established** (CFG-2019 and HEFI-2019 are not designed for special needs).
4. **No demonstrated link to health outcomes yet** — the association between HEFI-2019 and disease endpoints remained undetermined as of 2022. (Important: this is the gap that distinguishes a guideline-adherence index like HEFI from a disease-burden index like HENI in group C; our manuscript should not treat HEFI-2019 as a health-outcome predictor.)
5. **No absolute "healthy" threshold** (reiterated from B6): a target score above which a diet "meets the majority of CFG recommendations" remains to be determined; the low 99th percentile (62.9/80) suggests full adherence is hard to achieve.
6. **FFQ/food-record applicability** needs further research.
7. **Future scoring revisions possible** to improve discrimination on floor/ceiling components — but the authors caution that modified standards may no longer map cleanly to specific CFG-2019 recommendations.

---

#### Three-sentence relevance note

B7 supplies the psychometric numbers the wishlist requested for our §3.2 implementation citation: standardised Cronbach's α = 0.66 (95 % CI 0.63–0.69), strong convergent validity with the US HEI-2015 (r = 0.79, r² = 0.62), weak independence from energy intake (r = −0.13), and a multidimensional structure (≥4 PCA dimensions). It also fixes the national benchmark our S4 meal panel should be scored against — mean HEFI-2019 = 43.1/80 (≈ 53.9 %) with the full component percentile distribution in Table A2 (p. 591) — and pins down the validation sample (2015 CCHS-Nutrition PUMF, n = 20,103, ≥2 y) and the exact usual-intake machinery (NCI multivariate method, population-ratio method for subgroup means, BRR bootstrap) we must reproduce. Two cautions carry into our manuscript: a single one-day HEFI-2019 score is not interpretable as usual adherence, and HEFI-2019 was not validated against health outcomes, so it must be presented as a guideline-adherence measure distinct from the disease-burden (HENI/DALY) indices in group C, with both total and component scores always reported together.

---

### B8. Hutchinson et al. (2023) — Canadian Food Intake Screener: scoring system and construct validity [★★★]

**Citation.** Hutchinson JM, Dodd KW, Guenther PM, Lamarche B, Haines J, Wallace A, Perreault M, Williams TE, da Costa Louzada ML, Jessri M, Lemieux S, Olstad DL, Prowse R, Randall Simpson J, Vena JE, Szajbely K, Kirkpatrick SI. The Canadian Food Intake Screener for assessing alignment of adults' dietary intake with the 2019 Canada's Food Guide healthy food choices recommendations: scoring system and construct validity. Appl Physiol Nutr Metab. 2023;48(5):620–633.

**DOI.** 10.1139/apnm-2023-0018

**⚠ Wishlist correction.** The wishlist lists B8 as "Lamarche, B., Brassard, D., et al. (2023)." The correct lead author is **Hutchinson JM** (Lamarche is a co-author; Brassard is not an author of this paper, only acknowledged). Pages are **620–633**, vol. 48. There is also a separate companion development paper: Hutchinson et al. 2023, apnm-2023-0019 (the cognitive-testing / face-validity paper), which we do NOT have.

**Type.** Construct-validity and scoring paper for a brief screener. Open access, CC BY 4.0. Data collection Jul–Dec 2021. Code in Supplementary Files S4/S5; screener instrument in Supplementary File S1.

---

#### What the screener is (Introduction; Methods, pp. 621–624)

- **16-question, self-administered, ~5-minute** dietary screener, English and French, for adults **18–65 y** with marginal-or-higher health literacy.
- Assesses **frequency** of intake over the **past month** ("Over the past month, how often did you eat…") of healthy foods and foods-to-limit. **Frequency-based, NOT density-based** — this is the key contrast with HEFI-2019 (B6/B7).
- Designed to give a **single total score** signalling overall alignment with CFG-2019 healthy-food-choices recommendations when full 24-h recalls are not feasible.
- 10 ordinal response options per question (never → ≥6×/day), scored 0–9; healthy foods scored positively, foods-to-limit reverse-scored.

---

#### Table 1 (p. 624) — the screener scoring system. 8 components, max 65 points

| Component | Screener question(s) | Scoring | Max pts | Min-score (0) standard | Max-score standard |
|---|---|---|---|---|---|
| Vegetables and fruits | vegetables + potato + fruits | each 0–9, summed (/27) | 20 | never consuming any | each item ≥6×/day |
| Whole-grain foods | whole-grain foods | 0–9 | 5 | never | ≥6×/day |
| Grain foods ratio | whole-grain / total grain foods | ratio of frequencies | 5 | never whole-grain | ratio = 1.0 |
| Protein foods | plant protein + yogurt/cheese/kefir + animal protein + unsweetened milk | each 0–9, summed (/36) | 5 | never | each item ≥6×/day |
| Plant-based protein foods | plant protein / total protein foods | ratio of frequencies | 5 | never plant protein | ratio = 1.0 |
| Unsaturated oils | margarine + vegetable oils | 0–9 | 5 | never | ≥6×/day |
| Foods & beverages high in sugars | sweetened milk + sweetened beverages + sugary snacks | reverse-scored 0–9, summed (/27) | 10 | each item ≥6×/day | never |
| Foods high in sodium / saturated fat | fast food + processed meat + salty snacks | reverse-scored 0–9, summed (/27) | 10 | each item ≥6×/day | never |
| **Total** | | | **65** | | |

**Weighting deliberately mirrors HEFI-2019:** V&F = 20 (same as HEFI); the V&F / grain / protein weights track the CFG-2019 plate proportions (50 % / 25 % / 25 %); foods-to-limit total 20/65 = **31 %**, matching HEFI-2019's 25/80 = **31 %**. No upper frequency cap for healthy foods (consistent with CFG-2019's non-quantitative guidance).

**Critical caveat (p. 625):** screener "component" scores are derived ONLY to compute the total and **must not be interpreted individually** — each rests on one or a few questions insufficient to quantify a food group. Only the total screener score is meaningful.

---

#### Key differences from HEFI-2019 (Discussion p. 629) — important for our pipeline

1. **No Beverages component** — the screener does not assess water consumption, so HEFI-2019's beverages component has no analogue.
2. **Frequency vs. quantification** — the screener captures frequency of key sources of added sugars, saturated fat, and sodium; HEFI-2019 quantifies free sugars, saturated/unsaturated fat, and sodium.
3. **8 components / 65 points vs. HEFI-2019's 10 components / 80 points.**
4. Screener uses **"added/total sugars" framing**, HEFI-2019 uses **free sugars** specifically.

So the screener is a coarse, low-burden proxy; it is NOT a substitute for HEFI-2019 where component-level or quantitative resolution is needed.

---

#### Construct-validity results (Results pp. 625–626; Tables 2–3)

- **Sample: n = 154** adults (after removing 845 bogus/bot responses and 485 ineligible from 1,484 eligibility completions). 95 English, 59 French. 74 % women, 24.7 % men; 60 % White; skewed toward higher income adequacy and health literacy.
- **24-h recalls (ASA24-Canada-2018):** 132 completed recall 1, 105 completed recall 2; after dietitian cleaning, **128 first recalls (83 %) and 102 second recalls (66 %)** used. Recalls spread ~1 month apart to match screener window.
- **Mean screener score = 35.0 / 65 (SD 4.7)**, range 25.1 (p1) to 45.2 (p99). The low 99th percentile (45/65 = 69 %) indicates substantial room for improvement, paralleling HEFI-2019's low ceiling.
- **Correlation screener ↔ total HEFI-2019: r = 0.53 (SE 0.12)** — "moderately strong"; total screener explains **28 % (SE 12 %)** of HEFI-2019 variance. This is in line with other validated screeners (Mediterranean Diet Adherence Screener r = 0.52; Dutch screener τ-b = 0.51).
- **Correlation screener ↔ usual energy intake = 0.08 (SE 0.09)** — no meaningful association; higher scores are NOT just an artefact of eating more. (But authors caution self-report energy error makes this hard to detect.)
- **Mean HEFI-2019 in this sample = 40.9 / 80 (SE 1.2)**, range 25.9 (p1) to 56.0 (p99) — lower than the 2015 CCHS-Nutrition national mean of 43.1 (B7), and a lower 99th percentile (56 vs. 63).
- **Component scores (vs. total) explain 53 % (SE 9.9 %) of HEFI-2019 variance** — suggesting the scoring algorithm could be optimised further (though added predictors inflate R² by construction).

**Subgroup contrasts (Table 3, ANOVA):** differences in hypothesised directions for smoking (**p = 0.003**; non-smokers 35.4 vs. smokers 30.5, a 5-point gap — the largest), education (**p = 0.02**), gender (p = 0.06; women 35.4 vs. men 33.8), income adequacy (p = 0.07). **No** difference by age (p = 0.88) or health literacy (p = 0.22).

---

#### Statistical method (Methods pp. 625–626)

- **NCI multivariate MCMC method** (Zhang et al. 2011) with the **screener score as a covariate**, jointly modelling HEFI-2019 numerators/denominators; episodically-consumed categories (whole/non-whole grains, animal/plant protein, beverages, "other") flagged at the ≥5 %-of-recalls-zero threshold (Krebs-Smith et al. 2010). Covariates: screener score, gender, age, recall sequence, weekday/weekend.
- Correlation computed as √R² from linear regression (screener → HEFI-2019). Standard errors via **bootstrap, 200 replicates**. SAS 9.4.
- ASA24 auto-codes to the **2015 Canadian Nutrient File** + Health Canada surveillance recipe database; US food codes substituted when no Canadian match (with fortification adjustment).

---

#### Author-flagged limitations (Discussion pp. 628–630) — for our §7

1. **Moderate, not strong, validity** (r = 0.53). The screener is a rapid proxy, explicitly NOT a replacement for 24-h recalls; it should not replace 24HDR collection in CCHS nutrition cycles.
2. **No "healthy-diet" threshold** — as with HEFI-2019, there is no screener cutoff indicating CFG-2019 adherence. Scores can be categorised for knowledge-translation (above/below sample mean) but **should not be categorised for analysis** (information loss, misclassification).
3. **Correlation may be over-estimated** due to correlated errors between screener and 24HDR (both self-report).
4. **Sample skew** toward women, higher income, higher health literacy; smaller-than-target recall subset reduces precision.
5. **Sensitivity to change over time not assessed**; intervention-evaluation use needs care (reporting reactivity).
6. **Component scores not individually interpretable** (reiterated).
7. Built/validated for **adults 18–65 only**; youth/older-adult adaptation needs separate work.
8. **Efficiency note worth citing:** cleaning recalls and preparing HEFI-2019 variables in this study took **>75 h of registered-dietitian time** — a concrete illustration of why automated nutrient-scoring pipelines (like ours) have value, and why a 5-minute screener exists at all.

---

#### Three-sentence relevance note

B8 documents a low-burden, frequency-based alternative to HEFI-2019 (8 components, 65 points, deliberately weighted to match HEFI-2019 and the CFG-2019 plate) that correlates moderately with full HEFI-2019 (r = 0.53, 28 % of variance) and is essentially independent of energy intake (r = 0.08); it is relevant to our project only as a rapid-assessment proxy and a cautionary contrast, not as a scoring target, since it omits the beverages component and replaces quantification with frequency. The paper reinforces three points already flagged for HEFI-2019: there is no absolute "healthy-diet" threshold, scores should not be categorised for analysis, and single-instrument self-report carries correlated error. Its most directly useful nugget for our manuscript framing is the explicit >75-hour dietitian cost of manually preparing HEFI-2019 inputs from recalls, which motivates the automated recipe-to-nutrition scoring our pipeline performs; we should cite Hutchinson et al. 2023 (apnm-2023-0018, pp. 620–633) with the corrected authorship if we discuss screener-based rapid assessment as a complement to full HEFI-2019 scoring.

---

### B9. Mozaffarian, El-Abbadi et al. (2021) — Food Compass: the founding nutrient profiling system [★★★]

**Citation.** Mozaffarian D, El-Abbadi NH, O'Hearn M, Marino J, Masters WA, Jacques P, Shi P, Blumberg J, Micha R. Food Compass is a nutrient profiling system using expanded characteristics for assessing healthfulness of foods. Nat Food. 2021;2(10):809–818.

**DOI.** 10.1038/s43016-021-00381-y

**Source fetched.** Supplementary Information only (123 pp.), the version "in the format provided by the authors and unedited." This contains the full attribute-scoring algorithm (Table S3), worked examples (Table S4, Text S2), the score distribution by food group (Table S5), the cross-NPS comparison (Table S1), and the per-food crosswalk of FCS against Health Star Rating, Nutri-Score and NOVA for all 8,032 items (Table S7). **The main-article text is not in this PDF.** The headline narrative, the recommended interpretation cut-offs, and the health-outcome framing live in the main paper (and the validation against mortality is a separate paper, B11).

**Type.** Methodology paper introducing the original Food Compass Score (FCS). This is the founding reference that B10 (Food Compass 2.0, 2024) revises, B11 (O'Hearn et al. 2022) validates against health and mortality, and B12 (FCS-10, 2025) simplifies for label-only use. Extensive author food-industry ties (same Mozaffarian/Blumberg conflicts noted under B10–B12).

---

#### The scoring algorithm (Table S3, pp. 9–12) — the core of why we hold this entry

Food Compass scores every food on a common per-100-kcal basis (100 kcal = 418.4 kJ) across **54 attributes grouped into 9 domains**:

| # | Domain | Attributes | Scoring detail |
|---|---|---|---|
| 1 | Nutrient Ratios | 3 | Unsaturated:saturated fat, fiber:carbohydrate, potassium:sodium, each log-linear from −10 to +10 (anchored at 5th/95th percentile). Ratios suppressed where the relevant macronutrient is <10 % of energy. |
| 2 | Vitamins | 12 listed, **top 5 used** | Each 0 to 10, linear, target = 25 % RDA/AI. Only the 5 highest-magnitude attribute scores enter the domain average. |
| 3 | Minerals | 10 listed, **top 5 used** | Each 0 to 10 (sodium −10 to 0), target = 25 % RDA. Top-5 rule as for vitamins. |
| 4 | Food Ingredients | 10 | Healthful ingredients 0 to 10, harmful (refined grains, red/processed meat) −10 to 0, anchored at 95th percentile. **Summed, not averaged**, because ingredient contents are interdependent. |
| 5 | Additives | 7 | Added sugar (nonlinear −10 to 0), nitrites, plus 5 artificial additives. Added sugar and nitrites get full weight; the other 5 additives get half weight each. |
| 6 | Processing | 3 | NOVA level scored −10 / −5 / −2.5 / 0 (full weight), fermentation and frying half weight each. |
| 7 | Specific Lipids | 5 listed, **top 3 used** | Cholesterol and trans fats −10 to 0; MCFAs, ALA, EPA+DHA 0 to 10. |
| 8 | Fiber & Protein | 2 | Total fiber and total protein, each 0 to 10, target 25 % AI/RDA. |
| 9 | Phytochemicals | 2 | Total flavonoids and total carotenoids, each 0 to 10, anchored at 95th percentile. |

**Domain aggregation and final scaling (Table S3 footnote *).** Each domain score is the average of its attribute scores (or the sum, for Food Ingredients). The 9 domain scores are then summed, with **half-weights applied to Specific Lipids, Fiber & Protein, and Phytochemicals**. The summed score is truncated at the 5th and 95th percentiles across the 8,032 NHANES 2015–16 items (−10.7 and 26.1) and rescaled to a 1 (least healthful) to 100 (most healthful) scale:

$$\text{FCS} = 100 - \left( \frac{26.1 - \text{original score}}{36.7} \right) \times 99$$

**Reference-value rule (footnote †).** Where Dietary Reference Intakes vary by subgroup, the value for adults aged 19–50 (and for men where sex-varying) is used. The 25 % DRI threshold was found to be the most consistent discriminator and is close to the 95th-percentile content across all NHANES items. The authors explicitly flag as an open question whether scoring should stay fixed for other datasets and nations or be re-anchored to local food items, which is directly relevant to our Canadian and French food sets and belongs in §7.

---

#### Score distribution by food group (Table S5, p. 14) — discrimination evidence

Across 8,032 unique foods and beverages, overall **mean FCS 43.2 (SD 28.5), range 1.0 to 100.0, median 39.3**. Group means (n, mean) show the system separates broad categories in the expected direction:

- Highest: Legumes/Nuts/Seeds (264, 78.6), Fruits (264, 73.9), Vegetables (1565, 69.1), Fish and Seafood (434, 67.0).
- Lowest: Savory Snacks & Sweet Desserts (1000, **16.4**), Fats & Oils (129, 29.7), Mixed Dishes (2206, 33.1), Meat/Poultry/Eggs (763, 32.7), Grains (727, 33.8).
- Mid: Dairy (245, 43.1), Sauce/Condiment (160, 42.2), Beverages (275, 35.3).

The wide within-group spread (e.g. Vegetables span 1.1 to 100) is the headline selling point of a continuous NPS over categorical labels, and is the same property our platform exploits when scoring recipe-level rather than category-level items.

**Recommended interpretation cut-offs.** The supplement does not restate them, but the established Food Compass cut-offs (defined in the main paper and used in B11) are **FCS ≥ 70 = encourage, 31–69 = consume in moderation, ≤ 30 = minimize**. Cite the main article for these, not this supplement.

---

#### Cross-NPS positioning (Table S1, p. 3; Table S7, pp. 16+)

Table S1 contrasts Food Compass with 7 exemplar systems (Guiding Stars, Nutri-Score, Health Star Rating, Nordic Keyhole, Singapore Healthier Choice, Waqeya, Nestlé NPS). The framing claim is that the comparators apply **inconsistent attributes across 4 to 33 food categories** and assess relatively few unique attributes (roughly 7 to 11 for the numeric/categorical systems, e.g. HSR and Nutri-Score each 7), whereas Food Compass applies one consistent 54-attribute algorithm to all foods. Notably, the analyses used the **updated 2020 Health Star Rating** (the same algorithm documented in B13) and treated all foods as consumed rather than as packaged.

Table S7 provides the raw per-item crosswalk of FCS against HSR, Nutri-Score and NOVA for all 8,032 foods. The concordance statistics themselves (correlations, the 2.0-vs-1.0 shifts) are computed in B10, not here, but this table is the underlying data and the worked sweet-potato-chips-versus-bulgur example (Text S2: both score 69) illustrates the intended finer-grained discrimination.

---

#### Author-flagged limitations and open questions — for our §7

1. **US-anchored.** Scoring thresholds and percentile anchors derive from NHANES 2015–16; portability to non-US food supplies is explicitly left open (footnote †), the same caveat carried by B10–B12 and important for our Canadian/French sets.
2. **Attributes not always scorable.** In FNDDS, 7 of 54 attributes could not be scored (iodine, trans fat, and 5 artificial additives), so NHANES scoring used **47 of 54 attributes** (Text S1); flavonoids for 2,400 foods were imputed from subcategory averages across 150 WWEIA groups. This is a concrete precedent for attribute imputation and a caution that "Food Compass" in practice is often a 47-attribute approximation.
3. **As-consumed vs. as-purchased.** Most comparator NPS score packaged foods; Food Compass and its validation score foods as consumed, which matters for recipe-level work like ours.
4. **Top-5 / top-3 selection** for vitamins, minerals and specific lipids is a deliberate discrimination choice that limits the influence of fortification but means the domain score ignores most measured nutrients in nutrient-rich foods; worth noting if we reproduce the algorithm exactly.

---

#### Three-sentence relevance note

B9 is the founding Food Compass paper and the source of the exact scoring machinery our pipeline reproduces when FCS is one of the §3.2 indicators: 54 attributes across 9 domains scored per 100 kcal, domain scores averaged (summed for food ingredients) and combined with half-weights on specific lipids, fiber and protein, and phytochemicals, then truncated at the 5th/95th percentile and rescaled to 1–100 via FCS = 100 − ((26.1 − score)/36.7)×99. The supplement supplies the complete Table S3 algorithm, the by-food-group distribution (overall mean 43.2, with Savory Snacks/Desserts at 16.4 and Legumes/Nuts/Seeds at 78.6 demonstrating discrimination), and the raw FCS/HSR/Nutri-Score/NOVA crosswalk for 8,032 foods, while the recommended ≥70 / 31–69 / ≤30 cut-offs and the health-outcome validation must be cited from the main paper and from B11 respectively. The most important caveats for our §7 are that practical scoring used only 47 of 54 attributes in FNDDS and that all thresholds are US-anchored with the authors themselves flagging re-anchoring for other nations as unresolved; cite as Mozaffarian et al. 2021, Nat Food 2(10):809–818, doi:10.1038/s43016-021-00381-y.

---

### B10. Barrett, Mozaffarian et al. (2024) — Food Compass 2.0 [★★★]

**Citation.** Barrett EM, Shi P, Blumberg JB, O'Hearn M, Micha R, Mozaffarian D. Food Compass 2.0 is an improved nutrient profiling system to characterize healthfulness of foods and beverages. Nat Food. 2024;5(11):911–915.

**DOI.** 10.1038/s43016-024-01053-3

**⚠ Wishlist correction.** The wishlist lists B10 as "Mozaffarian, D., et al. (2024)." The correct lead author is **Eden M. Barrett** (Mozaffarian is senior/corresponding-adjacent last author). Type: Brief Communication, Nature Food, open access (CC BY 4.0). Published online 8 October 2024; print November 2024.

**Related papers in this set:** the original Food Compass (B9, ref. 4 here) = Mozaffarian D, et al. Nat Food. 2021;2:809–818 — NOT yet extracted. The mortality-validation paper (B11, ref. 5 here) = O'Hearn M, et al. Nat Commun. 2022;13:7066 — NOT yet extracted. FCS-10 (B12) = a 2025 AJCN paper — NOT yet extracted.

---

#### What Food Compass is (Introduction, p. 911)

A **nutrient profiling system (NPS)** that scores the healthfulness of foods, beverages, AND mixed meals on a **single continuous scale of 1 (least healthy) to 100 (most healthy)**, computed **per 100 kcal** (not per 100 g — explicitly to avoid water-content confounding). It aggregates **9 holistic domains** of product characteristics: nutrient ratios (fat, carbohydrate, mineral quality), food ingredients of greatest health relevance, food processing, phytonutrients, and additives. This is the design contrast with HEFI-2019 (which scores guideline *adherence* of a whole diet, per energy/RA ratios) and with the disease-burden indices in Group C.

**Recommended interpretive cut-offs (Methods, p. 914; carried from the 2021 original):**
- **FCS ≥ 70** → foods to be encouraged
- **FCS 31–69** → foods to be consumed in moderation
- **FCS ≤ 30** → foods to be minimized

Scores can also be used continuously; cut-offs are for when strict thresholds are needed.

---

#### What changed in 2.0 vs. the 2021 original (Methods p. 914; text p. 913) — for §3.2 version control

Five key updates:
1. **Broader discrimination for food processing** — and, importantly, 2.0 now gives **positive points for non-ultraprocessed foods**, rather than only negative points for ultraprocessed foods.
2. **Added sugar included as a food ingredient** (in the food-ingredients domain), not only as an additive — reflecting evidence of harm beyond its additive role.
3. **Higher scoring weight for dietary fibre** (positive attribute).
4. **Lower scoring weight for dairy fat** (negative attribute) — reflecting evidence of relatively neutral dairy-fat effects.
5. **New additive data (e.g. artificial sweeteners)** — these were attributes in the 2021 algorithm but previously unscored for lack of data; now scored, lowering scores of highly processed multi-additive foods.

Other updates: neutral scoring for fruit/vegetable juice as a food ingredient; greater weight for long-chain omega-3 vs. other lipids.

**Net direction:** 2.0 raises scores for minimally processed animal foods (seafood, dairy, meat, poultry, eggs) and lowers scores for processed cereals, beverages, flavoured yogurts, and processed plant-based meat/dairy/egg alternatives. **~90 % of products changed by ≤10 points** (framework is stable).

---

#### Score shifts by subgroup (text p. 911; Fig. 1) — useful if our manuscript discusses NPS sensitivity

Notable mean ± SD changes from original → 2.0:
- **Increases:** beef 33±6 → 44±6; pork 35±8 → 44±9; seafood 72±14 → 81±14; lamb & game 39±8 → 49±8; eggs 46±13 → 54±13; rice & pasta 43±26 → 49±23.
- **Declines:** cold cereals 51±21 → 41±20; plant-based dairy 54±21 → 43±20; cereal bars 42±16 → 34±15; fruit & vegetable juices 72±15 → 66±14.

Overall distribution (n = 9,273 items): **23 % score ≥70, 46 % score 31–69, 31 % score ≤30** (original was 22 % / 46 % / 33 %).

Within-category illustration of granularity: whole egg fried without fat 48 → 62, but egg substitute 50 → 45; blueberries FCS 100 vs. white rice FCS 23 (both NOVA-1).

---

#### Discrimination vs. other NPSs (text pp. 912–913; Fig. 2)

Food Compass 2.0 overlaps with but meaningfully discriminates against HSR (our B13 target), Nutri-Score, and NOVA:
- Among highest-HSR (5.0) products, 82 % had FCS ≥70 — but range 100 (chia seeds) to 10 (fat-free margarine).
- Among NOVA-1 products, 49 % had FCS ≥70 — but range 100 (raw blackberries) to 12 (rice noodles).
- Concordance improved in 2.0 for grains (FCS↔NOVA r 0.07 → 0.31; FCS↔HSR 0.27 → 0.42) and dairy (FCS↔NOVA 0.31 → 0.58); decreased for fats/oils (0.47 → 0.36).
- Nutri-Score ↔ HSR correlation is high (r = 0.83).

**Fig. 2 distribution by major group** (% ≤30 / 31–69 / ≥70), worth keeping as a comparator table: Beverages 54.0 / 32.3 / 13.7; Grains 46.0 / 48.3 / 5.8; Fruit 3.3 / 43.8 / 52.9; Vegetables 2.0 / 34.7 / 63.2; Legumes 0.9 / 19.3 / 79.7; Nuts 1.0 / 10.0 / 89.0; Meat 45.9 / 52.2 / 1.9; Poultry 8.7 / 91.0 / 0.3; Eggs 6.1 / 88.6 / 5.3; Seafood 0.3 / 17.9 / 81.8; Dairy 19.1 / 73.0 / 7.8; Plant oils 53.7 / 30.6 / 15.7; Dairy/animal fats 91.5 / 8.5 / 0; Mixed dishes 29.2 / 58.5 / 12.3; Sauces/condiments 31.6 / 41.8 / 26.5; Savoury snacks & sweet desserts 79.1 / 20.0 / 0.8; Overall 31.3 / 45.6 / 23.1.

---

#### Health-outcome validation — the i.FCS results (text p. 913) — this is what makes Food Compass a *validated* NPS

The individual-level diet score **i.FCS** is the **energy-weighted average FCS** of all foods/beverages a person consumes.

- **Validation cohort: nationally representative US adults from NHANES 1999–2018.** ⚠ **Sample-size discrepancy in the paper:** main text (p. 913) says **n = 47,099**; the Reporting Summary (p. 7) says **n = 47,999**. Cite cautiously — likely a typo in one location; verify against the published correction/supplement if we use the exact n.
- **Mean i.FCS = 36.6 ± 10.8** (a "relatively poor average diet").
- **i.FCS ↔ HEI-2015: r = 0.78** — strong convergent validity against a validated healthy-diet measure. (Compare: HEFI-2019 ↔ HEI-2015 was r = 0.79 in B7. The three indices converge.)
- **Per 1 SD (10.8 points) higher i.FCS, after multivariable adjustment** (Supplementary Table 7):
  - BMI −0.56 kg/m² (95 % CI −0.65, −0.47)
  - Systolic BP −0.55 mmHg (−0.77, −0.34); Diastolic BP −0.46 mmHg (−0.63, −0.29)
  - LDL-C −1.49 mg/dL (−2.10, −0.87); HDL-C +1.61 mg/dL (1.41, 1.81); TC:HDL ratio −0.12 (−0.13, −0.10)
  - HbA1c −0.02 % (−0.02, −0.01); fasting plasma glucose −0.36 mg/dL (−0.67, −0.05)
  - Metabolic syndrome OR 0.86 (0.83, 0.89); CVD OR 0.92 (0.88, 0.96); cancer OR 0.93 (0.89, 0.98); lung disease OR 0.90 (0.87, 0.94); optimal cardiometabolic health OR 1.22 (1.14, 1.30)
- **All-cause mortality:** per 1 SD HR 0.92 (0.88, 0.95); **highest vs. lowest i.FCS quintile HR 0.76 (0.68, 0.84) — 24 % lower risk** (Supplementary Table 8).

This health-outcome validation is the key reason Food Compass can be cited as more than a guideline-adherence index — unlike HEFI-2019 (B7), which was explicitly NOT validated against health outcomes.

---

#### Data sources and reproducibility (Methods p. 914; Data availability)

- **Algorithm fully specified in Supplementary Tables 9 & 10** (attribute → domain → overall FCS scoring). The 2021 paper (B9) plus these supplements allow full reproduction.
- **⚠ Code is NOT publicly available** — Tufts is considering commercial licensing. The authors state there are no IP/patent protections and the *algorithm* can be freely reproduced by anyone, but the *implementation code* is withheld. Implication for our pipeline: if we implement Food Compass, we must build from the published Supplementary Tables, not from author code.
- **Underlying data (all public):** USDA FNDDS 2001–2018 (nutrient composition); USDA FPED 2001–2018 (food ingredients / pattern equivalents); USDA Flavonoid Database 2007–2010; NHANES 1999–2018; National Death Index 1999–2018. HSR via the official Australian calculator; Nutri-Score via the 2023 updated algorithm (Merz et al. Nat Food 2024, ref. 14).
- **Item-scoring exclusions:** infant formula, baby foods, specialized dietary foods, alcohol, and products <5 kcal/100 g are NOT scored by Food Compass (Reporting Summary p. 7).
- **i.FCS analytic exclusions:** no valid dietary recall (n = 7,434), extreme energy (<500 or >5,000 kcal/d, n = 704), alcohol-only intake (n = 3), missing smoking status (n = 34), and (for mortality) no linked mortality data (n = 81).
- Software: R 4.3.1 + Stata SE 18.0; two-tailed α = 0.05.

**International portability:** validated already in Greece, Korea, and China; regional adaptations under development.

---

#### Limitations and cautions (for our §7)

1. **US-centric construction and validation** (NHANES/FNDDS/FPED). Direct transfer to Canadian or French food supplies (our S2/S4) would require re-mapping to CNF / Ciqual and possibly regional re-parameterisation — the authors note adaptation is needed.
2. **Per-100-kcal basis** differs from AGRIBALYSE (per kg) and from HEFI-2019 (per-energy and per-RA ratios) — unit reconciliation is required if Food Compass is run alongside either.
3. **Code withheld** (commercial licensing under consideration) — only the algorithm tables are open.
4. **Brief Communication** — most methodological detail and all attribute weights live in the supplements (Tables 1, 9, 10), which we do not yet have extracted; flag if we decide to implement Food Compass and I can pull the supplement.
5. **Conflicts of interest:** D. Mozaffarian reports extensive food-industry scientific-advisory and equity relationships; J. Blumberg reports fees from Guiding Stars Licensing. Worth noting given Food Compass's policy/commercial positioning.

---

#### Three-sentence relevance note

B10 is the current reference specification for the Food Compass nutrient profiling system (FCS, scale 1–100, per 100 kcal, 9 domains, cut-offs ≥70 / 31–69 / ≤30), the candidate NPS our project could implement as a per-item healthfulness score complementary to the diet-level HEFI-2019; its defining advantage over HEFI is health-outcome validation (i.FCS ↔ HEI-2015 r = 0.78; 24 % lower mortality in the top vs. bottom quintile), making it citable as a validated healthfulness metric rather than a mere guideline-adherence index. Two practical constraints matter for implementation: the scoring algorithm is openly published only in Supplementary Tables 9–10 (the code is withheld pending Tufts licensing), and the system is built and validated on US NHANES/FNDDS data, so applying it to our Canadian (CNF) or French (Ciqual/AGRIBALYSE) food sets would require explicit re-mapping and possibly regional re-parameterisation. Note for the reference list: lead author is Barrett (not Mozaffarian), pages 911–915, and there is an unresolved n = 47,099 vs. 47,999 discrepancy between the main text and the reporting summary that we should verify before quoting the exact validation sample size; the original Food Compass (B9, 2021), the O'Hearn mortality-validation paper (B11, 2022), and FCS-10 (B12, 2025) remain to be extracted to complete this sub-cluster.

---

### B11. O'Hearn, Mozaffarian et al. (2022) — Validation of Food Compass against health and mortality [★★★]

**Citation.** O'Hearn M, Erndt-Marino J, Gerber S, Lauren BN, Economos C, Wong JB, Blumberg JB, Mozaffarian D. Validation of Food Compass with a healthy diet, cardiometabolic health, and mortality among U.S. adults, 1999–2018. Nat Commun. 2022;13:7066.

**DOI.** 10.1038/s41467-022-34195-8

**⚠ Wishlist correction.** The wishlist lists B11 as "Mozaffarian, D., et al. (2022)." The correct lead author is **Meghan O'Hearn** (Mozaffarian is senior/last author). Open access, CC BY 4.0. Published 22 November 2022.

**Critical version note.** This paper validates the **original (2021) Food Compass** algorithm (the B9 reference, Mozaffarian et al. Nat Food 2021;2:809–818). The numbers here therefore differ slightly from the **Food Compass 2.0** revalidation in B10 (Barrett et al. 2024). When citing i.FCS validation, state which version: original (this paper) vs. 2.0 (B10). Same NHANES dataset underlies both.

---

#### What it validates (Abstract; Introduction pp. 1–2)

Establishes the **construct validity** of the original Food Compass at the *individual diet* level (not just the product level the 2021 paper covered) against three endpoints: (a) HEI-2015 (a validated healthy-diet pattern), (b) clinical risk factors and prevalent conditions, and (c) prospective all-cause mortality. Confirms that extending per-product FCS to a person's whole diet (i.FCS) yields a score that tracks diet quality and predicts health.

**Food Compass design recap (Methods pp. 9–11):** **54 attributes across 9 domains** — nutrient ratios, vitamins, minerals, food ingredients, additives, processing, specific lipids, fibre & protein, phytochemicals. Each attribute scored 0 to 10 (beneficial), −10 to 0 (harmful), or −10 to 10 (ratios); domain = average of its attributes (food-ingredients domain = sum); the last three domains (specific lipids, fibre & protein, phytochemicals) get **half weight**; summed and rescaled to **1–100**. Cut-offs ≥70 / 31–69 / ≤30 as in B10. **Per 100 kcal**, not per gram (avoids water-weight bias).

---

#### i.FCS construction (Methods p. 11)

**i.FCS = energy-weighted mean of the FCS of every food/beverage a person consumed**, weighted by each item's percent contribution to total energy, summed; theoretical range 1–100. **Alcohol energy is excluded** from the i.FCS (alcohol is unscored by FCS) and entered as a model covariate. Same energy-weighting method used to derive the 9 i.Domain scores separately (these were NOT used to build i.FCS — derived independently for the domain analysis).

---

#### Validation cohort (Results p. 2; Methods p. 9)

- **n = 47,999 US adults aged 20–85**, 10 NHANES cycles 1999–2000 through 2017–2018. (This is the same value the B10 reporting summary used; B10's main text said 47,099 — so **47,999 is the correct figure**, and B10's "47,099" is the typo.)
- Mortality analysis: **47,918** (81 excluded for no NDI linkage).
- Up to two 24-h recalls per person (second added for ~87 % from 2003–04 on), averaged.
- Mean age 47.2 y (SD 17.1); 52.2 % female; 27.8 % ≥college; mean BMI 28.8 (overweight); mean HEI-2015 = 57.3 (8.5).
- Population disease burden: 42.0 % metabolic syndrome, 12.9 % diabetes, 7.7 % CVD, 18.9 % lung disease, 9.8 % cancer; only 7.4 % optimal cardiometabolic health.

---

#### Headline validation results — original FCS (Results pp. 2–5; Table 2)

| Endpoint | Result | 
|---|---|
| **Mean i.FCS** | **35.5 (SD 10.9)**; 5th–95th pctl 19.5–55.3 |
| Population in i.FCS bands | 32.7 % ≤30 (poor), 66.8 % 31–69 (intermediate), **0.5 % ≥70 (ideal)**; 99.5 % below 70 |
| **i.FCS ↔ HEI-2015 (Spearman)** | **R = 0.81** (subgroups 0.76–0.83) |
| i.Domain ↔ HEI-2015 | 0.23 (i.Specific Lipids) to 0.76 (i.Nutrient Ratios) |

**Per 1 SD (10.9 points) higher i.FCS, multivariable-adjusted (Table 2):**
- BMI −0.60 kg/m² (−0.70, −0.51); SBP −0.69 mmHg (−0.91, −0.48); DBP −0.49 (−0.66, −0.32)
- LDL-C −2.01 mg/dL (−2.63, −1.40); HDL-C +1.65 (1.44, 1.85); TG −1.55 (−3.13, 0.03, **NS**); TC:HDL −0.13 (−0.15, −0.12)
- HbA1c −0.02 % (−0.03, −0.01); FPG −0.44 mg/dL (−0.74, −0.15)
- Metabolic syndrome OR 0.85 (0.82, 0.88); CVD 0.92 (0.88, 0.96); cancer 0.95 (0.91, 0.99); lung disease 0.92 (0.88, 0.96); diabetes 0.96 (0.91, 1.01, **NS**); optimal cardiometabolic health OR 1.24 (1.16, 1.32)

**Mortality (Results p. 4; Cox, NDI through 2018):** 7,481 deaths over 20.8 y follow-up (2,619 cardiometabolic, 1,691 cancer). **Per 1 SD higher i.FCS: all-cause mortality HR 0.93 (0.89, 0.96)** — 7 % lower. Cancer mortality 0.92 (0.85, 1.00, trend); cardiometabolic mortality 0.95 (0.89, 1.02, NS). Findings consistent across age, sex, race/ethnicity, education, income, BMI (all p-interaction > 0.05). Possible non-linearity (stronger protection up to i.FCS ≈ 40, the ~75th percentile) but not significant (p = 0.12).

**Comparison anchor:** the i.FCS mortality effect (HR 0.93 per SD) was similar in magnitude to that of some-college vs. <high-school education (0.94) and a 1-SD increase in physical activity (0.90).

---

#### Domain-level findings (Table 3) — relevant if our pipeline reports sub-domains

No single domain matched the full i.FCS for predictive strength, supporting the holistic multi-domain design. Strongest protective domains across risk factors: **i.Nutrient Ratios**, **i.Food Ingredients**, **i.Minerals**. Weaker/emerging: i.Phytochemicals, i.Specific Lipids (consistent with their half-weighting). Two notable reverse-causation flags the authors raise: the i.Additives domain (added sugar a major component) was paradoxically associated with *higher* fasting glucose (people with high blood sugar may avoid added sugar); and the i.Protein attribute was associated with *higher* diabetes prevalence (OR 1.10), consistent with meta-analytic protein-diabetes associations and de novo lipogenesis pathways.

---

#### Data, code, reproducibility (Data/Code availability pp. 11–12)

- **Algorithm** in Supplementary Table S2 + the 2021 Nature Food paper (B9); **freely reproducible**, no IP/patent.
- **⚠ Code NOT public** (Tufts considering commercial licensing) — same restriction as B10. Implement from published tables, not author code.
- Data: USDA FNDDS 2001–2018, FPED 2001–2018, USDA Flavonoid DB 2007–2010, NHANES 1999–2018, NDI through 2018.
- Exclusions: infant formula, baby foods, alcohol, specialized medical foods, supplements, items <5 kcal/100 g. Missing attributes filled by same-food-code propagation then predictive-mean-matching imputation.
- Software: R 4.0.3 + Stata SE 15.1.

---

#### Limitations and cautions (Discussion pp. 9–10) — for our §7

1. **Mostly cross-sectional** (risk factors, conditions); only mortality is prospective — temporality limited.
2. **Energy-weighting under-weights low-calorie foods** (fruits, vegetables); but gram/portion weighting would reintroduce water-weight bias. A genuine design trade-off our pipeline inherits if we adopt i.FCS.
3. **Simplifications:** several nutrient targets use the RDA for 19–50-y men; some nutrients (vitamin D, choline, flavonoids) imputed across cycles → likely attenuation toward null.
4. **Self-report dietary error** (misreporting, omission); if systematic (sicker people under-report unhealthy foods), it would *inflate* their i.FCS and make i.FCS look *less* protective — i.e. bias is conservative.
5. **US-only** (NHANES). Same portability caveat as B10 for our Canadian/French food sets.
6. **No head-to-head NPS comparison** against health outcomes — authors flag this as future work.
7. **Future direction explicitly named:** the "long-term vision of Food Compass is to score additional features… such as environmental sustainability, social justice, and animal welfare — one for each direction of the compass." **This is directly relevant to our manuscript** — Food Compass's own authors envision exactly the environment × nutrition integration our project performs, which is a citable framing point.
8. **Conflicts of interest:** extensive — Mozaffarian and Blumberg report numerous food-industry scientific-advisory and equity ties; worth noting given the policy-adoption advocacy in the discussion.

---

#### Three-sentence relevance note

B11 is the health-outcome validation of the original (2021) Food Compass: in 47,999 US adults the energy-weighted individual score i.FCS correlated with HEI-2015 at R = 0.81 and, per 1 SD, predicted lower BMI, blood pressure, LDL, HbA1c, glucose, metabolic syndrome, CVD, cancer, and lung disease, plus 7 % lower all-cause mortality (HR 0.93) — the evidence base that lets us cite Food Compass as a *health-validated* nutrient profiling system distinct from the guideline-adherence HEFI-2019. It also resolves the sample-size ambiguity flagged in B10: the correct cohort is n = 47,999 (B10's "47,099" is a typo), and it documents the exact i.FCS construction (energy-weighted mean of per-item FCS, alcohol excluded and covariate-adjusted) our pipeline would replicate. Two things to carry forward: the same code-withheld / algorithm-open and US-only constraints as B10 apply, and — most usefully for our manuscript's framing — the authors explicitly state Food Compass's long-term vision is to add environmental sustainability, social justice, and animal welfare as further "directions of the compass," which is precisely the environment × nutrition fusion our Call 1 work operationalises and a strong citation for motivating it.

---

### B12. Barrett, Mozaffarian et al. (2025) — Food Compass Score-10 (FCS-10) [★★★]

**Citation.** Barrett EM, Cudhea F, Washbon E, Levitan Z, Reedy Sharib J, Blumberg JB, Micha R, Mozaffarian D. Food Compass Score-10: validation of a method for evaluating the healthfulness of foods and beverages using ingredient list information. Am J Clin Nutr. 2025.

**DOI.** 10.1016/j.ajcnut.2025.01.014 (per wishlist). The uploaded copy is the accepted-manuscript version with line numbers, not journal pagination — verify final page numbers and exact publication details against the AJCN version of record before the reference list is finalised.

**⚠ Wishlist correction.** The wishlist lists B12 as "Mozaffarian, D., et al. (2025)." The correct lead author is **Eden M. Barrett** (Mozaffarian is senior/last author).

**Why this paper matters most to our project.** B12 is the Food Compass variant designed to be computed from **commonly available label data (Nutrition Facts panel + ingredient list)** rather than the full 54-attribute dataset. This is the closest Food Compass implementation to what a recipe-/label-driven pipeline like ours actually has access to, and it explicitly proposes LLMs/ML for ingredient-list parsing — directly bridging to wishlist group D.

---

#### The problem FCS-10 solves (Introduction pp. 3–4; Methods p. 5)

The full Food Compass (B9/B10) needs data on 54 attributes across 9 domains, several of which are NOT on mandatory labels — limiting practical application to real packaged products. **FCS-10 estimates the Food Compass score using only label-available nutrient and ingredient-list information.** It retains the underlying Food Compass principles but is **scaled 1–10** (not 1–100) to honestly reflect its lower precision.

**Recommendation cut-offs (rescaled):** **FCS-10 ≥7 = encourage, 4–6 = moderate, ≤3 = limit** (these map to the FCS ≥70 / 31–69 / ≤30 bands).

---

#### How FCS-10 is computed (Methods pp. 7–9) — the parts our pipeline can reuse directly

1. **18 attributes scored directly from labels** (e.g. fibre, the nutrient-ratio inputs, additives by presence in the ingredient list). These cover 6 of 9 domains: Nutrient Ratios, Vitamins, Minerals, Additives, Specific Lipids, Fibre/Protein.
2. **Food Ingredients domain scored from the ingredient list:** each of the **first five listed ingredients** is mapped to one of **168 ingredient categories** (adapted from 149 WWEIA categories), then to a food-based attribute and scored **+10 (e.g. fruit, vegetable, whole grain), −10 (refined carbs, processed/red meat), or 0 (other)**. For composite ingredients (e.g. "granola [rolled oats, sugar, honey]") the first three sub-ingredients are extracted. **Trace ingredients** ("additives/extracts/emulsifiers", "spices/seasoning/salt", and anything after them) are excluded.
3. **Ingredient-order weighting (Equation 1)** — directly usable in our pipeline. First ingredient gets weight x; each subsequent ingredient gets 2/3 of the previous; weights of the first five sum to 100:

   Σ (n=1→5) x·(2/3)^(n−1) = 100

   For a 4-non-trace-ingredient food, the four ingredients contribute ≈ **42 %, 28 %, 18 %, 12 %** respectively. This geometric-decay weighting is a clean, defensible heuristic we could adopt for recipe-ingredient importance when proportions are unknown.
4. **Missing Vitamin/Mineral/Specific-Lipid/Phytochemical attributes estimated** via a reference table: from 9,767 unique FNDDS foods, a mean reference FCS attribute score was computed for each of the 168 ingredient categories; a product's missing attribute = the same weighted sum (Eq. 1) of its first-five-ingredient reference scores.
5. **Processing (NOVA) from ingredient keywords:** NOVA-4 if it contains emulsifiers, artificial sweeteners, partially hydrogenated oils, HFCS, MSG, etc.; NOVA-3 / NOVA-2 / NOVA-1 by descending ingredient complexity. **Nitrites** (binary): cured-meat category or keywords (bacon, cured, nitrite, salami, sausage, smoked). **Fermented**: yogurt/cheese/keywords (culture, kefir, kimchi, kombucha, miso, natto, etc.). **Fried**: keywords (battered, breaded, deep-fried, tempura, etc.) + oil in first three ingredients.

---

#### Validation results (Results pp. 11–12; Tables 1–2)

**Test dataset:** 538 branded products with a previously published full FCS, built by matching USDA Global Branded Food Products Database (GBFPD, >400,000 products, updated through Oct 2021) to FNDDS 2015–2020 products. Same exclusions as Food Compass (infant formula, baby foods, specialized dietary foods, alcohol, <5 kcal/100 g). All 44 FNDDS food subcategories represented.

**Overall agreement with full FCS:**
- **49 % scored exactly**, **89 % within ±1 unit** (n = 481), **100 % within ±2 units** (none deviated more).
- **Spearman r = 0.93**; overall **RMSE = 0.90**.
- No systematic over- or under-estimation.

**Diagnostic accuracy vs. FCS recommendation categories (overall, micro-averaged, Table 2):**
- **Sensitivity 87 %, specificity 93 %, PPV 87 %, NPV 93 %.** Overall recommendation-category classification accuracy **87 %**.
- By band: foods-to-encourage (≥7) sens 89 %, spec 96 %; foods-to-limit (≤3) sens 87 %, spec 96 %; foods-to-moderate (4–6) weakest, sens 85 %, spec 88 %.

**By food category (Table 1) — RMSE / Spearman r / recommendation accuracy:**
- Best: Fruit (0.61 / 0.90 / 0.97), Seafood (0.60 / 0.48 / 1.00), Fats & oils (0.68 / 0.94 / 0.96), MPE (0.78 / 0.89 / 0.85), Vegetables (0.79 / 0.93 / 0.88).
- Weakest: **Sauces & condiments (1.01 / 0.86 / 0.87)** — large ingredient/nutrient variation (e.g. buffalo sauce energy density ranged 48–233 kcal/100 g with similar main ingredients); and **Legumes & nuts (0.99 / 0.75 / 0.84)** — but their scores are concentrated 7–10, so within-±1 accuracy stays high.
- Grains: 0.97 / 0.85 / 0.81 (lowest recommendation accuracy, owing to whole vs. refined grain discrimination challenges).

---

#### Machine-learning / LLM hooks (Discussion pp. 14–15) — relevant to wishlist group D

The authors explicitly note that:
- Automated ingredient-list coding is hard (synonyms: "HFCS" vs. "glucose-fructose syrup"; "non-fat milk" vs. "skim milk"; spelling/punctuation variation), and **integrating ML could improve speed/accessibility**.
- **"Use of artificial intelligence large language models could also facilitate the recognition and interpretation of ingredients lists."** (verbatim sense, line 362)
- ML has been used to estimate added sugar, fibre, NOVA processing, and food categories from labels (refs 20–25), including Menichetti et al. 2023 (Nat Commun) ML prediction of food processing degree.

This is a direct, citable bridge from Food Compass to our LLM-for-food-classification work (group D, S1/S7): the canonical NPS authors themselves call for exactly the LLM-based ingredient parsing our pipeline can supply.

---

#### Limitations (Discussion pp. 15–16) — for our §7

1. **Small per-category n** (e.g. only 9 seafood, 19 legumes/nuts) limits subcategory precision.
2. **US-derived reference data** (GBFPD/FNDDS/WWEIA). Reasonable for multinational packaged foods given the elemental nature of the 168 categories and the global descending-order labelling convention, but **less reliable for locally produced non-US products** — same portability caveat as B10/B11, important for our Canadian/French food sets.
3. **Ingredient proportions unknown** — only descending order is available; if proportion data existed (even for top ingredients), weighting precision would improve, especially for sauces/condiments.
4. **FCS-10 itself NOT yet validated against health outcomes** (only against the full FCS). The health-outcome validation lives in B11 (full FCS); FCS-10 inherits validity only by proxy.
5. **Manual ingredient categorisation is labour-intensive** — the bottleneck ML/LLMs would relieve.
6. **Conflicts of interest:** same extensive Mozaffarian/Blumberg food-industry ties as B10/B11.

---

#### Data and reproducibility (Data availability p. 17)

- **Fully reproducible and public:** algorithm (Supplementary Table 1), reference attribute scores (Supplementary Table 3), ingredient categorisation (Supplementary Table 4), and ingredient-weighting method (Methods/Supplementary Methods 1). Worked example in Supplementary Methods 1.
- Data: FNDDS 2015–2020; USDA GBFPD. Generated FCS and FCS-10 for all 538 items in Supplementary Table 2.
- Software: Stata 18 + R 4.4.1.
- Unlike the full-FCS papers (B10/B11, code withheld), **FCS-10's method is described in full and "straightforward to apply with modern technology and coding"** — meaning we can implement FCS-10 from this paper's supplements without needing Tufts' proprietary code. This makes FCS-10 the more practically implementable Food Compass variant for our pipeline.

---

#### Three-sentence relevance note

B12 (FCS-10) is the most directly implementable Food Compass variant for our project because it computes a Food Compass-aligned healthfulness score (1–10, cut-offs ≥7 / 4–6 / ≤3) from label-available data — Nutrition Facts plus the first five ingredients — using a fully published, code-free method, validating at Spearman r = 0.93 and 87 %/93 % sensitivity/specificity against the full FCS. Two components are immediately reusable in our pipeline: the geometric ingredient-order weighting (Equation 1: first ingredient ≈42 %, then ×2/3 decay across five ingredients) and the 168-category ingredient-to-attribute reference table (Supplementary Tables 3–4) for imputing unmeasured nutrients from ingredient lists. Most strategically, the authors explicitly call for LLMs to parse and interpret ingredient lists to scale the method — a direct, authoritative bridge to our wishlist-group-D LLM-classification work (S1/S7) — though the US-derived reference data and the fact that FCS-10 is validated only against the full FCS (not health outcomes) are caveats our §7 should carry; cite as Barrett et al. 2025, AJCN, doi:10.1016/j.ajcnut.2025.01.014.

---

### B13. Shahid, Neal & Jones (2020) — Uptake of Australia's Health Star Rating System 2014–2019 [★★]

**Citation.** Shahid M, Neal B, Jones A. Uptake of Australia's Health Star Rating System 2014–2019. Nutrients. 2020;12(6):1791.

**DOI.** 10.3390/nu12061791 (open access, CC BY 4.0)

**⚠ Wishlist substitution.** Wishlist B13 names the canonical HSR specification: "Australia New Zealand Food Regulation Ministerial Council (2014, with updates through 2020), Health Star Rating System, Calculator and Style Guide." This paper is **not** that specification. It is a five-year uptake and implementation study that documents the HSR algorithm's *structure* (categories, baseline and modifying points, output scale) and cites the actual specification documents as its refs 17 and 18: the **Health Star Rating System Style Guide v5** (HSRAC, 2017) and the **Guide for Industry to the Health Star Rating Calculator (HSRC) v5** (HSRAC, 2016). The exact per-category point tables and star-conversion matrices live in those two documents, not here. We can cite Shahid et al. 2020 for the algorithm's shape and for real-world uptake evidence, but **the exact scoring matrices and nutrient thresholds for our §3.2 implementation must still be taken from the HSRC v5 Guide for Industry** (their ref 18), which remains to be fetched.

**Type.** Cross-sectional implementation and uptake study using systematically collected annual product-label monitoring data (FoodSwitch Monitoring Datasets, 2014–2019, four Sydney metropolitan supermarkets). Conflicts of interest: authors declare none, a useful contrast with the extensive food-industry ties carried by B10/B11/B12 (Food Compass).

---

#### The HSR algorithm structure (§2.4, p. 4) — for our §3.2 implementation

**Output scale (Introduction, p. 1).** HSR assigns a rating from **0.5 stars (least healthy) to 5.0 stars (most healthy)** in **ten half-star increments**. A higher HSR indicates a healthier product *within its category*.

**Six scoring categories.** Every product is first assigned to one of six HSR categories, each with its own scoring matrix:
1. Non-dairy beverages
2. Dairy beverages
3. Oils and spreads
4. Cheese and processed cheese
5. All other dairy foods
6. All other non-dairy foods

**Point structure.** Within a category, the HSR score is computed as:

$$\text{HSR score} = \text{baseline points} - \text{modifying points}$$

where, per 100 g (or 100 mL):
- **Baseline points** (the "risk" nutrients) are assigned from **energy, saturated fat, total sugars, and sodium**.
- **Modifying points** (the protective components) are assigned from **fruit, vegetable, nut and legume content (FVNL %), concentrated FVNL %, protein, and fibre**, where applicable.

The resulting score is then mapped to a 0.5–5.0 star value through a **defined scoring matrix specific to each of the six categories**. The numerical point allocations and the score-to-star cut-offs are **not reproduced in this paper**; they are in the HSRC v5 Guide for Industry (ref 18).

This four-risk-nutrient / four-positive-component structure is what makes HSR cheap to compute from a standard Nutrition Information Panel, and it is the structure our pipeline encodes when HSR is run as one of the §3.2 nutritional-quality indicators alongside Food Compass / FCS-10 (B10–B12) and HEFI-2019 (B6/B7).

---

#### Nutrient-imputation note (§2.3, p. 3) — directly relevant to our §7.2

On the Australian nutrient declaration, **energy, protein, saturated fat, total sugar, and sodium are mandatory**, but **FVNL %, concentrated FVNL %, and fibre are optional** and frequently absent. Where these were not provided, the authors estimated them from the back-of-pack ingredients list, generic food composition databases, or by analogy with similar products. Their estimation produces a **proxy value at the finest category level for more than 700 individual food subcategories**, then substitutes that proxy for any product missing data in that category.

This is the same missing-input problem our pipeline faces, and the same family of solutions (ingredient-list inference, composition-database lookup, category-analogy imputation) that FCS-10 (B12) uses via its 168-category reference table. It is a concrete, citable precedent for §7.2 when we justify our own imputation of unmeasured attributes, and it is a candidate task for the LLM ingredient-parsing work in group D (S1/S7).

---

#### Uptake findings (Results §3, pp. 4–8) — for §2.1 framing and §6.3 policy implications

**Overall 2019 uptake.** HSR appeared on **7118 / 17,477 (40.7 %)** of eligible products. Of these, **5858 (33.5 %)** displayed the full HSR logo and **1260 (7.2 %)** displayed the "energy icon only" variant (since removed in the 2019 Review).

**Trend and projection (Fig. 1, p. 5).** Linear growth of about **8.4 % per annum** for any HSR variant; **6.8 % per annum** for the full logo alone. Trend equations: system (logo + energy icon) $y = 0.0836x + 0.0142$, $R^2 = 0.9869$; logo only $y = 0.0678x + 0.0212$, $R^2 = 0.9787$. Maintaining these trends would reach roughly **85 %** (any variant) or **70 %** (logo only) by 2024.

**Selective, score-skewed display (§3.2, p. 5).** Of the 5858 logo products, **4475 (76.4 %) had HSR ≥ 3.0**. Proportional logo uptake was highest at HSR 4.5 (**56.2 %** of 1126 eligible) and lowest at HSR 1.0 (**14.0 %**). Products displaying the logo had a significantly higher **mean HSR of 3.4 versus 2.6** for products not displaying it ($p < 0.001$). Most tellingly, **70.4 % of energy-icon-only products would have received an HSR between 0.5 and 2.0**, evidence that the non-interpretive variant was used to suppress low scores.

**By category (Table 1, p. 6).** Highest uptake: Fish and fish products (54.5 %), Fruit and vegetables (51.2 %), Convenience foods (50.9 %). Lowest uptake: Sugars, honey and related products (19.1 %), Edible oils and oil emulsions (25.0 %), Sauces, dressings, spreads and dips (28.1 %). In **12 of 15 categories**, logo products had a significantly higher mean HSR than non-logo products, the gap being largest for Non-alcoholic beverages (4.1 versus 2.3, $p < 0.001$).

**By manufacturer (Table 2, §3.4, pp. 6–8).** 139 manufacturers used HSR on at least one product. Grocery retailers **Coles, Woolworths and ALDI together accounted for 55.9 %** of all uptake and appear near-saturated on their private-label ranges (e.g. Coles 92.4 %, ALDI up from 31.3 % in 2017 to 81.9 %). AFGC members (the food-industry bloc on the governance committee) accounted for only **28.6 %** of uptake and displayed HSR on under half (45.5 %) of their joint portfolio.

---

#### Author-flagged limitations (§4, p. 10) — for our §7

1. **Coverage vs. trend trade-off.** The FoodSwitch Monitoring Dataset is robust for time trends but weak for absolute coverage of the food supply, relying on four metropolitan Sydney stores.
2. **2014 baseline set to zero** because HSR presence was not systematically recorded in its introduction year; a small number of early logos was likely missed.
3. **Algorithm-generated HSRs carry uncertainty.** Where no logo was present, the HSR had to be computed, and because FVNL and fibre are not mandatory on Australian panels, those inputs were estimated (see imputation note above), introducing error into the generated values.
4. **The algorithm itself is a moving target.** Review recommendations to better align the HSR algorithm with the Australian Dietary Guidelines will change the HSRs some products receive in future, so any HSR figures are version-dependent (a parallel to the ReCiPe versioning point in A3).

**Policy-relevant interpretive limitation (Discussion, pp. 8–9).** A voluntary HSR operates "more akin to a tick or green light" on products scoring 3.0 or above rather than as a full spectrum rating of healthiness. Selective display gives manufacturers a marketing benefit while denying consumers the comparisons that give the label its public-health value. This is the central argument we can borrow for §6.3: comprehensive, automated scoring of *every* product or recipe (which our platform performs) structurally avoids the selective-disclosure failure mode of voluntary front-of-pack labels.

---

#### Cross-links to other entries

- **B10 (Food Compass 2.0)** reports a high Nutri-Score ↔ HSR correlation ($r = 0.83$) and computes HSR using "the official Australian calculator." B13 supplies the algorithm structure behind that HSR column and confirms which specification document (HSRC v5) the official calculator implements.
- **B12 (FCS-10)** solves the same missing-attribute imputation problem with a published 168-category reference table; B13's >700-subcategory proxy approach is the front-of-pack analogue and a second precedent for §7.2.

---

#### Three-sentence relevance note

B13 serves two distinct roles in our manuscript: it documents the structure of the Health Star Rating algorithm we implement as a §3.2 nutritional-quality indicator (0.5–5.0 stars in half-star steps, six category-specific scoring matrices, baseline points from energy, saturated fat, total sugars and sodium minus modifying points from FVNL %, concentrated FVNL %, protein and fibre), and it supplies real-world uptake evidence that motivates automated comprehensive scoring over voluntary labelling. Its single most useful empirical result for §6.3 is that after five years of voluntary implementation HSR reached only 40.7 % of eligible products and was displayed disproportionately on high-scoring items (76.4 % of logo products scored ≥ 3.0; 70.4 % of energy-icon-only products would have scored ≤ 2.0), demonstrating the selective-disclosure failure mode our platform sidesteps by scoring every item. Note that this paper is an uptake study and not the HSR specification itself, so the exact point tables and star cut-offs for our implementation must still be taken from the Guide for Industry to the HSRC v5 (the paper's ref 18); cite as Shahid et al. 2020, Nutrients 12(6):1791, doi:10.3390/nu12061791.

---

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
