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

### C14. Stylianou, Heller, Fulgoni et al. (2016) — CONE-LCA: combining nutritional and environmental health impacts (milk case study) [★★★]

**Citation.** Stylianou KS, Heller MC, Fulgoni VL III, Ernstoff AS, Keoleian GA, Jolliet O. A life cycle assessment framework combining nutritional and environmental health impacts of diet: a case study on milk. Int J Life Cycle Assess. 2016;21(5):734–746.

**DOI.** 10.1007/s11367-015-0961-0 (received 30 Jan 2015, published 23 Sep 2015; print 2016)

**Type.** Methodology paper introducing the **Combined Nutritional and Environmental LCA (CONE-LCA)** framework, with a proof-of-concept milk case study. This is the **conceptual ancestor of HENI** (C15, Stylianou et al. 2021): same lead author, same idea of putting environmental and nutritional effects on a common DALY scale, but here applied to a single food via dietary scenarios rather than codified into per-food μDALY/g factors. Funding: an **unrestricted grant from the Dairy Research Institute (Dairy Management Inc.)**, a material conflict to note given the milk-favourable conclusion.

---

#### The CONE-LCA framework (§2.1, Fig. 1, pp. 735–736) — for our §3.2/§3.3 lineage

The core move is to assess **environmental and nutritional health effects in parallel and express both at the human-health endpoint in DALYs**, so they can be compared on one scale. The environmental track is a standard LCA: functional unit → inventory (emissions, resources) → midpoint categories (climate change, water, land, respiratory) → endpoint damage (human health in DALYs). The nutritional track operates on the food LCA "use stage": published epidemiology relates the food directly to disease outcomes in DALYs, or, where direct data are absent, nutrient contents (protein, calcium, vitamins, saturated fat, sodium) are linked to health effects via epidemiological data. The authors stress that putting nutrition into the *functional unit* (the older quality-corrected approach) creates "conceptual dissonance," and that their parallel-DALY approach avoids it. They are explicit that validity is "contingent on the data used, their availability, level of detail, and associated uncertainty."

This is exactly the dual-track logic our platform inherits through HENI, and C14 is the citable origin of it.

---

#### Environmental characterization factors (§2.2.3, Table 1, pp. 738–739) — provenance for our environmental endpoint factors

**Global warming, human-health endpoint:** **0.82 μDALY per kg CO2-eq** on a 100-year horizon, GSD² 4.8, attributed to "Bulle et al., manuscript in preparation" (i.e. the pre-publication IMPACT World+ factor). The authors caution this is far more uncertain than the midpoint radiative-forcing indicator and should be read as order-of-magnitude only.

**Particulate matter (Table 1).** PM-related precursor emissions were not routinely reported in food LCAs, so they were correlated to the GW indicator (kg CO2-eq) across **47 food-related Ecoinvent processes**, then converted to health damage:

| PM species | CO2-eq correlation factor (kg/kg CO2-eq) | GSD² | R² | CF (DALYs/kg emitted) |
|---|---|---|---|---|
| Primary PM2.5 (rural) | 2.4×10⁻⁴ | 1.5 | 0.92 | 3.0×10⁻⁴ |
| SO2 | 8.3×10⁻⁴ | 2.9 | 0.65 | 6.2×10⁻⁵ |
| NOx | 2.7×10⁻³ | 1.5 | 0.96 | 1.3×10⁻⁵ |
| NH3 | 3.5×10⁻³ | 6.8 | −0.02 (not used) | 1.3×10⁻⁴ |

PM health linkage followed Fantke et al. 2014 / Humbert et al. 2011 intake fractions with Gronlund et al. 2015 effect factors. For NH3, the CO2-eq correlation was effectively zero, so NH3 emissions were instead taken from food-specific factors (Meier and Christen 2013). Context figure: US PM2.5 causes **103,000 deaths/yr and 1,820,410 DALYs**.

These are 2015-vintage factors. Our implementation almost certainly uses updated IMPACT World+ or ReCiPe values (Group A), so cite C14 for the *method* and the provenance of the 0.82 μDALY/kg CO2-eq lineage, not as the current numbers.

---

#### Nutritional dose-response inputs (§2.2.4, pp. 739–740) — the epidemiology-to-DALY machinery

The nutritional track converts relative risks and national disease burdens into per-serving μDALY using GBD 2010 data and a theoretical-minimum-risk exposure level (TMREL) cap per outcome:

| Outcome (milk) | Relative risk used | TMREL / threshold | US 2010 burden (DALYs) |
|---|---|---|---|
| Colorectal cancer (benefit) | RR 1.11 (95 % CI 1.03–1.20) per 226.8 g/day decrease | no further benefit above 450 g/day | 1,146,830 |
| All stroke (benefit) | RR 0.85 (95 % CI 0.77–0.94), high vs low intake (≈541 g difference) | no benefit above 597 g | 1,569,720 |
| Prostate cancer (harm, males) | RR 1.03 (95 % CI 1.00–1.06) per 200 g/day increase, nonlinear | risk plateaus above ~200 g/day | 592,400 |

**Sugar-sweetened beverages** were assigned an **effect factor of 0.03 μDALY per SSB-calorie (95 % CI 0.02–0.04)**, derived from the US SSB burden of 770,584 DALYs, a TMREL of 0 g/day, and consumption of 236 cal/person/day. This per-calorie SSB factor is a clean, reusable number.

---

#### Case-study results (§3, pp. 740–742) — useful magnitudes

- **Average US diet baseline:** GHGE 5.0 kg CO2-eq/person/day (95 % CI 2.5–9.2) at 2534 cal/day; PM 2.2 g PM2.5-eq/person/day (95 % CI 1.1–3.9).
- **Adding one serving (244 g, 119 kcal) of fluid milk (scenario A):** GW 0.47 kg CO2-eq = 0.38 μDALY (GSD² 4.9); PM 0.26 g PM2.5-eq = 0.32 μDALY, dominated by NH3 from manure (80 %).
- **Net nutritional benefit of the added serving: 1.88 μDALY** (colorectal +1.10, stroke +0.95, prostate −0.16 population-weighted).
- **Replacing 119 kcal of SSB: 3.48 avoided μDALY** (95 % CI 2.23–5.43), which dominates scenario C.
- **Probability that benefits exceed impacts** (Hong et al. 2010 analytical uncertainty propagation): 98.1 % (A), 99.2 % (B), 100 % (C).

The headline: in this framing the use-stage nutritional effects are of **comparable or larger magnitude than the production-stage environmental effects**, which is the central argument for including nutrition in food LCA and the reason our platform reports both.

---

#### Author-flagged limitations (§4, pp. 743–744) — for our §7

1. **Proof-of-concept, high uncertainty.** Results are order-of-magnitude and "should be interpreted with caution and only within the context of this study"; a full Monte Carlo treatment is recommended (a hook for our §3.6 uncertainty work).
2. **GW endpoint CFs are very uncertain** (order-of-magnitude only); long-term GW health impacts beyond 100 years not assessed.
3. **Secondary PM2.5 double-counting risk:** NOx, SO2 and NH3 are characterised with independent CFs that ignore precursor interactions and background concentrations; better spatially-differentiated secondary-PM modelling is needed.
4. **The "average diet has no health effect" assumption** is a deliberate simplification; a worst-case substitution of fruits and vegetables could flip the sign of the result. This is the single most important caveat and maps directly onto our substitution-scenario handling.
5. **Sparse outcome set** (2 beneficial, 1 detrimental for milk); prostate-cancer evidence is "controversial" and a worst-case RR was used to avoid overstating net benefit.
6. **Epidemiology is correlation, not causation;** confounders (e.g. SSB burden confounded by sedentary lifestyle) may inflate effect sizes.
7. **No sex/age segmentation.**
8. **Dairy-industry funding** (not flagged by the authors as a limitation, but ours to note).

---

#### Cross-links to other entries

- **C15 (HENI, Stylianou et al. 2021)** is the direct successor: it generalises this single-food CONE-LCA exercise into per-food μDALY/g nutritional factors across ~14 dietary risk factors. C14 is the framework, C15 is the operationalised factor table.
- **Group A (ReCiPe / IMPACT World+)** supplies the modern environmental endpoint factors that supersede C14's 0.82 μDALY/kg CO2-eq and the PM CFs.
- **Hong et al. 2010** analytical uncertainty propagation here is a lighter-weight alternative to the Monte Carlo approaches in Group F.

---

#### Three-sentence relevance note

C14 is the founding CONE-LCA paper and the methodological root of the HENI health-burden indicator (C15) our platform implements: it establishes the principle of assessing environmental and nutritional food effects in parallel and expressing both at the human-health endpoint in DALYs, demonstrated on a milk case study where use-stage nutritional effects (net +1.88 μDALY per added serving) were of comparable or greater magnitude than production-stage environmental damage. For our methods sections it supplies the provenance of the 0.82 μDALY/kg CO2-eq global-warming endpoint factor and a usable PM characterization-factor set (primary PM2.5 3.0×10⁻⁴, SO2 6.2×10⁻⁵, NOx 1.3×10⁻⁵, NH3 1.3×10⁻⁴ DALYs/kg) plus an SSB effect factor of 0.03 μDALY/calorie, though these 2015-vintage values are likely superseded in our implementation by the Group A factors. Its limitations transfer almost wholesale to our §7 (the average-diet-no-effect assumption, secondary-PM double-counting, correlation-not-causation, and a thin single-food epidemiology base), and the dairy-industry funding is worth carrying when we describe HENI's lineage; cite as Stylianou et al. 2016, Int J Life Cycle Assess 21(5):734–746, doi:10.1007/s11367-015-0961-0.

---

### C15. Stylianou, Fulgoni & Jolliet (2021) — HENI: the canonical Health Nutritional Index paper [★★★]

**Citation.** Stylianou KS, Fulgoni VL III, Jolliet O. Small targeted dietary changes can yield substantial gains for human health and the environment. Nat Food. 2021;2(8):616–627.

**DOI.** 10.1038/s43016-021-00343-4 (received 28 Apr 2020, published 18 Aug 2021)

**Type.** Primary methodology + large-scale application paper. This is **the canonical HENI reference** and the one our wishlist marks for reproducing the per-food-category figure (Fig. 4). It operationalises the C14 CONE-LCA framework into a per-food index, applies it to 5,853 US foods, pairs it with 18 IMPACT World+ environmental indicators for 167 representative foods, and derives the headline substitution result. Funding: **unrestricted grant from the National Dairy Council** plus a UMich Dow Sustainability Fellowship; COI disclosures note Fulgoni does data analyses for the food industry and Jolliet later joined a Nutella-supported board. Same dairy-funding lineage as C14, worth carrying.

---

#### What HENI is and the exact scoring formula (Results p. 617; Methods pp. 624–626) — core of our §3.3

HENI is a **continuous single score giving the net minutes of healthy life gained (+) or lost (−)** from all-cause premature mortality and morbidity per reference amount of a food, attributable to adding a marginal amount of that food to the current US adult diet. The score for food *i* is:

$$\text{HENI}_i = -0.53 \times \sum_r \text{DRF}_r \times d_{i,r}$$

where DRF_r is the cumulative age- and gender-adjusted **dietary risk factor** for risk component *r* (in μDALY per g), and d_{i,r} is the amount of risk component *r* in food *i* (g per reference serving). The constant **−0.53 is minutes of healthy life per μDALY**: 1 μDALY = 10⁻⁶ × 365 × 24 × 60 ≈ 0.53 min of healthy life, and the negative sign flips the damage-oriented μDALY into a benefit-oriented "minutes gained" metric. **This −0.53 constant is the single most reusable number in the paper** and is exactly what our pipeline must hard-code to convert μDALY to HENI minutes.

**Key implementation rule (Methods p. 626):** for "milk" and "flavoured milk" the calcium DRF is *excluded* from the HENI sum to avoid double-counting the colorectal-cancer benefit already captured in the milk DRF. Our implementation needs this carve-out.

**Risk-component amounts** d_{i,r} are computed by the Fulgoni et al. 2018 method (ref 36), which maps WWEIA/NHANES foods to GBD risk components.

---

#### The dietary risk factors (DRFs) (Results pp. 617–618; Methods eq. 1–2, pp. 624–625)

DRFs are derived from a **comparative risk assessment adapted for marginal (1 g) intake changes**, under a log-linear dose-response, from the **2016 GBD**. The marginal DRF reduces (via Taylor expansion) to:

$$\text{DRF} = \frac{\ln(\overline{RR})}{\text{Ref}} \times \overline{BR}, \qquad \overline{BR} = \frac{BR}{\overline{RR}}, \quad \overline{RR} = \sum_x P_x \, RR_{x/\text{Ref}}$$

where RR is the relative risk for a risk-outcome pair, Ref is the RR's reference exposure (g/day), BR is the outcome-specific burden rate (μDALY/person/day), and P_x is the population fraction at intake level x. Morbidity (YLDs) and mortality (YLLs) are summed to DALYs. The full cumulative DRF (eq. 2) sums over age, gender, outcome, burden type and effect-modifier strata.

**Scale of the underlying model:** 15 dietary risks, 479 distinct risk-outcome RRs in GBD 2016, expanded to **6,195 age/gender/modifier/outcome/burden-specific RRs** and **6,041 probability distributions** for uncertainty. SSBs are 100% mediated through BMI; sodium through systolic blood pressure (modified by race and hypertension); fibre's cardiovascular effect is mediated through fruits/vegetables/legumes/whole grains and so split into separate DRFs to avoid double-counting.

**⚠ 15 vs 16 risk-component note.** The Results say HENI "combines the 15 DRFs," but the Methods HENI definition (eq. 3) says it is "based on the 16 selected dietary risk components." The reconciliation is that **fibre is one dietary risk split into two sources** (fibre from f/v/l/w, and fibre from other sources), so there are 15 risks but 16 risk components entering the sum. We should state this explicitly so our implementation count is unambiguous.

**The 15 risks** (signs from Fig. 2): beneficial = omega-3 from seafood, calcium, nuts and seeds, fibre (f/v/l/w), fibre (other), PUFAs, whole grains, legumes, fruits, vegetables, milk; detrimental = sodium, trans fatty acids (TFAs), processed meat, red meat, sugar-sweetened beverages (SSBs).

**DRF magnitudes (μDALY per g risk component):** range from a benefit of **81 avoided μDALY/g for omega-3 from seafood** (95 % CI 37–113) to a loss of **14 μDALY/g for sodium** (95 % CI 11–16; the chicken-wing worked example uses 13.9). The full per-risk table is **Supplementary Table 3, now retrieved and extracted in entry C15-SI** (note the SI gives omega-3 as −81 μDALY/g, CI −37 to −110, and sodium 13.9, CI 11.5–16.1 — use those authoritative values, not the abstract-derived figures in this paragraph). The health burden for most risks is driven by ischaemic heart disease; calcium/fibre/milk benefits act through avoided colorectal cancer; red meat acts mainly through diabetes (45 % morbidity, 27 % mortality).

---

#### HENI results across foods (Results pp. 618–620) — including the Fig. 4 we reproduce

- **5,853 foods scored** (WWEIA 2011–2016, US adults ≥25 yr). HENI per serving ranges, per the abstract, from **74 min lost to 80 min gained**; individual extremes reach **71 min lost** (corned beef with tomato sauce and onion, 95 % CI 38–91) and **82 min gained** (sardines in tomato sauce, 95 % CI 37–115).
- **Median HENI by food category (Fig. 4, the figure we reproduce):** from **35 min lost per serving for frankfurter sandwiches** (N = 37; IQR 31–41) to **33 min gained for peanut-butter-and-jelly sandwiches** (N = 17; IQR 29–34). Almost-always-negative categories: frankfurter/breakfast sandwiches, burgers, red meat. Almost-always-positive: nuts, PB&J, legumes, seafood, fruits, snack bars, ready-to-eat cereals, non-starchy vegetables.
- **No significant correlation** between HENI and energy density or serving size (Supplementary Fig. 3), so HENI is not reducible to "calories" or "portion."
- **Within-category variation exceeds the uncertainty of individual estimates**, which is the core argument for food-specific (not category-level) scoring, the same principle behind our recipe-level approach.

**Worked examples (Fig. 3) for validating an implementation:** chicken wings (85 g) = **3.3 min lost** (CI 2.5–3.9; sodium 0.49 g × 13.9 μDALY/g = 6.8 μDALY); beef hotdog on bun = **36 min lost** (CI 22–45, processed meat); vegetable pizza = **1.4 min lost** (CI 0.061–2.8); apple pie = **1.3 min gained** (CI −0.42 to 2.9). These are good unit-test targets for our HENI module.

---

#### Environmental side (Methods pp. 625–626) — the IMPACT World+ link

For 167 representative foods (~27 % of daily calories, 562 kcal/person/day), cradle-to-farm/processing-gate LCAs were run in **SimaPro v8.3** on **ecoinvent v3.3 + World Food LCA Database v3.1 + ESU**, characterised with **18 environmental indicators using IMPACT World+ v1.4 default factors** (Bulle et al. 2019, the now-published version of the "manuscript in preparation" cited in C14), except for **PM2.5 and blue water use, which use improved/spatialised methods**. The 18 indicators: global warming, land occupation, fossil energy use, mineral resources use, freshwater + terrestrial acidification, freshwater + marine eutrophication, freshwater ecotoxicity, ionising radiation, ozone depletion, water use, photochemical oxidants, fine PM2.5, cancer + non-cancer human toxicity, plus aggregated human-health and ecosystem-quality endpoints.

**This is the entry's most important cross-link to Group A:** HENI's environmental track uses IMPACT World+, whereas our platform may use ReCiPe (A1/A2). When we describe the environmental indicators we must be explicit about which method we adopt and reconcile category definitions accordingly.

**Environmental ranges (167 foods, per serving):** GW 0.0005 to 5.7 kgCO2eq (beef stew 5.7 ≈ 14 miles driven; beef ~2.5 average, GSD² 1.4; cheese/poultry ~0.3, GSD² 1.7); land 0 to 4.0 ha-yr arable; PM2.5 health 0.0001 to 1.5 min lost; consumptive water <0.01 to 116 L. Water use ranks foods very differently from GW (weak correlation), a recurring theme.

---

#### Food classification zones (Results pp. 619–620) — thresholds for our classification layer

| Zone | Criterion |
|---|---|
| Green (win-win) | HENI > 0 **and** GW below 50th percentile (< 0.32 kgCO2eq/serving) |
| Amber | intermediate; slightly detrimental (HENI 0 to 3.2 min lost) or moderate GW (50th–75th pctl) |
| Red | HENI > 75th pctl (> 3.2 min lost/serving) **or** GW > 75th pctl (> 0.61 kgCO2eq/serving) |
| Dark red (worst 10 %) | HENI > 15 min lost/serving **or** GW > 3.0 kgCO2eq/serving |

Green foods are mostly nuts, fruits, vegetables, legumes, whole grains, some seafood; red is driven nutritionally by processed meat and SSBs and environmentally by beef, processed meat, pork, lamb, cheese and some salmon; amber holds most poultry, dairy, eggs, cooked grains and greenhouse vegetables.

---

#### Headline substitution result (Results pp. 621–622) — for §6.3

Substituting **10 % of daily caloric intake (190 kcal/day, roughly ~20 g processed meat + ~40 g beef)** with an isocaloric mix of nutritious foods yields **+48 min of healthy life per person per day** (95 % CI 28–62) and a **33 % reduction in dietary carbon footprint** (95 % CI 22–46 %). All other environmental impacts fall by similar magnitudes **except consumptive water use (6 %, CI −9 to 26 %) and freshwater ecotoxicity (14 %, CI −6 to 55 %)**, which are weakly correlated with GW. Combined nutrition+climate optimisation gives environmental reductions 2–5× larger than nutrition-only, but **food replacements should be chosen primarily on nutrition** because the replacement mix barely affects the environmental savings. Aggregating health-related indicators, **nutritional health effects are on average 1–2 orders of magnitude larger than environmental health damages** (PM, photochemical oxidants, GW), which is the central justification for including HENI in food sustainability assessment.

---

#### Uncertainty methods (Methods p. 626) — for our §3.6

- **Nutritional (HENI):** Monte Carlo, **10,000 iterations in SAS 9.4**, log-normal distributions for RRs, BRs and the sodium-to-SBP conversion, normal for the other conversion factors; food-composition uncertainty assumed negligible relative to DRF uncertainty. Reported HENI uncertainty: ±1 min for |HENI| < 5 min, ±2.5 min for |HENI| ≈ 10 min, rising with HENI and highest for seafood.
- **Environmental:** the **Hong et al. 2010 analytical Taylor-series propagation** (same method noted in C14), characterised by squared geometric standard deviation GSD². Median GSD²: ~1.7 (GW, fossil energy), 2–3 (acidification, eutrophication, water, land), 5–7 (human-health and ecosystem endpoints), ~20 (human toxicity, ecotoxicity, photochemical oxidants). These give us realistic per-category uncertainty priors.

---

#### Author-flagged limitations (Discussion pp. 622–624) — for our §7

1. **HENI is marginal.** It estimates the effect of adding/removing a single reference serving and is "not applicable to substantial changes in diet." This is a hard scope limit our §7 must state plainly.
2. **Benefits are capped by TMREL/maximum intake** per risk (e.g. 250 g/day fruits) beyond which no further benefit accrues.
3. **Additivity and independence assumed** across risks unless a mediation mechanism is known; components not in the GBD are assumed health-neutral.
4. **Risk list is not exhaustive:** no potassium-CVD, no added sugar or saturated fat in the base model (only in sensitivity studies), no vitamin D or shortfall nutrients, no ultraprocessing or cooking effects, no bioavailability. HENI "could evolve" as GBD evidence grows.
5. **GW-to-health linkage is highly uncertain**, so the "nutrition dominates by 1–2 orders of magnitude" finding "is to be taken with care," compounded by different exposed populations and time horizons for nutritional vs environmental effects.
6. **Lag time** between exposure and disease makes the age distribution of DRFs "only indicative."
7. **US-specific** throughout (NHANES intakes, US burden rates), the same portability caveat as B9–B13 and central to our Canadian/French adaptation in §3.7.
8. **"Healthy/unhealthy food" terminology is limited in the context of the overall diet.**
9. **Dairy-industry funding** (ours to flag, as with C14).

---

#### Reconciliation with C14 (as promised)

| Aspect | C14 (2016, milk case study) | C15 (2021, HENI) |
|---|---|---|
| Scope | single food (milk), 3 dietary scenarios | 5,853 foods, per-food DRFs |
| Epidemiology base | GBD 2010 | GBD 2016 |
| Nutritional output | per-scenario μDALY | per-food μDALY → HENI minutes (×−0.53) |
| GW endpoint factor | 0.82 μDALY/kg CO2-eq ("Bulle et al., in prep") | IMPACT World+ v1.4 (Bulle et al. 2019, ref 38) — the same lineage, now published |
| PM characterisation | CO2-eq correlation proxies + Fantke/Humbert/Gronlund | improved/spatialised PM2.5 (refs 61,62,81,82) |
| SSB | 0.03 μDALY per SSB-calorie | SSB as a DRF in μDALY/g, mediated via BMI (different basis) |
| Uncertainty | Hong et al. 2010 analytical | Hong et al. 2010 (environmental) + 10k Monte Carlo (nutritional) |
| Funding | Dairy Research Institute (DMI) | National Dairy Council |

**Net:** C14 is the framework, C15 is the operational factor engine. The 0.82 μDALY/kg CO2-eq value in C14 is the pre-publication form of the IMPACT World+ factor that C15 uses through the published Bulle et al. 2019 method, so there is no real value conflict between them, only a maturation from a proxy to a published characterisation. The PM treatment did change (proxy correlation → spatialised), so if we ever cite a PM characterisation factor we should use the C15/IMPACT World+ lineage, not the C14 Table 1 proxies.

---

#### Three-sentence relevance note

C15 is the canonical HENI paper and the primary citation for the health-burden indicator our platform implements: HENI_i = −0.53 × Σ_r DRF_r × d_{i,r}, built on 15 dietary risks (16 risk components, with fibre split by source) drawn from GBD 2016, expressed in net minutes of healthy life per serving, with the −0.53 min/μDALY conversion and the milk-calcium double-counting carve-out being the two implementation details we must encode exactly. Beyond the method it gives us the Fig. 4 per-category distribution we reproduce, a set of unit-test foods (chicken wings 3.3 min lost, beef hotdog 36 min lost, apple pie 1.3 min gained), the green/amber/red classification thresholds, GSD² uncertainty priors by impact category, and the headline policy result that a 10 % targeted isocaloric substitution buys 48 min/day of healthy life and a 33 % carbon-footprint cut. The key reconciliation point for our methods is that HENI's environmental track uses IMPACT World+ v1.4 (the published form of C14's 0.82 μDALY/kg CO2-eq factor) whereas we may use ReCiPe from Group A, so §3 must state which we adopt; **the full DRF value table has now been retrieved — it is Suppl. Table 3, extracted in entry C15-SI — so our HENI factors can be reconciled cell-by-cell against it (and two numbers in this entry, omega-3 upper CI and sodium mean, are corrected there).** Cite as Stylianou et al. 2021, Nat Food 2(8):616–627, doi:10.1038/s43016-021-00343-4.

---

### C15-SI. Stylianou, Fulgoni & Jolliet (2021) — Supplementary Information: the canonical DRF factor table, HENI worked example, and full uncertainty/LCA methodology [★★★]

**Citation.** Stylianou KS, Fulgoni VL III, Jolliet O. Small targeted dietary changes can yield substantial gains for human health and the environment. Supplementary Information. Nat Food. 2021;2(8):616–627. doi:10.1038/s43016-021-00343-4. (93 pp. supplement; "Prioritization of healthy and sustainable foods for small targeted dietary changes…", sections S1–S5 plus Data S1.)

**Type.** Author-supplied, unedited supplement to C15. **This is the single most important PDF in Group C for our implementation**: it contains the published μDALY/g DRF factor table (Suppl. Table 3) that the C15 main-text entry flagged as "NOT in this PDF," the fully worked HENI calculation our unit tests need, and the complete environmental uncertainty methodology (GSD², pedigree, Taylor-series propagation) for our §3.6.

---

#### ★ The DRF factor table — Suppl. Table 3, p. 8 (lines 160–164). THE table our HENI module hard-codes.

**Suppl. Table 3. 95% CI characterization of dietary risk factors (DRFs) in μDALYs/g.** Reproduce verbatim in §3.2 / Supplementary, and reconcile our `heni_calculator` factor file against it cell-by-cell.

| Dietary risk component | DRF mean (μDALY/g) | Lower | Upper | Sign |
|---|---|---|---|---|
| Omega-3 (seafood) | −81 | −37 | −110 | beneficial |
| Calcium | −5.1 | −4.0 | −6.2 | beneficial |
| Nuts and seeds | −1.5 | −1.1 | −1.9 | beneficial |
| Fiber_other | −0.99 | −0.71 | −1.3 | beneficial |
| PUFA | −0.60 | −0.26 | −0.94 | beneficial |
| Whole grains | −0.34 | −0.28 | −0.40 | beneficial |
| Legumes | −0.23 | −0.10 | −0.34 | beneficial |
| Fiber_f,v,l,w | −0.19 | −0.11 | −0.26 | beneficial |
| Fruits | −0.18 | −0.12 | −0.22 | beneficial |
| Vegetables | −0.083 | −0.042 | −0.11 | beneficial |
| Milk | −0.0077 | −0.0027 | −0.012 | beneficial |
| Sugar-sweetened beverages (SSB) | 0.066 | 0.043 | 0.089 | detrimental |
| Red meat | 0.099 | 0.038 | 0.15 | detrimental |
| Processed meat | 0.86 | 0.41 | 1.1 | detrimental |
| Trans fatty acids (TFA) | 4.4 | 3.3 | 5.6 | detrimental |
| Sodium | 13.9 | 11.5 | 16.1 | detrimental |

