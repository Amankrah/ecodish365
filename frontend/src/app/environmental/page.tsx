/**
 * Environmental Impact Landing Page
 *
 * Manuscript-anchored copy. Scope of the current pipeline:
 *   • 3 ReCiPe 2016 v1.1 midpoints actually emitted (Global warming · Land
 *     use · Water consumption) backed by Poore & Nemecek 2018 per-food-group
 *     factors + the AGRIBALYSE 3.2 catalog (2,425 entries).
 *   • LLM-assisted retrieve-then-rank matcher (Zhou 2025; Furrer 2024) maps
 *     CNF / WAFCT foods to AGRIBALYSE entries with audit-logged confidence.
 *   • Uncertainty bands reflect within-product producer variability (P&N
 *     2018), NOT statistical 90 % CI.
 *   • EF 3.1 sensitivity overlay surfaced alongside ReCiPe primary.
 *
 * Out of scope in v1 (documented future work): toxicity / ecotoxicity /
 * particulates / ozone formation per-food; pesticide residue ingestion;
 * regenerative-practice premiums; end-of-life; household preparation.
 */
'use client';

import React from 'react';
import Link from 'next/link';
import {
  Card, CardContent, CardHeader, CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Leaf, Globe, Calculator, BarChart3, Droplets, TreePine,
  DollarSign, Users, BookOpen, ArrowRight, CheckCircle, Target,
  Sparkles, CalendarClock, Camera, AlertTriangle, Sigma,
} from 'lucide-react';

