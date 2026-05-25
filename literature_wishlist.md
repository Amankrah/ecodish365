# Literature Wishlist — Call 1 Manuscript

**Companion to** `manuscript_call1.md` and `scenarios.md`.
**For you to fetch via McGill access (most are paywalled).**
**Priority key:** ★★★ = must-have (cited as primary methodology); ★★ = supporting evidence; ★ = nice-to-have for framing.

Once you have a PDF, drop it into a `papers/` directory (or paste the relevant passages back to me) and I will pull exact wording, page citations and any data tables we should reproduce.

---

## A. LCA methodology (★★★)

1. **Huijbregts, M.A.J., Steinmann, Z.J.N., Elshout, P.M.F., Stam, G., Verones, F., Vieira, M., Zijp, M., Hollander, A., van Zelm, R. (2017).** *ReCiPe2016: a harmonised life cycle impact assessment method at midpoint and endpoint level.* **International Journal of Life Cycle Assessment** 22, 138–147. doi:10.1007/s11367-016-1246-y
   *Why we need it:* exact midpoint and endpoint formulas; need page-cited factor values to support our implementation.

2. **RIVM (2018).** *ReCiPe 2016 v1.1 — A harmonized life cycle impact assessment method at midpoint and endpoint level — Report I: Characterisation.* RIVM Report 2016-0104a.
   PDF: https://www.rivm.nl/sites/default/files/2018-11/Report%20ReCiPe_Update_20171002_0.pdf
   *Why:* documents the October 2017 update and 2024 normalization revision we cite.

3. **Vellinga, R.E., van de Kamp, M., Mason-D'Croz, D., et al. (2019).** *A taste of the new ReCiPe for life cycle assessment: consequences of the updated impact assessment method on food product LCAs.* **Int J Life Cycle Assess.** doi:10.1007/s11367-019-01653-3
   *Why:* shows how ReCiPe updates change food rankings — directly supports our methodology section.

4. **Poore, J., Nemecek, T. (2018).** *Reducing food's environmental impacts through producers and consumers.* **Science** 360 (6392), 987–992. doi:10.1126/science.aaq0216 *(plus supplementary materials)*
   *Why:* primary reference for our group-level factors and σ_g in S3.

5. **AGRIBALYSE 3.2 documentation (ADEME, 2024).** https://doc.agribalyse.fr/documentation-en/
   *Why:* will become a primary reference once we run S2.

---

## B. Diet quality / nutritional indices (★★★)

6. **Brassard, D., Elvidge Munene, L.A., St-Pierre, S., et al. (2022).** *Development of the Healthy Eating Food Index (HEFI)-2019 measuring adherence to Canada's Food Guide 2019 recommendations on healthy food choices.* **Applied Physiology, Nutrition, and Metabolism** 47(5), 595–610. doi:10.1139/apnm-2021-0415

7. **Brassard, D., et al. (2022).** *Evaluation of the Healthy Eating Food Index (HEFI)-2019…* **APNM** 47(5), 611–624. doi:10.1139/apnm-2021-0416

8. **Lamarche, B., Brassard, D., et al. (2023).** *Canadian Food Intake Screener…* **APNM**. doi:10.1139/apnm-2023-0018
   *Why for 6–8:* the gold-standard HEFI references for our implementation; need to cite construct validity & Cronbach's α numbers.

9. **Mozaffarian, D., El-Abbadi, N.H., O'Hearn, M., et al. (2021).** *Food Compass is a nutrient profiling system using expanded characteristics for assessing healthfulness of foods.* **Nature Food** 2, 809–818.

10. **Mozaffarian, D., et al. (2024).** *Food Compass 2.0 is an improved nutrient profiling system…* **Nature Food** 5(11). doi:10.1038/s43016-024-01053-3

11. **Mozaffarian, D., et al. (2022).** *Validation of Food Compass with a healthy diet, cardiometabolic health, and mortality among U.S. adults, 1999–2018.* **Nature Communications** 13. doi:10.1038/s41467-022-34195-8

