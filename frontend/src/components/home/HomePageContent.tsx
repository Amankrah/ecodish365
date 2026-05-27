'use client';

import React from 'react';
import Link from 'next/link';
import {
  BeakerIcon,
  UserGroupIcon,
  ArrowRightIcon,
  HeartIcon,
  SparklesIcon,
  CameraIcon,
  CalendarDaysIcon,
  ExclamationTriangleIcon,
  MapPinIcon,
} from '@heroicons/react/24/outline';

const lenses = [
  {
    emoji: '🥗',
    name: 'HEFI-2019',
    tagline: 'Adherence to Canada\'s Food Guide',
    meaning: 'How well does a day\'s eating line up with Canada\'s Food Guide? Scored 0–80 across 10 components.',
    citation: 'Brassard 2022, APNM',
    href: '/hefi',
    linkLabel: 'Open HEFI-2019',
    accent: 'from-green-500 to-emerald-600',
  },
  {
    emoji: '🧬',
    name: 'HENI',
    tagline: 'Minutes of healthy life per serving',
    meaning: 'Translates a food into minutes of healthy life gained or lost, drawn from 15 diet-related risks in the Global Burden of Disease study.',
    citation: 'Stylianou 2021, Nature Food',
    href: '/heni',
    linkLabel: 'Open HENI',
    accent: 'from-purple-500 to-violet-600',
  },
  {
    emoji: '⭐',
    name: 'HSR (HSRAC v9)',
    tagline: 'A star rating for packaged products',
    meaning: 'Rates a packaged product from 0.5 to 5 stars against others in its own category. Built for comparing products on the shelf.',
    citation: 'HSRAC Implementation Guide v9',
    href: '/hsr',
    linkLabel: 'Open HSR',
    accent: 'from-amber-500 to-orange-600',
  },
  {
    emoji: '🧭',
    name: 'Food Compass',
    tagline: 'How closely a food tracks longer-life eating patterns',
    meaning: 'Scores every food on a single 1 to 100 scale across nine areas of nutrition. Higher means the food more closely resembles patterns linked to longer, healthier lives in research studies.',
    citation: 'Mozaffarian 2021, Nature Food',
    href: '/fcs',
    linkLabel: 'Open Food Compass',
    accent: 'from-blue-500 to-cyan-600',
  },
  {
    emoji: '🌍',
    name: 'Environmental (ReCiPe 2016)',
    tagline: 'The climate, land, and water cost of producing this food',
    meaning: 'A production-stage footprint with honest uncertainty ranges, built on ReCiPe 2016 and AGRIBALYSE 3.2.',
    citation: 'Huijbregts 2017; Poore & Nemecek 2018; ADEME',
    href: '/environmental',
    linkLabel: 'Open Environmental',
    accent: 'from-emerald-500 to-teal-600',
  },
  {
    emoji: '🎯',
    name: 'Dietary pattern',
    tagline: 'Mediterranean, DASH, Vegan, West African, and more',
    meaning: 'Which well-studied eating pattern does your day most resemble? We compare it against 8 patterns drawn from the research.',
    citation: 'Trichopoulou 2003; Sacks 2001; Orlich 2013; Willett 2019',
    href: '/dietary-pattern',
    linkLabel: 'Open Dietary',
    accent: 'from-rose-500 to-pink-600',
  },
];

const tools = [
  {
    emoji: '✨',
    name: 'Scorecard (all metrics)',
    description: 'See all six lenses for the same food list in one clear view. One click, six compact summary cards.',
    href: '/scorecard',
    highlight: true,
  },
  {
    emoji: '🍽️',
    name: '24-h dietary recall wizard',
    description: 'Build a full day, occasion by occasion: breakfast, snack, lunch, and so on. Each meal breaks down into its individual foods, then you can score the whole day under any lens.',
    href: '/recall-24h',
  },
  {
    emoji: '📷',
    name: 'Packaged-food scanner',
    description: 'Snap one to three photos of a label. The app reads the Nutrition Facts panel and ingredient list, you confirm, and the product is scored across every lens.',
    href: '/scan-product',
  },
  {
    emoji: '📚',
    name: 'Recall history',
    description: 'Save your recall days, then reload one or average across several. Averaging gives a truer picture of how you usually eat than any single day can.',
    href: '/recall-history',
  },
  {
    emoji: '🔍',
    name: 'CNF + WAFCT explorer',
    description: 'Search the full food catalogue of 6,719 foods. Smart search understands synonyms, French, and compound queries.',
    href: '/cnf',
  },
  {
    emoji: '👥',
    name: 'My meals',
    description: 'Save the meals you eat often and re-score them under any lens whenever you like.',
    href: '/meals',
  },
];