export default function EnvironmentalMainPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-emerald-50">
      {/* Hero */}
      <section className="relative py-16 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center mb-5">
            <Leaf className="h-12 w-12 text-green-500 mr-3" />
            <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Environmental impact (ReCiPe 2016 + AGRIBALYSE 3.2)
            </h1>
          </div>
          <p className="text-lg text-gray-700 max-w-3xl mx-auto mb-5 leading-relaxed">
            Climate, land, and water cost of producing a food, a meal, or a full day&apos;s
            eating — backed by <strong>Poore &amp; Nemecek 2018</strong> per-food-group factors
            and the <strong>AGRIBALYSE 3.2</strong> commodity-level LCA catalog (2,425 entries).
            Foods in the integrated catalog (Canadian Nutrient File + WAFCT 2019) match to
            AGRIBALYSE via an audit-logged LLM-assisted retrieve-then-rank pipeline.
          </p>
          <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-6 text-sm text-amber-900 text-left">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Production-stage only.</strong> Excludes household preparation,
              retail transport, and end-of-life. Uncertainty bands reflect documented
              producer-to-producer variability, not statistical confidence intervals.
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            <Badge className="bg-green-100 text-green-700 px-3 py-1 text-xs">
              <CheckCircle className="h-3 w-3 mr-1" />
              ReCiPe 2016 v1.1
            </Badge>
            <Badge className="bg-blue-100 text-blue-700 px-3 py-1 text-xs">
              <Globe className="h-3 w-3 mr-1" />
              AGRIBALYSE 3.2 (2,425 entries)
            </Badge>
            <Badge className="bg-purple-100 text-purple-700 px-3 py-1 text-xs">
              <Sigma className="h-3 w-3 mr-1" />
              Uncertainty bands
            </Badge>
            <Badge className="bg-amber-100 text-amber-700 px-3 py-1 text-xs">
              <Sparkles className="h-3 w-3 mr-1" />
              EF 3.1 sensitivity overlay
            </Badge>
          </div>
        </div>
      </section>

      {/* Tools */}
      <section className="py-12 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Tools</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Score one food, two foods side-by-side, a full 24-h recall, or all 5 metrics at once.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mb-3">
                  <Calculator className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">Calculate impact</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  Pick foods from the integrated catalog (CNF or WAFCT). Choose perspective (Hierarchist default),
                  basis (per 100 g / per 100 kcal / per 100 g protein / per serving), and country.
                </p>
                <Link href="/environmental/calculate">
                  <Button className="w-full bg-green-600 hover:bg-green-700 text-white" size="sm">
                    Open calculator
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-3">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">Compare foods</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  Side-by-side CO₂ + land + water for two foods. The right tool when asking
                  &quot;beef vs lentils?&quot; — uncertainty bands stop you reading too much into single point estimates.
                </p>
                <Link href="/environmental/compare">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white" size="sm">
                    Compare
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center mb-3">
                  <CalendarClock className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">Score a 24-h recall</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  Log a full day occasion-by-occasion via the recall wizard. Daily totals
                  aggregate by FoodID with masses summed across meals — the right scale for
                  diet-level footprint reporting.
                </p>
                <Link href="/recall-24h?then=environmental">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white" size="sm">
                    Open recall wizard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-3">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">✨ Scorecard</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  See environmental impact alongside HEFI, HENI, HSR, FCS, and dietary pattern
                  on the same food list. One click, all six lenses, consumer-friendly framing.
                </p>
                <Link href="/scorecard">
                  <Button className="w-full bg-amber-600 hover:bg-amber-700 text-white" size="sm">
                    Open Scorecard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* What's actually emitted */}
      <section className="py-14 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Three midpoint indicators (v1)</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              ReCiPe 2016 defines 18 midpoint categories. Our v1 pipeline emits the three
              that have reliable per-food-group literature backing (Poore &amp; Nemecek 2018,
              <em> Science</em> 360:987–992). The remaining 15 are documented future work — we
              do not surface point estimates we cannot defend.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border border-red-200 shadow-sm">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-3">
                  <Globe className="h-6 w-6 text-red-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Global warming</h3>
                <Badge variant="outline" className="text-xs mb-2">kg CO₂-eq</Badge>
                <p className="text-sm text-gray-600 leading-snug">
                  100-year time horizon (GWP100). Includes biogenic CO₂, methane, N₂O,
                  fluorinated gases across the production phase. Beef ≈ 10 kg/100 g;
                  lentils ≈ 0.4 kg/100 g.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-green-200 shadow-sm">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-3">
                  <TreePine className="h-6 w-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Land use</h3>
                <Badge variant="outline" className="text-xs mb-2">m²·yr</Badge>
                <p className="text-sm text-gray-600 leading-snug">
                  Agricultural land occupation × time. Beef ≈ 9 m²·yr/100 g; lettuce ≈
                  0.5 m²·yr/100 g. Excludes land-use-change emissions (separate bucket
                  in some methods).
                </p>
              </CardContent>
            </Card>

            <Card className="border border-blue-200 shadow-sm">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mb-3">
                  <Droplets className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Water consumption</h3>
                <Badge variant="outline" className="text-xs mb-2">m³ (blue-water deprived)</Badge>
                <p className="text-sm text-gray-600 leading-snug">
                  Blue-water consumption weighted by local water-scarcity factor.
                  Varies by crop type, irrigation, and country. Most country-specific
                  factor available in ReCiPe (288 countries).
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-6 bg-white border border-gray-200 rounded-lg p-4 text-sm text-gray-700">
            <strong>Documented but not emitted in v1:</strong> Fine particulate matter
            formation, terrestrial acidification, freshwater &amp; marine eutrophication,
            stratospheric ozone depletion, photochemical ozone formation, fossil / mineral
            resource scarcity, human carcinogenic &amp; non-carcinogenic toxicity,
            terrestrial / freshwater / marine ecotoxicity, ionising radiation. These require
            licensed ecoinvent re-scoring (TODO-CODE-LCA-2). Pesticide residue ingestion,
            regenerative-practice premiums, and end-of-life are categorically out of scope.
          </div>
        </div>
      </section>

      {/* Pipeline capabilities */}
      <section className="py-14 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Pipeline capabilities</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              The same parameters that ReCiPe and AGRIBALYSE expose to researchers
              are surfaced as request fields on{' '}
              <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">POST /api/environmental-impact/</code>.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Four functional units (basis)</h3>
                <p className="text-sm text-gray-600">
                  Per 100 g, per 100 kcal, per 100 g protein, or per serving. <em>Per 100 kcal</em>
                  is default (Poore &amp; Nemecek Panel C basis) — fairest for comparing
                  caloric-density-different foods like cucumber vs pasta. All four are
                  always computed; the chosen basis just picks which one headlines.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Three cultural perspectives</h3>
                <p className="text-sm text-gray-600">
                  ReCiPe&apos;s Individualist / Hierarchist / Egalitarian lenses select different
                  midpoint-to-endpoint conversion factors. <strong>Hierarchist</strong> is
                  default (RIVM convention). Egalitarian inflates the Human Health endpoint
                  ~14× for climate change — useful for sensitivity-of-conclusions reporting.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Country adaptation (5 categories)</h3>
                <p className="text-sm text-gray-600">
                  ReCiPe&apos;s workbook covers country-specific factors for 5 indicators only:
                  water consumption (288 countries), terrestrial acidification (224),
                  freshwater eutrophication (159), photochemical ozone (70), fine PM (66).
                  Toggle <em>consumer perspective</em> between &quot;global&quot; (default,
                  defensible for multi-country supply chains) and &quot;national&quot;.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">EF 3.1 sensitivity overlay</h3>
                <p className="text-sm text-gray-600">
                  Where AGRIBALYSE supplies the food, we also surface the parallel
                  Environmental Footprint 3.1 values — climate aligns directly with ReCiPe;
                  the other 14 EF categories are surfaced in native units as audit /
                  cross-method check, not primary output.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">LLM-assisted matcher (retrieve-then-rank)</h3>
                <p className="text-sm text-gray-600">
                  Each food description → 1,536-dim embedding → top-20 AGRIBALYSE candidates
                  → LLM ranker (gpt-4.1-mini, T = 0). The ranker is constrained to the
                  retrieved set — no free generation, hallucinated Ciqual codes fail at parse
                  time. Confidence ≥ 0.6 uses the matched per-food value; below falls back
                  to the food-group default and flags as such.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Recipe decomposition for composites</h3>
                <p className="text-sm text-gray-600">
                  Borderline matches on composite foods (pizza, stew, casserole) trigger
                  LLM ingredient-level decomposition. Mass-conservation gate (±5 g) +
                  confidence ≥ 0.30 + ≤ 10 % unresolved mass; ingredient masses then
                  mass-weight per-100 g impacts to produce a granular per-food result.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Uncertainty bands (low / central / high)</h3>
                <p className="text-sm text-gray-600">
                  Per indicator. Bands reflect <strong>within-product producer variability</strong>{' '}
                  documented in Poore &amp; Nemecek 2018 (up to 50× spread within a single
                  commodity). They are NOT statistical 90 % CI — they are honest worst /
                  best-case envelopes. Bands surface only for the 3 grounded midpoints.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Monetisation (¢ social cost)</h3>
                <p className="text-sm text-gray-600">
                  Optional overlay: estimated social cost of the food&apos;s climate impact
                  at published SC-CO₂ values. Shown in ¢/serving so a user can compare two
                  meals on a single financial axis. Provenance + the SC-CO₂ value used are
                  audit-logged.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Audience modes */}
      <section className="py-14 px-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Audience-tailored explanations</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Every result emits an explanations block in one of three packs
              (AUDIENCE-CODE-1) — same data, different framing.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <Card className="border-l-4 border-l-blue-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-base">Individual</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 leading-snug">
                  &quot;Climate, land, and water cost of producing this food.&quot; Plain English
                  band (low / moderate / high), interpretation, and mandatory caveat.
                  No methodology math.
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-green-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-base">Researcher</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 leading-snug">
                  Full ReCiPe 2016 v1.1 methodology, perspective audit, per-food matcher
                  confidence + fallback reasons, AGRIBALYSE DQR, EF 3.1 cross-method
                  comparison, P&amp;N 2018 band provenance.
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-purple-600" />
                  <CardTitle className="text-base">Policy</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 leading-snug">
                  Population framing for procurement, taxation, and labeling regulation.
                  Optional monetised SC-CO₂ overlay; country / consumer-perspective notes
                  surfaced explicitly.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* What it is not */}
      <section className="py-14 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              What this is <em>not</em>
            </h2>
            <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
              <li><strong>Not whole-life-cycle.</strong> Production phase only — no household preparation, retail transport, refrigeration, or end-of-life.</li>
              <li><strong>Not statistical CI.</strong> Uncertainty bands reflect documented within-product producer variability (Poore &amp; Nemecek 2018), not statistical 90 % intervals.</li>
              <li><strong>Not toxicity.</strong> ReCiPe&apos;s toxicity and ecotoxicity factors are flagged as provisional (RIVM 2017 §1.3); v1 deliberately omits them rather than report low-confidence numbers.</li>
              <li><strong>Not dietary pesticide risk.</strong> AGRIBALYSE does not track residues; ReCiPe characterises environmental release, not ingestion. Separate question, separate analysis.</li>
              <li><strong>Not regenerative.</strong> AGRIBALYSE 3.2 inventories are conventional-agriculture; regenerative / perennial / carbon-sequestration premiums are not quantified.</li>
              <li><strong>Per-food-group fallback is a known limit.</strong> When the matcher cannot resolve a per-food AGRIBALYSE entry (confidence &lt; 0.6), we fall back to a group default — audit-logged as <code className="text-xs bg-amber-100 px-1 rounded">fallback_reason: group_default</code>. Within-group variance can dominate between-group variance (skim milk vs aged cheddar ~10× on GWP).</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Data + integrations */}
      <section className="py-14 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Food composition databases</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700 space-y-2">
                <p>
                  Environmental scoring runs over the same source-tagged catalog used by HEFI / HENI /
                  HSR / FCS: <strong>CNF 5,691 + WAFCT 1,028 = 6,719</strong> foods. The matcher
                  resolves each food to AGRIBALYSE regardless of source. WAFCT entries (West African
                  staples) inherit environmental scoring transparently — the manuscript &sect;3.8.5
                  notes that environmental impact is unit-agnostic to nutrient analytical method, so
                  no WAFCT-specific caveat surfaces here.
                </p>
                <p>
                  Further composition databases (USDA, EuroFIR, additional regional FCTs) plug into
                  the same source-tagged extension architecture.
                </p>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">LCA reference catalog</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700 space-y-2">
                <p>
                  <strong>AGRIBALYSE 3.2</strong> (ADEME, November 2024) — 2,425 commodity-level
                  entries with dual-namespace storage (ReCiPe-equivalent subset alongside the full
                  16-indicator EF 3.1 set). Quality tracked via Data Quality Rating 1–5; 67 % of
                  entries at DQR ≤ 3. Published errata for 7 known-issue Ciqual codes (eggs 26232,
                  quinoa 25998, etc.) are flagged in the catalog with warnings.
                </p>
                <p>
                  <strong>Poore &amp; Nemecek (2018)</strong> per-food-group meta-analysis grounds
                  the per-100 kcal default basis and the within-product uncertainty bands.
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-6 grid md:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Camera className="h-5 w-5 text-amber-700" />
                  Packaged-food scanner
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700">
                <p>
                  Photograph the NF panel + ingredient list of a packaged product. Multimodal
                  extraction proposes the ingredient set; you confirm; the resulting CNF-resolved
                  composition routes into the environmental scorer (and the other 5 metrics).
                  Methodology-honest: HEFI and HENI were validated on 24-h recall data, NOT
                  single-product point estimates — single-product environmental scoring is
                  exploratory.
                </p>
                <Link href="/scan-product">
                  <Button variant="outline" size="sm" className="mt-3">
                    Scan a product →
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-700" />
                  Cross-metric scorecard
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700">
                <p>
                  Environmental is one of six lenses on the <Link href="/scorecard" className="text-emerald-700 underline">Scorecard</Link>{' '}
                  (HEFI / HENI / HSR / FCS / Environmental / Dietary Pattern). Same food list,
                  one Score-all click, six compact summary cards with audience-appropriate
                  copy. Sustainability decisions rarely live alone — diet quality, healthy-life
                  minutes, and product-level ratings travel with environmental on the same panel.
                </p>
                <Link href="/scorecard">
                  <Button variant="outline" size="sm" className="mt-3">
                    Open Scorecard →
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* References */}
      <section className="py-14 px-6 bg-gradient-to-r from-green-700 to-blue-700">
        <div className="max-w-5xl mx-auto text-white">
          <h2 className="text-2xl font-bold mb-5 text-center">Primary references</h2>
          <div className="grid md:grid-cols-2 gap-5 text-sm">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-5">
              <h3 className="font-semibold mb-2">Method</h3>
              <ul className="space-y-2 list-disc list-inside">
                <li>
                  Huijbregts M.A.J. et al. (2017). ReCiPe 2016 v1.1 — A harmonised life cycle
                  impact assessment method at midpoint and endpoint level. <em>Int. J. LCA</em>{' '}
                  22, 138–147.
                </li>
                <li>
                  RIVM (2017). <em>ReCiPe 2016 v1.1 Report I: Characterisation</em>, Report
                  2016-0104a.
                </li>
                <li>
                  Poore J. &amp; Nemecek T. (2018). Reducing food&apos;s environmental impacts
                  through producers and consumers. <em>Science</em> 360, 987–992.
                </li>
              </ul>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-5">
              <h3 className="font-semibold mb-2">Data + matcher</h3>
              <ul className="space-y-2 list-disc list-inside">
                <li>
                  ADEME (2024). <em>AGRIBALYSE® 3.2 — Programme de référence sur les
                  indicateurs d&apos;impacts environnementaux</em>. doi:10.57745/XTENSJ.
                </li>
                <li>
                  Furrer C. et al. (2024). Interlinking environmental and food composition
                  databases. <em>J. Cleaner Prod.</em> 470, 143198.
                </li>
                <li>
                  Zhou Z. et al. (2025). NutriRAG — retrieve-then-rank food matching with LLMs.
                  doi:10.1101/2025.03.19.25324268.
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6 bg-gray-900 text-white text-center">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Ready to score an impact?</h2>
          <p className="text-base mb-6 opacity-90 max-w-2xl mx-auto">
            Single food, full meal, or 24-h recall — same pipeline, audience-appropriate
            framing, honest about what we know and what we don&apos;t.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/environmental/calculate">
              <Button size="lg" className="bg-green-600 hover:bg-green-700">
                <Calculator className="mr-2 h-5 w-5" />
                Calculate impact
              </Button>
            </Link>
            <Link href="/recall-24h?then=environmental">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700">
                <CalendarClock className="mr-2 h-5 w-5" />
                Score a 24-h recall
              </Button>
            </Link>
            <Link href="/scorecard">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-gray-900">
                <Sparkles className="mr-2 h-5 w-5" />
                Cross-metric Scorecard
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