12. **Mozaffarian, D., et al. (2025).** *Food Compass Score-10 validation.* **Am. J. Clin. Nutr.** doi:10.1016/j.ajcnut.2025.01.014
    *Why 9–12:* the FCS / Food Compass 2.0 reference set.

13. **Australia New Zealand Food Regulation Ministerial Council (2014, with updates through 2020).** *Health Star Rating System — Calculator and Style Guide.*
    *Why:* canonical HSR specification for §3.2.

---

## C. Health-burden / DALY food scoring (★★★)

14. **Stylianou, K.S., Heller, M.C., Fulgoni, V.L., Ernstoff, A.S., Keoleian, G.A., Jolliet, O. (2016).** *A life cycle assessment framework combining nutritional and environmental health impacts of diet: a case study on milk.* **Int J Life Cycle Assess.** 21, 734–746.

15. **Stylianou, K.S., et al. (2021).** *Small targeted dietary changes can yield substantial gains for human health and the environment.* **Nature Food** 2, 616–627. doi:10.1038/s43016-021-00343-4
    *Why:* the canonical HENI paper — primary citation for the DALY methodology and the figure showing HENI per food category we reproduce.

16. **Stylianou, K.S. (2018/2021).** *Health-based food evaluation.* PhD thesis or related publication providing the 14-factor μDALY/g table.

17. **Stylianou, K.S., et al. (2024).** *The complementarity of nutrient density and disease burden for Nutritional Life Cycle Assessment.* **Frontiers in Sustainable Food Systems** 8: 1304752.
    URL: https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1304752/full

18. **GBD 2019 Diet Collaborators (2019).** *Health effects of dietary risks in 195 countries, 1990–2017: a systematic analysis for the Global Burden of Disease Study 2017.* **The Lancet** 393, 1958–1972.

19. **GBD 2021 / 2023 Risk Factors Collaborators — most recent update.** **The Lancet** 2024.
    *Why 18–19:* source of the dietary risk-factor RRs underpinning HENI.

20. **DANI — DALY Nutritional Index** (cited by Stylianou et al. 2024). Find the originating paper.

21. **medRxiv 2024 preprint: Quantifying the health impact of food interventions: Revisiting the Disability-Adjusted Life Years Approach.** doi:10.1101/2024.08.26.24312574
    *Why:* contemporary methodological critique we should engage with.

---

## D. AI / LLMs for food classification & LCA (★★★)

22. **Wijesinghe, D.G.N.G., et al. (2026).** *Large Language Models for Real-World Nutrition Assessment: Structured Prompts, Multi-Model Validation and Expert Oversight.* **Nutrients** 18(1):23. doi:10.3390/nu18010023
    URL: https://www.mdpi.com/2072-6643/18/1/23
    *Why:* contemporaneous benchmark of LLMs on dietary classification — the most relevant baseline for S1.

23. **NutriRAG (2025).** *Unleashing the Power of Large Language Models for Food Identification and Classification through Retrieval Methods.* PMC PMC11957177.

24. **FoodyLLM (2025).** PMC PMC12927182.
    *Why 23–24:* RAG-based food classification — directly informs S7 design.

25. **(2025).** *Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from Food Images.* **Current Developments in Nutrition.** doi:10.1016/j.cdnut.2025…
    PMC PMC12513282.

26. **Eisenberg, M.D., et al. (2022).** *Natural language processing and machine learning approaches for food categorization and nutrition quality prediction compared with traditional methods.* **American Journal of Clinical Nutrition** 116. doi:10.1093/ajcn/nqac225

27. **Any 2024–2026 paper on LLM-based linkage between FNDDS / USDA SR and ecoinvent / Agribalyse.** *(searching — please send anything you find via McGill databases.)*

---

## E. Sustainability assessment frameworks (★★)

28. **EAT–Lancet Commission 2.0 (2025).** *The EAT–Lancet Commission on healthy, sustainable, and just food systems.* **The Lancet.** doi:10.1016/S0140-6736(25)01201-2 — ✅ *Extracted* — [`literature_extractions.md`](literature_extractions.md) §E28.