const audiences = [
  {
    name: 'Individuals',
    description: 'Plain-language interpretation with the caveats that matter and no methodology jargon. Score a meal, a packaged product, or a day, and get an honest read.',
    icon: HeartIcon,
  },
  {
    name: 'Researchers',
    description: 'A full methodology audit for every score: component-by-component breakdowns, citations, data-quality ratings, matcher confidence, and sensitivity overlays.',
    icon: BeakerIcon,
  },
  {
    name: 'Policy makers',
    description: 'Population-level framing for procurement, taxation, labelling, and food-environment surveillance, with a monetised social-cost overlay where the evidence supports it.',
    icon: UserGroupIcon,
  },
];

const stats = [
  { value: '6,719', label: 'Foods in catalogue', sub: 'Canadian Nutrient File plus the West African Food Composition Table' },
  { value: '6', label: 'Scoring lenses', sub: 'HEFI, HENI, HSR, FCS, Environmental, Dietary pattern' },
  { value: '2,425', label: 'Environmental inventory entries', sub: 'AGRIBALYSE 3.2, ADEME 2024' },
  { value: '3', label: 'Ways to read every score', sub: 'Individual, Researcher, Policy' },
];

export default function HomePageContent() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-emerald-50 py-16 sm:py-24">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-gray-900 leading-tight">
            Is this food good for you, and for the planet?
          </h1>
          <p className="mt-6 text-base sm:text-lg text-gray-700 max-w-3xl mx-auto leading-relaxed">
            Score a single product, a homemade dish, or a whole day of eating against six published
            research measures, all in one place. Every result is explained in plain language and
            carries the limits the original studies set. No invented grades, and no single number
            pretending to settle the question.
          </p>
          <p className="mt-4 text-sm text-gray-500 max-w-3xl mx-auto leading-relaxed">
            HEFI-2019 (Brassard 2022), HENI healthy-life-minutes (Stylianou 2021), Health Star Rating
            (HSRAC v9), Food Compass (Mozaffarian 2021), ReCiPe 2016 LCA (AGRIBALYSE 3.2), and
            dietary-pattern resemblance across Mediterranean, DASH, Vegan, West African staple, and more.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg text-white bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-700 hover:to-blue-700 transition shadow-lg hover:shadow-xl"
            >
              <SparklesIcon className="mr-2 w-5 h-5" aria-hidden="true" />
              Open the Scorecard
              <ArrowRightIcon className="ml-2 w-5 h-5" aria-hidden="true" />
            </Link>
            <Link
              href="/recall-24h"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition shadow-sm"
            >
              <CalendarDaysIcon className="mr-2 w-5 h-5" aria-hidden="true" />
              Log a 24-h recall
            </Link>
            <Link
              href="/scan-product"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition shadow-sm"
            >
              <CameraIcon className="mr-2 w-5 h-5" aria-hidden="true" />
              Scan a product
            </Link>
          </div>

          <div className="mt-6 inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm text-amber-900 text-left">
            <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <span>
              <strong>Research-grade, consumer-friendly.</strong> The platform reports what each
              metric was designed to measure, and the limits the original papers state. We do not
              invent thresholds or fold disagreement into a single composite score.
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
                <div className="text-3xl sm:text-4xl font-bold text-emerald-600">{s.value}</div>
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
              Each measure answers a different question about the same food. No single score wins.
              The right answer depends on what you are asking.
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
                  <div
                    className={`w-11 h-11 rounded-lg bg-gradient-to-br ${l.accent} flex items-center justify-center text-xl shadow-sm`}
                    aria-hidden="true"
                  >
                    {l.emoji}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{l.name}</h3>
                    <p className="text-xs text-gray-600 italic">{l.tagline}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-700 leading-snug mb-2">{l.meaning}</p>
                <p className="text-[11px] text-gray-500">{l.citation}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-blue-700 group-hover:text-blue-900">
                  {l.linkLabel} →
                </div>
              </Link>
            ))}
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg text-white bg-emerald-600 hover:bg-emerald-700"
            >
              <SparklesIcon className="mr-2 w-4 h-4" aria-hidden="true" />
              See all six at once on the Scorecard
            </Link>
          </div>
        </div>
      </section>

      {/* Ways to get started */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Ways to get started</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Different ways to bring food into the platform. However you start, it lands in the
              same food list and can be scored under any of the six lenses.
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
                <p className="text-sm text-gray-700 leading-snug">{t.description}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-blue-700 group-hover:text-blue-900">
                  Open →
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Food catalogue */}
      <section className="py-14 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                <MapPinIcon className="w-6 h-6 text-blue-700" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">A multi-database food catalogue</h2>
                <p className="text-sm text-gray-700 mb-4">
                  New food-composition databases can be added without changing any of the scoring,
                  so the catalogue keeps growing. The West African Food Composition Table was the
                  first addition in May 2026, and other regional databases can follow the same way.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active, authoritative</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
                    <div className="text-xs text-gray-600 mt-0.5">5,691 foods, Health Canada</div>
                  </div>
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active, extension</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
                    <div className="text-xs text-gray-600 mt-0.5">1,028 West African foods, Vincent 2019. Each source keeps its own notes, so differences in how foods were measured stay visible.</div>
                  </div>
                  <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
                    <div className="text-sm font-medium text-gray-700 mt-1">Further composition tables</div>
                    <div className="text-xs mt-0.5">USDA, EuroFIR, and other regional tables can plug in the same way.</div>
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
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Three audiences, one set of numbers</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              Every score can be read in three ways. The numbers never change; the explanation does.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {audiences.map((a) => (
              <div key={a.name} className="text-center">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <a.icon className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{a.name}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{a.description}</p>
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
              <ExclamationTriangleIcon className="w-5 h-5" aria-hidden="true" />
              What the platform is <em>not</em>
            </h2>
            <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
              <li><strong>Not clinical advice.</strong> Scoring is population-anchored, not a personal diagnosis or prescription.</li>
              <li><strong>Not a single composite score.</strong> The six lenses answer different questions, so we report all six rather than fold disagreement into one number.</li>
              <li><strong>Not a whole-life-cycle footprint.</strong> ReCiPe and AGRIBALYSE cover the production phase. Household preparation and end-of-life are out of scope in this version.</li>
              <li><strong>Not yet Canadian-anchored everywhere.</strong> HEFI is Canadian by design. HENI uses US Global Burden of Disease epidemiology, with Canadian portability noted as future work, and Food Compass is anchored to NHANES with Canadian validation still pending.</li>
              <li><strong>No account, no health-data collection.</strong> Your recall history and active food list live in your browser only. There is no login and no personal data stored on our servers.</li>
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
              <li>HSRAC, <em>HSR Implementation Guide v9</em> (Dec 2025); Shahid 2020, <em>Nutrients</em> 12, 1791.</li>
              <li>Brassard et al. 2022a/b. HEFI-2019 development and evaluation. <em>APNM</em> 47, 595–610 / 582–594.</li>
              <li>Stylianou et al. 2021. HENI healthy-life-minutes framework. <em>Nature Food</em> 2, 616–627.</li>
              <li>Mozaffarian et al. 2021. Food Compass nutrient profiling system. <em>Nature Food</em> 2, 809–818. O&apos;Hearn et al. 2022 mortality validation, <em>Nature Communications</em> 13, 7066.</li>
            </ul>
            <ul className="space-y-1.5 list-disc list-inside">
              <li>Huijbregts et al. 2017. ReCiPe 2016 v1.1. <em>Int. J. LCA</em> 22, 138–147. RIVM 2016-0104a (2017).</li>
              <li>Poore &amp; Nemecek 2018. Food supply-chain LCI meta-analysis. <em>Science</em> 360, 987–992.</li>
              <li>ADEME 2024. AGRIBALYSE 3.2. doi:10.57745/XTENSJ. Furrer et al. 2024 LCI interlinking, <em>J. Cleaner Prod.</em> 470:143198.</li>
              <li>Vincent et al. 2019. WAFCT 2019 (FAO/INFOODS). Dietary-pattern prototypes from Trichopoulou 2003, Sacks 2001, Orlich 2013, Willett 2019.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-to-r from-emerald-600 to-blue-600">
        <div className="max-w-5xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Start scoring</h2>
          <p className="text-base text-emerald-50 mb-8 max-w-2xl mx-auto">
            Score a single product, a homemade dish, or a full day&apos;s eating. Every published
            lens, in plain English, with the caveats the literature requires.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-emerald-700 bg-white hover:bg-gray-50 shadow"
            >
              Scorecard
            </Link>
            <Link
              href="/recall-24h"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-white border border-white hover:bg-white/10"
            >
              24-h recall
            </Link>
            <Link
              href="/scan-product"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-white border border-white hover:bg-white/10"
            >
              Scan a product
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