Sign convention: a **negative DRF is health-beneficial** (consuming more reduces burden); positive is detrimental. In the HENI sum these multiply the risk-component mass d_{i,r} (g/serving), then × −0.53 min/μDALY flips the overall sign so that positive HENI = minutes gained. Fiber_other = fiber from sources other than fruit/vegetables/legumes/whole grains; Fiber_f,v,l,w = fiber from those four sources (the two are kept separate because they map to different disease sets — see double-counting rules below). Omega-3 restricted to seafood-origin EPA + DHA.

**⚠ Resolves the C15 count ambiguity definitively.** The table has **16 rows = 16 risk components from 15 dietary risks** (fiber is one GBD risk split into two source-specific components). This confirms the "15 risks / 16 components" reading in the C15 entry and is the number our pipeline should use, *not* the 14-component Dutch list (C17) or the thesis-era 14 factors (C16).

**⚠ Correction to two numbers carried in the C15 main-text entry.** The C15 entry, working from the abstract/main text, recorded omega-3 as "+81 avoided μDALY/g (CI 37–113)" and sodium "14 (CI 11–16)." The authoritative SI Table 3 values are: **omega-3 = −81 μDALY/g, CI −37 to −110** (the upper CI is −110, not −113), and **sodium = 13.9, CI 11.5–16.1**. Use the SI values. The DRF relative uncertainty is largest for red meat and milk (~58% around the mean) and smallest for sodium and whole grains (~17%); PUFA and legumes are also relatively uncertain (S1.3, p. 7, lines 146–148).

---

#### ★ Worked HENI example — Suppl. §S2.2, p. 13 (lines 190–206). Our canonical unit test.

An 85 g serving of **chicken wings** decomposes to four HENI-active components: 1.85 g PUFA and 0.0281 g calcium (beneficial), 0.492 g sodium and 0.139 g TFA (detrimental); the rest (poultry) is health-neutral. Eq. S3:

$$\text{HENI}_{\text{chicken wing}} = -0.53 \times \left[ 1.85 \times (-0.60) + 0.0281 \times (-5.1) + 0.492 \times 13.9 + 0.139 \times 4.4 \right] = -3.3 \text{ min/serving}$$

Per-component minutes: PUFA +0.59, calcium +0.076 (gained); sodium −3.6, TFA −0.33 (lost); net **−3.3 minutes of healthy life per serving**. This is exactly the chicken-wing test value already in the C15 entry, now with the full arithmetic so we can assert each intermediate term in a unit test. Note sodium dominates (0.492 g × 13.9 = 6.84 μDALY) — a good sanity check that the sodium DRF is wired correctly.

**The μDALY → minutes constant, derived explicitly (ref 65, p. 98, line 1291):** 1 μDALY = 1 yr × 365 × 24 × 60 × 10⁻⁶ = 0.53 min, hence the **−0.53 min/μDALY** HENI constant. This nails down the constant our pipeline hard-codes.

---

#### Dietary risk definitions and TMRELs — Suppl. Table 1, pp. 4–5 (lines 79–99)

Each risk has a GBD-defined **theoretical-minimum-risk effective intake** (the threshold beyond which the marginal DRF applies) and an associated outcome set. Values our categorizer/exposure logic should respect: calcium <1.25 g/day (colorectal cancer); fiber <23.5 g/day (IHD + colorectal cancer); PUFA <11% energy (IHD); omega-3 seafood <250 mg/day (IHD); sodium >3.49 g/day dietary (15 outcomes, mediated via SBP); TFA >0.5% energy (IHD); fruits <250 g/day (10 outcomes); milk <435 g/day (colorectal cancer); nuts/seeds <20.5 g/day (T2DM, IHD); processed meat >2 g/day (T2DM, IHD, colorectal cancer); legumes <60 g/day (IHD); red meat >22.5 g/day (T2DM, colorectal cancer); SSB >2.5 g/day (38 outcomes, mediated via BMI); vegetables <360 g/day (haemorrhagic + ischaemic stroke, IHD); whole grains <125 g/day (T2DM, haemorrhagic + ischaemic stroke, IHD). The sodium effective-intake conversion: urinary→dietary at 0.85 (3 g urinary/day ÷ 0.85 = 3.49 g dietary/day). Definitions sourced from Gakidou et al. 2017 (GBD 2016).

**Mediated risks (S1.2, pp. 5–7):** sodium acts through systolic blood pressure (Eq. S1; effect modifiers race and hypertension status; urinary-to-dietary factor f = 0.86, SE 1.6%; SBP reference 10 mmHg); SSB acts through BMI (Eq. S2; modifier BMI ≥25 vs <25; BMI reference 5 kg/m²; 226.8 g/day reference serving). These two-step mediations are why SSB and sodium carry far larger outcome sets than the directly-acting risks.

---

#### Sensitivity analyses — added sugar, SFA, TFA (S2.6–S2.8, pp. 25–31). Directly relevant to our §3.2 design choices.

- **Added sugar (S2.6, p. 25, Eq. S4):** not a GBD risk, so excluded from base HENI. If included, an extrapolated DRF of **0.51 μDALY/g added sugar (95% CI 0.33–0.69)**, derived as half the SSB burden per gram of added-sugar equivalent. Effect is minor for ~85% of foods (<1 min lost/serving) but shifts desserts, candy, sweet bakery, sweetened dairy drinks and RTE cereals by 3–4 min lost. Useful precedent if a reviewer asks why we (presumably) follow GBD and omit added sugar from HENI.
- **Saturated fat (S2.7, pp. 27–29, Eq. S5):** excluded from base HENI (mediated via total cholesterol; conversion 0.045 mmol/L per 1% energy from SFA, CI 0.038–0.051; fat energy 9.25 kcal/g). Median HENI_SFA ranges 0.008–3.9 min lost; coconut milk worst at 17 min lost, but the authors flag source-specific SFA effects (coconut, dairy may be neutral/protective) so SFA contributions "should be interpreted with caution."
- **TFA (S2.8, pp. 29–31):** TFA *is* in base HENI but is the weakest-supported component — **~60–63% of WWEIA foods have imputed TFA** (regression model, R² = 0.69, S2.1 p. 12) and TFA burden is declining since the 2013 US partial-hydrogenation phase-out. Median HENI_TFA mostly <2 min lost; ruminant-TFA foods (red meat 0.41, cheese 0.40, milk 0.20 min lost/serving; Suppl. Table 6 p. 31). **This is a real limitation for us:** if our CNF pipeline lacks measured TFA, our HENI TFA term inherits the same imputation uncertainty, and the component may be near-obsolete for recent Canadian formulations.

---

#### Double-counting carve-outs — S2.9, pp. 35–36 (lines 490–505). Implementation rules our HENI module must encode.

1. **Milk vs calcium:** DRF_milk is applied **only** to foods classified "milk" and "flavored milk"; for all other foods only the calcium benefit is counted (avoids double-counting the colorectal-cancer benefit). This matches the rule already in the C15 entry.
2. **Fiber split:** two source-specific fiber DRFs. DRF_fiber(f,v,l,w) counts **only colorectal-cancer** benefit (its IHD benefit is already mediated through the fruit/vegetable/legume/whole-grain DRFs); DRF_fiber(other) counts **both colorectal cancer and IHD**. This is the mechanistic reason there are 16 components for 15 risks, and it must be implemented exactly or fiber benefits will be double-counted.
3. **TFA** double-counting was checked via the S2.8 sensitivity study.

---

#### Environmental LCA + uncertainty methodology (S3, pp. 37–58) — primary source for our §3.6

**Note on LCIA method:** the environmental side uses **IMPACT World+ v1.4** (Bulle et al. 2019), *not* ReCiPe — Suppl. Table 7 (pp. 46–47) lists the indicator set and units. This reinforces the C15 cross-link: if we adopt ReCiPe (Group A) we cannot reuse these endpoint factors directly. PM2.5 and water use use improved methods (US-specific PM2.5 CFs in Suppl. Table 8, p. 47: PM2.5 1.13×10⁻⁴, SO₂ 7.52×10⁻⁵, NOx 3.80×10⁻⁵, NH₃ 9.37×10⁻⁵ DALYs/kg).

**The uncertainty framework we should mirror (S3.5, pp. 47–52):**
- Uncertainty expressed as **squared geometric standard deviation GSD²** under a lognormal assumption (95% of estimates fall within median ÷ GSD² and median × GSD²). This is the same GSD²-based scheme noted in the C15 entry and is directly portable to our Monte Carlo layer.
- **Overall GSD² (Eq. S6)** combines a *base* uncertainty with three *pedigree* components (LCI match, loss/waste, consumable-amount adjustment) in quadrature of log-GSD² terms.
- **Pedigree GSD² ranges (Suppl. Table 9, p. 49):** LCI match 1–1.5; loss/waste 1–5; consumable-amount 1–1.5 (scored on a 1–5 data-quality scale). A concrete, citable alternative to the ecoinvent pedigree matrix our §3.6 currently falls back to.
- **Base uncertainty (Eq. S7) by impact category (Suppl. Table 10, p. 51):** GSD²_LCI ranges from ~1.18 (terrestrial acidification, marine eutrophication) to ~2.56 (ionizing radiation); midpoint LCIA pedigree gives GSD² 1.4–10; **endpoint LCIA pedigree gives GSD² 2.5–1000** (the midpoint→endpoint conversion is the dominant uncertainty, esp. human toxicity non-cancer at GSD²_LCI 6.39). These are realistic per-category priors we can borrow when Poore & Nemecek (A4) does not cover a category.
- **GHG GSD² (Eq. S8):** CO₂ assigned GSD²=1 (reference), other GHGs (CH₄, N₂O) GSD²=1.4 per IPCC 2013, combined by the fraction of GWP from fossil CO₂. This is a cleaner, citable basis for the GWP uncertainty in our pipeline than a flat assumption.
- Propagation is **analytical Taylor-series** (Hong et al. 2010), Eq. S9 — an alternative to our Monte Carlo, useful as a cross-check.

---

#### Correlation structure across indicators — Suppl. Fig. 17, pp. 76–77. Supports our multi-indicator argument.

Per-serving Pearson correlations (Fig. 17A): most environmental midpoints correlate with global warming at **r > 0.90**, **except consumptive water use (~0.50) and freshwater ecotoxicity (~0.40–0.52)**. HENI correlates only **0.26–0.31** with GW/water (and 0.08–0.44 across all environmental indicators). On a per-100-kcal basis (Fig. 17B) the HENI–environment correlations collapse further (−0.16 to 0.4, several near zero). **This is independent corroboration of the Poore & Nemecek "single-indicator proxies are weak" point we make in §1**, from the HENI side: health burden is essentially orthogonal to environmental burden, and water/ecotoxicity are orthogonal to carbon. Good supporting citation for our multi-indicator design alongside C17.

**HENI ≈ total human-health damages (Suppl. Fig. 18, p. 78):** HENI vs total human-health damages (nutrition + environmental) regresses at **y = 1.04x − 1.0, R² = 0.98**, i.e. nutritional health effects dominate total human-health damages — the same "1–2 orders of magnitude" point in the C15 entry, here as a tight regression we can cite.

---

#### Recommendation-zone thresholds — Suppl. Table 11, pp. 63–64. Numeric cut-offs for our classification layer.

Suppl. Table 11B gives the **exact per-indicator zone limits** on both a per-serving and per-100-kcal basis (the C15 entry has the qualitative scheme; this is the numeric version). Nutrition: Beneficial HENI > 0; Slightly detrimental 25th pctl–0 (per serving: −3.2 to 0); Detrimental ≤25th pctl (≤ −3.2/serving, ≤ −1.6/100 kcal). Environment (per serving, Low/Moderate/High at 50th/75th pctl), selected: GW shorter-term [0,0.32)/[0.32,0.61)/[0.61,∞) kg CO₂eq; land [0,0.24)/[0.24,0.70)/… ha-yr; water [0,20)/[20,45)/… L; freshwater eutrophication [0,0.23)/[0.23,0.67)/… g PO₄-P. The 0.32 and 0.61 kg CO₂eq GW cut-offs match the C15 green/red thresholds exactly — confirming those numbers. Full table to be reproduced in our Supplementary if we adopt a zone scheme.

---

#### Food-decomposition pipeline — S3.1–S3.3, pp. 38–43. Methodological precedent for our CNF→LCA matcher (§3.5).

Stylianou maps WWEIA foods to LCI through a **tiered ingredient decomposition**: SR v.28 standard recipes (tier 1, 281 ingredients from 169 foods) → FCID agricultural commodities (tier 2, 98 ingredients) → FICRCD dairy commodities (tier 3); 344 unique ingredients total, 306 matched to 120 LCIs (~60% direct, ~40% proxy). This is the closest published analogue to **our AI-assisted food-to-LCA matcher (§3.5)** — worth citing as the manual, expert-judgment precedent that our LLM matcher aims to automate and scale. Their honest "~40% proxy LCIs by expert judgment" admission is exactly the laborious, non-reproducible matching our §3.5 is designed to replace.

---

#### Author-flagged limitations specific to the SI (for §7, supplementing the C15 list)

- **TFA imputation (S2.8):** ~60% of foods have imputed TFA; component near-obsolete post-2013 — our pipeline inherits this if CNF lacks measured TFA.
- **System boundary cradle-to-farm/processor-gate (S3.6, p. 55):** post-farm-gate stages omitted, so impacts underestimated; per Poore & Nemecek post-farm-gate adds ~18% to climate (processing 4%, transport 6%, packaging 5%, retail 3%). Relevant if we claim completeness for our LCA.
- **Water use under-spatialised (S3.4–S3.6):** only ~15% of LCIs are US-specific; milk blue-water in WFLDB (15 L/kg) vs US actual (50–200 L/kg) — a 3–13× gap. A cautionary precedent for our Canadian water factors (§3.7).
- **Loss/waste applied at ingredient level (S3.6, p. 56):** may overestimate food-level impacts; loss/waste is >60% of impact for fruit/veg, ~25% for beef/pork/lamb.

---

#### Three-sentence relevance note

This supplement is the authoritative home of the **DRF μDALY/g factor table (Suppl. Table 3, p. 8)** that the C15 main-text entry could not supply, giving us all 16 risk-component values with 95% CIs to reconcile our `heni_calculator` against cell-by-cell, and it corrects two numbers we had carried (omega-3 upper CI is −110 not −113; sodium 13.9 not 14). It also pins down the **−0.53 min/μDALY constant** with its derivation, the **fully worked chicken-wing example (−3.3 min/serving)** for unit-testing, the **milk-calcium and fiber-source double-counting rules** our HENI module must encode, and the **complete GSD²/pedigree/Taylor-series uncertainty methodology (S3.5)** that is directly portable to our §3.6 (including per-category base GSD² priors and the CO₂=1 / other-GHG=1.4 GWP scheme). The standing caveat for our methods is that the environmental side uses **IMPACT World+ v1.4, not ReCiPe**, so the endpoint factors and zone thresholds here (Suppl. Tables 7, 11) cannot be transplanted into a ReCiPe pipeline without re-derivation; cite as Stylianou et al. 2021 Supplementary Information, Nat Food 2(8):616–627, doi:10.1038/s43016-021-00343-4.

---

### C16. Stylianou (2018) — Health-based food evaluation (PhD thesis): the 14-factor μDALY/g table [★★★]

**Citation.** Stylianou KS. Nutritional and Environmental Impacts of Foods on Human Health (Ch. 4: health-based food evaluation). PhD thesis, University of Michigan, 2018. (Cited as ref. 81 in C15.)

**✓ Factor table now retrieved — see C15-SI.** This entry was originally a placeholder held open because the wishlist marks the thesis as the origin of the per-risk μDALY/g factor table. **That table has now been obtained** in its published form as **Suppl. Table 3 of C15 (see entry C15-SI)**, so the numerical reconciliation no longer depends on retrieving the thesis PDF itself. The thesis (Ch. 4) is still the place to cite if we need the *original derivation* of the framework or the spatially-explicit PM2.5 characterisation factors (the thesis is also cited as ref. 62 in C15-SI for the PM2.5 CFs in Suppl. Table 8).

**What we know so far.** The thesis develops the health-based food evaluation in which Stylianou's HENI uses dietary risk factors to compute a μDALY/g score quantifying the marginal health burden (positive or negative) of food consumption from Global Burden of Disease data. This is the **direct precursor to C15**. **Note on the "14-factor" framing:** the C15 published form is unambiguously **15 dietary risks / 16 risk components** (confirmed by C15-SI Suppl. Table 3, which lists 16 rows; fibre is split into f,v,l,w and other). The Dutch adaptation (C17) uses a 14-component list. The "14 factors" attributed to the thesis should be treated as provisional until the thesis PDF is seen — given the published table has 16 components, the count attribution in the wishlist may itself need correcting, and we should not assert "14" in the manuscript without the thesis in hand.

**Action for us.** Treat **C15-SI (Suppl. Table 3) as the citable home of the μDALY/g factor values** and the algorithm; cite C16 (the thesis) only if we need to attribute the *original* framework derivation, discuss the evolution of the factor count, or cite the PM2.5 spatially-explicit CFs. No further numerical reconciliation is blocked on this entry.

---

### C17. Cardinaals, Verly, Jolliet et al. (2024) — Complementarity of nutrient density and disease burden for nLCA [★★★]

**Citation.** Cardinaals RPM, Verly E Jr, Jolliet O, Van Zanten HHE, Huppertz T. The complementarity of nutrient density and disease burden for Nutritional Life Cycle Assessment. Front Sustain Food Syst. 2024;8:1304752.

**DOI.** 10.3389/fsufs.2024.1304752 (open access, CC BY; received 29 Sep 2023, published 30 May 2024)

**Type.** Original-research methodology paper comparing two nutrition indicators (a 24-nutrient Nutrient Rich Food index, NRF24, and HENI) against each other and against environmental indicators, for 1,826 Dutch foods. Jolliet (co-author of C14/C15) links this directly to the HENI lineage. Funding: none declared; authors declare no COI, though Huppertz is affiliated with FrieslandCampina (a dairy company), worth a quiet note.

---

#### Why this paper matters most to us: ReCiPe + HENI portability

Two features make C17 unusually relevant:

1. **It pairs HENI with ReCiPe 2016 (hierarchical), not IMPACT World+.** The environmental side uses ReCiPe 2016 H (Huijbregts et al. 2017, our **A1**) for GWP, land use and freshwater use. So C17 is a published precedent for exactly the HENI + ReCiPe combination our platform may adopt, in contrast to C15's HENI + IMPACT World+. This resolves the A-vs-IMPACT-World+ tension flagged in C15: it is legitimate to run HENI alongside ReCiPe.
2. **It is the HENI portability blueprint.** HENI was recomputed for the Netherlands by **updating to GBD 2019 relative risks and substituting Dutch burden rates for US ones** (Methods 2.2). This is precisely the procedure our §3.7 needs for Canada and France: keep the algorithm, swap in local burden rates and the latest GBD RRs.

---

#### The two nutrition indicators (Methods 2.1–2.2)

**NRF24 (nutrient density), per 100 kcal (Eq. 1):**

$$\text{NRF24} = \left( \sum_{i=1}^{24} \frac{EN_i}{DRI_i} \right) \times \frac{100}{E}$$

where EN_i is essential-nutrient content per 100 g, DRI_i the Dutch daily recommended (or adequate) intake, E the energy (kcal/100 g), each nutrient **capped at 100 % of its DRI**. The 24 essential nutrients: protein, three essential fatty acids (DHA, ALA, LA), sodium, potassium, calcium, phosphorus, magnesium, iron, copper, selenium, iodine, zinc, and vitamins A, C, D, E, B1, B2, B3, B6, B9, B12. NRF24 is a deliberate adaptation of NRF9.3 that **strips out the "limit" and disease-risk components (saturated fat, added sugar, fibre)** so it reflects only essential-nutrient adequacy, leaving disease risk entirely to HENI. For reference, NRF9.3 (Fulgoni et al. 2009, our **B-group lineage**) sums % RDI for 9 nutrients to encourage (protein, fibre, vitamins A/C/E, calcium, iron, magnesium, potassium) minus % RDA for 3 to limit (sodium, saturated fat, added sugar) per 100 kcal.

**HENI (disease burden), per 100 kcal (Eq. 2):**

$$\text{HENI} = -0.53 \times \left( \sum_{i=1}^{15} DRF_i \times R_i \right) \times \frac{100}{E}$$

with DRF_i the dietary risk factor (μDALY/g), R_i the risk-component content per 100 g, E energy (kcal/100 g). **The −0.53 min/μDALY constant is identical to C15**, confirming that value.

**⚠ 14-vs-15 component note (ties to C16).** The HENI summation here is written to 15, but the explicitly listed risk components number **14**: calcium, fibre, omega-3 from seafood, PUFA, trans fatty acids, sodium, fruits, vegetables, milk, legumes, nuts and seeds, red meat, processed meat, whole grains. SSBs are referenced separately in the Discussion as being captured in HENI (so possibly the 15th), and unlike C15 there is no separate fibre-source split. This matches the **14-factor formulation attributed to C16** and is fewer than C15's 15 risks / 16 components. We should record that the HENI factor count is not fixed across the literature: 14 (thesis C16, Dutch C17) vs 15/16 (US C15).

**DRF computation (Dutch):** a non-linear optimisation fits the best dose-response curve to the GBD's **81 risk-outcome-specific relative risks** (far fewer than C15's 479, reflecting GBD 2019 + Dutch scope + 14 risks), giving change in risk per g change in intake; multiplied by Dutch observed burden rates (μDALY per 100,000 per year) to yield DRFs in μDALY/g. Risk-component content comes from the NEVO composition data (for calcium, fibre, omega-3, PUFA, TFA, sodium) or from the nature of the food (for fruits, vegetables, milk, legumes, nuts, red/processed meat, whole grains); composite foods use Albert Heijn retailer ingredient lists.

