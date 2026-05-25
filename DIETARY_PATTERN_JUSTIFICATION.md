# Dietary-pattern algorithm for individuals — justification + recommended path

*Memo, 2026-05-24. Written before any code is committed; companion to [`WAFCT_EXPLORATION.md`](WAFCT_EXPLORATION.md). Reviews [`literature_extractions.md`](literature_extractions.md) (B6–B12, C15–C21, D22–D27), [`literature_wishlist.md`](literature_wishlist.md), and the current [`manuscript_call1.md`](manuscript_call1.md) §3.4–§3.8.5, §4.5, §5.1.*

## Executive verdict

**Do it — but framed as descriptive resemblance, not classification, and reusing existing primitives rather than introducing new ML.** The recommended approach is **embedding-space prototype matching**: take the aggregated daily ingredient list the 24-h recall wizard already produces ([`backend/api/services/cnf_recall_24h.py`](backend/api/services/cnf_recall_24h.py)), build a mass-weighted "day vector" by averaging the per-food embeddings already shipped in [`cnf_corpus_embeddings.npz`](backend/api/data/cnf_corpus_embeddings.npz), and cosine-rank it against a small library of literature-anchored prototype patterns (Mediterranean, DASH, Vegetarian, Vegan, CFG-Healthy, Standard Western, optionally a WAFCT West African staple-based pattern). Show **all top-3 resemblances simultaneously** (not a single label), pair every output with the Brassard 2022b single-day caveat the rest of the platform already enforces, and use the existing LLM client to generate the audience-appropriate narrative. **Estimated effort: ~15-16 hr across 7 phases, ~60 % the size of WAFCT-EXTEND.**

**Why this passes the discipline test of the rest of the platform**:
1. Reuses three primitives already shipped (embedding corpus, 24-h recall, audience-aware explanations) — no new ML, no new validation framework.
2. Architecturally novel (embedding-space pattern matching is **not** in the extracted literature) so it earns a manuscript §3.8.6 in the same shape as the existing §3.5 / §3.8 AI-subsystem subsections.
3. Honest about its inferential ceiling — descriptive resemblance, not outcome prediction — so it does **not** put HEFI / FCS / HENI's outcome-validated scoring at risk.

The rest of this memo documents the literature review behind that verdict, three architecture alternatives weighed against each other, the recommended path, and the risks.

## 1. What does "dietary pattern algorithm for an individual" actually mean?

The phrase covers three quite different research traditions. Disambiguating is critical because choosing one of them silently determines what we can claim.

### 1.1 A priori (index-based) patterns
A fixed scoring rubric is built from nutrition-policy guidelines; an individual diet is graded against it. **The platform already ships three of these:**

