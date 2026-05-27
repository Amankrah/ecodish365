/**
 * EcoDish365 — main landing page.
 *
 * Manuscript-anchored copy. Every claim here is backed by what the platform
 * actually ships today (HEFI Brassard 2022; HENI Stylianou 2021; HSR HSRAC v9;
 * FCS-10 Barrett 2025; ReCiPe 2016 v1.1 + AGRIBALYSE 3.2; Mediterranean / DASH /
 * Vegetarian / Vegan / CFG-Healthy / West African Staple / EAT-Lancet
 * dietary-pattern prototypes; CNF 5,691 + WAFCT 1,028 foods; audience-aware
 * explanations under AUDIENCE-CODE-1; Scorecard SCORECARD-1; multimodal
 * packaged-food scanner PKG-IMG-1/2.x).
 */
'use client';

import React from 'react';
import Link from 'next/link';
import {
  ChartBarIcon,
  BeakerIcon,
  GlobeAltIcon,
  UserGroupIcon,
  ArrowRightIcon,
  ScaleIcon,
  DocumentChartBarIcon,
  HeartIcon,
  SparklesIcon,
  CameraIcon,
  CalendarDaysIcon,
  BookmarkIcon,
  MapPinIcon,
  ExclamationTriangleIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';

// ---------------------------------------------------------------------------
// The six scoring lenses (HEFI-2019 / HENI / HSR / FCS-10 / Environmental /
// Dietary pattern). One-line meaning derived from the manuscript's
// user-facing copy and each landing page's individual-mode caveat.
// ---------------------------------------------------------------------------

const lenses = [
  {
    emoji: '🥗',
    name: 'HEFI-2019',
    tagline: 'Adherence to Canada\'s Food Guide',
    meaning: 'Score how well a 24-h recall day aligns with Canada\'s Food Guide. 0–80 across 10 components.',
    citation: 'Brassard 2022 · APNM',
    href: '/hefi',
    accent: 'from-green-500 to-emerald-600',
  },
  {
    emoji: '🧬',
    name: 'HENI',
    tagline: 'Minutes of healthy life per serving',
    meaning: 'Net population-marginal healthy-life-minutes added or subtracted, from 15 GBD dietary risk factors.',
    citation: 'Stylianou 2021 · Nature Food',
    href: '/heni',
    accent: 'from-purple-500 to-violet-600',
  },
  {
    emoji: '⭐',
    name: 'HSR (HSRAC v9)',
    tagline: 'Per-product nutrient profiling',
    meaning: 'Rate a packaged product 0.5–5 stars within its own HSR category — designed for label comparison.',
    citation: 'HSRAC Implementation Guide v9',
    href: '/hsr',
    accent: 'from-amber-500 to-orange-600',
  },
  {
    emoji: '🧭',
    name: 'FCS-10 / i.FCS',
    tagline: 'Resemblance to longer-life food patterns',
    meaning: 'Score a food (1–10) or full day (1–100, energy-weighted) on 18 attributes across 9 health-relevant domains.',
    citation: 'Barrett 2025 · AJCN',
    href: '/fcs',
    accent: 'from-blue-500 to-cyan-600',
  },
  {
    emoji: '🌍',
    name: 'Environmental (ReCiPe 2016)',
    tagline: 'Climate · land · water of producing this food',
    meaning: 'Production-stage LCA across 3 grounded midpoints with uncertainty bands. ReCiPe + AGRIBALYSE 3.2.',
    citation: 'Huijbregts 2017; Poore & Nemecek 2018; ADEME',
    href: '/environmental',
    accent: 'from-emerald-500 to-teal-600',
  },
  {
    emoji: '🎯',
    name: 'Dietary pattern',
    tagline: 'Mediterranean · DASH · Vegan · West African …',
    meaning: 'Which canonical pattern does today\'s day-vector most resemble? Cosine similarity vs 8 literature-anchored prototypes.',
    citation: 'Trichopoulou 2003; Sacks 2001; Orlich 2013; Willett 2019',
    href: '/dietary-pattern',
    accent: 'from-rose-500 to-pink-600',
  },
];

// ---------------------------------------------------------------------------
// Cross-cutting tools — the entry points that feed the six scoring lenses
// above.
// ---------------------------------------------------------------------------

const tools = [
  {
    emoji: '✨',
    name: 'Scorecard (all metrics)',
    description: 'See all six lenses for the same food list in one consumer-friendly view. One click, six compact summary cards.',
    href: '/scorecard',
    highlight: true,
  },
  {
    emoji: '🍽️',
    name: '24-h Dietary recall wizard',
    description: 'Build a full day occasion-by-occasion (breakfast, snack, lunch, …). Decomposes each meal into CNF/WAFCT foods, then routes to any scorer.',
    href: '/recall-24h',
  },
  {
    emoji: '📷',
    name: 'Packaged-food scanner',
    description: '1–3 photos of a packaged label → AI extracts the Nutrition Facts panel + ingredient list → you confirm → scored across all metrics.',
    href: '/scan-product',
  },
  {
    emoji: '📚',
    name: 'Recall history',
    description: 'Save recall days; reload one or average across N days. Multi-day averaging softens the single-day caveat for usual-eating claims.',
    href: '/recall-history',
  },
  {
    emoji: '🔍',
    name: 'CNF + WAFCT explorer',
    description: 'Search the integrated food-composition catalog (6,719 foods). AI-enhanced search supports synonyms, French, and compound queries.',
    href: '/cnf',
  },
  {
    emoji: '👥',
    name: 'My meals',
    description: 'Create reusable meal templates and re-score them under any lens as the codebase evolves.',
    href: '/meals',
  },
];

// ---------------------------------------------------------------------------
// Three-audience block.
// ---------------------------------------------------------------------------

const audiences = [
  {
    name: 'Individuals',
    description: 'Plain-language interpretation, mandatory caveats, no methodology jargon. Score a meal, a packaged product, or a day and get an honest read.',
    icon: HeartIcon,
  },
  {
    name: 'Researchers',
    description: 'Full methodology audit per scorer: per-component breakdowns, audience-aware citations, AGRIBALYSE DQR, matcher confidence, EF 3.1 sensitivity overlay.',
    icon: BeakerIcon,
  },
  {
    name: 'Policy makers',
    description: 'Population framing for procurement, taxation, labelling, and food-environment surveillance. Monetised social cost overlay where defensible.',
    icon: UserGroupIcon,
  },
];

// ---------------------------------------------------------------------------
// Realistic platform stats — replace the marketing-fluff numbers.
// ---------------------------------------------------------------------------

const stats = [
  { value: '6,719', label: 'Foods in catalog', sub: 'CNF 5,691 + WAFCT 1,028' },
  { value: '6', label: 'Scoring lenses', sub: 'HEFI · HENI · HSR · FCS · Env. · Pattern' },
  { value: '2,425', label: 'AGRIBALYSE LCA entries', sub: 'Commodity-level inventories (ADEME 2024)' },
  { value: '3', label: 'Audience modes', sub: 'Individual · Researcher · Policy' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-emerald-50 py-16 sm:py-24">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-6xl font-bold tracking-tight">
            <span className="text-gradient">EcoDish365</span>
          </h1>
          <p className="mt-3 text-lg sm:text-xl font-medium text-gray-700">
            Score a food, a meal, or a full day across six published research lenses — in one place.
          </p>
          <p className="mt-5 text-base sm:text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
            HEFI-2019 (Brassard 2022) · HENI healthy-life-minutes (Stylianou 2021) ·
            Health Star Rating (HSRAC v9) · FCS-10 / i.FCS (Barrett 2025) ·
            ReCiPe 2016 LCA (AGRIBALYSE 3.2) · Dietary-pattern resemblance
            (Mediterranean, DASH, Vegan, West African Staple, …). Every result
            comes with audience-aware explanations and the caveats the literature requires.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg text-white bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-700 hover:to-blue-700 transition shadow-lg hover:shadow-xl"
            >
              <SparklesIcon className="mr-2 w-5 h-5" />
              Open the Scorecard
              <ArrowRightIcon className="ml-2 w-5 h-5" />
            </Link>
            <Link
              href="/recall-24h"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition shadow-sm"
            >
              <CalendarDaysIcon className="mr-2 w-5 h-5" />
              Log a 24-h recall
            </Link>
            <Link
              href="/scan-product"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition shadow-sm"
            >
              <CameraIcon className="mr-2 w-5 h-5" />
              Scan a product
            </Link>
          </div>

          <div className="mt-6 inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm text-amber-900 text-left">
            <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Research-grade, consumer-friendly.</strong> The platform reports
              what each metric was designed to measure — and the limits the original papers
              state. We do not invent thresholds or fold disagreement into a single composite score.
            </span>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 bg-white border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold text-emerald-600">
                  {s.value}
                </div>
                <div className="mt-1 text-sm font-medium text-gray-800">{s.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{s.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Six lenses */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Six published lenses</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Each metric answers a different question about the same foods. No single
              score wins — the right answer depends on what you&apos;re asking.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {lenses.map((l) => (
              <Link
                key={l.name}
                href={l.href}
                className="bg-white rounded-2xl border border-gray-200 p-5 hover:shadow-lg hover:-translate-y-0.5 transition group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-11 h-11 rounded-lg bg-gradient-to-br ${l.accent} flex items-center justify-center text-xl shadow-sm`} aria-hidden="true">
                    {l.emoji}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{l.name}</h3>
                    <p className="text-xs text-gray-600">{l.tagline}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-700 leading-snug mb-2">
                  {l.meaning}
                </p>
                <p className="text-[11px] text-gray-500 italic">{l.citation}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-blue-700 group-hover:text-blue-900">
                  Open {l.name.split(' ')[0]} →
                </div>
              </Link>
            ))}
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg text-white bg-emerald-600 hover:bg-emerald-700"
            >
              <SparklesIcon className="mr-2 w-4 h-4" />
              See all six at once on the Scorecard
            </Link>
          </div>
        </div>
      </section>

      {/* Cross-cutting tools */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Cross-cutting tools</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Acquisition surfaces and shared utilities. They feed every scoring lens via
              the same source-tagged active food list.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {tools.map((t) => (
              <Link
                key={t.name}
                href={t.href}
                className={`rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition group border ${
                  t.highlight
                    ? 'bg-gradient-to-br from-emerald-50 to-blue-50 border-emerald-300'
                    : 'bg-white border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="text-2xl" aria-hidden="true">{t.emoji}</div>
                  <h3 className="text-base font-semibold text-gray-900">{t.name}</h3>
                </div>
                <p className="text-sm text-gray-700 leading-snug">
                  {t.description}
                </p>
                <div className="mt-3 flex items-center text-sm font-medium text-blue-700 group-hover:text-blue-900">
                  Open →
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Food databases */}
      <section className="py-14 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                <MapPinIcon className="w-6 h-6 text-blue-700" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">A multi-database food catalog</h2>
                <p className="text-sm text-gray-700 mb-4">
                  Foods are stored under a source-tagged extension architecture so additional
                  composition databases plug in without changing scoring code. WAFCT was the
                  first such extension (May 2026); the same pattern carries any further FCT.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active · authoritative</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
                    <div className="text-xs text-gray-600 mt-0.5">5,691 foods · Health Canada</div>
                  </div>
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active · extension</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
                    <div className="text-xs text-gray-600 mt-0.5">1,028 West African foods · Vincent 2019 · per-source caveat surfaces analytical-method deltas</div>
                  </div>
                  <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
                    <div className="text-sm font-medium text-gray-700 mt-1">Further composition tables</div>
                    <div className="text-xs mt-0.5">USDA / EuroFIR / additional regional FCTs via the same source-tagged extension.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Audience modes */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Three audiences, one set of computations</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              Every scorer toggles between three explanation packs (AUDIENCE-CODE-1). The
              numbers are the same; the framing changes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {audiences.map((a) => (
              <div key={a.name} className="text-center">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <a.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{a.name}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {a.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Honest framing */}
      <section className="py-14 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              What the platform is <em>not</em>
            </h2>
            <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
              <li><strong>Not clinical advice.</strong> Population-anchored scoring; not a personal diagnosis or prescription.</li>
              <li><strong>Not a single composite score.</strong> The six lenses answer different questions — we report all six rather than fold disagreement into one number.</li>
              <li><strong>Not whole-life-cycle environmental.</strong> ReCiPe + AGRIBALYSE cover the production phase; household preparation and end-of-life are out of scope in v1.</li>
              <li><strong>Not yet Canadian-anchored everywhere.</strong> HEFI is Canadian by design; HENI uses US GBD epidemiology with Canadian portability documented as future work; FCS-10 is anchored to NHANES with Canadian validation pending.</li>
              <li><strong>No user account, no health-data collection.</strong> Recall history and active food list live in browser storage only; no auth, no server-side personal data.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Primary references */}
      <section className="py-14 bg-white border-t border-gray-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-6">Primary references</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-700">
            <ul className="space-y-1.5 list-disc list-inside">
              <li>HSRAC, <em>HSR Implementation Guide v9</em> (Dec 2025); Shahid 2020 <em>Nutrients</em> 12, 1791.</li>
              <li>Brassard et al. 2022a/b. HEFI-2019 development &amp; evaluation. <em>APNM</em> 47, 595–610 / 582–594.</li>
              <li>Stylianou et al. 2021. HENI healthy-life-minutes framework. <em>Nature Food</em> 2, 616–627.</li>
              <li>Barrett et al. 2025. FCS-10 simplification. <em>AJCN</em>. (Mozaffarian 2021 origin; O&apos;Hearn 2022 mortality validation).</li>
            </ul>
            <ul className="space-y-1.5 list-disc list-inside">
              <li>Huijbregts et al. 2017. ReCiPe 2016 v1.1. <em>Int. J. LCA</em> 22, 138–147. RIVM 2016-0104a (2017).</li>
              <li>Poore &amp; Nemecek 2018. Food supply-chain LCI meta-analysis. <em>Science</em> 360, 987–992.</li>
              <li>ADEME 2024. AGRIBALYSE 3.2. doi:10.57745/XTENSJ. Furrer et al. 2024 LCI interlinking <em>J. Cleaner Prod.</em> 470:143198.</li>
              <li>Vincent et al. 2019. WAFCT 2019 (FAO/INFOODS). Trichopoulou 2003 / Sacks 2001 / Orlich 2013 / Willett 2019 (dietary-pattern prototypes).</li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-to-r from-emerald-600 to-blue-600">
        <div className="max-w-5xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Start scoring
          </h2>
          <p className="text-base text-emerald-50 mb-8 max-w-2xl mx-auto">
            Score a single product, a homemade dish, or a full day&apos;s eating — under
            every published lens, in plain English, with the caveats the literature requires.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-emerald-700 bg-white hover:bg-gray-50 shadow"
            >
              <SparklesIcon className="mr-2 w-5 h-5" />
              ✨ Scorecard
            </Link>
            <Link
              href="/recall-24h"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-white border border-white hover:bg-white/10"
            >
              <CalendarDaysIcon className="mr-2 w-5 h-5" />
              24-h recall
            </Link>
            <Link
              href="/scan-product"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-white border border-white hover:bg-white/10"
            >
              <CameraIcon className="mr-2 w-5 h-5" />
              Scan a product
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