**Double-counting carve-outs (extends C15's milk-calcium rule):** diseases already captured in the calcium, sodium and fibre DRFs are excluded from the disease sets of milk, processed meat, and fruit/vegetables/legumes respectively.

---

#### Environmental side (Methods 2.3)

LCA for **200 of the 1,826 foods** (de Valk et al. 2016 / RIVM 2023): attributional, ISO 14040/44, cradle-to-consumer including end-of-life for losses and packaging. LCI from Agri-footprint + ecoinvent v3 + Blonk; economic allocation (physical for milk, IDF 2015). Characterised with **ReCiPe 2016 hierarchical** at midpoint: GWP (CO2/CH4/N2O as CO2-eq), land use (m²·yr), freshwater consumptive use (m³/kg), all recalculated per 100 kcal.

---

#### Key results (Results 3.1–3.4)

- **NRF24 vs HENI is essentially uncorrelated overall:** Spearman r = 0.21 per 100 kcal (p < 0.05) in Results 3.1, cited as r = 0.32 in Discussion 4.1 (an internal inconsistency worth noting); either way "very weak." This is the paper's central finding: **nutrient density and disease burden are independent and complementary**, so a high-nutrient-density food is not necessarily low-disease-burden.
- **Strongly food-group-dependent:** plant-source foods show positive NRF24-HENI correlation (r = 0.62; fruits 0.63, vegetables 0.62, tubers 0.53), animal-source negative (r = −0.13; significant negatives for poultry, fish, processed meat, red meat). Nuts/seeds (0.16) and legumes (0.12) not significant.
- **Score ranges (per 100 kcal):** NRF24 0.0 to 12.0 (highest Fish, Vegetables; lowest Sweets & Snacks, Cereal grains, Condiments); HENI **−38.8 to +50.5 min** healthy life (highest Vegetables; lowest Red Meat, Processed Meat).
- **Nutrition vs environment correlations are weak:** NRF24-GWP r = 0.69 (the strongest), NRF24-LU 0.37, NRF24-WU 0.42; HENI-GWP and HENI-LU not significant, HENI-WU only 0.35. HENI-vs-GWP is U-shaped (both very-low and very-high HENI foods can have high GWP).
- **+/+ classification (Table 1):** threshold NRF24 ≥ 1.2 (= optimal 24 per 2000 kcal ÷ 20) and HENI ≥ 0. 44 % of foods are +/+, 11 % −/−. Vegetables 98 % +/+, fish 76 % +/+, red meat 97 % +/− (high density, high burden), processed meat 72 % +/−.

---

#### Sensitivity analyses (Results 3.3)

- **Reference unit matters:** the weak overall NRF24-HENI correlation holds across bases (r = −0.16 per 100 g, r = 0.00 per serving), but food-group correlations shift; energy basis favours low-energy foods (fruits, vegetables) nutritionally while raising their per-100-kcal environmental impact.
- **Sodium:** NRF23 (excluding sodium) vs NRF24 r = 0.99, so including sodium as an essential nutrient does not skew NRF24; sodium's detrimental effect is better left to HENI.
- **NRF9.3 vs HENI** (r = 0.38) is higher than NRF24 vs HENI (r = 0.20) because NRF9.3 shares sodium and fibre with HENI and proxies added sugar via SSBs, i.e. overlap inflates the correlation, which is the argument for using the overlap-free NRF24 beside HENI.

---

#### Author-flagged limitations (Discussion 4.4–4.7) — for our §7

1. **Indicator overlap / double counting.** NRF24 and HENI both include calcium and omega-3 (which are essential nutrients *and* GBD disease-risk components), so combining them may double-count those health effects; there is no evidence that the inadequate-intake and disease-risk channels are independent. Directly relevant if our platform reports both an NRF-type index and HENI.
2. **HENI is marginal.** Valid only for marginal dietary shifts within the current food environment; not valid for radically redesigned diets, because DRFs rest on current exposure and LCA on current production. Reinforces the C15 marginality caveat.
3. **Food-item vs diet level.** GBD risks are defined at the dietary level; HENI pushes them to the food-item level, and nutrient adequacy at the diet level can contradict food-item-level findings.
4. **No generic cut-offs** exist for "high"/"low" environmental impact, complicating classification and labelling.
5. **Reference-unit and food-group-definition choices** strongly affect interpretation; the authors recommend reporting multiple reference units and note within-group variability makes group-level conclusions reductive.
6. **Portability is robust in one direction:** the lack of NRF-HENI correlation holds across US (C15), Switzerland (Ernstoff et al. 2020) and the Netherlands, so the complementarity finding is not an artefact of one data source.

---

#### Cross-links

- **A1 (ReCiPe 2016, Huijbregts et al.)** is the LCIA method used here; C17 is our worked precedent for HENI + ReCiPe.
- **C15 (HENI)** is the method this paper recomputes for the Netherlands; C17 confirms the −0.53 constant and the double-counting logic, and supplies the portability procedure.
- **C16** is the origin of the 14-factor count that C17 uses.
- **B-group NRF / nutrient-density indices** connect through NRF9.3/NRF24 (Fulgoni et al. 2009).

---

#### Three-sentence relevance note

C17 is the most directly actionable Group C paper for our build because it does two things our platform needs: it runs HENI alongside ReCiPe 2016 (hierarchical), establishing that the HENI + ReCiPe combination is legitimate rather than requiring IMPACT World+, and it demonstrates HENI portability by recomputing the index for the Netherlands using GBD 2019 relative risks and Dutch burden rates, which is exactly the procedure our §3.7 must follow for Canada and France. Its central empirical finding, that essential-nutrient density (NRF24) and disease burden (HENI) are uncorrelated overall (r ≈ 0.2 to 0.3) and only weakly correlated with GWP, land and water, is the strongest available justification for our multi-indicator design and against collapsing health and environment into a single score. The key caveats for our §7 are the calcium/omega-3 double-counting risk when an NRF-type index is reported beside HENI, the strict marginality of HENI, and the food-item-versus-diet-level tension; cite as Cardinaals et al. 2024, Front Sustain Food Syst 8:1304752, doi:10.3389/fsufs.2024.1304752.

---

### C18. GBD 2017 Diet Collaborators (2019) — Health effects of dietary risks in 195 countries: the 15-risk-factor source dataset behind HENI [★★★]

**Citation.** GBD 2017 Diet Collaborators (Afshin A, Sur PJ, Fay KA, Cornaby L, Ferrara G, Salama JS, Mullany EC, ... Willett WC, ... Murray CJL). Health effects of dietary risks in 195 countries, 1990–2017: a systematic analysis for the Global Burden of Disease Study 2017. Lancet. 2019;393(10184):1958–1972.

**DOI.** 10.1016/S0140-6736(19)30041-8 (Open Access, CC BY 4.0; published online 3 April 2019; corrected version first appeared 24 June 2021). Funding: Bill & Melinda Gates Foundation; the funder had no role in design, analysis, interpretation, or writing (p. 1961, Role of the funding source).

**Type.** Comparative risk-assessment (CRA) study, part of the GBD enterprise. This is the upstream epidemiological source for the dietary risk factors, exposure definitions, optimal intakes, and disease-burden machinery that HENI (C15/C16) operationalises at the food-item level. Lead author Afshin and senior authors Mozaffarian, Micha and Willett also appear across the HENI and Food Compass lineages, so this is the connective tissue between Groups B and C.

---

#### Why this paper matters most to us: it is the foundation HENI sits on

HENI converts the GBD's diet-disease epidemiology into a per-gram μDALY factor (the DRF) for each risk component. This paper is where those risk components, their exposure definitions, and their optimal-intake midpoints come from. Three things our manuscript needs directly:

1. **The canonical list of 15 dietary risk factors** (the table, p. 1960) — the master set from which HENI's 14-factor formulation (C16/C17) is drawn. This resolves part of the 14-vs-15-vs-16 count question we have been tracking: GBD 2017 defines **15** risk factors; HENI variants drop or merge some (e.g. the seafood-omega-3 / PUFA split, SSBs) to land at 14 in the thesis (C16) and Dutch (C17) implementations.
2. **Optimal-intake levels (TMREL midpoints)** for every risk factor (p. 1960 table) — the reference points against which intake gaps are computed. Our §3.4 categorizer maps CNF foods to exactly these risk factors.
3. **The comparative-risk-assessment method** (PAF × disease-specific deaths/DALYs; p. 1960 Disease burden of dietary risks) — the formal pipeline whose marginal-effect logic HENI inherits and whose limitations our §7 must engage with.

**Important version note.** This is **GBD 2017**, using GBD 2017 relative risks and burden estimates. Our manuscript states HENI factor values currently rest on **GBD 2019** epidemiology (§7.4, manuscript line 263), and C17 recomputes HENI on **GBD 2019** relative risks. C18 is therefore the *methodological and definitional* reference (the 15-factor framework, exposure definitions, optimal intakes, CRA approach), **not** the numerical-RR source for our current factor table. When we cite specific RR or DRF values we must cite the GBD vintage actually used (2019), with C18 cited for the framework and definitions. Flag this explicitly so a reviewer does not read C18 as our RR source.

---

#### The 15 dietary risk factors, exposure definitions, and optimal intakes (Table, p. 1960)

Reproduce this table in our SI (it is the definitional backbone of the §3.4 categorizer). Optimal level = midpoint of the optimal range; "high"/"low" intake is defined relative to that midpoint (p. 1961, top-left).

| # | Risk factor | Exposure definition (abbreviated) | Optimal intake (range) | Data representativeness index |
|---|---|---|---|---|
| 1 | Diet low in fruits | Fresh/frozen/cooked/canned/dried fruits; excl. fruit juices, salted/pickled | 250 g/day (200–300) | 94.9% |
| 2 | Diet low in vegetables | Excl. legumes, salted/pickled, juices, nuts, seeds, starchy veg (potatoes/corn) | 360 g/day (290–430) | 94.9% |
| 3 | Diet low in legumes | Fresh/frozen/cooked/canned/dried legumes | 60 g/day (50–70) | 94.9% |
| 4 | Diet low in whole grains | Bran/germ/endosperm in natural proportion (cereals, bread, rice, pasta, etc.) | 125 g/day (100–150) | 94.9% |
| 5 | Diet low in nuts and seeds | Nut and seed foods | 21 g/day (16–25) | 94.9% |
| 6 | Diet low in milk | Non-fat/low-fat/full-fat milk; excl. soy milk and plant derivatives | 435 g/day (350–520) | 94.9% |
| 7 | Diet high in red meat | Beef, pork, lamb, goat; excl. poultry, fish, eggs, all processed meats | 23 g/day (18–27) | 94.9% |
| 8 | Diet high in processed meat | Meat preserved by smoking, curing, salting, or chemical preservatives | 2 g/day (0–4) | 36.9% |
| 9 | Diet high in sugar-sweetened beverages | Beverages ≥50 kcal per 226.8 g serving; excl. 100% fruit/veg juices | 3 g/day (0–5) | 36.9% |
| 10 | Diet low in fibre | Fibre from all sources (fruits, veg, grains, legumes, pulses) | 24 g/day (19–28) | 94.9% |
| 11 | Diet low in calcium | Calcium from all sources (milk, yogurt, cheese) | 1.25 g/day (1.00–1.50) | 94.9% |
| 12 | Diet low in seafood omega-3 fatty acids | EPA + DHA | 250 mg/day (200–300) | 94.9% |
| 13 | Diet low in polyunsaturated fatty acids | Omega-6 from all sources (mainly liquid vegetable oils) | 11% of total daily energy (9–13) | 94.9% |
| 14 | Diet high in trans fatty acids | Trans fat from all sources (PHVOs, ruminant products) | 0.5% of total daily energy (0.0–1.0) | 36.9% |
| 15 | Diet high in sodium | 24 h urinary sodium, g/day | 3 g/day (1–5)* | 26.2% |

*Sodium optimal-intake uncertainty (table footnote, p. 1960): the 1–5 g/day range reflects that <2.3 g/day is associated with the lowest blood pressure in RCTs while 4–5 g/day is associated with the lowest CVD risk in observational studies. For sodium the optimal level itself was sampled from a uniform distribution in the uncertainty analysis (p. 1960, Optimal level of intake).

**Selection criteria for the 15 factors (p. 1959, Selection of dietary risk factors):** importance to disease burden or policy; sufficient exposure data; strength of epidemiological evidence for a causal diet-disease relationship plus a quantifiable dose-response; and generalisability across populations.

**For our categorizer:** note that 11 of 15 factors have a 94.9% data-representativeness index, but processed meat, SSBs, trans fat (36.9%) and sodium (26.2%) are far sparser. This is upstream exposure-data sparsity, separate from but worth distinguishing against our own categorization confidence.

---

#### Headline burden results (for framing in §1 / §6, with care)

- **Global diet-attributable burden, 2017 (Findings, p. 1958; Results, p. 1961):** 11 million deaths (95% UI 10–12) = 22% (21–24) of all adult deaths, and 255 million DALYs (234–274) = 15% (14–17) of all adult DALYs.
- **The three leading risks** (more than half of diet-related deaths and two-thirds of diet-related DALYs; p. 1965, Impact of individual components): high sodium (3 million deaths [1–5]; 70 million DALYs [34–118]); low whole grains (3 million deaths [2–4]; 82 million DALYs [59–109]); low fruits (2 million deaths [1–4]; 65 million DALYs [41–92]).
- **Cardiovascular disease dominates** diet-related mortality: 10 million deaths (9–10) and 207 million DALYs (192–222), followed by cancers and type 2 diabetes (p. 1961).
- **"One in five deaths"** framing (Discussion, p. 1967): improving diet could potentially prevent one in five deaths globally; suboptimal diet is responsible for more deaths than any other risk including tobacco. *(Use this carefully; it is the paper's headline and is widely quoted, but the authors temper it heavily in their own limitations.)*
- **Ranking is robust to geography:** low whole grains was the most common leading risk for deaths (16 of 21 regions) and DALYs (17 of 21 regions); high sodium led in East Asia and high-income Asia Pacific (p. 1965).
- **All statistical analyses in Python 3.5; 1000-draw Monte Carlo** for parameter and model uncertainty, reporting mean and 95% UI (p. 1961, Methods). This Monte Carlo precedent is a small cross-link to our own uncertainty approach (Group F), though our N = 10 000 is larger.

---

#### Methodological structure HENI inherits (Methods, pp. 1959–1961)

1. **Exposure estimation:** spatiotemporal Gaussian process regression for mean intake by age/sex/country/year; 24 h diet recall treated as the gold standard, with availability/sales/household data adjusted to it.
2. **Effect sizes:** relative risks from published meta-analyses of prospective observational studies; for diet-disease pairs with morbidity-only evidence, the morbidity RR was assumed to apply to mortality; age-trends of metabolic-risk RRs applied to CVD and T2D; sodium modelled via the urinary-sodium → systolic-BP → outcome chain.
3. **Optimal intake (TMREL):** level minimising all-cause mortality risk, computed as the death-weighted mean of disease-specific lowest-risk levels, with ±20% uniform uncertainty.
4. **Burden:** PAF per diet-disease pair × disease-specific deaths/DALYs from GBD 2017, by age/sex/country/year.

This is exactly the chain HENI compresses into a single μDALY/g DRF. Our §3.4 and §7 should cite C18 for the definitions and the CRA structure, and C15/C16/C17 for the conversion of that structure into the per-food HENI factor.

---

#### Author-flagged limitations (Discussion, pp. 1968–1969) — directly usable in our §7

These are the epidemiological-foundation caveats our HENI numbers inherit. The strongest ones for our §7:

1. **Observational-evidence limitation (p. 1968–1969).** Effect sizes come mostly from meta-analyses of prospective observational studies; residual confounding cannot be excluded, and the strength of evidence is generally *weaker* than for established risks such as tobacco or systolic blood pressure, and varies across foods and nutrients. This is the single most important caveat to carry into our §7 when we report HENI: the disease-burden indicator rests on observational epidemiology of uneven strength.
2. **Energy-adjustment / substitution ambiguity (p. 1968).** Because most cohorts adjust for total energy intake, diet components are defined as risks *in terms of share of diet, not absolute exposure*; an increase in one component implies a compensating decrease in another, but the meta-analytic RRs do not specify the substitution. This directly affects how our diet-shift counterfactuals (S5: beef→legumes, etc.) should be interpreted: the RR of a swap depends on what is substituted, and HENI's marginal logic (C15/C17) is the food-item projection of this same caveat.
3. **Definitional heterogeneity (p. 1968).** The definition of dietary factors (e.g. "whole grains") varies across the source studies.
4. **Correlated risk factors may inflate individual effect sizes (p. 1968).** Healthy factors are positively correlated with each other and inversely with harmful factors; the independence assumption across factors within a unit of analysis could over- or under-estimate combined effects. The authors quantified this using NHANES individual-level data and found the absolute difference in joint PAFs averaged <2% (p. 1969).
5. **Publication bias and unpublished cohort data (p. 1969).**
6. **No undernutrition or obesity** forms of malnutrition were evaluated (p. 1969).
7. **Dietary-data sparsity and mixed sources** increase statistical uncertainty (Findings abstract p. 1958; p. 1969); sodium excluded spot-urine data, lowering its representativeness index (26.2%).
8. **Local food-composition gaps (p. 1968):** many countries rely on foreign food-composition tables (e.g. USDA), and mixed-dish recipes and product formulations vary across countries and time. Relevant to our CNF-based pipeline: it underlines why a Canada-specific composition source (CNF) plus the Rana et al. free-sugars supplement matters.

---

#### Conflict-of-interest note (p. 1971, Declaration of interests)

Several senior authors report food-industry relationships. Most relevant to our framework: **Dariush Mozaffarian** (also senior author of the Food Compass / FCS series, B9–B12) reports research funding from NIH and the Gates Foundation; personal fees from GOED, DSM, Nutrition Impact, Pollock Communications, Bunge, Indigo Agriculture, Amarin, Acasti Pharma, and America's Test Kitchen; advisory-board roles (some with stock options) with Elysium Health, Omada Health and DayTwo; and is co-inventor on two Tufts patents. **Renata Micha** reports grants from NIH, the Gates Foundation and Unilever, and personal fees from the World Bank and Bunge. We already disclose the Mozaffarian/Blumberg COI for Food Compass in §7.3; C18 reinforces that the same senior-author network spans the GBD diet, HENI and Food Compass literatures, which is worth a single clean disclosure rather than three scattered ones.

---

#### Cross-links

- **C15 (HENI, Stylianou et al. 2021)** converts this paper's CRA structure into per-food μDALY/g DRFs; C18 is the definitional/epidemiological source those DRFs rest on.
- **C16 (Stylianou thesis)** and **C17 (Cardinaals et al. 2024)** use a **14-factor** subset of the 15 defined here; C18 is where the master 15-factor list is defined, resolving the count-discrepancy lineage.
- **C17** recomputes HENI on **GBD 2019** RRs and Dutch burden rates; C18 is the **GBD 2017** vintage, so cite C18 for framework/definitions and the appropriate GBD vintage for numerical RRs.
- **Manuscript §3.4 / Highlight A2** ("maps food items to GBD dietary risk factors") and **§7.4** ("HENI factor values rest on GBD epidemiology, currently GBD 2019") should both cite C18 for the risk-factor definitions and the CRA approach.
- **Reference #42 in C18's own bibliography is Heller, Keoleian & Willett (2013)** — our wishlist E32 / manuscript reference 23 — confirming that the diet-environment integration our paper performs was already being called for within the GBD diet network.
- **Group F (uncertainty):** C18's 1000-draw Monte Carlo over exposure/RR/optimal-intake/mortality is a domain precedent for parameter-uncertainty propagation, though smaller than our N = 10 000.

---

#### Three-sentence relevance note

C18 is the epidemiological foundation of our entire HENI indicator: it defines the 15 GBD dietary risk factors, their exposure definitions and optimal-intake midpoints (Table, p. 1960), and the comparative-risk-assessment machinery (PAF × disease-specific DALYs, p. 1960) that HENI compresses into a single per-gram μDALY factor, so our §3.4 categorizer and §7.4 must cite it for the risk-factor framework and definitions. Critically, this is the GBD 2017 vintage, whereas our pipeline uses GBD 2019 relative risks (per §7.4 and C17), so C18 should be cited for the framework and definitions and not as the numerical-RR source; we must keep that distinction explicit for reviewers. Its author-flagged limitations, the uneven and largely observational strength of the diet-disease evidence, the energy-adjustment/substitution ambiguity that bears directly on our diet-shift counterfactuals, and the correlated-risk-factor caveat (joint-PAF effect <2%, p. 1969), are the core inheritance our §7 must engage with when presenting HENI; cite as GBD 2017 Diet Collaborators, Lancet 2019;393:1958–1972, doi:10.1016/S0140-6736(19)30041-8.

---

### C19. GBD 2023 Disease and Injury and Risk Factor Collaborators (2025) — the most recent GBD vintage, the burden-of-proof method, and the trans-fat TMREL revision [★★★]

**Citation.** GBD 2023 Disease and Injury and Risk Factor Collaborators (Hay SI, Ong KL, Santomauro DF, ... Brauer M, Vos T, Murray CJL, Gakidou E). Burden of 375 diseases and injuries, risk-attributable burden of 88 risk factors, and healthy life expectancy in 204 countries and territories, including 660 subnational locations, 1990–2023: a systematic analysis for the Global Burden of Disease Study 2023. Lancet. 2025;406(10512):1873–1922.

**DOI.** 10.1016/S0140-6736(25)01637-X (Open Access, CC BY 4.0; published online 12 October 2025). Funding: Gates Foundation and Bloomberg Philanthropies; funders had no role in design, analysis, interpretation, or writing (p. 1880, Role of the funding source).

**Type.** Combined GBD disease/injury burden and risk-attributable burden synthesis, the headline paper of the GBD 2023 cycle. **Scoping note for us:** unlike C18 (GBD 2017), this is *not* a dedicated dietary-risk paper. The 15 dietary risk factors appear here only inside the global summary-exposure-value (SEV) table (Table 2, pp. 1887–1888); per-diet-factor relative risks and attributable DALYs live in appendix 3 (tables S13, S17) and in the parallel risk-factor-specific Burden-of-Proof papers, not in this main text. C19 is therefore our reference for the **current GBD vintage, the current method, and the trans-fat TMREL change**, not a source of per-diet RR or DRF numbers.

---

#### Why this paper matters to us: it defines "current GBD" and one diet-factor change

Our manuscript states HENI factor values "currently rest on GBD 2019" (§7.4) and C17 recomputed HENI on GBD 2019. C19 is the next vintage after that. Three concrete things it gives us:

1. **The dietary risk factors persist unchanged in the GBD 2023 hierarchy.** GBD 2023 analysed 88 risk factors and 676 risk-outcome pairs (p. 1879); **no new risk factors were added** for 2023, though 50 new risk-outcome pairs were and two were removed (p. 1876, Methods). The 15 diet factors of C18 remain the operative diet set (Table 2 lists all 15: low fruits, vegetables, legumes, wholegrains, nuts and seeds, milk, calcium, seafood omega-3, omega-6 PUFA, fibre; high red meat, processed meat, SSBs, trans fat, sodium). This matters because it means a future GBD-2023-based HENI recompute would use the **same 15-factor scaffold** our pipeline already targets.
2. **One diet-relevant TMREL revision.** "the TMREL was revised for one risk factor: diet high in trans fatty acids" (p. 1880, and Research-in-context p. 1875). This is the single dietary-factor methodological change in GBD 2023 and the one we must note if we ever move HENI from GBD 2019 to GBD 2023: the trans-fat optimal-intake counterfactual changed.
3. **The current burden-of-proof (BPRF) method and mediation matrix.** GBD 2023 estimates relative risks for 256 of the 676 pairs via the burden-of-proof meta-regression (p. 1879), which fits non-linear ensemble-spline risk curves, trims outliers, and folds between-study heterogeneity into a star-rated risk-outcome score (ROS, 1–5 stars; appendix 2 table S8). Dietary risks are explicitly noted as mostly acting through mediating metabolic risks (e.g. high sodium to hypertensive heart disease via high SBP), handled by the GBD 2023 mediation matrix of 165 mediated pairs (p. 1879). This is the methodological machinery any GBD-2023 HENI recompute inherits.

---

#### The comparative-risk-assessment chain (Methods, pp. 1878–1880) — what HENI's DRFs would inherit at this vintage

Same four-input CRA structure as C18, now with updated tooling:

1. **Exposure:** mean exposure by age-sex-location-year via ST-GPR or DisMod-MR 2.1; distribution fitted as an ensemble of parametric distributions to predicted mean and SD; summarised as SEVs (p. 1879).
2. **Relative risk:** from meta-analyses of RCTs and prospective cohorts; for 256 pairs the burden-of-proof framework replaces the older log-linear assumption (p. 1879).
3. **TMREL:** counterfactual minimum-risk exposure, set to zero where achievable, empirically derived otherwise; **for protective risks (which includes the "low intake of X" diet factors) the TMREL is generally set at the 85th percentile of observed exposure** to avoid extrapolating beyond the data-rich range (p. 1903, Limitations). This 85th-percentile rule for protective dietary factors is worth flagging: it bounds how much benefit the model will attribute to higher intake of fruits, wholegrains, etc.
4. **PAF and attributable burden:** PAF × disease-specific DALYs, mediation-adjusted (p. 1879).

**Uncertainty:** mean across **250 draws** (reduced from 500 in GBD 2021), 95% UI from the 2.5th/97.5th percentiles; the reduction was shown to affect estimates minimally (p. 1880). Smaller draw count than C18's 1000 and our own N = 10,000, but the principle (Monte Carlo over parameter uncertainty) is the same; a minor Group F cross-link.

**Software:** Python 3.10.4, Stata 13.1, R 4.2.1; statistical code publicly available (p. 1880).

---

#### Dietary-risk SEV data (Table 2, p. 1888) — the only diet numbers in the main text

These are **summary exposure values** (0–100, reflecting how far a population sits from the TMREL weighted by relative harm), *not* relative risks or attributable DALYs. Global age-standardised SEVs, 2023, with annualised rate of change 2010–23:

| Dietary risk factor | SEV 2023 | ARC 2010–23 |
|---|---|---|
| Dietary risks (aggregate) | 38.4 | 0.0% |
| Diet low in fruits | 40.5 | 0.0% |
| Diet low in vegetables | 26.1 | −0.1% |
| Diet low in legumes | 42.2 | −0.3% |
| Diet low in wholegrains | 40.5 | 0.1% |
| Diet low in nuts and seeds | 42.0 | −0.6% |
| Diet low in milk | 65.1 | 0.0% |
| Diet high in red meat | 26.7 | 0.1% |
| Diet high in processed meat | 13.7 | 0.4% |
| Diet high in sugar-sweetened beverages | 16.7 | 1.6% |
| Diet low in fibre | 20.7 | −1.5% |
| Diet low in calcium | 20.3 | −0.9% |
| Diet low in seafood omega-3 fatty acids | 28.9 | −1.5% |
| Diet low in omega-6 PUFA | 57.8 | −0.5% |
| Diet high in trans fatty acids | 29.5 | −2.7% |
| Diet high in sodium | 41.1 | −0.2% |

Note the trans-fat SEV fell fastest among diet factors (ARC −2.7%), consistent with global trans-fat-elimination policy; and that SSBs is the only diet exposure rising materially (+1.6%/yr). Diet-aggregate exposure is essentially flat (0.0%). These are exposure trends, useful only as context, not as inputs to our HENI factor table.

**Where diet sits in the leading risks (Figure 7, p. 1890):** among the 25 leading level-3 risks by share of total DALYs in 2023, the diet factors that appear are diet low in fruits (13th, 1.7%), diet high in sodium (18th, 1.4%), diet low in wholegrains (20th, 1.1%), and diet low in vegetables (25th, 0.8%). High SBP leads overall (8.4% of DALYs). This is a useful framing point for §1 (diet remains a top-tier modifiable risk) but cite carefully: these are GBD 2023 ranks, and many diet effects are folded into the metabolic mediators (high SBP, high BMI, high FPG) rather than attributed to the diet factor directly.

---

#### Author-flagged limitations (Limitations, pp. 1902–1903) — for our §7

The GBD-inheritance caveats relevant to HENI, at the 2023 vintage:

1. **Mediation assumption (p. 1902).** Relative risks are mediation-adjusted assuming joint risks are **multiplicative**, but real combinations may be super- or sub-multiplicative; the authors flag this as "particularly relevant to analyses of dietary risk factors that yield protective effects, such as fruit or wholegrain intake." This is the most diet-specific limitation in the paper and belongs directly in our §7 when we discuss HENI's treatment of protective foods.
2. **Constant-across-location-and-time RR assumption (p. 1903).** Risk-outcome relationships are assumed constant across location and time (with noted exceptions for temperature and BMI-breast-cancer). For diet this is the same portability caveat C17 addresses by swapping local burden rates: the *RR shape* is held constant, only exposure and background burden vary by place. Reinforces that HENI portability (our §3.7) rests on a GBD assumption, not an empirically re-fitted local dose-response.
3. **Protective-risk TMREL at the 85th percentile (p. 1903).** A modelling choice that conservatively bounds attributable benefit for "low intake" factors; the authors note further refinements may be needed.
4. **Burden-of-proof not yet applied to all pairs (p. 1903).** The flexible non-log-linear method covers 256 of 676 pairs; the rest use older approaches, so evidence-strength treatment is uneven across diet-disease pairs.
5. **General GBD data-quality and sparsity limits (p. 1902).** Variable input-data availability and quality; COVID-19 delayed survey releases (only 19 STEPS surveys since 2020 vs 41 in the prior 4 years), which thins recent dietary-exposure data.

---

#### Conflict-of-interest and authorship note

This is a mega-collaboration (more than 14,000 collaborators, p. 1880). The corresponding author is Simon I Hay; senior authors include Christopher Murray, Theo Vos, Michael Brauer and Emmanuela Gakidou (p. 1920). **Dariush Mozaffarian is not in the C19 author list** (unlike C18), so the Food-Compass-network COI we track via C18 and §7.3 does not directly attach to C19. The COI section (pp. 1903–1914) is enormous but concerns mostly clinical/pharma relationships of individual collaborators, none material to our diet-LCA framework. Statistical code is public (p. 1880), and full data are on the GBD 2023 Sources/Results tools (GHDx).

---

#### Cross-links

- **C18 (GBD 2017 Diet)** defines the 15-factor diet framework and is the dedicated diet-risk paper; **C19 (GBD 2023)** is the current vintage of that same enterprise, confirms the 15 diet factors persist, and documents the single diet change (trans-fat TMREL). Cite C18 for the diet-factor definitions, C19 for "most recent GBD" and the trans-fat TMREL revision.
- **C17 (Cardinaals et al. 2024)** recomputes HENI on **GBD 2019**; our manuscript §7.4 also says GBD 2019. C19 is the upgrade path: if we move HENI to GBD 2023 we inherit the burden-of-proof RRs, the 165-pair mediation matrix, and the revised trans-fat TMREL.
- **C15 / C16 (HENI / Stylianou)** convert the GBD CRA structure into per-food μDALY/g DRFs; C19 is the latest GBD machinery those DRFs would draw on.
- **Manuscript §3.4 / §7.4:** when we state the GBD vintage underpinning HENI, C18 + C19 together let us be precise (15-factor framework from GBD 2017; GBD 2019 RRs currently in our factor table per C17; GBD 2023 available as the newest vintage with a revised trans-fat TMREL).
- **Group F (uncertainty):** C19's 250-draw Monte Carlo and burden-of-proof heterogeneity quantification are domain precedents, though our N = 10,000 propagation is larger and targets LCA characterization factors rather than epidemiological RRs.

---

#### Three-sentence relevance note

C19 is the most recent GBD vintage and our reference for "current GBD" in the manuscript: it confirms that the 15 dietary risk factors defined in GBD 2017 (C18) persist unchanged in the GBD 2023 hierarchy of 88 risk factors and 676 risk-outcome pairs, and it documents the one diet-relevant methodological change, a revised theoretical-minimum-risk exposure level for diet high in trans fatty acids (p. 1880). Critically, this is a combined burden-and-risk synthesis, not a dedicated diet paper, so per-diet relative risks and attributable DALYs are in appendix 3 and the parallel risk-factor papers rather than the main text; C19 should be cited for the vintage, the burden-of-proof and mediation methodology, and the trans-fat TMREL revision, with C18 retained for the diet-factor definitions and C17 for the GBD 2019 RRs our factor table currently uses. The diet-specific limitation most useful for our §7 is the explicit multiplicative-mediation caveat the authors flag as "particularly relevant to analyses of dietary risk factors that yield protective effects, such as fruit or wholegrain intake" (p. 1902); cite as GBD 2023 Disease and Injury and Risk Factor Collaborators, Lancet 2025;406:1873–1922, doi:10.1016/S0140-6736(25)01637-X.

---

### C20. Weidema & Stylianou (2020) — Nutrition in food LCA, function vs impact, and the originating description of DANI [★★★]

**Citation.** Weidema BP, Stylianou KS. Nutrition in the life cycle assessment of foods — function or impact? Int J Life Cycle Assess. 2020;25(7):1210–1216. (Received 13 Feb 2019; accepted 28 June 2019; published online 18 July 2019.)

**DOI.** 10.1007/s11367-019-01658-y (Springer; part of the "Sustainable Food Production and Consumption" topical collection, responsible editor Bruno Notarnicola).

**Type.** Conceptual / methodological position paper (not an empirical study). Two authors: Bo Weidema (Aalborg, LCA functional-unit theory) and Katerina Stylianou (Michigan; co-author of C14 CONE-LCA and the HENI lineage). This is the **wishlist's "DANI originating paper" (#20)** and the clearest published statement of where the DALY Nutritional Index (DANI) sits conceptually relative to HENI.

---

#### Why this paper matters to us, and the crucial DANI-vs-HENI distinction

This is the paper that names and conceptually frames **DANI (DALY Nutritional Index)**. The single most important thing to extract is that **DANI and HENI are sibling indices from the same Stylianou/Jolliet/Fulgoni lineage but are not identical**, and the difference is precisely in the risk-component count our file has been tracking:

- **HENI (C15/C15-SI):** 15 GBD dietary risks → **16 risk components** (fibre split into two source-specific components to avoid double-counting), expressed in net minutes of healthy life per serving, US-based, IMPACT World+ on the environmental side.
- **DANI (this paper, p. 1211–1212):** "**based on 15 dietary risks from the GBD studies plus saturated fatty acids**" → **16 dietary risk components**, expressed in DALYs (μDALYs) per serving / per functional unit. The 16th component here is **saturated fatty acids**, NOT a fibre split.

So both indices land on "16 components" but reach it differently: HENI's 16th is a fibre-source split; DANI's 16th is saturated fat added on top of the 15 GBD risks. This is a real distinction we must not blur, and it definitively extends the factor-count thread tracked in C15-SI (16 = 15 risks + fibre split) and C16/C17 (14 factors). **Recommended canonical statement for our notes: the count depends on the index — HENI = 16 (15 risks, fibre split); DANI = 16 (15 risks + saturated fat); the Dutch/thesis variants = 14.**

For our manuscript this matters because §3.2 says HENI is "computed as Σ (g × μDALY/g) over 14 GBD risk factors." That "14" is now triply contestable (HENI uses 16 components, DANI uses 16, only the thesis/Dutch lineage uses 14). We should reconcile the §3.2 wording against C15-SI's 16-component table and decide explicitly which index and which count we implement.

---

#### The paper's central conceptual contribution: function vs impact (Results 3.1–3.2)

The paper's thesis is that nutrition plays **two distinct roles** in food LCA that prior work conflated:

1. **Nutrition as a function (the functional unit).** The authors argue *against* loading weighted nutrient-profiling scores into the functional unit. Their reasoning (p. 1211): a product property only belongs in the functional unit if it is *obligatory* (essential for the food to be a relevant alternative to customers), and desirable nutrients are usually "positioning" properties (like price), not obligatory ones. Nutrient-profiling scores in the denominator also create the problem that LCA results are impacts-per-FU, so putting key impacts in the denominator "leaves the question: what is then left in the numerator?" They flag that limiting-nutrient profiling can even yield *negative* functional units (a conceptual breakdown). **Their recommendation: satiety is the appropriate central nutritional attribute for the functional unit** ("how much / how long / how well" → portion size / satiety-weight / exclusion criteria), not continuous nutrient scores. They concede satiety data are not yet sufficient to quantify at the food-component level.

2. **Nutrition as a risk factor / impact pathway.** This is where DANI lives: nutrition enters the *impact* side as the marginal health effect of adding or subtracting a specific food from an existing diet, quantified in DALYs via GBD epidemiology.

**Relevance to us:** our pipeline keeps nutrition (HEFI, HSR, FCS) and health-burden (HENI) and environment (ReCiPe LCA) as *separate indicators* rather than collapsing nutrition into the LCA functional unit. C20 is the conceptual authority for exactly that separation: it argues nutrient profiling is "largely misplaced as part of the functional unit" and that health effects belong in a dedicated impact pathway. This supports our multi-indicator design (the same argument C17 makes empirically) and is citable in §1.2 / §2 / §6.4 when we justify not building a single composite score.

---

#### DANI mechanics as described here (Results 3.2, pp. 1212–1213)

DANI requires two data sets, exactly mirroring HENI's structure:

1. **Nutritional inventory flows:** the mass (kg) of each of the 16 dietary risk components per serving, aligned to the GBD definition of each risk, obtained via the **Fulgoni et al. (2018)** methodology for WWEIA/NHANES foods. (Fulgoni et al. 2018, Nutrients 10(10):1441 is the inventory-flow method paper; worth noting as a dependency for any DANI/HENI implementation.)
2. **Nutritional characterization factors** (DALYs per kg of risk component): the marginal change in disease burden per additional intake. Developed for **US adults ≥25 y**, from **6,195 risk-outcome-strata-age-gender-burden pairs** and US-specific burden rates (Stylianou 2018 thesis; Stylianou et al. 2019). **Positive CF = detrimental; negative CF = protective.**

DANI score = Σ (inventory flow × characterization factor), assuming dietary risks act **independently and additively** in the marginal context (small changes in intake). This independent-additive assumption is the same marginal-validity premise as HENI.

**Note the "6,195 ... pairs" here vs C15-SI's "6,195 risk-outcome-strata-age-group-gender-burden pairs."** These match, confirming DANI and HENI's published US factor set share the same underlying GBD-derived RR expansion. So although the indices are conceptually distinct (saturated-fat 16th vs fibre-split 16th, DALYs vs minutes-of-life), they draw on the same epidemiological factor-development effort.

---

#### Worked example: the burrito comparison (Fig. 1, p. 1213) — usable as a DANI unit test

The paper demonstrates DANI on two 140 g burritos in the US diet:

| Food | DANI score | Driver breakdown |
|---|---|---|
| Beef ("meat") burrito | **+19.6 μDALY/serving** (net detrimental) | sodium +9.2, saturated fat +6.5, red meat +3.8 μDALY/serving |
| Bean ("veggie") burrito | **−5.8 μDALY/serving** (net protective) | benefits dominated by legumes (−12.4 μDALY/serving), exceeding sodium/SFA detriments |

Composition: meat burrito = 7% red meat + 61% neutral ingredients (poultry, white rice); veggie burrito = 38% legumes + 15% vegetables + 36% neutral. The meat burrito covers 7 of 16 DANI risks, the veggie burrito 9 of 16. **Double-counting carve-out:** fibre is split into "fibre from fruit/vegetable/legumes/whole grains" (benefits colorectal cancer only) vs "fibre from other sources" (benefits both colorectal cancer and ischemic heart disease), to avoid double-counting the cardiovascular fibre benefit (citing Gakidou et al. 2017). This is the **same fibre-source double-counting logic** documented for HENI in C15-SI, and worth flagging: even though DANI's nominal 16th component is saturated fat, it *also* carries the fibre split internally, so the "16" arithmetic across DANI and HENI is subtler than the headline counts suggest. We should reconcile this carefully against C15-SI before encoding either.

This burrito pair is a clean unit-test analogue to the HENI test foods in C15 (chicken wings, beef hotdog, apple pie); cite both sets when validating our HENI/DANI kernel.

---

#### Author-flagged limitations (Results 3.2 discussion, pp. 1213–1214) — for our §7

These are largely shared with HENI's caveats but stated crisply here:

1. **Food-group, not food-item, granularity.** Epidemiology investigates food groups (for statistical power), so DANI "lacks epidemiological data supporting differentiated health effects between foods of the same food group." Worked example: SSBs have a robust dose-response on *amount of beverage*, but not on *sugar content*, so two SSBs of different sugar content get the same DANI health effect even though a nutrient-profiling model would score them differently. The authors concede that for added sugar an extrapolation "appears warranted" but flag it as stretching the evidence. **Directly relevant to our SSB→water counterfactual (S5)** and to any claim our pipeline makes about sugar-content gradients.
2. **Generalisation beyond Europe/US.** Robust diet-disease associations from European/US cohorts may not transfer; e.g. some Asian studies (Lee et al. 2013) find a *beneficial* health effect of increased red-meat consumption, opposite to the European/US consensus (Forouzanfar et al. 2016). This is the geographic-portability caveat that bears on our Canada (and any France) HENI application, complementing C17's portability procedure.
3. **Marginal-vs-diet-level (the big one).** DANI in its current form evaluates the *marginal* health effect of a food-level change and "fails to capture the aggregated health effect of nutrients and food groups at the diet level, which are multiplicative and not additive." Consequence stated explicitly: "using marginal DANI might lead to overestimating the nutritional benefits of 'healthy' diets and underestimate the benefits from 'unhealthy' diets." They call for a future **"diet-DANI"** that handles multiplicative aggregation, complemented with the Fern et al. (2015) nutrient-balance indicator. **This is the same marginality limitation HENI carries (C15, C17), and our §7 should state it once for both indices.** It also echoes GBD 2023's own multiplicative-mediation caveat (C19, p. 1902).
4. **Nutrient-profiling models are only indirectly linked to health** (McCullough & Willett 2006), "limiting their ability to quantify health damages," so combining nutrient-profiling models with GBD food-group epidemiology "must be done with great care." Relevant to how we report FCS/HSR (nutrient-profiling) alongside HENI/DANI (epidemiology-based) in the same platform without conflating them.

The authors' overall stance (Conclusions, p. 1214): nutrition is "not an either/or" — it enters the functional unit as satiety AND the impact calculation as marginal health effect; DANI is "a novel and promising approach" that "introduces a nutritional impact category" enabling environment-vs-health trade-off quantification, and "may be combined with the nutrient balance indicator."

---

#### A GBD-vintage / citation-hygiene note

C20 cites GBD via **Forouzanfar et al. 2016 (GBD 2015)** and **Gakidou et al. 2017 (GBD 2016)** for the dietary risk definitions and TMRELs, and reports the burden figure "9.6% of the 2016 Global Burden of Disease or 229 million DALYs annually" (p. 1212, citing Forouzanfar 2016). Note these are **older GBD vintages** than our C18 (GBD 2017) / C19 (GBD 2023) references and than HENI's GBD 2016 base (C15). When we cite DANI's conceptual framing we use C20; when we cite the underlying diet-risk definitions we should anchor to the GBD vintage actually used (C18/C19), not to C20's 2015/2016 citations. The unbalanced-diet definition C20 quotes (low in fruits, vegetables, legumes, whole grains, nuts/seeds, milk, fibre, calcium, PUFA, omega-3; high in red meat, processed meat, SSBs, trans fat, sodium) is the same 15-factor list as C18.

---

#### Cross-links

- **C14 (Stylianou et al. 2016, CONE-LCA):** C20 explicitly builds on CONE-LCA as "a first attempt" at the nutritional impact pathway, generalising it from single-component foods (milk) to any food via DANI's 16 risk components.
- **C15 / C15-SI (HENI):** DANI's sibling. Same lineage, same ~6,195-pair US factor development, same fibre-source double-counting, same marginal-additivity assumption. **Key difference: DANI's 16th component is saturated fat (added to the 15 GBD risks) and its unit is μDALY/serving; HENI's 16th component is a fibre split and its unit is minutes of healthy life.** This is the cleanest place in the file to record that distinction.
- **C16 (Stylianou 2018 thesis):** the source of both DANI's and HENI's US characterization-factor table; C20 cites it (with Stylianou et al. 2019) as the CF source.
- **C17 (Cardinaals et al. 2024):** uses HENI (not DANI) and a 14-factor Dutch list; C20 + C15-SI together explain why the count differs across the literature.
- **C18 (GBD 2017) / C19 (GBD 2023):** the diet-risk framework DANI rests on; cite these for current diet-factor definitions rather than C20's 2015/2016 GBD citations.
- **Manuscript §1.2 / §2 / §6.4:** C20 is our conceptual authority for keeping nutrition out of the LCA functional unit and treating health as a dedicated impact pathway, supporting the multi-indicator (not single-composite) design.
- **Manuscript §3.2:** the "14 GBD risk factors" wording for HENI should be reconciled against C15-SI (16 components) and this entry; flag the HENI-16 vs DANI-16 vs Dutch-14 distinction.
- **Dependency note:** Fulgoni et al. 2018 (Nutrients 10(10):1441), the WWEIA/NHANES inventory-flow methodology, is a prerequisite for implementing either DANI or HENI inventory flows; not yet on our wishlist but worth retrieving if we build the kernel.

---

#### Three-sentence relevance note

C20 is the originating conceptual description of DANI and the clearest published statement that nutrition plays two separate roles in food LCA, a functional-unit role (best captured by satiety, not by nutrient-profiling scores) and an impact-pathway role (the marginal health burden of a food, quantified in DALYs via GBD epidemiology), which is the strongest conceptual authority for our platform's decision to keep diet-quality, health-burden, and environmental indicators separate rather than collapsing them into one composite score. Its most consequential detail for our notes is that **DANI is built on "15 dietary risks from the GBD plus saturated fatty acids" for 16 components, whereas HENI reaches 16 by splitting fibre**, so the two sibling indices share a lineage and a ~6,195-pair US factor set but are not interchangeable, and our §3.2 "14 GBD risk factors" wording needs reconciling against this. The author-flagged limitations we carry into §7, the food-group (not food-item) granularity that prevents distinguishing same-group foods such as differently-sweetened SSBs, the Europe/US-to-other-population generalisation risk, and above all the marginal-versus-diet-level problem (marginal DANI may overestimate the benefit of healthy diets and underestimate the harm of unhealthy ones because real diet-level effects are multiplicative not additive), are shared with HENI and should be stated once for both; cite as Weidema & Stylianou 2020, Int J Life Cycle Assess 25(7):1210–1216, doi:10.1007/s11367-019-01658-y.

---

### C21. Lenaerts (2025, medRxiv v2) — a modified DALY method for fortification/biofortification using relative nutrient-intake metrics [★★☆]

**Citation.** Lenaerts B. Quantifying the health impact of food interventions: revisiting the Disability-Adjusted Life Years approach. medRxiv 2024.08.26.24312574 (version 2, posted 15 December 2025). Preprint, not peer-reviewed. Sole author: Bert Lenaerts, Sustainable Impact through Rice-based Systems Platform, International Rice Research Institute (IRRI), Los Baños, Philippines.

**DOI.** 10.1101/2024.08.26.24312574 (CC-BY-NC-ND 4.0). Acknowledges Erick Boy and Victor Taleon (HarvestPlus) for feedback and data.

**Type.** Methods paper (development-economics / agricultural-nutrition framing). **This is wishlist #21.** Important scoping correction: despite a working description of this as a "DALY-methodology critique," it is **not a critique of the HENI/DANI dietary-risk approach**, and it sits in a *different branch of the DALY literature* from the rest of Group C. It proposes a modified DALY method for estimating the health impact of **fortification and biofortification interventions on micronutrient-deficiency burden** (iron, zinc, vitamin A, calories, protein), drawing on the GBD **nutritional-deficiency cause/risk factors**, not the GBD **dietary-risk factors** (high sodium, low fruit, etc.) that HENI (C15) and DANI (C20) are built on. Its star rating is downgraded to ★★☆ here to reflect that its relevance to our dish-level Canadian sustainability platform is real but limited and high-level, not central.

---

#### Why this paper matters to us, honestly scoped

The rest of Group C is one coherent thread: the GBD comparative-risk-assessment framework for *dietary* risks, converted into per-food health-burden factors (HENI/DANI). C21 belongs to a *parallel* DALY literature, the Stein/Zimmermann-Qaim tradition of valuing crop-improvement and food-fortification interventions in low- and middle-income countries by the **deficiency burden they avert**. The two share only the DALY endpoint and a reliance on GBD/IHME burden data; their risk objects, populations, and policy questions are different.

Three things in it are genuinely useful to us, all methodological rather than substantive:

1. **A clean argument for relative over absolute intake metrics under data scarcity.** Lenaerts' central move (Section 2, pp. 2–3) is that current intake (CI), post-intervention intake (BI), and recommended dietary allowance (RDA) "exhibit considerable variation across sources" and that absolute estimates are unreliable, so he reformulates the efficacy calculation entirely in **relative** terms: a relative intake increase ϘCI = BI/CI > 1 (Eq. 3) and a relative intake gap ƒCI = CI/RDA < 1 (Eq. 4). His stated rationale, that relative parameters cancel systematic measurement error, enable cross-nutrient comparison, keep repeated measurements consistent, and can be re-tuned without recalibrating the whole system (p. 3), is a transferable data-gap-robustness argument we could cite in §7 when discussing how our platform handles uncertain or inconsistent input data, even though our problem (dish-level dietary-risk burden) is different.
2. **A documented cross-source inconsistency in nutrient-intake data.** The paper shows (Section 2.3.3, p. 7) that intake estimates disagree badly across sources, e.g. Lividini & Masters (2022) report apparent vitamin A intake *exceeding* reference values in West Africa while IHME (2024) places West Africa's vitamin-A-deficiency burden in the highest global quintile; and several published per-capita-intake metrics correlate *low or negatively* with GDP per capita, ranking low-income countries among the highest-intake (Figure 2 correlograms; Table 2). This is a useful cautionary citation for any claim that nutrient-intake databases are interchangeable, complementing the data-quality caveats already logged for GBD itself (C18, C19).
3. **A model-ensemble approach to filling intake gaps.** To estimate the relative intake gap where data are missing, he compares a **quadratic** inversion, a **random forest**, and a **Cubist** model (controlling for sanitation access and intestinal-infection burden), then takes an equal-weight **ensemble** as most robust (p. 7). A mild methods cross-link to our Group D (ML) and Group F (uncertainty/ensemble) threads, again at the level of technique rather than content.

I would not force any tighter connection than these. This paper does not inform our HENI implementation, our dietary-risk factor list, or our Canadian case study directly.

---

#### The method, as stated

**Classic approach (Section 1, p. 2).** The Stein et al. (2005) / Zimmermann & Qaim (2004) efficacy formula, Eq. 1, computes E, the relative reduction in hunger burden, from CI, BI and RDA via a log-and-linear bracket, bounded to 0 when CI ≥ RDA (no gap to close) and to 1 when intervention pushes intake past RDA. Health impact then follows as

> DALYs_saved ≡ ΔDALYs_lost = E × DALYs_BAU  (Eq. 2)

i.e. efficacy times the business-as-usual deficiency burden.

**Relative reformulation (Sections 2.2–2.4).** Eq. 9 rewrites Eq. 1 purely in terms of ϘCI and ƒCI, yielding E ∈ [0,1]; Eq. 10 is the symmetric case for *declines* in nutrient supply (climate, price shocks, conflict) that *increase* hunger burden. The relative intake increase is itself decomposed (Eq. 6) as ϘCI = 1 + ΔrNS × ƒDIET × ƒTARGET × ƒCOV, where ΔrNS is the relative nutrient-supply gain (Eq. 7, combining yield gain ΔrY and fortification content gain ΔrFI), ƒDIET the share of a nutrient supplied by the commodity (FAOSTAT Supply Utilization Accounts), ƒTARGET the share of consumption targeted, and ƒCOV the intervention coverage. The relative intake gap ƒCI is recovered by inverting an empirical quadratic relating prevalence of undernourishment to relative calorie supply (Fischer et al. 2005; Robinson et al. 2015), Eq. 8, or by regression/ML (Section 2.3.2). Note ϘCI is bounded near 1, "most relative nutrient intake increases are not expected to exceed 1.125" (p. 9).

**Burden data (Section 2.1, Table 1, pp. 3–4).** Deficiency burden in DALYs comes from **IHME GBD 2021** (with GBD 2019 also referenced). He distinguishes GBD **cause** factors (deficiency diseases that directly cause death/disability) from **risk** factors (causally associated with multiple downstream outcomes) and **recommends using risk factors where available** because they capture indirect effects. Chronic hunger is proxied by **child wasting** (Caulfield et al. 2006, since wasting is short-term and yield-responsive, unlike stunting); hidden hunger aggregates iodine, iron, zinc, vitamin A and "other" deficiencies (Gödecke et al. 2018), with maternal disease excluded and a manual **zinc-burden adjustment** because GBD 2019/2021 under-counts zinc for lack of data (Han et al. 2022; Hess et al. 2022). Table 1's headline 2021 DALY figures include child wasting → diarrhoeal diseases (0–4 y) 1.59 × 10⁷ DALYs, iron deficiency → dietary iron deficiency (10+ y) 2.24 × 10⁷, and child wasting → protein-energy malnutrition (0–4 y) 7.93 × 10⁶.

---

#### Author-flagged limitations and cautions (relevant to our §7 only at the level of method-transparency)

The paper is candid that nutrient-intake data are unreliable and inconsistent across sources (the entire motivation for going relative), that the quadratic intake-gap relationship was empirically established by Fischer et al. (2005) only for **calories** and is *assumed* to transfer to micronutrients after normalisation (p. 5), and that the random-forest model is "sensitive to generating outliers" (e.g. implausible iron intake in Turkey, zinc/vitamin A in Nepal), which is why he prefers the ensemble (p. 7). These are honest method caveats; none bears directly on our dietary-risk pipeline, but the calorie-to-micronutrient transfer assumption and the ML-outlier caution are worth remembering if we ever borrow the relative-metric or ensemble technique.

---

#### GBD-vintage note

C21 uses **GBD 2021** (IHME 2024) as its primary burden source, with **GBD 2019** also cited; its references include the GBD 2021 Risk Factors Collaborators (Lancet 2024;403:2162–203), which is the dedicated risk-factor paper that is *also* C19's own reference #13 and the place we identified for actual GBD diet relative risks. So C21 and C19 point to the same GBD 2021 risk-factor publication, though for different factor branches (deficiency vs dietary risk). When citing GBD vintages in our manuscript we continue to anchor diet-factor definitions to C18 (GBD 2017) and the current vintage to C19 (GBD 2023); C21's GBD 2021 usage is incidental to its own deficiency-burden problem.

---

#### Cross-links

- **Different branch from C14–C20.** C21 uses GBD *nutritional-deficiency* cause/risk factors (iron, zinc, vitamin A, wasting); HENI (C15), DANI (C20), CONE-LCA (C14), and the GBD diet papers (C18, C19) use GBD *dietary-risk* factors. Both end in DALYs, but they are not the same factor set and should never be conflated in our writing.
- **C18 / C19 (GBD vintages):** C21's GBD 2021 deficiency-burden usage shares the GBD 2021 Risk Factors paper with C19's bibliography; cite C18/C19 for our diet-factor framework, not C21.
- **Group F (uncertainty):** the relative-metric robustness argument and the quadratic/RF/Cubist ensemble are method-level analogues to our uncertainty-propagation interest, though our N = 10,000 Monte Carlo over LCA characterization factors is a different construction.
- **Group D (ML):** the random-forest / Cubist intake-gap models are a minor ML-for-nutrition cross-link.
- **Manuscript relevance:** marginal. If our §1 or §6 ever situates dish-level dietary-risk health burden within the broader landscape of "food-health DALY methods," C21 is a legitimate citation for the *fortification/biofortification deficiency-burden* corner of that landscape, illustrating that the DALY endpoint is used across very different food-health problems. It does **not** support any methodological choice in our HENI implementation or Canadian case study.

---

#### Three-sentence relevance note

C21 is a methods preprint proposing a modified Disability-Adjusted Life Years approach for valuing fortification and biofortification interventions by the micronutrient-deficiency burden they avert, reformulated entirely in relative nutrient-intake terms (relative intake increase ϘCI = BI/CI and relative intake gap ƒCI = CI/RDA) to overcome the unreliability and cross-source inconsistency of absolute intake and RDA data. It belongs to a different branch of the DALY literature from the rest of Group C, drawing on the GBD nutritional-deficiency cause/risk factors rather than the GBD dietary-risk factors that underpin HENI and DANI, so its relevance to our dish-level Canadian dietary-risk platform is limited and high-level: the genuinely transferable elements are its argument that relative metrics are more robust than absolute ones under data scarcity, its documentation that published nutrient-intake databases disagree sharply (and sometimes correlate negatively with GDP), and its quadratic/random-forest/Cubist ensemble for filling intake gaps. It is appropriately cited only as an example of the fortification/deficiency-burden corner of the broader food-health DALY landscape and not as support for any choice in our HENI methodology; cite as Lenaerts 2025, medRxiv 2024.08.26.24312574 v2, doi:10.1101/2024.08.26.24312574 (preprint, not peer-reviewed).

---

*Group C complete (C14–C21).*

## Group D. AI / LLMs for food classification and LCA

### D22. Ase, Borowicz, Rakocy & Piekarska (2026) — LLMs for real-world nutrition assessment: structured prompts, multi-model validation, expert oversight [★★★]

> ⚠️ **CITATION CORRECTION — READ FIRST.** The wishlist (entry 22) and the current manuscript reference list (ref. 36) attribute this paper to **"Wijesinghe DGNG, et al."** This is **wrong.** The DOI (10.3390/nu18010023), title, journal, volume/issue and page (*Nutrients* 2026;18(1):23) all match the wishlist exactly, so it is the intended paper — but the actual authors are **Aia Ase, Jacek Borowicz, Kamil Rakocy and Barbara Piekarska** (Medical University of Warsaw). The "Wijesinghe" name appears nowhere in the article (not as author, not in the reference list). **Action:** correct ref. 36 in `manuscript_call1.md` and every in-text citation that currently reads "Wijesinghe et al., 2026" (§2.2, §3.4) to "Ase et al., 2026." All bracketed-URL citations in the draft (§1.1, §2.2) point to the correct DOI and need no URL change, only author-name correction where a name is given.

**Citation.** Ase A, Borowicz J, Rakocy K, Piekarska B. Large Language Models for Real-World Nutrition Assessment: Structured Prompts, Multi-Model Validation and Expert Oversight. *Nutrients.* 2026;18(1):23. doi:10.3390/nu18010023.

**DOI.** 10.3390/nu18010023

**Access.** Open access (CC BY 4.0). Received 29 Oct 2025; accepted 17 Dec 2025; published 20 Dec 2025. 16 pp.

**Type.** Original research — observational LLM-vs-expert classification benchmark on a real-world clinical dataset.

---

#### Study design at a glance (p. 3, §2.1; Figure 1, p. 6)

- **Dataset.** 1992 food items drawn from the personal-cabinet ("off-menu") food supplies of residents in Polish long-term care facilities (LTCFs), within a larger 2017–2021 longitudinal cohort of 1000 LTCF residents funded by the Polish Ministry of Health (National Health Program 2016–2020). Items are foods purchased by residents or brought by family, i.e. *not* part of the prescribed facility diet — deliberately chosen to stress-test real-world, irregular descriptions.
- **Language.** All items kept in **Polish** (native language retained on purpose; the authors argue Polish morphology aids LLM disambiguation, p. 10–11 §4.3, citing the RULER multilingual benchmark, ref. 26).
- **Models (release dates given p. 3).** Claude Opus 4.5 (Anthropic, 24 Nov 2025); Gemini 3 pro (Google, 18 Nov 2025); GPT-5.1-chat-latest (OpenAI, 12 Nov 2025). All accessed via API on 30 Nov 2025.
- **Temperature = 1.0 for all three models** (p. 5, §2.6) — chosen because Gemini's docs warn against lowering temperature below 1.0; the authors wanted "as-is" default behaviour. **NB for our §3.4:** our pipeline uses `temperature 0`; this is a deliberate design divergence, not an error, but it means this paper's numbers are *not* a like-for-like baseline for a temperature-0 categorizer.
- **Task.** Binary **healthy / unhealthy** classification — *not* GBD-risk-factor mapping. UNHEALTHY = positive class for all metrics.
- **Gold standard.** Two human experts: expert 1 classifies + justifies; expert 2 reviews and corrects expert 1 to form a consensus reference (p. 4–5, §2.5). Experts told to judge "holistically and generally," not tailored to LTCF clinical needs. **No inter-rater κ is reported** (the second expert corrects rather than independently rates), which contrasts with our S1 plan to report Cohen's κ between two dietitians.
- **Reference distribution (p. 7, §3.1).** 41.9% healthy (n = 835); 58.1% unhealthy (n = 1157).

---

#### The two prompt designs (p. 3–4, §2.2–2.4) — directly relevant to our §3.4

**Structured "double-step" prompt (NOVA + WHO):**
1. *Step 1 — NOVA:* "Act as a helpful dietary assistant. Classify the following food products as 'healthy' or 'unhealthy'… consider foods unhealthy if they are… ultra-processed according to the NOVA classification system. For each product, provide details in the following format: {product, weight (g), calories, classification}. Finally, sum the total calories for each category."
2. *Step 2 — WHO thresholds (only on items passed as HEALTHY in Step 1):* reclassify as unhealthy if exceeding WHO limits — **free sugars > 10% of total energy, saturated fat > 10%, sodium > 2 g/day.**

**Simplified single-step prompt:** "Evaluate each product as healthy or unhealthy and explain why — in two columns: 'evaluation' and 'description.'"

This is a clean, citable example of the *exact* structured-prompt-with-explicit-criteria-plus-JSON-shaped-output design our HENI categorizer uses, and a precedent for constraining the LLM to a defined rubric. Worth citing in §3.4 next to the Barrett et al. (2025) "LLMs could… facilitate… interpretation of ingredients lists" endorsement.

---

#### Tables to reference (do NOT need full reproduction; cite selectively in §4.1 framing)

**Table 2 (p. 7) — double-step (NOVA+WHO) metrics, UNHEALTHY = positive (N = 1992):**

| Model | Acc | Prec | Recall | F1 | Spec |
|---|---|---|---|---|---|
| GPT-5.1-chat-latest | 0.904 | 0.870 | 0.980 | 0.922 | 0.798 |
| Claude Opus 4.5 | 0.913 | 0.895 | 0.963 | 0.928 | 0.844 |
| Gemini 3 pro | 0.913 | 0.881 | 0.982 | 0.929 | 0.817 |
| Dominant (consensus) | 0.910 | 0.881 | 0.977 | 0.927 | 0.818 |

**Table 4 (p. 8) — simplified single-step metrics, same ground truth:**

| Model | Acc | Prec | Recall | F1 | Spec |
|---|---|---|---|---|---|
| GPT-5.1-chat-latest | 0.936 | 0.928 | 0.964 | 0.946 | 0.897 |
| Claude Opus 4.5 | 0.927 | 0.962 | 0.909 | 0.935 | 0.951 |
| Gemini 3 pro | 0.928 | 0.958 | 0.916 | 0.937 | 0.944 |
| Dominant (consensus) | 0.942 | 0.962 | 0.937 | 0.949 | 0.948 |

**Headline numbers for in-text use:**
- Overall LLM–expert agreement: **90.3–94.2%** across both prompts (the figure our draft already cites).
- Double-step agreement 90.3–91.3% (Opus highest, 91.3%); simplified agreement 92.5–93.6% (GPT highest, 93.6%; dominant consensus 94.2%) — p. 7–8, §3.2–3.3.
- F1 range **0.922–0.949** (UNHEALTHY positive class) — note this is far above the NutriRAG F1 ≈ 0.82 our §2.2 cites for D23; useful as the upper end of plausible S1 performance.
- Share labelled unhealthy: **64.4% under double-step vs 56.6% under simplified** (p. 10, §4.2).
- Pearson χ²: **all 36 pairwise comparisons significant, χ² 1174.5–1897.1, df = 1, p < 0.001** (Table 5, p. 9). Most divergent pair: WHO Gemini vs WHO Dominant (1897.1). LLMs vs human expert: χ² 1296.6–1547.6.

---

#### Findings worth flagging in our framing (§2.2 nuance + §4.1 / §4.6)

1. **"Structured prompts" ≠ "higher agreement" here — important nuance for §2.2.** Our draft §2.2 currently says LLMs reach "near-expert classification with structured prompts (Wijesinghe et al., 2026)." In this paper the *structured* (double-step) prompt actually produced **lower** total agreement and lower specificity than the *simplified* prompt; its advantage was very high Recall on UNHEALTHY (0.963–0.982) at the cost of Specificity (0.798–0.844). The honest reading is: structured prompts maximise guideline adherence and sensitivity (safety-oriented), simplified prompts track holistic human judgment better. Recommend softening §2.2 to reflect the recall/specificity trade-off rather than implying structured prompts are uniformly superior.
2. **Conservative ("safety") bias (p. 11, §4.4).** All models, especially under structured prompts, default to "unhealthy" when ingredient detail is incomplete. The authors frame false negatives as more harmful than false positives in clinical settings. This is a useful precedent for how we discuss our categorizer's error asymmetry in §4.1.
3. **Multi-model consensus ("dominant") matched or slightly beat the best single model** across metrics under both prompts (e.g. dominant simplified Acc 0.942, F1 0.949). Supports any multi-model voting we propose; our pipeline is currently single-model (`gpt-4o-mini`), so this is a possible robustness extension to mention.
4. **Workflow-efficiency argument (p. 11, §4.5)** mirrors our own motivation: with 90–94% pre-correct, experts shift from classifying-from-scratch to review-and-refine, focusing on the 6–10% borderline cases. This pairs well with our §1.2 ">75 RD-hours" Hutchinson (B8) point.

---

#### Author-flagged limitations (§4.7, p. 12 — for engagement in our §7)

1. Accuracy is bounded by completeness of product descriptions; ambiguous/poorly-described items drive errors.
2. Polish-language advantage may not transfer to less morphologically inflected languages — multilingual validation needed (relevant caveat: our pipeline is English-language CNF, so the Polish-specific gains here do **not** carry over and we should not over-claim from this paper).
3. Current LLMs lack true multimodal reasoning (cannot read labels/ingredient photos directly).
4. Population mismatch: experts judged "holistically/generally," not against LTCF-specific clinical needs, so the reference standard may not reflect the target population's actual nutritional constraints.

---

#### Three-sentence relevance note

This is the most contemporaneous, directly-on-point benchmark of frontier LLMs (incl. Claude Opus 4.5) on expert-validated food classification, and it is the empirical anchor for our claim (§1.1, §2.2) that LLMs reach near-expert accuracy under structured prompts — properly recited as **Ase et al., 2026**, not Wijesinghe. Its structured NOVA+WHO double-step prompt with JSON-shaped output is a clean published precedent for the rule-anchored, criteria-explicit prompting our §3.4 categorizer uses, and its 90.3–94.2% agreement plus 0.922–0.949 F1 set a realistic upper expectation for our S1 benchmark (tempered by the facts that its task is binary healthy/unhealthy rather than 16-component GBD mapping, it ran at temperature 1.0 rather than our 0, and its gains are partly Polish-language-specific). The recall-vs-specificity trade-off it documents (structured = high recall/low specificity; simplified = balanced) should be folded into both our §2.2 description and our §4.1 discussion of categorizer error asymmetry, and its two-expert consensus design is a near-parallel to our planned S1 gold standard (though it reports no inter-rater κ, which we will).

---

### D23. Zhou, Chow, Harnack et al. (2025) — NutriRAG: retrieval-augmented LLMs for food identification and classification [★★★]

> ⚠️ **CITATION / VERSION FLAGS — READ FIRST.**
> 1. **This is a non-peer-reviewed medRxiv preprint** (doi:10.1101/2025.03.19.25324268, v1 posted 20 March 2025), explicitly stamped "not certified by peer review… should not be used to guide clinical practice." The wishlist (entry 23) and manuscript ref. 37 cite it as **"PMC PMC11957177."** A PMC accession usually implies a peer-reviewed *published* version. **Action:** reconcile these — if PMC11957177 is a published version of this exact work, (a) re-verify the F1 numbers against the published copy before final submission (preprint values can shift in review), (b) update the citation type from "preprint" to the published journal/venue, and (c) re-cite as **Zhou et al., 2025** (lead author Huixue Zhou; corresponding author Rui Zhang, U Minnesota). The manuscript ref. 37 currently reads "NutriRAG authors," which should become the proper author list.
> 2. **Licence is CC-BY-ND 4.0** (No Derivatives). We may cite and quote within normal limits, but must NOT reproduce or adapt their figures/tables as derivatives. We don't need to reproduce any of their tables, so this is low-risk, but worth noting in case anyone wants to lift Figure 2.

**Citation.** Zhou H, Chow LS, Harnack L, Panda S, Manoogian ENC, Li M, Xiao Y, Zhang R. NutriRAG: Unleashing the Power of Large Language Models for Food Identification and Classification through Retrieval Methods. *medRxiv* [preprint]. 2025 Mar 20. doi:10.1101/2025.03.19.25324268. (Wishlist/manuscript cite PMC11957177 — see flag above.)

**DOI.** 10.1101/2025.03.19.25324268 (preprint). Word count 3286.

**Type.** Methods preprint — a retrieval-augmented-generation (RAG) NER framework for classifying free-text diet-app food entries, applied within a 12-week RCT.

---

#### What the "F1 ≈ 0.82" in our §2.2 actually refers to (p. 11, Table)

Our draft §2.2 states "Retrieval-augmented approaches reach F1 ≈ 0.82 on food identification and classification tasks (NutriRAG, 2025)." **Confirmed:** the number is the **retrieval-augmented GPT-4 Micro F1 = 82.24**, the single best model in their Table (vs **73.84** for standard, non-RAG GPT-4 — a +8.4-point RAG gain, the paper's headline finding, Results p. 11 and Discussion p. 17).

**Critical qualifiers to keep our §2.2 honest:**
- It is a **micro-averaged F1** on a **51-class** food-classification/NER task over **free-text diet-tracking-app entries**, evaluated on a **182-entry test set** (gold standard hand-labelled by NDSR-certified staff against the Nutrition Coordinating Center [NCC] Food Database's 51 classes). It is **not** a binary task (contrast D22's 0.92–0.95 F1, which was binary healthy/unhealthy) and **not** a database-linkage task. So 0.82 is the closest published RAG-NER analogue to our work, but it is not a like-for-like benchmark for either S1 (16 GBD risk factors on CNF) or S7 (CNF↔Agribalyse matching).
- The 82.24 figure is from GPT-4-class models (2024 vintage), below the frontier models in D22.

---

#### Architecture — the direct precedent for our §3.5 matcher (and partly §3.4)

NutriRAG's pipeline (Methods pp. 7–9, Figures 1–2) is **structurally the same** as the LLM-assisted food-to-LCA matcher we describe in §3.5:
1. **Query formulation** — the free-text food string is the query.
2. **Retrieval & prompt context** — an "LLM Similarity Calculator" computes **cosine similarity between the embedding of the query and embeddings of candidate examples** in a reference set, ranks them, and selects the **top-k**.
3. **LLM processing** — the LLM is given instruction + retrieved top-k input→output exemplars + the query, and maps each food token to its class.
4. **Output organisation** — LLM output is normalised to structured form via string matching.

This is exactly our §3.5 design ("candidate Agribalyse entries are first retrieved by embedding similarity over food descriptions, then ranked by an LLM"). **Recommendation:** cite NutriRAG in §3.5 as the published precedent for the retrieve-then-rank RAG architecture, not only in §2.2. It also supports the few-shot, **no-parameter-tuning / in-context** approach our pipeline uses.

**Design details we can borrow/cite:**
- Retrieval depth swept from **k = 1–20 examples**; example ordering tested in three arrangements (highest→lowest similarity, and random) — useful precedent if a reviewer asks why we fixed our k or ordering.
- Cosine-similarity retrieval formula given on p. 8 (standard `sim = e(q)·e(d) / (|e(q)||e(d)|)`).

---

#### Results table — key comparators (for §4.4 / S7 framing; do NOT reproduce as a derivative)

Micro F1 (with Micro P / R), food classification, 51 classes:

| Model | Micro P | Micro R | Micro F1 |
|---|---|---|---|
| BERT (fine-tuned) | 56.36 | 62.74 | 59.38 |
| BlueBERT | 49.84 | 57.26 | 53.29 |
| PubMedBERT/BioBERT | 56.82 | 59.71 | 58.22 |
| GPT-3.5 (random examples) | 64.54 | 66.43 | 65.47 |
| GPT-4 (random examples) | 75.97 | 71.53 | 73.84 |
| RAG Llama-2-70b | 68.81 | 58.75 | 63.38 |
| RAG Mixtral 8×7b | 76.07 | 79.89 | **77.93** (best open-source; 2nd overall) |
| RAG GPT-3.5 | 75.00 | 80.29 | 77.55 |
| **RAG GPT-4** | 79.10 | 85.64 | **82.24** (best overall) |

Takeaways usable in our §4: (i) RAG lifts every base model; (ii) the best open-source RAG model (Mixtral, 77.93) nearly matched RAG GPT-3.5 and beat standard GPT-4 — relevant if we discuss cost/open-weight options for our matcher; (iii) fine-tuned BERT-family encoders (53–59 F1) were clearly beaten by RAG-LLMs, supporting our choice of an LLM-augmented rather than classical-ML approach.

*Minor internal inconsistency in the source:* the food-classification table is labelled "Table 1" but referred to as "Table 2" in the Results text (p. 11); the actual "Table 2" is the RCT baseline data. Not material to us, but note it if quoting a table number.

---

#### Secondary content (not central to our manuscript)

The second half applies the classifier within the parent RCT (NCT04259632; Oldenburg et al. 2025, *Obesity*): 77 analysable obese-without-diabetes participants (27 TRE / 25 CR / 25 UR), 12-week intervention, 32,825 free-text entries; eating-occasion (EO) timing analysis showing TRE/CR reduced daily EOs and shifted meal timing, with a breakfast-EO ↔ HOMA insulin-resistance association. **Not relevant to ecodish365** beyond demonstrating a downstream use of the classifier; we do not need any of these numbers.

---

#### Author-flagged limitations (Discussion p. 19 — for our §7)

1. **RAG quality is bounded by retrieval-corpus quality** — performance degrades "in situations where relevant external data are limited or biased." This is the key transferable caveat: our §3.5 matcher's accuracy is similarly hostage to the coverage/representativeness of the Agribalyse candidate pool and the embedding index, and we should say so in §7.
2. (Implicit) preprint status / single-cohort, single-app data source; English-only; no external validation.

---

#### Three-sentence relevance note

NutriRAG is the empirical source of our §2.2 "F1 ≈ 0.82" claim (specifically the retrieval-augmented GPT-4 Micro F1 of 82.24 on a 51-class free-text food-classification task) and, more importantly, it is the closest published architectural precedent for the retrieve-by-embedding-then-rank-by-LLM design of our §3.5 food-to-LCA matcher — so it should be cited in §3.5, not only §2.2. Its core lesson, that RAG lifts every base model and that retrieval quality bounds output quality, transfers directly to our matcher and belongs in our §7 limitations. Two cautions before final submission: it is a non-peer-reviewed CC-BY-ND preprint cited in our draft via a PMC ID that implies a published version (reconcile and re-verify the numbers if so), and its 0.82 is a micro-F1 on a multi-class NER task that is not a like-for-like benchmark for either our S1 (16 GBD risk factors) or S7 (CNF↔Agribalyse linkage), so it should frame expectations rather than serve as a direct target.

---

### D24. Gjorgjevikj, Martinc, Cenikj et al. (2026) — FoodyLLM: a domain-specialized fine-tuned LLM for food/nutrition tasks [★★★]

> ⚠️ **CITATION CORRECTION + USAGE CORRECTION — READ FIRST.**
> 1. **Wrong venue/year in the draft.** Wishlist (entry 24) and manuscript ref. 38 cite this as **"FoodyLLM. 2025. PMC PMC12927182."** It is in fact a **peer-reviewed Elsevier journal article: Gjorgjevikj A, et al. *Current Research in Food Science* 2026;12:101351, doi:10.1016/j.crfs.2026.101351** (received 13 Nov 2025; accepted 13 Feb 2026; online 16 Feb 2026; open access, CC BY-NC-ND). **Action:** replace ref. 38 with the full author list and CRFS citation; lead author **Gjorgjevikj**, corresponding **Tome Eftimov** (Jožef Stefan Institute). Update the in-text "(FoodyLLM, 2025)" in §2.2 to "(Gjorgjevikj et al., 2026)."
> 2. **The §2.2 sentence mischaracterizes this paper.** Our draft §2.2 reads: "Recent work demonstrates that LLMs can classify food items at near-expert accuracy when prompted with structured criteria and validated by domain experts ([Nutrients 2026]…; [FoodyLLM, 2025])." FoodyLLM is **not** a structured-prompting result — it is a **fine-tuning** result, and its headline finding is the *opposite* of what that sentence implies: general-purpose LLMs (Gemini 2.0, Llama 3 8B) **fail** these tasks even with five-shot prompting, and only **domain-specific fine-tuning** closes the gap. **Action:** remove FoodyLLM from that sentence (leave Ase et al. 2026 as the structured-prompting citation) and instead cite FoodyLLM where the manuscript discusses the prompting-vs-fine-tuning design choice (see "Tension" below). Citing it as-is invites a reviewer to point out we mis-read our own reference.

**Citation.** Gjorgjevikj A, Martinc M, Cenikj G, Stojanov R, Drole J, Ispirova G, Menichetti G, Ogrinc N, Trajanov D, Džeroski S, Koroušić Seljak B, Eftimov T. Large language models in food and nutrition science: Opportunities, challenges, and the case of FoodyLLM. *Current Research in Food Science.* 2026;12:101351. doi:10.1016/j.crfs.2026.101351.

**DOI.** 10.1016/j.crfs.2026.101351 (open access, CC BY-NC-ND 4.0 — no derivatives, so do not reproduce their figures/tables as adaptations; factual numbers may be reported).

**Type.** Review + original methods. Introduces a fine-tuned domain LLM and benchmarks it on three food tasks.

---

#### What FoodyLLM actually is (§3, Appendix A)

A **fine-tuned Llama 3 8B Instruct** model (LoRA, 4-bit; r = 16, α = 16, dropout 0.05, lr 2e-4, 1 epoch, max seq 1024), multi-task-trained on **~225k task-aligned QA pairs** for three tasks: (i) recipe macronutrient estimation, (ii) FSA traffic-light classification, and (iii) ontology-based food **named-entity recognition + linking (NER/NEL)** to FoodOn, SNOMED-CT and Hansard. Benchmarked against non-fine-tuned **Llama 3 8B** and **Gemini 2.0 Flash** under zero-/one-/five-shot prompting, five-fold evaluation. Recipe1M+ is the primary recipe source. Compute: ~500 A100-GPU-hours. Code: github.com/matejMartinc/FoodyLLM; weights: huggingface.co/Matej/FoodyLLM.

**Training-data composition (Table 5, p. 15) — useful as a precedent for dataset scale:**
recipe nutrient profile 29,410 QA (19,524 train / 9,886 test); traffic-light 29,410 (same split); food NER+NEL 21,027 (16,822 / 4,205); plus train-only auxiliaries — ingredient nutrition 9,196, food synonyms 11,463, household-measure conversion 65,955.

---

#### Headline results (Tables 1–4, 10–12; do NOT reproduce as derivatives — report figures only)

- **Nutrient estimation, tolerance-based accuracy** (EU Reg. 1169/2011 tolerances, Appendix B): FoodyLLM **0.909–0.972** (protein 0.972, saturates 0.938, fat 0.920, sugar 0.917, salt 0.909) vs **Gemini 2.0 best (5-shot) 0.433–0.628** and Llama 3 8B far lower. Abstract summary: accuracy rises "from 0.43 to 0.63 to 0.91–0.97."
- **Traffic-light classification, macro F1:** FoodyLLM **0.865–0.971** vs Gemini **0.453–0.797**. Abstract: "0.46 → 0.80 → 0.86–0.97."
- **NEL on artificial data, macro F1:** FoodyLLM **0.942 (FoodOn), 0.975 (SNOMED), 0.932 (Hansard)** vs Gemini best (5-shot) **0.330 / 0.330 / 0.438** (Table 4/10).
- **NER+NEL on real corpora, macro F1:** FoodyLLM **0.665–0.835** (CafeteriaFCD 0.823–0.835; CafeteriaSA 0.665–0.735) vs Gemini **0.240–0.505** and Llama 3 8B **0.161–0.417** (Tables 4, 11, 12). Beats prior BERT/BioBERT literature baselines (0.43–0.789).
- **Generalization to branded foods (Open Food Facts, 2070 products): FoodyLLM drops to 0.29–0.46 accuracy** because branded products list ingredients *without quantities* (p. 8). This is the single most transferable warning for us (see below).

---

#### The tension this paper creates for our design (§3.4 / §3.5 / §7) — the most important takeaway

FoodyLLM is the strongest published evidence that, on food classification / nutrient-estimation / ontology-linking tasks, **prompting general-purpose LLMs (even five-shot) substantially underperforms a fine-tuned domain model.** Our pipeline deliberately uses **rule + prompting** (§3.4) and **RAG prompting** (§3.5), *not* fine-tuning. A reviewer who knows this paper will ask "why didn't you fine-tune?" We should pre-empt that in §3.4/§7 with the principled reasons our draft already gestures at — auditability, openness, zero training cost, LLM confined to the ambiguous long tail — while honestly acknowledging FoodyLLM shows fine-tuning would likely raise accuracy. Two specific contrasts to fold in:
- **For §3.5 (the matcher):** FoodyLLM's NEL numbers show general-purpose LLMs reach only **0.33–0.51 macro F1 on food→ontology linking even with five-shot prompts** (Table 4). Our matcher does food→Agribalyse linking by RAG prompting, which is conceptually the same problem. NutriRAG (D23) shows RAG *lifts* this (to ~0.82), but FoodyLLM shows the prompting-only floor is low — so our §3.5 success hinges on retrieval quality, and we should say so. Helpfully, **FoodyLLM's own authors recommend RAG as the mitigation** for the linking task's brittleness (Discussion p. 9, citing their forthcoming FoodOntoRAG / Drole et al. 2025) — i.e. our RAG choice in §3.5 is endorsed by this paper's authors.
- **For §3.4 (the categorizer):** their tolerance-based-accuracy evaluation against a regulatory standard (EU 1169/2011) is a clean precedent for how to report classification accuracy, and the two-prompt (with/without title) ablation is a precedent for prompt-sensitivity reporting in our S1.

Note: unlike our task, FoodyLLM *estimates* nutrient values from ingredients; ecodish365 reads CNF nutrient values directly, so the nutrient-estimation track is **not** something we replicate — it is context, not a method we adopt.

---

#### Author-flagged limitations (Discussion pp. 9–11, Conclusion — for our §7)

1. **Coverage bound to training data:** FoodyLLM can only link ontology concepts **present in its training corpus** — "newly introduced ontology concepts that are absent from the training corpus cannot yet be linked" (Conclusion). This is the generic failure mode of fine-tuning vs. our RAG approach, which can in principle retrieve unseen targets — a point in favour of our §3.5 design.
2. **Quantity-free inputs degrade performance** (branded-food drop to 0.29–0.46). Relevant: where our CNF entries or Agribalyse candidates lack quantity/composition detail, matcher/score quality will fall.
3. **Non-negligible residual error** "from a clinical and public health perspective"; positioned explicitly as a **semi-automatic decision-support tool requiring human oversight** (AI Act / GDPR framing). Directly parallels our framing of AI as bounded, human-checked subsystems.
4. **Cultural/linguistic bias not analyzed**; model reflects the (largely English, Recipe1M+) training distribution.

---

#### Three-sentence relevance note

FoodyLLM is a peer-reviewed (CRFS 2026;12:101351 — not the 2025 PMC preprint our draft cites) demonstration that domain fine-tuning massively outperforms prompting on food nutrient-estimation, traffic-light, and ontology-linking tasks, which is why it should be removed from the §2.2 "structured-prompting near-expert" sentence (it shows the opposite) and instead cited where we justify our prompting-not-fine-tuning design. Its most useful contribution to our manuscript is the explicit prompting-vs-fine-tuning tension: general-purpose LLMs reach only 0.33–0.51 macro F1 on food→ontology linking even at five-shot, which both warns that our §3.5 RAG matcher's accuracy is hostage to retrieval quality and, helpfully, is the exact problem the FoodyLLM authors say RAG should mitigate (endorsing our §3.5 architecture and that of NutriRAG, D23). Its branded-food generalization drop (0.29–0.46 when quantities are absent) and its "coverage bounded to training data" limitation are concrete §7 material, the latter actually favouring our retrieval-based approach over fine-tuning for handling unseen CNF/Agribalyse entries.

---

### D25. Fridolfsson, Sjöberg, Thiwång & Pettersson (2025) — Performance of 3 LLMs for nutritional estimation from food images [★★ — framing only; image-based, not a method we adopt]

> ⚠️ **CITATION + RELEVANCE FLAGS — READ FIRST.**
> 1. **Citation.** Wishlist (entry 25) gives "PMC PMC12513282" and §2.2 cites it as a bare "[ScienceDirect 2025]" URL with no numbered reference. It is **Fridolfsson J, Sjöberg E, Thiwång M, Pettersson S. *Current Developments in Nutrition* 2025;9:107556, doi:10.1016/j.cdnut.2025.107556** (open access, CC BY; American Society for Nutrition / Elsevier). Lead author **Fridolfsson** (U Gothenburg). **Action:** add a proper numbered reference. Cross-reference: this is **ref. 7 in the Ase et al. (D22) paper** — same image-assessment subfield.
> 2. **Relevance is framing only.** ecodish365 reads CNF nutrient values directly from `FoodID`; it does **no image-based estimation**. None of this paper's MAPE numbers are a benchmark for any ecodish365 task. It supports exactly one §2.2 sentence and otherwise serves as a vivid illustration of the misidentification-cascade failure mode that motivates our confidence-thresholding (§3.5) and rule-first (§3.4) design. Models tested are **mid-2024 vintage** (now dated); avoid over-relying on the absolute numbers.

**Citation.** Fridolfsson J, Sjöberg E, Thiwång M, Pettersson S. Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from Food Images. *Current Developments in Nutrition.* 2025;9:107556. doi:10.1016/j.cdnut.2025.107556.

**DOI.** 10.1016/j.cdnut.2025.107556 (open access, CC BY 4.0 — reproduction permitted with attribution; still default to paraphrase).

**Type.** Validation study comparing three multimodal LLMs against weighed-reference + database nutritional values on standardized food photographs.

---

#### Design (Methods, pp. 2–3)

- **Models:** ChatGPT-4o (OpenAI, 2024-05-13), Claude 3.5 Sonnet (Anthropic, 2024-06-21), Gemini 1.5 Pro (Google, 2024-04-09). Analyses run Sept 2024, fresh chat per image (no cross-image learning).
- **Stimuli:** 52 standardized photographs (iPhone 13; white 24.3 cm plate, 19 cm fork / 20.5 cm knife as size references; 42° angle). Built from 12 base dishes (3 starch bases × protein/vegetable combinations + 3 prepackaged meals), in 3 portion sizes (small = 50%, medium, large = 150% of Swedish Food Agency standard portions).
- **Reference:** calibrated weighing + Dietist NET software (which references the **USDA National Nutrient Database**), manufacturer labels for prepackaged items.
- **Identical prompt for all models** (recognize components → estimate volume using objects for scale → assign nutrient values → tabulate weight/energy/CHO/fat/protein per component + total). Authors note adding plate dimensions or "act as nutritionist" framings gave no clear benefit; simpler prompt chosen for realism.
- **Metrics:** MAPE (bootstrap 95% CI), Pearson r, mean bias, systematic-bias slope (regression of difference on reference), Bland–Altman.

*Internal inconsistency to be aware of (not our problem to fix):* the abstract says "individual food components (n = 16) and complete meals (n = 36)," while Methods says "complete meals (n = 12) and individual components (n = 16)" and breaks the 52 photos down as 9 starch-only + 9 protein + 4 vegetable + 30 complete meal. Cite the paper's conclusions, not its component counts.

---

#### Key results (Table 1, p. 4 — report figures, do not reproduce the table)

MAPE / Pearson r (UNHEALTHY n/a; continuous estimation):

| Nutrient | ChatGPT-4o | Claude 3.5 Sonnet | Gemini 1.5 Pro |
|---|---|---|---|
| Weight | 36.3% / r 0.77 | 37.3% / r 0.81 | 65.0% / r 0.71 |
| Energy | 35.8% / r 0.73 | 35.8% / r 0.78 | 64.2% / r 0.63 |
| CHO | 47.9% / r 0.67 | 72.8% / r 0.75 | 66.1% / r 0.73 |
| Protein | 60.7% / r 0.73 | 61.7% / r 0.75 | 109.9% / r 0.58 |
| Fat | 51.8% / r 0.65 | 41.7% / r 0.72 | 89.6% / r 0.64 |

- **ChatGPT ≈ Claude** (no significant MAPE difference except fat, where Claude better, p = 0.04); both significantly beat Gemini on weight/energy/protein (p < 0.01).
- **All models systematically underestimate, worsening with portion size** (bias slopes −0.23 to −0.50); MAPE ~20–30% lower for small than large portions. Authors partly attribute this to vegetables placed in front obscuring calorie-dense starch/protein behind them as portions grew.
- **Gemini** had large positive mean bias (weight +64.6 g, energy +65.0 kcal); ChatGPT/Claude near-zero, nonsignificant.
- **Misidentification → catastrophic error:** Gemini called falafel "meatballs" (+360% protein); Claude called scrambled eggs "pasta" (+1788% CHO, which alone inflated Claude's CHO MAPE); ChatGPT under-weighed a lentil curry (255 g vs 480 g actual).
- **Benchmark context:** authors compare to athlete estimated-diet-record validation (MAPE 26.5% ± 16.8%); ChatGPT/Claude at ~36% are "comparable with traditional self-report" but Gemini markedly worse. Conclusion: general-purpose LLMs **not yet suitable for precise dietary assessment** in clinical/athletic settings.

---

#### How this maps to our manuscript

- **§2.2:** the one sentence it supports — "for images, GPT-class models approach but do not yet meet expert nutritional content estimation" — is fairly characterized. Tighten slightly: this paper benchmarks against *self-reported* methods, not experts directly; the "comparable to dietitian" claim comes from its internal citation to Lo et al. 2024 (GPT-4V mean abs error 46.3 g vs dietitian 48.5 g). Either keep the §2.2 sentence as-is with the Fridolfsson cite, or add Lo et al. 2024 (*IEEE J Biomed Health Inform* 28(12):7577) if we want the explicit dietitian comparison.
- **§3.4 / §3.5 (failure-mode motivation):** the 1788%-CHO and 360%-protein misID cascades are the cleanest published illustration of *why* a single LLM output must not be trusted unguarded — directly motivating our rule-first gate (§3.4) and confidence-threshold-with-fallback (§3.5, fallback at confidence < 0.6). Worth a one-line cite there.
- **§3.6 / uncertainty:** the authors' suggestion to run multiple stochastic inferences and report ranges/CIs rather than point estimates is philosophically aligned with our Monte Carlo uncertainty stance, though for a different source of variance (LLM stochasticity vs LCA factor uncertainty). Minor, optional.

---

#### Author-flagged limitations (Discussion pp. 6–7 — for our §7 if cited)

Static single-angle 2D images; relatively simple plated presentations vs real mixed dishes; no food-specific fine-tuning; mid-2024 models (authors explicitly note reasoning models like o1 and food-specific LLMs may close the gap); volume-from-2D is the core hard problem; privacy/compute concerns from uploading photos to data centres.

---

#### Three-sentence relevance note

This is a framing-only citation for ecodish365: it underpins the single §2.2 statement that image-based general-purpose LLMs approach but do not yet match expert/traditional nutritional estimation (ChatGPT/Claude ~36% MAPE on weight/energy, comparable to self-report; Gemini markedly worse), and nothing in it benchmarks any ecodish365 task because our pipeline reads CNF values directly rather than estimating from images. Its real utility is illustrative: the misidentification-driven error cascades (a single wrong food label producing a 1788% macronutrient error) are the most vivid published justification for our rule-first categorizer (§3.4) and confidence-thresholded matcher with fallback (§3.5). It needs a proper numbered reference (currently a bare URL in the draft), should be recited as Fridolfsson et al., 2025 (*Curr Dev Nutr* 9:107556), and its mid-2024 model vintage means we should lean on its qualitative lesson rather than its absolute error figures.

---

### D26. Hu, Ahmed & L'Abbé (2023) — NLP + ML for food categorization and nutrition-quality-score prediction vs traditional methods [★★★]

> ⚠️ **CITATION CORRECTION — READ FIRST (this resolves the flag raised under D23/D25).**
> The wishlist (entry 26) and the draft cite this as **"Eisenberg, M.D., et al. (2022). … *Am. J. Clin. Nutr.* 116. doi:10.1093/ajcn/nqac225."** The **title is verbatim identical**, confirming this is the intended paper, but the author, volume and DOI are all wrong. Correct citation: **Hu G, Ahmed M, L'Abbé MR. *Am J Clin Nutr.* 2023;117(3):553–563. doi:10.1016/j.ajcnut.2022.11.022** (received 14 Sep 2022; accepted 29 Nov 2022; online 23 Dec 2022; published vol. 117, 2023). This is the **same paper** that appears — correctly attributed to Hu/L'Abbé — as **refs 16 and 19 in the NutriRAG (D23) paper**. **Action:** in the draft, replace "Eisenberg et al., 2022" with **Hu et al., 2023**, fix the volume to 117(3):553–563 and the DOI to 10.1016/j.ajcnut.2022.11.022. (The "nqac225" Oxford-style DOI predates AJCN's 2023 move to Elsevier and does not resolve to this article as published.) Note this paper currently has **no in-text citation** in the draft — it should be added to §3.2/§3.4 (see below).

**Citation.** Hu G, Ahmed M, L'Abbé MR. Natural language processing and machine learning approaches for food categorization and nutrition quality prediction compared with traditional methods. *Am J Clin Nutr.* 2023;117(3):553–563. doi:10.1016/j.ajcnut.2022.11.022.

**DOI.** 10.1016/j.ajcnut.2022.11.022. © 2022 American Society for Nutrition / Elsevier (all rights reserved — paywalled; paraphrase only).

**Type.** Original research — automating food categorization (classification) and nutrient-profiling-score prediction (regression) on a large **Canadian** branded-food database using sentence-BERT embeddings + classical ML, benchmarked against bag-of-words and structured-nutrient-facts models. L'Abbé group, U Toronto.

---

#### Why this is highly relevant to ecodish365 (shared Canadian dependencies)

This is the most methodologically adjacent Group D paper to our actual pipeline, on three fronts the others don't touch:
1. **Health Canada Table of Reference Amounts (TRA)** is the classification target here (24 major categories, 172 subcategories) — and **TRA 2016 is a mandatory external database in our §3.2** (HEFI-2019 reference amounts). Same canonical Canadian reference.
2. **FSANZ nutrient-profiling score** is the regression target — and **FSANZ/NPSC is the algorithmic basis of our HSR** (§3.2). Their structured-vs-text comparison directly informs our HSR design choice.
3. **FVNL (Fruit/Veg/Nut/Legume) estimation from ingredient lists without quantitative declarations** is a sub-problem they solve — and it is **exactly the problem our §3.2 HSR FVNL step faces** (we use Barrett et al. 2025 geometric weighting; they use the Vergeer et al. 2020 descending-ingredient-order method).

---

#### Methods (pp. 2–4)

- **Data:** University of Toronto FLIP (Food Label Information and Price) database — Canadian branded packaged foods. FLIP2020 (n = 74,445; 46,020 after exclusions for TRA, 33,917 for FSANZ) for development (70/30 train/test); FLIP2017 (n = 19,720; 19,323 / 18,934 after exclusions) as an **external generalization test set**.
- **Gold standard:** manual TRA categorization and FSANZ scoring by trained nutrition researchers (MSc/PhD), each verified by a second member; **inter-rater agreement >96% overall (≈96–99% by category)** — a useful benchmark for our own S1 two-dietitian κ target.
- **Representation:** Siamese / sentence-BERT encoding of food-label text (name, brand, ingredients) into **384-dimensional dense vectors**; compared against bag-of-words (top 100/500/1000/2000 ingredients, one-hot) and, for FSANZ, against **structured nutrient-facts inputs** (nutrients per 100 g/mL).
- **Classifiers/regressors:** elastic net, KNN, XGBoost. XGBoost best throughout.

---

#### Key results (Tables 1–3 — report figures, do not reproduce)

**TRA food categorization (Table 1; sentence-BERT + XGBoost, name+brand+ingredients):**
- Major category **accuracy 0.98** (balanced 0.96); subcategory **accuracy 0.96** (balanced 0.89).
- Per-category F1 0.90–0.99; **115/145 subcategories (n > 5) had F1 > 0.9**.
- Pretrained LM beat bag-of-words at equal dimensionality and was **more generalizable** to FLIP2017 (0.91 acc vs BoW-2000 0.90, at 768-dim vs 2000-dim) because top-ingredient lists drift across databases/years — directly relevant to our cross-database harmonisation concerns.
- 80% of subcategory predictions reached F1 > 0.9 with the pretrained LM vs 32–70% (BoW) and 62% (structured nutrient facts).

**FSANZ nutrient-quality-score prediction (Table 3) — the key result for our HSR design:**

| Method | Input | R² | MSE |
|---|---|---|---|
| Structured nutrient facts | nutrients per 100 units | **0.98** | **2.5** |
| Structured nutrient facts | nutrient facts table | 0.91 | 9.8 |
| Pretrained LM | name+brand+ingredients | 0.87 | 14.4 |
| Bag-of-words | top 2000 ingredients | 0.84 | 17.6 |
| Bag-of-words | top 100 ingredients | 0.72 | 30.3 |

**Takeaway that validates our HSR approach:** when structured nutrient values are available, computing/predicting the nutrient-profiling score from **structured nutrient data (R² 0.98)** vastly outperforms text-based prediction (R² 0.84–0.87). Our pipeline **computes HSR deterministically from CNF nutrient values** (§3.2) rather than predicting it from text — this paper is direct empirical support for that choice, and the text-based route is only a fallback when nutrient data are missing. (Avg manually-computed FSANZ scores: FLIP2017 = 7.1, FLIP2020 = 6.8.)

---

#### How to use it in the manuscript

- **§3.2 (HSR):** cite as Canadian empirical support that nutrient-profiling scores are best computed from structured nutrient data (R² 0.98), justifying our direct-from-CNF HSR computation. Also cite the **Vergeer et al. 2020 FVNL-from-ingredient-order method (their ref. 14)** as the established Canadian alternative to our Barrett-2025 geometric FVNL weighting — a useful cross-check or sensitivity comparison for §3.2, since both confront the same "no quantitative ingredient declarations in Canada" problem.
- **§3.4 (categorizer):** cite as a Canadian precedent that automated food→category mapping is highly tractable (TRA accuracy 0.98) and that **embedding-based representations generalize better across databases/years than ingredient-frequency features** — supporting our embedding-retrieval design over brittle keyword/frequency rules. Caveat: their target is the TRA taxonomy, not GBD dietary risk factors, so it shows feasibility, not a transferable accuracy figure.
- **§4.1 (S1 benchmark design):** their >96% manual inter-rater agreement and second-reviewer verification is a clean precedent for our two-dietitian gold-standard protocol.

---

#### Author-flagged limitations (Discussion pp. 9 — for our §7)

1. **General-corpus BERT, not food-specific** — authors state "further model training to leverage food-specific corpora is needed." Echoes FoodyLLM (D24): domain specialization helps. Relevant caveat for any embedding model we use in §3.5.
2. **Small-class fragility:** subcategories with < ~350 training products had F1 0.55–0.84; accuracy is highly dependent on per-class sample size. Directly relevant to our long-tail GBD-risk-factor categories and rare CNF foods — the exact case where our §3.4 escalates to the LLM.
3. **FVNL estimated from descending ingredient order** (no quantitative declarations in Canada) introduces error into FSANZ — the identical limitation our HSR FVNL step carries; we should acknowledge it in §7.
4. Data limited to retailer-website information; e-commerce labelling unstandardized; imbalanced classes.

---

#### Three-sentence relevance note

This is the most pipeline-adjacent Group D paper because it operates on the same Canadian infrastructure we do — Health Canada's Table of Reference Amounts (our HEFI-2019 dependency) and the FSANZ nutrient-profiling system (our HSR's algorithmic basis) — and it empirically establishes that nutrient-profiling scores are far better computed from structured nutrient data (R² 0.98) than predicted from label text (R² 0.84–0.87), which is direct support for our decision to compute HSR deterministically from CNF rather than infer it. Its TRA categorization result (0.98 accuracy, embeddings generalizing better than ingredient-frequency features across databases) is a Canadian precedent for the feasibility and design of our §3.4 categorizer, and its >96% two-reviewer manual gold standard is a model for our S1 protocol. It must be re-cited as Hu et al., 2023 (*AJCN* 117(3):553–563, not "Eisenberg 2022, vol 116, nqac225"), added as a new in-text citation in §3.2/§3.4, and its Vergeer et al. 2020 FVNL-from-ingredient-order method (its ref. 14) is worth citing in §3.2 as the established Canadian alternative/cross-check to our Barrett-2025 geometric FVNL weighting.

---

### D27. Krahmer (2024) — LEAF: predicting the environmental impact of food products from their name (food-text → Agribalyse LCA) [★★★ — the key prior-art test of our §3.5 novelty claim]

> ⚠️ **NOVELTY-CLAIM IMPACT — READ FIRST.** This is the closest published prior art to our §3.5 LLM-assisted food→LCA matcher, and it **directly contradicts the blanket version** of our §2.2 / abstract claim. LEAF links a food product **name → an Agribalyse class → that class's Agribalyse life-cycle (EF) score**, and explicitly states it is "the first work exploring the usage of NLP methods specifically for the estimation of environmental impact of food products" (p. 133, §1.1). **Action:** we must (a) cite Krahmer 2024, and (b) **narrow our novelty claim** from "no published system uses LLMs to bridge nutrition databases with LCA inventories" to a defensible, distinction-based claim (see "Surviving novelty" below). Leaving the broad claim unqualified would be falsified by this single paper.

**Citation.** Krahmer B. LEAF: Predicting the Environmental Impact of Food Products based on their Name. In: *Proceedings of the 1st Workshop on Natural Language Processing Meets Climate Change (ClimateNLP 2024)*, Bangkok: Association for Computational Linguistics; 2024. p. 133–142.

**Venue/Access.** ACL Anthology, ClimateNLP 2024 workshop (peer-reviewed workshop; openly available, ACL © 2024, CC BY 4.0). Single author, independent researcher. Code/data/models released (GitHub baskrahmer/LEAF; HF baskra/leaf, leaf-base, leaf-large).

**Type.** Methods paper — multilingual NLP model that predicts a food's PEF Environmental Footprint score from its product name via an Agribalyse-class intermediary.

---

#### What LEAF does (Figure 2; §2)

Pipeline: **product name (any language) → NLP model → predicted Agribalyse class (of 2518) → Agribalyse lookup → EF score (mPt/kg) → optional discretization to an A–E Eco-Score.** This is the same *food-text → Agribalyse-LCA* bridge our §3.5 builds, but with four mechanistic differences that matter for our novelty framing (below).

- **Data.** Open Food Facts (OFF), exported 31 Mar 2024; 800,589 products, filtered to those with an Agribalyse class; **2518 Agribalyse classes**. Multilingual (French 40%, English 32%, Spanish 10%). ODbL-licensed.
- **Target = PEF Environmental Footprint, not ReCiPe.** EF score is the European Commission's **14-factor PEF** aggregate (mPt/kg), climate-dominated (CO₂eq); discretized to Eco-Score (analogous to but distinct from Nutri-Score). **This is exactly the PEF method our §3.2 explicitly argues is *not* interchangeable with ReCiPe** — so LEAF outputs the very metric we deliberately avoid.
- **Model.** Frozen multilingual **sentence-embedding base** (distiluse-multilingual-base-v2, 135M; or bge-m3, 561M) + a **trained readout head** (LEAFc classification / LEAFr regression / LEAFh hybrid). The base is **not fine-tuned**; only the head is learned. So the production model is an **embedding-+-classifier**, *not* a generative LLM.

---

#### Key results (Tables 1–2)

| Model | Accuracy | MAE (EF) |
|---|---|---|
| LEAFc (DU, 135M) | 0.731 | 0.071 |
| LEAFc (M3, 561M) | **0.772** | **0.057** |
| LEAFh (hybrid) | 0.696 | 0.224 |
| LEAFr (regression) | n/a | 0.233 |
| GPT-3.5-turbo zero-shot (175B) | 0.374 | 0.110 |
| Cosine-similarity baseline (M3, untrained) | 0.193 | 0.300 |

- **A small trained classifier head beats GPT-3.5 zero-shot by ~2× on accuracy** (0.73 vs 0.37) despite ~1000× fewer parameters; classification > regression for EF prediction. (GPT-3.5 had a *better* MAE than LEAFh, because its misclassifications stayed within tighter EF bounds.) Global EF σ = 0.448; LEAFc MAE 0.057–0.071.
- **GPT-3.5 hallucinated non-existent class labels** at rate 0.19; the author notes this "can be prevented by limiting token generation to the possible class names" — reinforcing our §3.5 design of constraining the LLM to retrieved valid Agribalyse candidates.
- Multilingual: strong for top-5 languages (fr/en/es/it/de, acc 0.63–0.80), collapses for low-resource (Chinese/Hindi/Bengali, tiny n).
- **Cross-link:** LEAF's related-work cites **Hu et al. 2023 (our D26)** and Balaji et al. 2023 (CaML, zero-shot sentence-BERT emissions estimation of consumer products) — useful additional citations for our §2.2.

---

#### The surviving (narrowed) novelty for §2.2 / §3.5

LEAF pre-empts the broad claim, but our §3.5 contribution survives on **four concrete distinctions**, which we should state explicitly rather than asserting blanket priority:
1. **Source side:** LEAF links a **product-name string** (Open Food Facts); ecodish365 links **entries of a structured national nutrition database (CNF, with composition/serving fields)**. Bridging a *composition database* to LCA is a different task from name-string classification.
2. **LCIA target:** LEAF outputs the **aggregate PEF/EF (single Eco-Score)** baked to French assumptions; ecodish365 re-scores inventories under **ReCiPe 2016 (17 midpoints / 3 endpoints), with Canadian regional layers and Monte Carlo uncertainty** — not a single aggregate.
3. **Mechanism:** LEAF uses a **closed-set classifier head over 2518 fixed classes**; ecodish365 uses **open retrieval (embedding similarity) + LLM ranking with a 0–1 confidence score and logged fallback** to food-group defaults. Different machinery, and open-set vs closed-set.
4. **"LLM" specifically:** LEAF's production model is a **frozen sentence-embedding + trained head**, not a generative LLM (its only LLM use, GPT-3.5, is a *losing baseline*). Our matcher uses a generative LLM for reasoning/ranking. *Caveat:* a reviewer may regard sentence-transformers as "language models," so do **not** rest the novelty solely on the LLM-vs-embedding distinction — lean primarily on distinctions 1–3 (structured-DB source, ReCiPe-not-PEF, open retrieve-rank-with-confidence-and-fallback).

Recommended rewrite of the §2.2 sentence (currently "To our knowledge, no published system uses LLMs to bridge nutrition databases (CNF, FNDDS) with environmental LCA inventories"): something like — "Prior NLP work links food *names* to Agribalyse's aggregate PEF/Eco-Score (Krahmer, 2024) or interlinks composition and LCI databases via classification metadata [Interlinking paper, if obtained]; to our knowledge no system uses an LLM-assisted open retrieval-and-ranking matcher with confidence-scored fallback to link structured nutrition-database entries to peer-reviewed inventories re-scored under ReCiPe."

---

#### Author-flagged limitations (§5) — two are directly useful to us

1. **"Fixed Consumption Location: models assume the product is consumed in France, per Agribalyse assumptions… transportation is location-specific… caution is needed for locations with significantly different food supply chains than France."** This is **independent third-party support for our §3.7 Canadian regional adaptation** — it confirms that Agribalyse's France-baked assumptions (especially transport) must be adjusted for other geographies, exactly the gap our Canadian factor layer fills. Cite in §3.7.
2. **"Additional Data Sources": name-only is limited; ingredient lists, country of production/consumption, transport, packaging "could provide additional insights… A new model that combines different data sources under varying levels of uncertainty could be superior."** This both motivates our richer matcher inputs (we use descriptions/composition, not just names) and aligns with our uncertainty-aware design — a tidy citation for §3.5/§3.6.
3. *Other:* limited within-class specificity (an apple is "apple" regardless of origin); LCA-class redundancy (3 almond classes, identical LCA).

---

#### Three-sentence relevance note

LEAF is the single most important prior-art paper for our §3.5 contribution because it builds the same food-text → Agribalyse-LCA bridge and self-declares NLP-for-food-environmental-impact priority, so our §2.2/abstract novelty claim must be cited against it and narrowed to the defensible distinctions our system actually holds: a structured nutrition-database (CNF) source rather than product names, ReCiPe 2016 with regional layers and Monte Carlo uncertainty rather than the aggregate French PEF/Eco-Score, and an open LLM retrieve-rank matcher with confidence-scored fallback rather than a closed-set classifier head. Its empirical lesson — a small trained classifier beat GPT-3.5 zero-shot ~2× on food→Agribalyse-class accuracy, and GPT-3.5 hallucinated invalid classes at 0.19 — is a further caution (echoing FoodyLLM D24 and Fridolfsson D25) that our prompting-based matcher must constrain outputs to retrieved valid candidates and may underperform a trained classifier on the closed-set sub-problem. Its "Agribalyse assumes consumption in France" limitation is independent support for our §3.7 Canadian regionalization, and its call for multi-source, uncertainty-aware models aligns with our §3.5/§3.6 design; cite Krahmer 2024 in §2.2 (with Hu et al. 2023/D26 and Balaji et al. 2023, both in LEAF's related work), §3.5, and §3.7.

---

### D27b. Furrer, Sieh, Jank, Le Bras, Herrmann, Reguant-Closa & Nemecek (2024) — Semi-automated EuroFIR ↔ Agribalyse interlinkage via LanguaL™ harmonized descriptors (non-LLM, classification-metadata) [★★★ — the closest *task-level* prior art to our §3.5 matcher]

> ⚠️ **NOVELTY-CLAIM IMPACT — COMPANION TO D27.** Where D27/LEAF is the closest *NLP*-prior art (food name → Agribalyse class via sentence-embeddings), Furrer et al. 2024 is the closest *task*-prior art: it directly interlinks a composition database (EuroFIR) with an LCI database (Agribalyse) at the food-item level. It is **non-LLM and classification-metadata-based**, so it does *not* falsify our LLM-specific framing, but it does pre-empt the broader "no published system bridges nutrition and LCI databases" claim. Cite alongside D27 in §2.2 and lean the surviving novelty on (a) **structured-DB source side (CNF vs EuroFIR)**, (b) **ReCiPe re-scoring vs PEF/EF inheritance**, (c) **open retrieve-rank with confidence vs closed descriptor-set matching**, and (d) **composite-food / meal support**, since Furrer et al. **explicitly exclude composite foods** from their case study (~22 % of EuroFIR, ~2 % of Agribalyse; §2.4 p. 3 + Table 7 p. 6).

**Citation.** Furrer C, Sieh D, Jank A-M, Le Bras G, Herrmann M, Reguant-Closa A, Nemecek T. Interlinking environmental and food composition databases: An approach, potential and limitations. *Journal of Cleaner Production.* 2024;470:143198. doi:10.1016/j.jclepro.2024.143198.

**Venue/Access.** *Journal of Cleaner Production* (Elsevier; Maria Teresa Moreira, handling editor). Received 23 Oct 2023; revised 30 June 2024; accepted 17 July 2024; published online 18 July 2024. **Open access under CC BY 4.0.** Funded by EU Horizon 2020 OptiSignFood (grant 971242, EIC Fast Track to Innovation). Authors at Agroscope LCA group (Zurich, Switzerland), Themakers.ai GmbH (Berlin), and The Makers Food GmbH (Berlin). **Data availability: confidential** (licensed EuroFIR data) — the connection list itself is not released as supplementary.

**Type.** Methods paper — semi-automated procedure to merge food-item (FI) entries between an LCI database (Agribalyse v3.1) and an FCDB (EuroFIR licensed national data for CH, FR, DK, SI, EE, UK; 11,911 FI total) via a manually-curated "connection list" of harmonized LanguaL™ descriptors.

---

#### What Furrer et al. 2024 do (Fig. 1; §2)

Pipeline: **per-DB FI extraction → exclude composite foods → build a manual "connection list" of harmonized LanguaL™ descriptors (5 categories: Name, Specification, Treatment, Processing, Production system) → auto-attach descriptors to FI in each DB using Python (regex + Levenshtein distance + Siamese-BERT-Networks/SBERT for synonym discovery + LanguaL™-code matching when EuroFIR carries them) → automatic interlinkage when matched descriptors align across both DBs (Fig. 4) → manual validation of a 54-entry sample (Table 9).** This is the same *FCDB ↔ LCI-DB linkage* task our §3.5 builds, with three mechanistic differences relevant to our novelty framing (below).

- **Source side.** EuroFIR (multi-country European harmonized FCDB) ↔ Agribalyse v3.1 (French LCI / Ciqual food-code linked at agriculture, food, consumption-mix and transformation life-cycle stages). Single foods only — composite foods (pizza, lasagna, burger) are excluded by name-fragment filter and recipe-formulation complexity (§2.4 p. 3 + p. 6 col. 2).
- **Harmonization spine: LanguaL™.** A controlled thesaurus from EFSA's FoodEx2 lineage that maps every food to a code (e.g., "A01DJ" = apple). EuroFIR carries LanguaL™ codes natively for all national entries (Table 4 p. 5); Agribalyse does *not*, so codes are assigned indirectly via synonym matching (§3.2 p. 6 + Table 6 p. 6). The most-completed code system, **EFSA FoodEx2 (4,524 LanguaL™ codes)**, was *not* used in EuroFIR — only Eurofir's own thesaurus (120 codes, but tagging 13,689 FI in the licensed national data), Eurocode 2, EFG, GS1 GPC, US CFR, USDA SR (Table 6 p. 6). This unevenness is why the team built a 5-category descriptor scheme rather than rely on a single classification.
- **Validation.** 6 name-specification-treatment combinations (beef-minced-cooked, cashew-roasted, cheese-emmental, rice-flour, sunflower-oil, sweet-potato-cooked) × 7 countries → 54 entries manually compared (Table 9 p. 8). **2 of 54 incorrectly matched (≈3.7 % error)**: (a) "Tuna in sunflower oil, canned" matched to sunflower because the FI name contained "sunflower" and "oil"; (b) one strawberry entry pulled in an "additional cooking aid: cream" descriptor.

---

#### Key results (Tables 1, 6, 7, 9)

| Quantity | Value | Source |
|---|---|---|
| EuroFIR licensed FI total (6 countries) | 11,911 | Table 1 + §3 |
| Agribalyse v3.1 FI total | 1,321 | Table 7 |
| EuroFIR single-foods after composite filter | 9,308 (78.1 %) | Table 7 |
| EuroFIR composite-foods removed | 2,603 (21.9 %) | Table 7 |
| Agribalyse single-foods | 1,298 (98.3 %) | Table 7 |
| Agribalyse composite-foods removed | 23 (1.7 %) | Table 7 |
| Manual validation error rate | 2 / 54 ≈ 3.7 % | §3.4 + Table 9 |
| Highest-coverage classification system | Eurofir thesaurus (13,689 FI; only 120 codes) | Table 6 |
| Most-completed system *unused* by EuroFIR | EFSA FoodEx2 (4,524 codes, 0 FI tagged) | Table 6 |

- **Composite-food exclusion is structural, not incidental.** Recipe-level differences between databases for the same composite (e.g., a EuroFIR pizza recipe vs an Agribalyse pizza recipe) made interlinkage unreliable enough that the team excluded all composites from the case study (§2.4 p. 3 + §4.1 p. 7). For meal-level analysis (our entire use case) this is not just an out-of-scope choice — it is a structural limitation of name-fragment + descriptor matching.
- **3.7 % manual error rate at the FI-level for single foods** is the best published benchmark for matcher accuracy on this task. Our §3.5 confidence-scoring and group-level fallback must be evaluated against this number.
- **Asymmetric meta-data availability** (Table 3 p. 5): "country of origin" is fully in Agribalyse but absent in EuroFIR; "yield" and "production system" only in Agribalyse base data; "food specification" and "food processing" only in entry names, requiring extraction. This justifies our open-set matcher (different DBs surface different fields) over a rigid descriptor-spine like Furrer et al.'s.

---

#### The surviving (narrowed) novelty for §2.2 / §3.5 — companion distinctions to D27

D27 (LEAF) pre-empted the *NLP*-priority claim; D27b pre-empts the broader *task*-level claim. Our §3.5 contribution still survives on **four concrete distinctions**, which directly extend the D27 narrowed-novelty framing:

1. **Source side:** Furrer et al. link **EuroFIR (multi-country European FCDB)** to Agribalyse; ecodish365 links **CNF (Canadian Nutrient File)** to Agribalyse with a Canadian regional layer (§3.7). Different geography, different FCDB schema, different downstream consumers.
2. **Composite-food / meal support:** Furrer et al. **explicitly exclude composite foods** (the 22 % of EuroFIR that are mixtures of single foods) because recipe-level differences make descriptor matching unreliable. ecodish365 is a *meal* scorer — composite foods are the unit of analysis, not the exclusion criterion. This is a hard structural distinction our pipeline holds.
3. **LCIA target:** Furrer et al. establish FI ↔ FI links that **inherit Agribalyse's PEF/EF aggregate score directly** (the inherited score is climate-dominated and France-baked). ecodish365 re-scores inventories under **ReCiPe 2016 v1.1 (17 midpoints / 3 endpoints), with the audited endpoint factors, Canadian regional adjustments, and Monte Carlo uncertainty** documented in CODE-1 through CODE-7 — not a single aggregate, and not PEF.
4. **Mechanism:** Furrer et al. match on a **manually-curated closed descriptor set** (one connection-list entry per harmonized term, 5 categories). ecodish365 uses **open retrieval (embedding similarity) + LLM ranking with a 0–1 confidence score and group-default fallback** — no pre-curated descriptor list, and the matcher is open-set by design. The author's own §4.6 ("Techniques for database interlinkage", p. 9 col. 2) explicitly flags AI/NLP as the next-step methodology the field needs to develop.

Recommended rewrite of the §2.2 novelty sentence (refining the rewrite already staged in D27):

> "Prior work links food *names* to Agribalyse's aggregate PEF/Eco-Score via sentence-embedding classification (Krahmer, 2024) and links EuroFIR ↔ Agribalyse food items via manually-curated LanguaL™ descriptor matching with composite foods excluded (Furrer et al., 2024); to our knowledge no published system uses an LLM-assisted open retrieval-and-ranking matcher with confidence-scored fallback to link structured Canadian nutrition-database entries — *including composite meals* — to peer-reviewed inventories re-scored under ReCiPe 2016 with regional adjustments and Monte Carlo uncertainty."

---

#### Author-flagged limitations (§4 + §5) — four are directly useful to us

1. **"Agribalyse does not provide LanguaL™ codes for inventories" (§3.2 p. 6 + Table 6).** Without a native classification spine in the LCI database, every approach that relies on closed descriptor matching has to invent one (Furrer et al. via Python synonym discovery; we via open embedding retrieval). This is an independent third-party justification for our retrieval-based design choice.
2. **"Foods such as 'strawberries' from the French EuroFIR database … could be that it was imported from other countries such as Spain or Italy. Similarly, there is also no indication of the type of variety of a FI" (§4.1 p. 7 col. 2 + §4.1 p. 7 col. 1).** This is exactly the geographic-representativeness gap our §3.7 Canadian factor layer addresses; cite as third-party confirmation that even "national" FCDBs do not encode the supply-chain geography needed for accurate LCA.
3. **"Composite foods … connection of composite foods (e.g., pizza) between databases was found to be complex and expected to be unprecise due to limited information (e.g., missing recipe composition)" (§3.2 p. 6).** Cite in our §7 limitations section for the meal-level matcher: we *do* attempt composite-food matching (by ingredient decomposition + per-ingredient matching), but the recipe-composition gap is real and must be flagged.
4. **"A lack of international standards for documentation has also been found for EuroFIR. Improperly documented datasets limit data integration" (§4.3 p. 9 col. 1) + "AI techniques could promote the development of standardization procedures and should be extensively investigated in future studies" (§4.6 p. 10 col. 1).** The authors themselves identify AI/NLP as the next-step methodology. This is the cleanest citation possible for our §1 / §2.2 motivation: an LCA-domain methods paper, peer-reviewed in *JCleanProd*, explicitly calling for the kind of work we are doing.

---

#### Three-sentence relevance note

Furrer et al. 2024 is the closest published task-level prior art to our §3.5 matcher because it establishes the same FCDB ↔ LCI-DB linkage at the food-item level (EuroFIR ↔ Agribalyse), reports a 3.7 % manual-validation error rate on a 54-entry test sample, and explicitly motivates AI/NLP as the next-step methodology — so it must be cited in §2.2 alongside D27 (Krahmer 2024) and §3.5, with the §2.2 novelty sentence narrowed accordingly. The surviving novelty for our system rests on (a) CNF (Canadian) rather than EuroFIR (European) as the source FCDB, (b) **composite-food / meal-level support** where Furrer et al. structurally exclude composite foods (~22 % of EuroFIR) because of recipe-formulation incompatibility, (c) re-scoring under ReCiPe 2016 v1.1 with audited endpoint factors, Canadian regional adjustments, and Monte Carlo uncertainty rather than inheriting Agribalyse's PEF/EF aggregate, and (d) open retrieval-and-ranking with confidence-scored fallback rather than a manually-curated closed descriptor set. The author's own observations — that Agribalyse does not carry LanguaL™ codes natively, that "French" EuroFIR strawberries may have been imported from Spain or Italy, and that composite-food recipe gaps make descriptor matching unreliable — are independent third-party support for the open-retrieval design (§3.5), the Canadian regional layer (§3.7), and the meal-level composite-handling caveats (§7.3), respectively.

---

*Group D status: D22–D27, D27b complete. **No further Group D papers outstanding.** FoodSEM (Gjorgjevikj et al., 2025, Discovery Science) remains a FoodyLLM sibling (food→ontology NEL, no LCA bridge) and, if wanted, belongs as a supporting cite near D24 rather than as a food↔LCA paper.*

## Group E. Sustainability assessment frameworks

### E28. Rockström, Thilsted, Willett et al. (2025) — The EAT–Lancet Commission on healthy, sustainable, and just food systems (EAT–Lancet 2.0) [★★]

**Citation.** Rockström J, Thilsted SH, Willett WC, Gordon LJ, Herrero M, Hicks CC, Mason-D'Croz D, Rao N, Springmann M, Wright EC, et al. The EAT–Lancet Commission on healthy, sustainable, and just food systems. Lancet. 2025;406(10510):1625–700.

**DOI.** 10.1016/S0140-6736(25)01201-2

**Type.** Lancet Commission — a consensus expert report combining an evidence review (diet–health, planetary boundaries), a novel multimodel scenario ensemble, and a normative justice framework. Direct successor to Willett et al. 2019 (wishlist E29). Of the three wishlist "framework" papers, this is the one that updates both the reference diet and the environmental targets, so it anchors our framing in §1 and §2.1.

---

#### Page-cited results and formulas

**The Planetary Health Diet (PHD) reference values — Table 1, p. 1632.** A flexitarian reference pattern at a population-level intake of ~2400 kcal/day (revised down from 2500 kcal/day in the 2019 Commission; p. 1636). The "name arose from the evidence that adoption would reduce the environmental impacts and nutritional deficiencies of most current diets," but the PHD itself "is based entirely on the direct effects of different diets on human health, not on environmental criteria" (Glossary, p. 1628) — an important framing distinction for us, since our pipeline scores health and environment as *separate* axes rather than collapsing them.

**Health-burden estimates (Panel 1, p. 1629).** Two methods, both pairing relative risks with country-specific diet and mortality data:
- Comparative risk assessment (CRA): adoption of the PHD would prevent ~10 million deaths/yr among adults (17% of total mortality). ~50% of the reduction is composition-related (more whole grains, fruits, vegetables, legumes, nuts; less red and processed meat); ~50% from reduced under/overweight.
- PHD-index pattern method (cohort of >200,000 adults, >30 yr follow-up): achieving a PHD score of 120 (140 = perfect) would avert ~15 million deaths/yr (27% of total deaths); a score of 100 would avert ~7 million/yr (13%).
- Highest-decile PHD adherence = 28% lower overall mortality vs lowest decile (n=206,404; >54,000 deaths; p. 1636).

**Macronutrient profile of the PHD (p. 1637):** ~14% of energy from protein, ~53% from carbohydrate, ~35% from total fat. Added/free sugar capped at 5% of energy; sodium ≤2000 mg/day (5 g salt).

**Food system boundaries — Table 2, p. 1640 (the headline new contribution).** For the first time the Commission quantifies the food system's share of all nine planetary boundaries and proposes science-based food-system targets. Food is "the single largest cause of planetary boundary transgressions, driving the transgression of five of the six breached boundaries" (Executive summary). Food systems = ~30% of GHG emissions (16–17.7 Gt CO₂e/yr; p. 1641).

**Inequality / responsibility (Key messages, p. 1626; Section 3, p. 1661).** The diets of the richest 30% of the global population drive >70% of food-system environmental pressures. Only 1% of the global population lives in a country within the "safe and just space"; 6.9 billion people live in countries that (if their diet were adopted globally) would transgress planetary boundaries, while 3.7 billion fall below social foundations.

**Externalities / economics (p. 1629; Section 6).** The global food system generates ~US$10 trillion/yr in value but ~US$15 trillion/yr in negative externalities (health sector largest). Transformation cost estimated at $200–500 billion/yr; benefits ~$5 trillion/yr. Agricultural subsidies ~$851 billion (2020–22, OECD reporters); ≥1/3 have no public benefit; in the EU 82% favour animal-based agriculture. Fossil-energy subsidies ~$7 trillion (2022).

**Affordability metric (Section 3, p. 1655).** Adopts the FAO Cost of a Healthy Diet (COHD) threshold: a healthy diet is "affordable" when it costs <52% of average household income. In 2022, 2.8 billion people could not afford a healthy diet. Across scenarios the share of income spent on food falls toward 4–5% by 2050.

**Modelling architecture (Section 4, pp. 1661–1670).** A multimodel ensemble of 10 global economic models (AIM, CAPRI, ENVISAGE, FARM, GCAM, GLOBIOM, IMPACT, IMAGE, MAGNET, MAgPIE) plus the static DIA-GIO (Global Input–Output module of the Dietary Impact Assessment model — the updated 2019-Commission input–output model), with FABLE and CiFoS for deep dives. Three core scenarios: BAU (SSP2, RCP 7.0, ~2°C by 2050), EAT–Lancet (PHD adoption + 7–10% productivity gain + halved food loss and waste), and EAT–Lancet Mitigation (ELM, adds ambitious emissions pricing/land-use policy). Results reported as ensemble medians with min–max ranges.

---

#### Tables to reproduce or reference in the manuscript

**Table 1 (p. 1632) — PHD reference diet.** The reference pattern our diet-shift counterfactuals (S5 / §5.2) should benchmark against. Intake in g/day (range), kcal/day at 2400 kcal/day:

| Food group | g/day (range) | kcal/day |
|---|---|---|
| Whole grains | 210 (20–50% of energy) | 735 |
| Tubers and starchy roots | 50 (0–100) | 50 |
| Vegetables | 300 (200–600) | 95 |
| Fruits | 200 (100–300) | 145 |
| Tree nuts and peanuts | 50 (0–75) | 275 |
| Legumes | 75 (0–150) | 275 |
| Milk or equivalents | 250 (0–500) | 145 |
| Chicken and other poultry | 30 (0–60) | 60 |
| Fish and shellfish | 30 (0–100) | 25 |
| Eggs | 15 (0–25) | 20 |
| Beef, pork, or lamb | 15 (0–30) | 45 |
| Unsaturated plant oils | 40 (20–80) | 355 |
| Palm and coconut oil | 6 (0–8) | 55 |
| Lard, tallow, butter | 5 (0–10) | ·· |
| Sugar (added or free) | 30 (0–30) | 115 |
| Sodium | <2 g | ·· |

**Table 2 (p. 1640) — food system boundaries (selected control variables).** Use in §1/§2.1 to situate our per-meal indicators within global targets:

| Earth-system process (control variable) | Current food-system contribution | Proposed food-system boundary |
|---|---|---|
| Climate (atmospheric CO₂) | 16–17.7 Gt CO₂e/yr (30% of anthropogenic emissions) | 5 Gt CO₂e/yr |
| Land system change (agricultural area) | 48 M km² (34% of land surface) | <48 M km² (halt conversion of intact nature) |
| Biosphere integrity (HANPP) | 9.9–11.7 Gt C/yr (72–85% of total HANPP) | 5.5 Gt C/yr |
| Stratospheric ozone (N₂O) | 3.9–4.2 Tg N₂O-N/yr (54–69% of total) | 1.8 Tg N₂O-N |
| Ocean acidification | 25% of CO₂ emissions | Zero CO₂ from land-use change + fossil energy in the food chain |
| Nitrogen surplus | 119 Tg N/yr | <57 Tg N/yr |
| Phosphorus loss to surface water | 7.2 Tg P/yr (75% of total) | 4.6 Tg P/yr |
| Blue water (consumptive) | 1200–1800 km³/yr | 2000 km³/yr |
| Novel entities (pesticides) | 3.3–3.7 Tg PAS/yr (85–90% of use) | 1 Tg PAS/yr (high-risk avoidance); 0.2 Tg PAS/yr (low risk) |

**Table 4 (p. 1655) — social-foundation harms quantified in DALYs.** Directly relevant to our HENI/DALY methodology (cross-link Group C): unsafe water ~42 million DALYs; high temperatures ~14 million DALYs; SSB-heavy/unhealthy diets ~3.6 million DALYs; ~75,725 SSB-linked deaths/yr. These are population-level DALY attributions, not the μDALY/g per-food factors we use, but they demonstrate the same comparative-risk-assessment lineage (GBD) that underpins HENI (C15, C18).

---

#### Author-flagged limitations (useful for §7)

1. **Relative risks drawn primarily from high-income-country cohorts** (Panel 1, p. 1629); LIC/MIC cohort data are scarce — flagged as "an important research gap." Mirrors our own §7.5 cohort-representativeness caveat and the geographic-representativeness gap our §3.7 Canadian layer addresses.
2. **Sodium effects excluded from the mortality estimates** (measurement difficulty), and the estimates exclude environmentally-mediated indirect diet effects (Panel 1) — a clean precedent for explicitly bounding what a health-impact score does and does not capture.
3. **Scenarios model only 2050 endpoints, not transition pathways** (p. 1664); ensemble agreement is *low* on whether nitrogen, phosphorus, and water reductions are sufficient to return within boundaries.
4. **Soil-carbon sequestration estimates taken from global meta-analyses do not account for regional/local saturation limits** (Panel 6) — cite if we discuss uncertainty inheritance.
5. **Agency / corporate-concentration harms left "Not determined"** in Table 4 because well-established metrics do not exist — an honest data-gap admission worth noting if we discuss multi-indicator coverage.
6. **The Commission used ChatGPT to draft its Executive Summary** (Acknowledgments, p. 1686), with author review. A concrete, citable data point for our §2.4 / §6.5 sustainability-of-AI and AI-in-food-science discussion: even a flagship sustainability assessment now embeds LLMs in its workflow.

---

#### Three-sentence relevance note

EAT–Lancet 2.0 is the canonical framing reference for §1 and §2.1 and the authoritative source for both the PHD reference diet (Table 1), which anchors our diet-shift counterfactuals in S5/§5.2, and the food system boundaries (Table 2), against which we can situate per-meal environmental scores at the planetary scale. Its DALY-based health-burden accounting (15 million avoidable deaths/yr; Table 4 harm attributions) shares the GBD comparative-risk lineage that underpins our HENI methodology (Group C), and its externality figures ($10 trillion value vs $15 trillion negative externalities) support the monetization framing in §3.3. Two incidental but quotable facts strengthen our AI-for-sustainability narrative: the Commission's reliance on a 10-model economic ensemble plus DIA-GIO illustrates the modelling-uncertainty problem our Monte Carlo work (S3) engages, and its disclosed use of ChatGPT to draft the Executive Summary is a real-world instance of LLM integration into sustainability assessment for §2.4/§6.5.

---

### E29. Willett, Rockström, Loken et al. (2019) — Food in the Anthropocene (EAT–Lancet 1.0) [★★]

**Citation.** Willett W, Rockström J, Loken B, Springmann M, Lang T, Vermeulen S, Garnett T, Tilman D, DeClerck F, Wood A, Jonell M, Clark M, Gordon LJ, Fanzo J, Hawkes C, Zurayk R, Rivera JA, De Vries W, Sibanda LM, Afshin A, Chaudhary A, Herrero M, Agustina R, Branca F, Lartey A, Fan S, Crona B, Fox E, Bignet V, Troell M, Lindahl T, Singh S, Cornell SE, Reddy KS, Narain S, Nishtar S, Murray CJL. Food in the Anthropocene: the EAT–Lancet Commission on healthy diets from sustainable food systems. Lancet. 2019;393:447–492.

**PDF.** [`papers/PIIS0140673618317884.pdf`](papers/PIIS0140673618317884.pdf)

**DOI.** 10.1016/S0140-6736(18)31788-4 (corrected republications documented on the Lancet splash page through Oct 1, 2020).

**Type.** Earlier EAT–Lancet synthesis: expert consensus framing of a **healthy reference diet at 2500 kcal/day**, global **six-process food-production boundaries** anchored in Steffen planetary-boundaries lineage, and scenario modelling tying diet shifts, halved waste (SDG 12.3), and productivity tiers to boundary transgression (IMPACT-derived global food-system model; appendix pp 19–23; scenario core extends Springmann and colleagues (*Nature* 2018, 562:519–525)). Wishlist entry E29; **superseded for numeric PHD/env targets by Rockström et al. 2025 (E28)** — cite E29 only when deliberately anchoring the **2019** reference pattern (prototype `literature_anchor` in `dietary_pattern_prototypes.json`, manuscript researcher-mode text).

---

#### Page-cited results and formulas

**Energy basis for tables (p. 454).** Scenario food amounts are calibrated to **2500 kcal/day** (explicitly defended as aligning with moderate-to-high physical activity for a 70 kg man / 60 kg woman aged ~30 yr; contrasts with WHO 2100-kcal BMI-22 archetypes the authors reject as unrealistic given unresolved obesity reversal).

**Reference diet composition — Table 1 (p. 451).** Key midpoint intakes vs E28 PHD highlights: split **beef+lamb vs pork** (7 g/day each midpoint, interchangeable), **whole grains 232 g/day** (~811 kcal; range allows grain mix up to ~60 % of energy), **fish 28 g/day** (vs revised PHD midpoint values in E28). Red-meat midpoint combined = 14 g/day (matching E28 lexicon). Added sugar cap **31 g/day** (**< 5 %** energy).

**Environmental scientific targets — Table 2 (p. 453).** Six aggregated processes (narrower framing than E28’s expanded nine-boundary food-system accounting): methane+nitrous-oxide-from-food-production **≤ 5 Gt CO₂e/yr (4·7–5·4)**; cropland cap **≤ 13 M km² (11–15)**; freshwater consumptive allocation for food production **≈ 2500 km³/yr (1000–4000)**; nitrogen fertiliser/application boundary **≈ 90 Tg N/yr (65–90; upper extension 90–130 with redistribution)**; phosphorus **≈ 8 Tg P/yr (6–12; upper 8–16 if recycling assumptions met)**; biodiversity loss **≤ 10 E/MSY (1–80)**.

**Avoided premature mortality from global adoption of reference diet — Table 3 (p. 461).** Concordant triangulation:
- Comparative risk modelling (CRA with agriculture–consumption statistics — Table 3 * and ref 131): ~**19 %** premature mortality reduction, ~**11 100 000** deaths/yr avoided (158 regions; fruits/vegetables/nuts/legumes-dominated swings).
- GBD-aligned optimal diet (Commission Table 3 † and ref 132): **22·4 %** adult deaths preventable, ~**10 886 000** deaths/yr; sodium + fruits/vegetables/whole grains/nuts dominate.
- AHEI-2010 empirical scoring (Table 3 ‡; refs 133–134) across 190 countries: **23·6 %** adult deaths preventable, ~**11 600 000** deaths/yr.

**Environmental footprint hierarchy caveat (§3 intro, pp. 470–471).** Authors stress **indicator-unit sensitivity** (“per kcal misleading for vegetables”; prefer **per serving** for heterogeneous energy-density categories) — a methodological caution echoed by our §3 dual-axis indicators (nutrition vs environmental).

**Climate accounting split (§2, pp. 462–463).** Food-related boundary isolates unavoidable **biotic CH₄/N₂O** under Paris-compatible budgets (~**¼** of contemporary all-source GHG share discussed in-text) while assigning **fossil combustion** mitigation to wider energy-sector decarbonisation narratives.

---

#### Tables to reproduce or reference

**Contrasting use vs E28:** For submission-facing diet-shift benchmarking and boundary tables, cite **E28**; retain **Table 1 (2019, p. 451)** verbatim only when reproducibility/traceability to Willett-et-al.-anchored artefacts is required.

| Item | Primary page |
|---|---|
| Healthy reference diet (group g/day ranges + kcal) | Table 1, p. 451 |
| Six production boundaries + uncertainty footnotes | Table 2, p. 453 |
| Three-method avoided-mortality reconciliation | Table 3, p. 461 |

---

#### Author-flagged limitations (Scope + Results — useful for §7)

1. **Deliberate narrowing to consumption + production endpoints** (Food system glossary, pp. 450–452); distribution, labour, welfare, antimicrobial resistance flagged as under-addressed domains requiring parallel agendas.
2. **No granular organic-vs-conventional production prescription** — explicitly avoided because “debates … can be overly prescriptive” (§2 prelude, ~p. 453).
3. **SSP / population pathway ensembles not explored in depth** (main text anchors moderate-growth narrative; p. 453); SRH access noted as requisite for feasibility.
4. **High uncertainty on boundary numeric values** acknowledged throughout (risk-precaution framing; Table 2 footnotes tie nitrogen/phosphorus upper ranges to redistribution + phosphorus-recycling optimism — pp. 451–453).
5. **Geographically averaged water boundary masks acute basin-level transgression** (§2 freshwater narrative, pp. 464–465; appendix p 17)—mirrors rationale for §3.7 regional specificity.
6. **Biodiversity modelling paradox**: reference-diet uplift in low-calorie-intake regions can increase land-use extinction pressure if domestic sourcing naïvely expands nuts/pulses footprints (§3, pp. 473–474; optimisation scenarios in appendix pp 25–26).
7. **Evidence geography skew**: European/North American dominance for several meat-health associations with Asian pooled exceptions discussed (§1, pp. 456–457).

---

#### Three-sentence relevance note

E29 is the foundational EAT–Lancet planetary-health citation for our **researcher/policy-mode EAT–Lancet prototype** and any historical comparison to PHD-era science, pairing a flexitarian **reference diet (Table 1 @ 2500 kcal/day)** with the original **six global production boundaries** and triangulated comparative-risk mortality benefits **≈11 million deaths/year averted depending on modelling branch (Table 3)**—all articulated before the 2025 Commission’s calorie revision, boundary expansion to nine Earth-system domains, justice layer, and multi-model ensemble. Methodologically it links cleanly to Group C via **explicit GBD-based optimal-diet attribution (Table 3 row)** and reinforces our dual-indicator design by warning that universal functional units distort rankings across energy-dilute produce vs animal-source foods (§3). Practically **E28 should replace E29 wherever normative citation targets reflect current Lancet consensus**, keeping E29 for traceability when JSON prototypes or reproducibility artefacts remain pinned to 2019 group gram midpoints.

---

### E32. Heller, Keoleian, Willett (2013) — Diet-level LCA + nutritional quality framework (EST critical review) [★★]

**Citation.** Heller MC, Keoleian GA, Willett WC. Toward a life cycle-based, diet-level framework for food environmental impact and nutritional quality assessment: a critical review. Environ Sci Technol. 2013;47(22):12632–12647.

**PDF.** [`papers/toward-a-life-cycle-based-diet-level-framework-for-food-environmental-impact-and-nutritional-quality-assessment-a.pdf`](papers/toward-a-life-cycle-based-diet-level-framework-for-food-environmental-impact-and-nutritional-quality-assessment-a.pdf)

**DOI.** 10.1021/es4025113 (received June 2013; published online 23 Oct 2013). **Competing interests.** None declared (p. 12644). Acknowledges Olivier Jolliet and Victor Fulgoni III for framework development input.

**Type.** *Environmental Science & Technology* **Critical Review**: synoptically maps how LCA extends from product-level food studies to **consumption-oriented (meal / diet-level)** assessment, inventories the **LCA-based diet and meal literature** (abstract: **32** studies; §3 notes **48** English-language diet-consumption-impact studies of which the LCA subset drives Table 2), and argues explicitly for **nutrition-grounded functional units** and **nutrition–environment co-assessment** rather than mass-only aggregation — the conceptual ancestor of our separate health (HENI/HEFI lane) and environmental (ReCiPe lane) indicators at the meal boundary.

---

#### Page-cited results and constructs

**Consumption share / motivation (§1, pp. 12632–12633).** Cites developed-country estimates that **food consumption contributes ~15–28 %** of national greenhouse-gas emissions (ref. 4 in paper); highlights water withdrawals, N/P cycle disruption, and land-driven biodiversity loss as systemic food-system pressures.

**Functional-unit–scope map — Figure 2 (pp. 12633–12634).** Stratifies **production-oriented** LCAs (hotspots, comparative technology) from **consumption-oriented** work to the right of the conceptual divide; anchors the paper’s thesis that **mass/volume FUs** suffice for intra-system improvement but break down for **cross-food-type** comparisons where **nutritional roles** differ.

**Demonstrator food table — Table 1 (pp. 12634–12635).** For selected minimally processed items, reports **GHGE** on **four FU bases** (per kg as sold, per serving, per 100 g protein, per 1000 kcal food energy) alongside a **weighted nutrient density score (WNDS)** (nutrients per Arsenault/Fulgoni-style profile: protein, fiber, calcium, unsaturated fat, vitamin C, saturated fat, added sugars, sodium — footnote Table 1). Illustrates **rank reversals** across FUs and flags **hothouse veg** and **air-freighted** perishables as outliers to simple plant-vs-animal generalizations.

**Diet / meal LCA literature register — Table 2 (pp. 12635–12639, extends).** Tabulates geographic scope, **process vs hybrid / EIO** LCAs, indicators (dominated by GHG / CED in the reviewed era), aggregation level (**meal vs diet**), stated **equalizing basis** (often none beyond raw intake mass), and study aim. Notes **81 %** Table-2 studies **process-LCA** aggregate per-kg factors into intake lists (§3.1, p. 12637).

**Nutrition integration taxonomy — §5 (pp. 12639–12641).** Two families: (i) **iso-nutrient meal/diet construction** (energy + protein matching, linear programming with macro/micro constraints + “acceptability constraints” after Macdiarmid et al.), and (ii) **nutrient profiling / diet quality indices** as **FU** or **parallel axis** (examples: NDS vs NRF9.3 altering meal contrasts in Kagi et al.; RDV-capping argument in Kernebeek et al.; MAR/MER/ED stratification vs GHGE in Vieux et al.).

**Integrated mental model — Figure 3 (p. 12641).** **Diet definition → life-cycle supply chains → LCA + nutritional quality assessment**, with optional future harmonization of human-health effect metrics with environmental health endpoints.

**Global Burden of Disease cross-link (§4/§5 narrative, pp. 12638–12640).** Describes **GBD 2010** amalgamation of **14 dietary risk factors** (fruits, vegetables, whole grains, nuts/seeds, milk, fish/fiber/calcium/PUFA lows; red meat, processed meat, SSB, trans fat, sodium highs) as a possible **health baseline** to pair with dietary LCA — aligns with our Group C / HENI provenance even though this review predates Stylianou/NaturFood operationalization.

---

#### Author-flagged limitations and research needs (Discussion §6 — useful for §7 / methods)

1. **Environmental indicator narrowness:** most diet-LCAs of the period focus on **GHGE**; authors call for broadening LCIA + **regionalized food/agriculture inventories** (§6.2, pp. 12641–12642).
2. **Land-use change (direct/indirect):** can be **16–30 %** of diet GHG in Meier & Christen German scenarios; IPCC guidance exists but **methodological disagreement** persists (§6.2.1, p. 12642).
3. **Food loss and waste:** ~**¼** of produced food lost globally; US-context **10 % retail / 19 % consumer** loss cited; stresses **consistency** between FBS vs survey “consumption” data (§6.2.2 opening, p. 12642).
4. **Health–environment non-alignment:** Discussion flags **Vieux et al.** — **higher author-defined nutritional-quality class** associated with **slightly higher** GHGE at population scale in French self-selected diets (low-GHGE starches/sugars confound); “sustainable = healthy” not automatic (§6, pp. 12640–12641).
5. **Trans-disciplinarity gap:** calls for ongoing **LCA ↔ nutrition science** collaboration on **nutrient indices as FU**; positions **LCSA** as umbrella for social/economic deepening (§6.2, p. 12641).
6. **System boundary completeness:** notes **agricultural production** often dominates but **household refrigeration + wastage** materially shape full-chain results (§6 opening, p. 12640).

---

#### Three-sentence relevance note

Heller et al. 2013 gives our Call-1 narrative a **peer-reviewed, Willett-co-authored** precedent for treating **meals/diets as the natural unit** where **environmental inventories** (today: ReCiPe + Agribalyse/CNF linkage) meet **nutritional or health metrics** (today: HEFI + HENI rather than a single hybrid FU). Its **Figure 2 / Table 1** arm us for §2–§3 exposition on **functional-unit sensitivity and rank reversals**; **Table 2** historicizes the literature our stack extends; **Figure 3** is a schematic cousin of our dual-score architecture. We should cite it as **framework motivation**, not as justification for any specific numeric factor—while flagging its pre-**ReCiPe 2016**, pre-**GBD2017/2019 HENI**, and **GHG-centric** review scope as inherited limitations our implementation explicitly updates.

---

*Group E — extracted for this manuscript: **E28**, **E29**, **E32** (wishlist 28–29, 32). **Not extracted (de-scoped)** per author choice: wishlist **E30** (IPCC AR6 WGIII ch. 5), **E31** (IRP 2019 Global Resources Outlook).*

### F33. Heijungs (2020) — On the number of Monte Carlo runs in comparative probabilistic LCA [★★]

**Citation.** Heijungs R. On the number of Monte Carlo runs in comparative probabilistic life cycle assessment. Int J Life Cycle Assess. 2020;25(2):394–402.

**DOI.** 10.1007/s11367-019-01698-4 (Received 14 May 2019; Accepted 8 October 2019; Published online 22 October 2019.)

**PDF.** [`papers/On_the_number_of_Monte_Carlo_runs_in_comparative_p.pdf`](papers/On_the_number_of_Monte_Carlo_runs_in_comparative_p.pdf)

**Open access.** Yes — Creative Commons Attribution 4.0 International (CC BY 4.0).

**Type.** Methods article. Combines probability theory review (§2) with two numerical simulation experiments (§3) to question the standard practice of running 1,000–100,000 Monte Carlo iterations in LCA, arguing the number of runs should not exceed the sample sizes used to estimate the input distributions.

---

#### Core argument — precision vs accuracy (§§2.7–2.8, pp. 397–398)

Heijungs draws a fundamental distinction between two properties of a Monte Carlo estimate:

- **Precision** — the width of the confidence interval around the Monte Carlo estimate; decreases with √N_run (more runs → narrower CI).
- **Accuracy** — how close the estimate is to the true population value; governed entirely by the accuracy of the *input parameter estimates* (μ̂_X, σ̂_X), NOT by N_run.

When input parameters are estimated from a small empirical sample of size *n*, the estimated mean x̄ has a standard error σ_X/√n (central limit theorem). Running N_run >> n in the subsequent Monte Carlo simulation does not recover this imprecision; instead it *converts* a visibly imprecise estimate (large SE on x̄) into an *invisibly inaccurate* one (near-zero SE on ȳ, but ȳ converges to the wrong value x̄ rather than the true μ_X). Heijungs' compact summary (p. 400): **"Garbage in, garbage out, but the type of garbage has changed: from imprecise to inaccurate. That is a problem, because imprecision is visible through a large standard error of the mean … while inaccuracy is not visible."**

---

#### Page-cited numerical results

**Example 1 — stand-alone system (p. 399, Fig. 1).**
Parent distribution X ~ N(10, 1); sample size n = 16; Monte Carlo N_run = 100,000.

| Approach | Estimate | 95 % CI | Contains true μ = 10? |
|---|---|---|---|
| Inferential (from n = 16 sample) | x̄ = 10.31 ± 0.25 | [9.819, 10.799] | **Yes** |
| Monte Carlo (N_run = 100,000) | ȳ = 10.31 ± 0.003 | [10.305, 10.318] | **No** |

The Monte Carlo approach is ~80× more *precise* but the confidence interval has drifted entirely away from the true value because it merely converges to the inaccurate input estimate x̄ = 10.31.

**Example 2 — comparative LCA (p. 400, Fig. 2).**
Two systems A and B with identical true means μ_XA = μ_XB = 10; n_A = n_B = 16; N_run = 100,000.

| Test | p-value | Conclusion |
|---|---|---|
| Two-sample t-test on raw input data | p = 0.67 | Correctly fails to reject equality |
| Monte Carlo two-sample test (N_run = 100,000) | p ≈ 10⁻¹⁶ | Incorrectly rejects equality with overwhelming significance |

The Monte Carlo analysis manufactures an essentially certain conclusion that product A is better than B, when the underlying input data show no statistically distinguishable difference. "Seemingly precise estimates of the impact of products A and B can lead to the conclusion that A is better than B, while the real situation is that B is better than A." (p. 400)

---

#### Key recommendation (pp. 400–401)

> "Apart from the obvious recommendation to use larger samples for estimating input distributions, we suggest to restrict the number of Monte Carlo runs to a number **not greater than the sample sizes used for the input parameters**."

If input X₁ is estimated from n₁ = 16 data points and X₂ from n₂ = 9, the recommended N_run ≤ min(9, 16) = **9**. This makes the output CI visibly wide — but accurately reflects real uncertainty — rather than deceivingly narrow.

The practical fix is also noted: the solution of capping N_run simultaneously resolves the problem of "overly significant results" documented by Heijungs et al. (2016, *Entropy* 18:361).

---

#### Pedigree approach incompatibility (pp. 400–401)

The **ecoinvent pedigree approach** (Frischknecht et al., 2004; Weidema et al., 2013) assigns default standard deviations from qualitative data-quality indicators (representativeness, age, etc.) rather than from empirical sample estimation. For such inputs, sample size *n* is undefined — meaning there is no principled cap on N_run, and yet "the parameters of the input distribution are not at all accurate." Heijungs' conclusion (p. 401):

> **"Pedigree-based probability distributions are incompatible with large-scale Monte Carlo simulations."**

He explicitly flags this as an unresolved research gap: "This suggests a major area of research in dealing with uncertainty in LCA."

---

#### Author-flagged limitations and research needs (Discussion, pp. 400–401)

1. **Generalisation to multi-input functions:** The argument is demonstrated for Y = f(X) = X but held to carry over to Y = f(X₁, X₂, …) of arbitrary complexity (p. 400); the paper does not provide a formal proof for non-linear functions beyond a narrative assertion.
2. **No practical algorithm for multi-input cases:** When inputs have different sample sizes (n_X1 ≠ n_X2), the "weakest link" rule (N_run ≤ min n_Xi) is offered as an heuristic but acknowledged as requiring further development (p. 401).
3. **Non-normal / non-standard distributions not treated fully:** The main analysis uses normal distributions with known σ; lognormal and other distributions common in LCA (Frischknecht et al., 2004) follow the same qualitative logic but add computational complexity (p. 400).
4. **No guidance on the pedigree problem:** The incompatibility of pedigree-based SDs with MC is identified but no solution is proposed — it is left as an open research area (p. 401).

---

#### Implications for our manuscript (§§2.3, 3.8, 7.4)

Our pipeline uses **N_run = 10,000** (Highlight A4; Abstract). This number is defensible specifically because our σ_g values come from **Poore & Nemecek's (2018) deposited archive**, which is empirically derived from meta-analysed LCI surveys across tens of thousands of farms and processing operations globally — **not** from pedigree scoring. Poore & Nemecek report effective sample sizes per food group ranging from ~dozens (minor processed categories) to several thousand (major commodity groups: dairy ~2,800; beef/lamb ~742; wheat ~2,813). For well-sampled groups, N_run = 10,000 is comfortably within Heijungs' bound; for the sparsest groups (n ≈ 30–80 for some minor categories), N_run = 10,000 technically exceeds the recommended cap.

This creates a minor limitation to flag in §7: for food groups where Poore & Nemecek's survey has fewer than ~1,000 data points, our 10,000-run MC overstates precision and the resulting per-food-group CIs should be treated as indicative rather than definitive. A conservative mitigation is to additionally report sensitivity at N_run = min(n_group, 500) for the five most-sampled and five sparsest groups as a robustness check (SI table). We should cite Heijungs (2020) at both §2.3 ("Monte Carlo propagation remains the dominant approach… with the caveat that N_run should not substantially exceed the sample size of input parameter estimates") and §7 (limitation discussion).

The pedigree incompatibility finding also underpins our choice **not** to propagate ecoinvent background uncertainty via MC (we use fixed background characterisation factors and only vary the σ_g foreground distributions from Poore & Nemecek) — a design choice now citable directly to this paper.

---

#### Three-sentence relevance note

Heijungs (2020) provides the foundational theoretical argument that running 10,000+ Monte Carlo iterations in LCA is only statistically legitimate when the input distributions are themselves estimated from samples of comparable size — otherwise the procedure delivers results that are **precise but inaccurate**, a failure mode invisible to the analyst because the reported CI shrinks to near-zero while converging to the wrong value. For our pipeline, this paper is the citation that justifies two key design choices simultaneously: (i) grounding σ_g in Poore & Nemecek's empirical meta-survey (n >> pedigree) rather than ecoinvent pedigree scoring, and (ii) not propagating background ecoinvent uncertainty through MC at all. We must engage with it in §7 by acknowledging that for the handful of Poore & Nemecek food groups with n < 1,000, our N_run = 10,000 modestly overclaims precision, and propose the N_run = min(n_group, 500) robustness check as the mitigation.

---

### F34. Kim, Mutel & Hellweg (2025) — Global sensitivity analysis of correlated uncertainties in LCA [★★]

**Citation.** Kim A, Mutel C, Hellweg S. Global sensitivity analysis of correlated uncertainties in life cycle assessment. J Ind Ecol. 2025;29(4):1090–1104.

**DOI.** 10.1111/jiec.70036

**PDF.** [`papers/J of Industrial Ecology - 2025 - Kim - Global sensitivity analysis of correlated uncertainties in life cycle assessment.pdf`](papers/J%20of%20Industrial%20Ecology%20-%202025%20-%20Kim%20-%20Global%20sensitivity%20analysis%20of%20correlated%20uncertainties%20in%20life%20cycle%20assessment.pdf)

**Open access.** Yes — Creative Commons Attribution License (CC BY), © 2025 The Author(s).

**Affiliations.** Aleksandra Kim & Christopher Mutel: Paul Scherrer Institute (Laboratory for Energy Systems Analysis), Villigen, Switzerland. Kim & Stefanie Hellweg: ETH Zurich (Dept. of Civil, Environmental and Geomatic Engineering). **Open-source code:** AKULA repository, MIT license (doi:10.5281/zenodo.12599545); runs on Brightway 2.5.

**Type.** Methods article. Extends two prior GSA protocols (Cucurachi et al., 2021; Kim et al., 2022) — which assumed independent inputs — to handle **correlated and causally-linked parameters** in high-dimensional LCA models. Introduces four sampling modules and an updated multi-step GSA pipeline; demonstrates on climate-change footprint of average Swiss household consumption (ecoinvent v3.8 cutoff, ~415,000 uncertain exchanges).

---

#### The core problem: why independent sampling misleads (§1, pp. 1090–1091)

Standard MC simulations in LCA draw each uncertain input independently, even when physical or economic constraints force variables to co-move. The authors illustrate with a food example directly relevant to our pipeline:

**Basmati rice market-share example (Fig. 1, p. 1090–1091).** A global market is modelled as 70 % India (3.4 kg CO₂-eq/kg) + 30 % Rest-of-World (3.0 kg CO₂-eq/kg). If shares are sampled independently as lognormals (S_IN ~ LN(log 0.7, 0.1); S_RoW ~ LN(log 0.3, 0.1)), the two shares need not sum to 1 at each simulation draw. The resulting CF distribution is **significantly wider** than when the constraint S_IN = 1 − S_RoW is enforced. Consequence: **independent sampling overestimates uncertainty**, which in a comparative LCA could mask a real difference between rice types that correlated sampling would correctly identify as significant — the same class of false-negative/false-positive error documented by Heijungs (2020, §F33 above) but now from a different source (correlation neglect rather than N_run inflation).

---

#### Four correlated/dependent sampling modules (§2.2, pp. 1092–1096, Fig. 2)

| Module | Mechanism | Scale in ecoinvent v3.8 |
|---|---|---|
| **(a) Parameterized inventories** | Named variable → formula → technosphere/biosphere flow; heavier car → higher brake wear | 565 activities; 857 parameters; 7,509 biosphere + 640 technosphere exchanges |
| **(b) Carbon balancing in combustion** | Fuel input and CO₂ output linked by stoichiometry; "market for diesel/petrol" → "carbon dioxide, fossil" treated as dependent | 812 activities; 407 biosphere + 1,403 technosphere exchanges |
| **(c) ENTSO-E electricity time-series** | Annual ecoinvent averages replaced by real 2019–2021 hourly generation data for 32 European countries; correlations between generation types preserved | 821 technosphere exchanges in 87 electricity markets |
| **(d) Dirichlet for implicit markets** | Shares that must sum to a fixed total (e.g. natural gas offshore+onshore) modelled with multivariate Dirichlet instead of independent lognormals | 61 implicit markets; 517 technosphere exchanges |

For module (d): ecoinvent's *formal* markets already have uncertainty removed (the algorithm detects them). But **implicit markets** — where product names do not exactly match — retain independent lognormal uncertainty, causing their sums to deviate from the physical total at each draw. The Dirichlet distribution enforces the "fixed total" constraint while preserving marginal uncertainty widths (§2.2.4 + Section 3 of SI; validated on Danish electricity data, Fig. 6, p. 1098).

---

#### Multi-step GSA protocol (§2.4, pp. 1096–1097, Fig. 5)

The protocol progressively filters ~415,000 uncertain inputs down to a rankable ~2,000, **without losing influential ones** (each step validated by scatter-plot comparison of Y_all vs Y_subset from 2,000 MC runs):

| Step | Method | Inputs remaining after step | Computation |
|---|---|---|---|
| **1. Remove non-influential** | Supply chain traversal (technosphere); matrix-structure zero-contribution pruning (biosphere/CF); formula analysis (parameterized) | 20–30 % of original (cutoff 1×10⁻⁷) | Minutes |
| **2. Remove lowly influential** | Local one-at-a-time sensitivity (±10× perturbation); discard low-variance contributors | 10,000–30,000 (k_lsa) | Hours |
| **3. Screen high-dimensional** | XGBoost on N_xgb = k_lsa to 4k_lsa MC samples; feature importance as proxy sensitivity index | 1,000–3,000 (k_xgb) | Hours |
| **4. Rank** | SHAP / TreeSHAP on the trained XGBoost model; Shapley effects as final sensitivity indices | Top 200 reported | Minutes |

Total runtime: < 24 h on a personal laptop (11th Gen Intel i5, 32 GB RAM) for the full Swiss consumption model. **R² of XGBoost model in Step 3:** 0.79 (independent sampling) / 0.84 (correlated sampling) — adequate for feature-importance ranking even without hyperparameter tuning (§3.3, p. 1100).

SHAP is used because Shapley effects extend naturally to **correlated inputs** (Iooss & Prieur, 2019; Janzing et al., 2020), unlike classical Sobol first/total order indices which assume independent inputs (§2.4, p. 1097).

---

#### Key GSA results (§3.3, pp. 1100–1101, Fig. 8)

For Swiss household carbon footprint (deterministic score: 1,870 kg CO₂-eq/month):

- Independent vs correlated sampling share **81 technosphere + 17 biosphere** inputs in the top 200.
- Major uncertainty drivers under both: electricity transformation/heat production; passenger car operation + petroleum production; electronics manufacturing; **agricultural processes including milk, cheese and meat** (p. 1101) — the food-LCA-adjacent result.
- **Critical divergence:** With independent sampling, GSA flags 10 CO₂ biosphere flows from "transport, passenger car" and several characterisation factors and "carbon dioxide from soil/biomass stock" as top-200. With correlated sampling, **these inputs drop entirely out of the top 2,000** — they were false positives generated by uncorrelated pedigree-based ecoinvent uncertainty, not by true physical drivers (§3.3, pp. 1100–1101).
- With correlated sampling, the true driver is correctly identified as **combustion of petrol/diesel** (20 technosphere inputs from the carbon-balancing module) + **electricity mix uncertainty** (60 technosphere inputs from the ENTSO-E module).

Key quote (p. 1101): *"When correlations are properly accounted for, the overall uncertainty in LCIA scores is more heavily influenced by combustion and electricity inputs, whose contributions overshadow errors in the ecoinvent database. In practical terms, this suggests that addressing uncertainties in these primary sources — combustion and electricity — should take precedence over those in ecoinvent."*

---

#### Author-flagged limitations (§4 Discussion, pp. 1101–1102)

1. **Pedigree–parameterization mismatch (p. 1101, point i).** When the parameterized module was applied, the distribution width obtained by propagating independent named-variable uncertainty "was arbitrarily higher, lower, or well aligned with the predefined [pedigree-based] distribution. We could not track any systematic relation between the two." Likely caused by pedigree scoring rather than empirical fitting — reinforces the Heijungs (2020) critique of pedigree+MC.
2. **ENTSO-E disaggregation ambiguity (p. 1101, point iii).** ENTSO-E categories don't map 1:1 to ecoinvent; disaggregation choices introduce their own uncertainty. ENTSO-E data quality gaps (Hirth et al., 2018) also limit reliability.
3. **Dirichlet fails for multimodal marginals (p. 1101, point v).** High-voltage electricity markets with many suppliers exhibit multimodal distributions (intermittent wind effects); Dirichlet cannot capture these. Further disaggregation by season/time-of-day needed.
4. **Implicit markets Dirichlet — large-n case (p. 1101, point v).** For large numbers of variables the single scaling factor λ cannot fit all marginals simultaneously; needs further development.
5. **Case study scope (p. 1099, §2.6).** Swiss household consumption only; climate change LCIA only. Other products, regions and impact categories may yield different module importance rankings.
6. **No coverage of characterization factor correlations across impact categories.** The framework addresses technosphere/biosphere and parameterized flows; cross-category CF correlations (relevant for single-score aggregation under ReCiPe) remain outside the protocol.

---

#### Implications for our manuscript (§§2.3, 3.8, 4.3, 7.4)

Our pipeline implements **Sobol-index sensitivity analysis** (Highlight A4; §3.8) with independent sampling — the same baseline that Kim et al. extend. Three specific implications:

1. **Sobol indices assume independence.** Our §4.3 Sobol analysis over ReCiPe characterisation factors assumes each factor varies independently. This is defensible for a first-pass analysis (most CF categories are assigned to distinct elementary flows with different uncertainty sources), but the basmati rice example (Fig. 1) shows that market-share correlations within a food group inflate estimated uncertainty if not corrected. Our Poore & Nemecek σ_g distributions are group-level aggregates — they implicitly average over the correlated sub-regional variation, which may partially but not fully mitigate this. We should flag independent-sampling as a simplification in §7 and cite Kim et al. (2025) as the reference for the correlated extension.

2. **SHAP vs Sobol for food LCA.** Kim et al.'s finding that SHAP with XGBoost correctly ranks correlated inputs while standard sensitivity methods produce false-positives is directly relevant to the credibility of our factor-importance ranking. For the initial publication, Sobol indices are the simpler and more widely reported choice; SHAP/XGBoost ranking following Kim et al.'s protocol is a natural v2 upgrade to flag in §7 / Future Work.

3. **Pedigree discrepancy corroboration (p. 1101, point i).** Kim et al.'s empirical finding that pedigree-based ecoinvent distributions show no systematic relationship with propagated parameterized uncertainty independently corroborates our design choice to use Poore & Nemecek's empirical σ_g rather than ecoinvent pedigree scoring. This is now citable to both Heijungs (2020) and Kim et al. (2025).

---

#### Three-sentence relevance note

Kim et al. (2025) provides the state-of-the-art protocol for GSA in high-dimensional LCA models when inputs are correlated — the direct methodological successor to the independent-sampling Sobol approaches our §3.8 currently implements, and the food-relevant basmati rice figure (Fig. 1) gives a concrete illustration that independent sampling overestimates food-group market-share uncertainty by a measurable margin. For our manuscript, this paper serves three roles: (i) it is the citation for "correlated Sobol/SHAP extensions" that we explicitly defer to future work in §7, (ii) its empirical finding that pedigree-based ecoinvent distributions are uncorrelated with propagated parameterized distributions corroborates our §3.8 design choice to use Poore & Nemecek σ_g instead of ecoinvent pedigree, and (iii) the SHAP/XGBoost ranking methodology is the upgrade path for a v2 sensitivity analysis once AGRIBALYSE-grounded LCIs are available under TODO-CODE-LCA-2. Cite at §2.3 ("Global sensitivity analysis with correlated inputs has been formalised recently — Kim et al., 2025") and §7 limitation on independent sampling assumption.

---

*Pending: papers F35 through F38.*

## Group G. Sustainability of AI

*Pending: papers G39 through G46.*

## Group H. Monetary valuation and externalities

*Pending: papers H47 through H50.*

## Group I. Canadian regional context

*Pending: papers I51 through I54.*

## Group J. Data and study cohorts

*Pending: papers J55 through J57.*