29. **Willett, W., et al. (2019).** *Food in the Anthropocene: the EAT–Lancet Commission on healthy diets from sustainable food systems.* **The Lancet** 393, 447–492. ✅ *Extracted* — [`literature_extractions.md`](literature_extractions.md) §E29; PDF [`papers/PIIS0140673618317884.pdf`](papers/PIIS0140673618317884.pdf).

30. **IPCC AR6 Working Group III (2022).** *Chapter 5: Demand, services and social aspects of mitigation.*

31. **IRP (2019).** *Global Resources Outlook.* UNEP International Resource Panel.

32. **Heller, M.C., Keoleian, G.A., Willett, W.C. (2013).** *Toward a life cycle–based, diet-level framework for food environmental impact and nutritional quality assessment.* **Environmental Science & Technology** 47, 12632–12647. doi:10.1021/es4025113 — ✅ *Extracted* — [`literature_extractions.md`](literature_extractions.md) §E32; PDF [`papers/toward-a-life-cycle-based-diet-level-framework-for-food-environmental-impact-and-nutritional-quality-assessment-a.pdf`](papers/toward-a-life-cycle-based-diet-level-framework-for-food-environmental-impact-and-nutritional-quality-assessment-a.pdf).

---

## F. Uncertainty quantification in LCA (★★)

33. **Heijungs, R. (2020).** *On the number of Monte Carlo runs needed to compare the impacts of alternatives…* **Int J Life Cycle Assess.** 25, 394–402. doi:10.1007/s11367-019-01698-4 — ✅ *Extracted* — [`literature_extractions.md`](literature_extractions.md) §F33; PDF [`papers/On_the_number_of_Monte_Carlo_runs_in_comparative_p.pdf`](papers/On_the_number_of_Monte_Carlo_runs_in_comparative_p.pdf).

34. **Kim, A., Mutel, C., Hellweg, S. (2025).** *Global sensitivity analysis of correlated uncertainties in life cycle assessment.* **Journal of Industrial Ecology** 29(4):1090–1104. doi:10.1111/jiec.70036 — ✅ *Extracted* — [`literature_extractions.md`](literature_extractions.md) §F34; PDF [`papers/J of Industrial Ecology - 2025 - Kim - Global sensitivity analysis of correlated uncertainties in life cycle assessment.pdf`](papers/).

35. **Mendoza Beltran, A., et al. (2018).** *When the background matters: using scenarios from integrated assessment models in prospective LCA.* **J Ind Ecol.** 23(1).

36. **Lo Piano, S., Saltelli, A. (2022).** *Two-dimensional Monte Carlo simulations in LCA: an innovative approach to guide the choice for the environmentally preferable option.* **Int J Life Cycle Assess.** doi:10.1007/s11367-022-02041-0

37. **Saltelli, A., et al. (2008).** *Global Sensitivity Analysis: The Primer.* Wiley. *(method baseline for Sobol indices)*

38. **Igos, E., Benetto, E., Meyer, R., et al. (2019).** *How to treat uncertainties in life cycle assessment studies?* **Int J Life Cycle Assess.** 24, 794–807.

---

## G. Sustainability of AI (★★)

39. **Strubell, E., Ganesh, A., McCallum, A. (2019/2020).** *Energy and Policy Considerations for Modern Deep Learning Research.* AAAI / ACL.

40. **Patterson, D., Gonzalez, J., Le, Q., et al. (2021).** *Carbon Emissions and Large Neural Network Training.* arXiv:2104.10350.

41. **Luccioni, A.S., Viguier, S., Ligozat, A.-L. (2023).** *Estimating the carbon footprint of BLOOM, a 176B-parameter language model.* **JMLR.**

42. **Patterson, D., et al. (2024 update).** *The carbon footprint of machine learning training will plateau, then shrink.* IEEE Computer.

43. **Li, P., Yang, J., Islam, M.A., Ren, S. (2023).** *Making AI Less "Thirsty": Uncovering and Addressing the Secret Water Footprint of AI Models.* arXiv:2304.03271.