- **HEFI-2019** ([Brassard 2022a](literature_extractions.md#L806), [B7 evaluation](literature_extractions.md#L937)) — measures adherence to Canada's Food Guide 2019, 10 components → 0-80, Cronbach's α 0.66, convergent validity with US HEI-2015 r = 0.79.
- **FCS / FCS-10** ([Mozaffarian 2021 B9](literature_extractions.md#L1151), [Barrett 2024 B10](literature_extractions.md#L1224), [Barrett 2025 B12](literature_extractions.md#L1428)) — per-food healthfulness score 1-100; diet-level aggregate i.FCS = energy-weighted mean; outcome-validated (O'Hearn 2022 [B11](literature_extractions.md#L1336): R = 0.81 vs HEI-2015, 7 % lower mortality per 1 SD).
- **HSR** — Australian per-product star rating.

These are **scoring** systems. They answer "*how well* are you eating?" with a number — they do not answer "*what kind* of eating are you doing?".

### 1.2 A posteriori (data-driven) patterns
Patterns are *learned* from population data: principal component analysis (PCA), reduced-rank regression (RRR), or cluster analysis on food-group intake frequencies extracts factors like "Western", "Prudent", "Mediterranean-like", or risk-factor-mediating patterns. The extracted literature contains **no PCA/RRR/cluster paper for dietary patterns** (`grep -i 'principal component|reduced rank|cluster.*diet' literature_extractions.md` returns zero matches). This tradition is dominant in nutritional epidemiology — Hu (2002), Ocké (2013), Schulze (2003) — but absent from our reference set, and for good reason: it requires population-scale labelled cohort data and produces population-level factors that are awkward to apply to one individual's 24-h recall. **Not the right shape for our platform.**

### 1.3 Reference-pattern resemblance
A fixed library of **canonical example diets** (Mediterranean, DASH, Western, Vegetarian, Vegan, NCD-Protective, CFG-Healthy) is curated from the policy/clinical literature; an individual diet is scored on its similarity to each. This is what dietitians and nutrition educators actually use in practice — "you eat like a Mediterranean", "your day looks more Western", etc. It's the user-facing UX nutrition apps converge on (MyFitnessPal's "Diet Quality Score", Cronometer's pattern labels, Whisk's meal-plan matching).

**The literature backing for each prototype is well-established:**
- **Mediterranean**: Trichopoulou 2003 (NEJM 348:2599), Estruch 2013 PREDIMED (NEJM 368:1279) — outcome-validated for CVD reduction.
- **DASH**: Sacks 2001 (NEJM 344:3), Appel 1997 (NEJM 336:1117) — outcome-validated for blood pressure.
- **Vegetarian / Vegan**: Orlich 2013 (JAMA Intern Med 173:1230) — Adventist Health Study.
- **CFG-Healthy (Canada)**: anchored to Brassard 2022a HEFI-2019 components ([B6](literature_extractions.md#L806)).
- **Standard Western / NHANES baseline**: Krebs-Smith 2010 (J Nutr 140:1832), B7's national mean of HEFI = 43.1/80.
- **EAT-Lancet planetary-health pattern** (Willett 2019 in wishlist E29) — adds a sustainability dimension we already have the LCA infrastructure to score.
- **West African staple pattern** — natural complement to the WAFCT integration (fonio / cassava / jollof / baobab-leaf-sauce). Documented in the Vincent 2019 WAFCT introduction.

**This is the tradition our platform's existing primitives map onto cleanly.** It treats the algorithm as a *descriptor* (resemblance vector), not a *classifier* (single label) — which sidesteps the outcome-validation requirement that would otherwise be a manuscript blocker.

## 2. Why this is genuinely missing from what we already ship

Our pipeline scores meals through three independent lenses. **All three are quality scores, none are pattern descriptors:**

| Question users want answered | What we already ship | Gap |
|---|---|---|
| "How healthy is my day?" | HEFI / FCS / HSR scores | ✓ covered |
| "How does it harm/help my expected lifespan?" | HENI healthy-life-minutes | ✓ covered |
| "What's my environmental footprint?" | Per-day LCA + monetisation | ✓ covered |
| "**What KIND of eating am I doing?**" | — | **gap** |
| "**Compared to what canonical pattern?**" | — | **gap** |
| "**If I wanted to shift toward Mediterranean, what would I swap?**" | — | **gap** |

The cross-system correlation work in §4.5 (HENI × HEFI ρ = 0.886) confirms the three scoring systems converge on *quality* ranking — they all agree on whether a meal is "good" or "bad". They do **not** disagree about that. Where users still get nothing is the **categorical / qualitative** question: what *kind* of eating is this? That is the dietary-pattern question, and it is genuinely orthogonal to the scoring question.

## 3. Architectural alternatives

Three candidate paths, weighed honestly.

### 3.1 Option A — A posteriori (PCA / RRR on population data)
Run PCA on the 2015 CCHS-Nutrition food-group intake matrix (the same dataset §5.1 already plans to use for S4). Extract 4-6 dietary-pattern factors. Score each user's day on the factor loadings.

**Pros**: Statistically principled; produces patterns that *exist* in the Canadian population rather than ones we curate.
**Cons**:
- Requires CCHS PUMF access ([wishlist J55](literature_wishlist.md#L177)) — currently flagged as RDC-application-blocked.
- Factor labels ("Western-leaning", "Plant-forward") are post-hoc and require expert naming.
- Loadings change with each dataset refresh — provenance becomes fragile.
- **Doesn't reuse our embedding infrastructure at all** — PCA on intake counts is a parallel pipeline.

### 3.2 Option B — A priori index extension (a "pattern HEFI")
Build a new index whose components literally are "Mediterranean-like-ness", "DASH-like-ness", etc. — each scored against a fixed rubric of foods + frequencies, like HEFI's 10-component structure.

**Pros**: Defensible (just like HEFI); deterministic; researcher-friendly.
**Cons**:
- We'd be inventing a new index with no published validation.
- The Mediterranean / DASH literature defines components in ways that don't always map cleanly onto CNF / WAFCT (e.g. "olive oil servings per day" assumes Mediterranean food typology).
- **Doesn't use AI / embeddings at all** — the user's framing requested AI + embeddings + 24-h decomposer composition; this option ignores that.
- Multiplicative complexity: 5-7 patterns × 8-15 component rules each = 40-100 hand-curated rubric entries to defend.

### 3.3 Option C — Embedding-space prototype resemblance *(recommended)*
For each prototype pattern, hand-curate 3-5 example days, look up each food's embedding from the existing `cnf_corpus_embeddings.npz` (6,719 × 1,536 dims), compute the mass-weighted mean (a single "prototype vector" per pattern). For an individual's day, build the same mass-weighted day vector and report cosine similarity to each prototype.

**Pros**:
- **Reuses every primitive already shipped** — recall wizard for input, embedding corpus for vectors, LLM client for narrative, audience-aware explanations panel for output.
- **Architecturally novel** — `grep -i 'embedding|RAG' literature_extractions.md` shows embeddings are used for food→food matching ([NutriRAG D23](literature_extractions.md#L2520), our own §3.5 LCA matcher) but **not** for dietary-pattern resemblance. The extracted literature does not contain this method applied to diet patterns.
- **Multilingual + cross-database transparent** — the embedding text already concatenates English + French + food group; WAFCT-EXTEND already merged WAFCT into the same corpus. A West African day's resemblance to a West African prototype works for free; an English-speaking Canadian user typing "salade niçoise" gets the same Mediterranean similarity as a French-speaking user typing "salade niçoise". No translation table needed.
- **Cheap and deterministic** — no per-query LLM call required for the similarity computation; only optional LLM call for the narrative.
- **Avoids the inferential pitfall** — by reporting *all* top-3 resemblances with explicit cosine values, we never tell a user "you eat Mediterranean" based on one day; we tell them "today's day-vector is closest to Mediterranean (0.73), DASH (0.66), and CFG-Healthy (0.61)". The framing maps the LLM-RAG literature's similarity-ranking discipline ([NutriRAG D23](literature_extractions.md#L2520), [Ase 2026 D22](literature_extractions.md#L2429)) onto a dietary-pattern task — same architecture, different target ontology.

**Cons**:
- **No outcome validation in the pipeline** — we'd be reusing the *published* outcomes attached to each prototype pattern (Trichopoulou 2003 / Sacks 2001 / Orlich 2013) by reference, not computing them. Has to be honest about this in the audience-aware caveat.
- **Prototype curation is non-trivial** — 5-7 patterns × 3-5 example days each = 15-35 literature-anchored reference days. ~3 hours of careful curation work.
- **Embedding semantics may not perfectly track nutrition semantics** — `text-embedding-3-small` was trained on web text, not on food-composition data. Two foods with similar names but very different macronutrient profiles (e.g. "almond milk" vs "whole milk") might cluster too closely. Mitigation: empirical validation in Phase 6 of the recommended path below.

**Recommendation**: **Option C**, because it is the option that reuses the platform's architectural commitments rather than working around them.

## 4. Recommended path (Option C, ~15-16 hr across 7 phases)

### Phase 1 — Prototype library (~3 hr)
NEW: `backend/api/data/dietary_pattern_prototypes.json` — 7 patterns × 3-5 hand-curated example days, each with literature anchor:

```json
[
  {
    "pattern_id": "mediterranean",
    "display_name": "Mediterranean",
    "literature_anchor": "Trichopoulou 2003 (NEJM 348:2599); Estruch 2013 PREDIMED (NEJM 368:1279)",
    "outcome_evidence": "CVD risk reduction 0.70 HR (Estruch 2013)",
    "example_days": [
      {
        "name": "PREDIMED-style Mediterranean day",
        "foods": [
          {"food_id": 4471, "mass_g": 200, "comment": "whole-grain pasta"},
          {"food_id": 1704, "mass_g": 120, "comment": "banana"},
          {"food_id": 419,  "mass_g": 15,  "comment": "olive oil"}
        ]
      }
    ]
  }
]
```

7 patterns: **Mediterranean** (Trichopoulou 2003), **DASH** (Sacks 2001), **Western / Standard American** (NHANES mean, Krebs-Smith 2010), **Vegetarian** (Orlich 2013), **Vegan** (Orlich 2013), **CFG-Healthy** (Brassard 2022a, anchored to HEFI components), **West African Staple** (Vincent 2019, anchored to WAFCT sheet 09 mixed-dish recipes — natural complement to the WAFCT integration). Optional 8th: **EAT-Lancet** (Willett 2019 / wishlist E29) for sustainability framing.

### Phase 2 — Embedding aggregation service (~2 hr)
NEW: `backend/api/services/dietary_pattern.py`:

```python
class DietaryPatternMatcher:
    def __init__(self, corpus: CNFCorpus, prototypes: dict): ...

    def classify(self, foods: list[dict]) -> PatternResemblanceResult:
        """Compute mass-weighted day vector → cosine vs each prototype vector."""
        # 1. Map foods[i].food_id → corpus.embeddings[corpus_idx]
        # 2. Day vector = L2-normalize(Σ mass_g * embedding) / Σ mass_g
        # 3. For each prototype, cosine(day_vector, prototype_vector)
        # 4. Softmax-normalize for a probability-like distribution
        # 5. Return top-3 + confidence band + caveat
```

Single dependency: the existing `CNFCorpus` from `backend/api/services/cnf_matcher.py`. No new ETL, no new model, no new external service.

### Phase 3 — Backend endpoint (~1 hr)
NEW: `POST /api/dietary-pattern/classify` in `backend/api/views/cnf_ai_search_views.py` (extending the existing AI-MATCH view module). Accepts `{foods: [{food_id, mass_g}], user_type}`. Same rate-limit machinery as the other AI endpoints (likely 1¢ — no LLM call required unless narrative is requested).

### Phase 4 — Optional LLM narrative (~2 hr)
For researcher / individual modes that want a plain-language explanation: pass the top-3 patterns + user's actual top-5 foods + cosine values to `gpt-4.1-mini` with a structured rubric:
- Individual: "Today's food choices resemble Mediterranean eating most closely (73 %), with DASH (66 %) and CFG-Healthy (61 %) close behind. Distinctive: olive oil + leafy greens + legumes. Note: one day's eating is only a snapshot — repeat the recall on different days to see your usual pattern."
- Researcher: full similarity vector, prototype anchor citations, methodological caveat citing Brassard 2022b.

Optional — gates behind a `?narrative=true` query param so the no-LLM baseline path stays free.

### Phase 5 — Frontend (~3 hr)
- Add a **6th score-routing button on `/recall-24h` Step 4**: "🧭 Dietary Pattern" — routes the aggregated daily ingredient list to a new `/dietary-pattern` page via the existing `useRecall24hReceiver` mechanism.
- NEW: `frontend/src/app/dietary-pattern/page.tsx` — renders a small radar chart (one axis per prototype) + the top-3 resemblance list with cosine bars + the LLM narrative + the multi-day caveat banner.
- NEW: `frontend/src/components/shared/PatternResemblanceCard.tsx` — reusable display component.
- Add the pattern score adapter to `frontend/src/lib/api.ts` so the wizard can also surface it inline in Step 3.

### Phase 6 — Validation (~3 hr)
NEW: `backend/_smoke_dietary_pattern.py` — 6-gate harness:
1. **Self-match**: each prototype's own example days score highest against that prototype (sanity).
2. **Cross-prototype distinguishability**: no two prototypes have median cross-cosine > 0.85 (they're genuinely different).
3. **Known-pattern reference days**: 10 hand-labelled non-prototype days (e.g. "ovo-lacto-vegetarian day featuring eggs + cheese + lentil stew") classify to the expected top-1.
4. **WAFCT-aware sanity**: a canonical West African day (fonio breakfast + jollof lunch + baobab-leaf-sauce dinner — the AI-MATCH-2 smoke fixture) scores highest against "West African Staple", not Mediterranean.
5. **Robustness to portion changes**: scaling all masses by 0.5 / 2.0 doesn't change the ranking.
6. **Empty/degenerate inputs handled** (single-food day, missing FoodIDs, etc.).

### Phase 7 — Manuscript §3.8.6 + code_action_items SHIPPED (~1.5 hr)
- Manuscript new subsection §3.8.6 "Dietary-pattern resemblance via embedding similarity" (~300 words) — rationale, embedding-space method, prototype library, audience-aware caveats, smoke-harness gates.
- `code_action_items.md` "DIET-PATTERN-1 SHIPPED" entry.

**Total estimated effort: 15-16 hr.** About 60 % of WAFCT-EXTEND.

## 5. Risks + mitigations

1. **Single-day inferential ceiling.** A user's day vector built from one 24-h recall does not characterise their *usual* eating pattern any better than HEFI-2019 from one recall characterises their usual diet (Brassard 2022b Discussion p. 588 — the [`hefi_explanations.py`](backend/api/views/hefi_explanations.py) mandatory caveat). **Mitigation**: reuse the *exact same caveat machinery* — never report a pattern label without the multi-day disclaimer, and frame outputs as "today's food choices resemble…" not "you eat like…".

2. **Outcome-validation gap.** Our pipeline cannot directly attribute health outcomes to a resemblance score. **Mitigation**: cite the published outcomes of each prototype by reference (Trichopoulou 2003 for Mediterranean / CVD, Sacks 2001 for DASH / blood pressure, Orlich 2013 for Vegetarian / mortality) without computing them. Researcher mode shows the citation; individual mode shows a hyperlink. This is the same discipline §3.7 already uses for HEFI's missing-outcome caveat ("HEFI-2019 is NOT health-outcome-validated; do not interpret as a disease-burden predictor").

3. **Embedding semantics ≠ nutrition semantics.** `text-embedding-3-small` was trained on web text. Two foods with similar names but different nutrient profiles may cluster too closely. **Mitigation**: Phase 6 Gate 3 (known-pattern reference days) catches the worst cases empirically; if a vegetarian reference day is misclassified as Mediterranean because the embedding over-weighted "olive oil" semantics, the gate fires. If gates fail, fall back to a hybrid: cosine + nutrient-profile distance (Mahalanobis on the standard HEFI input vector that the pipeline already computes per food).

4. **Prototype curation is opinionated.** What is a "canonical Mediterranean day"? Literature gives ranges, not single days. **Mitigation**: per-prototype 3-5 example days span the variation the source paper documents; each curated day is annotated with the paper section it derives from; literature-anchor field is mandatory in the JSON schema.

5. **Identity confusion / labelling risk.** Telling a user "you eat Western" based on one day risks identity essentialism + may discourage variety. **Mitigation**: never show a single label; always show top-3 resemblance values; never use the verb "are" ("you are eating…"), use the verb "resembles" ("today's day resembles…").

6. **Manuscript scope creep.** §3.8.6 + a new §4.x validation subsection adds ~500-700 words. **Mitigation**: keep the section in the existing §3.8 cluster (parallel to §3.8.5 WAFCT) rather than promoting it to a top-level §3.9 — same architectural-extension framing.

7. **Single-pattern ambiguity at low cosine differences.** If the top-3 patterns all sit between 0.62 and 0.68, the "winner" is noise. **Mitigation**: add a confidence band — if the top-1 cosine is within 0.05 of the top-2, report both as "co-leading" and lean on the LLM narrative to explain the mixed signal.

## 6. What I deliberately argued AGAINST

- **Standalone score that competes with HEFI / FCS / HENI.** Avoided. Pattern resemblance is positioned as a *descriptor* alongside the existing scores, never as a replacement.
- **Population-scale PCA on CCHS data.** Avoided. Requires RDC access; produces brittle factors; doesn't reuse the embedding infrastructure.
- **Per-user pattern classifier trained on labelled data.** Avoided. Requires a labelled dataset we don't have; introduces ML model lifecycle management we don't want to take on.
- **Inventing a new index ("Pattern-HEFI").** Avoided. Adds an un-validated scoring rubric the pipeline doesn't need.
- **Auto-detecting cultural/regional pattern from browser locale.** Avoided. Magic; hard to override; risks essentialism.
- **Persisting per-user pattern history.** Avoided. No auth integration in v1.

## 7. What would make me change my mind

The "do it" verdict in §0 flips to "defer" if any of the following surface during prototype curation:

1. The 7 prototype patterns can't be distinguished in cosine space (median cross-prototype cosine > 0.85). This would mean the embedding doesn't carry pattern-discriminating signal and Option A or B becomes necessary.
2. We discover that a published embedding-space dietary-pattern method already exists in literature we haven't extracted yet — would change the novelty story for the manuscript.
3. The Brassard 2022b "single day ≠ usual intake" caveat proves too rhetorically heavy for the user-facing copy to land cleanly — i.e. users keep ignoring it despite prominent placement.

The first is empirical and resolves in Phase 6. The second is a literature check I'd do before Phase 1 starts (specifically: search for "embedding dietary pattern" / "vector-space dietary similarity" / "text-embedding nutrition pattern" — none of which appear in the current extracted set). The third is a UX-test concern, not a methodology concern, and can be addressed iteratively.

## 8. Open question for you

Before I write the implementation plan, one decision worth your input:

**Should the prototype library include EAT-Lancet planetary-health pattern?** Pros: ties dietary patterns to the LCA / environmental work the manuscript leads with; Willett 2019 is in the wishlist ([E29](literature_wishlist.md#L102)). Cons: EAT-Lancet is sustainability-framed rather than health-outcome-framed and may not be what users typing "what's my diet pattern" expect to compare against. I'd lean toward including it as an *optional 8th prototype* so we keep the option to surface it in researcher / policy mode without polluting the individual-mode display.

Everything else is settled enough that I'd propose entering plan mode for the implementation plan as soon as you confirm the verdict + the EAT-Lancet question.

## Files referenced

- [`literature_extractions.md`](literature_extractions.md) — B6 (HEFI dev), B7 (HEFI eval, Cronbach), B9-B12 (FCS family + O'Hearn mortality validation), C15-C17 (HENI / nLCA), D22 (Ase LLM food classification), D23 (NutriRAG embedding + RAG), D24 (FoodyLLM fine-tuning).
- [`literature_wishlist.md`](literature_wishlist.md) — E29 (EAT-Lancet), B6-B8 (HEFI), B9-B12 (FCS).
- [`manuscript_call1.md`](manuscript_call1.md) §3.4 (LLM categorizer), §3.5 (LCA matcher), §3.6 (FPED bridge), §3.8 (AI-MATCH), §3.8.5 (WAFCT), §4.5 (cross-system coherence), §5.1 (S4 / NCI usual-intake), §6.1 (what AI adds + doesn't).
- [`backend/api/services/cnf_recall_24h.py`](backend/api/services/cnf_recall_24h.py) — input source.
- [`backend/api/data/cnf_corpus_embeddings.npz`](backend/api/data/cnf_corpus_embeddings.npz) — embedding source.
- [`backend/api/services/cnf_matcher.py`](backend/api/services/cnf_matcher.py) — `CNFCorpus` loader to reuse.
- [`backend/api/views/hefi_explanations.py`](backend/api/views/hefi_explanations.py) — caveat machinery to reuse.