44. **NTT DATA (2025).** *AI's growing demand for resources is unsustainable…* https://www.nttdata.com/global/en/news/press-release/2025/october/102800

45. **(2025).** *To be Artificial Intelligence for sustainability or not to be sustainable Artificial Intelligence.* **Renewable & Sustainable Energy Reviews.** doi:10.1016/j.rser.2025…

46. **(2025).** *Artificial Intelligence for Sustainability: A Systematic Review and Critical Analysis…* **Sustainability** 17(17): 8049. https://www.mdpi.com/2071-1050/17/17/8049

---

## H. Monetary valuation / externalities (★★)

47. **Environment and Climate Change Canada (2023).** *Guidance on the social cost of greenhouse gas emissions.* Government of Canada.
    URL: https://www.canada.ca/en/environment-climate-change/services/climate-change/science-research-data/social-cost-ghg.html

48. **CE Delft (2018, updated 2024).** *Environmental Prices Handbook EU28 version.*
    *Why:* used as fallback monetary values for non-GHG categories (and we *must* replace the personal-communication references in `monetization.py`).

49. **True Price Foundation (2022, updated 2024).** *Methodology for True Pricing of Food.*

50. **Drupp, M.A., et al. (2021).** *Discounting Disentangled.* **American Economic Journal: Economic Policy.** *(for SCC discounting context.)*

---

## I. Canadian regional context (★★)

51. **ECCC National Inventory Report 1990–2022 (2024).** *Canada's GHG sources and sinks.*
    *Why:* underpins our Canadian grid intensity factor (current 0.85 multiplier).

52. **Statistics Canada (2024).** *Census of Agriculture and Net Farm Income.*

53. **Boulay, A.-M., et al. (2018).** *The WULCA consensus characterization model for water scarcity footprints: assessing impacts of water consumption based on available water remaining (AWaRE).* **Int J Life Cycle Assess.** 23, 368–378.

54. **Pelletier, N., et al. (2022).** *Canadian food system environmental performance review.* Agriculture & Agri-Food Canada (if available).

---

## J. Data and study cohorts (★★)

55. **Statistics Canada (2017).** *Canadian Community Health Survey – Nutrition, 2015: Public-Use Microdata File.*
    *Why:* primary data source for S4 meal panel.

56. **Health Canada (2024).** *Canadian Nutrient File — Compilation of Canadian Food Composition Data.* User's Guide.

57. **USDA (2020).** *FNDDS 2017–2018.* Beltsville Human Nutrition Research Center. *(comparison cohort if we extend.)*

---

## What I need from each paper (please paste back to me)

For each paper you fetch:
- **Title + DOI + page-number for the specific result/formula we cite**;
- **Any data tables we should reproduce** (especially factor tables in §A and §C);
- **Methods limitations the authors flag** (we engage with these in §7);
- **A 3-sentence note on what's directly relevant to our manuscript section.**

Once you've pulled the top-priority ★★★ papers (groups A, B, C, D), come back and I will:
1. Insert page-accurate citations into the draft.
2. Reconcile our HENI factor table with Stylianou's exact values.
3. Update §3.2 to cite ReCiPe 2016 v1.1 v. 2024 normalization update precisely.
4. Sanity-check the LLM benchmark prompts against the Nutrients 2026 paper's structured-prompt design.

---

## Suggested McGill database routes

- **ScienceDirect / Lancet** (Elsevier + Lancet) — best for #4, #6–8, #11, #28–29, #32, #36
- **Springer Nature** — best for #1, #3, #5, #9, #10, #11, #28
- **Web of Science / Scopus** — discovery + back-citations
- **PubMed/PMC** — open versions of #22, #23, #24, #25
- **ADEME / RIVM portals** — open #2 and #5
- **arXiv** — #40, #43
- **Statistics Canada EFT / RDC** — #55 (needs RDC application; flag this early; McGill has on-campus RDC at CIQSS).
