'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { CNFApiService } from '@/lib/api';
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
  BookOpenIcon,
  StarIcon,
  GlobeAltIcon,
  MagnifyingGlassIcon,
  BookmarkSquareIcon,
} from '@heroicons/react/24/outline';
import { Salad, Dna, Compass, Target, Utensils } from 'lucide-react';
import type { ComponentType, SVGProps } from 'react';

type IconType = ComponentType<SVGProps<SVGSVGElement>>;

type LensCard = {
  icon: IconType;
  name: string;
  tagline: string;
  meaning: string;
  citation: string;
  href: string;
  linkLabel: string;
};

const lenses: LensCard[] = [
  {
    icon: Salad,
    name: 'Healthy eating',
    tagline: 'How well you match Canada\'s Food Guide',
    meaning: 'Scores a day of eating from 0 to 80 across vegetables, grains, protein, drinks, and more.',
    citation: 'Brassard 2022, APNM',
    href: '/hefi',
    linkLabel: 'Open healthy eating score',
  },
  {
    icon: Dna,
    name: 'Health impact',
    tagline: 'Minutes of healthy life per serving',
    meaning: 'Estimates minutes of healthy life gained or lost from one serving, based on long-term disease research.',
    citation: 'Stylianou 2021, Nature Food',
    href: '/heni',
    linkLabel: 'Open health impact',
  },
  {
    icon: StarIcon,
    name: 'Health Star Rating',
    tagline: 'Stars for packaged products',
    meaning: 'Rates a packaged product from 0.5 to 5 stars against others in the same category on the shelf.',
    citation: 'HSRAC Implementation Guide v9',
    href: '/hsr',
    linkLabel: 'Open star ratings',
  },
  {
    icon: Compass,
    name: 'Food Compass',
    tagline: 'One score across all food types',
    meaning: 'Grades every food from 1 to 100 on nutrition and processing. Higher scores align with eating patterns linked to longer life in research.',
    citation: 'Mozaffarian 2021, Nature Food',
    href: '/fcs',
    linkLabel: 'Open Food Compass',
  },
  {
    icon: GlobeAltIcon,
    name: 'Environmental impact',
    tagline: 'Climate, land, and water',
    meaning: 'Estimates the climate, land, and water needed to produce your food, with honest uncertainty ranges.',
    citation: 'Poore & Nemecek 2018; Mekonnen & Hoekstra',
    href: '/environmental',
    linkLabel: 'Open environmental impact',
  },
  {
    icon: Target,
    name: 'Dietary pattern',
    tagline: 'Mediterranean, DASH, and more',
    meaning: 'Shows which familiar eating style your day most closely matches, from eight patterns in the research.',
    citation: 'Trichopoulou 2003; Sacks 2001; Orlich 2013',
    href: '/dietary-pattern',
    linkLabel: 'Open eating styles',
  },
];

type ToolCard = {
  icon: IconType;
  name: string;
  description: string;
  href: string;
  highlight?: boolean;
};

const tools: ToolCard[] = [
  {
    icon: SparklesIcon,
    name: 'All scores',
    description: 'See healthy eating, health impact, stars, Food Compass, environment, and eating style for the same food list in one view.',
    href: '/scorecard',
    highlight: true,
  },
  {
    icon: Utensils,
    name: 'Food diary',
    description: 'Log a full day meal by meal: breakfast, snacks, lunch, and dinner. Each meal breaks into individual foods you can score under any measure.',
    href: '/recall-24h',
  },
  {
    icon: CameraIcon,
    name: 'Scan a product',
    description: 'Photograph a nutrition label, confirm the details, and score the product across every measure.',
    href: '/scan-product',
  },
  {
    icon: BookmarkSquareIcon,
    name: 'Saved days',
    description: 'Save logged days and revisit them, or average several days together for a truer picture of how you usually eat.',
    href: '/recall-history',
  },
  {
    icon: MagnifyingGlassIcon,
    name: 'Food search',
    description: 'Search over twenty-four thousand foods from Canadian, West African, US, and French databases. Smart search understands synonyms and everyday names.',
    href: '/cnf',
  },
  {
    icon: UserGroupIcon,
    name: 'My meals',
    description: 'Save the meals you eat often and re-score them under any lens whenever you like.',
    href: '/meals',
  },
];

const audiences = [
  {
    name: 'Researchers',
    description: 'A full methodology audit for every score: component-by-component breakdowns, citations, data-quality ratings, matcher confidence, and sensitivity overlays.',
    icon: BeakerIcon,
    cta: { label: 'Open the research hub', href: '/research' },
  },
  {
    name: 'Policy makers',
    description: 'Population-level framing for procurement, taxation, labelling, and food-environment surveillance, with a monetised social-cost overlay where the evidence supports it.',
    icon: UserGroupIcon,
    cta: { label: 'Open the policy hub', href: '/policy' },
  },
  {
    name: 'Individuals',
    description: 'Plain-language interpretation with the caveats that matter and no methodology jargon. Score a meal, a packaged product, or a day, and get an honest read.',
    icon: HeartIcon,
    cta: { label: 'Open the individuals hub', href: '/me' },
  },
];

const staticStats = [
  { value: '6+', label: 'Published lenses', sub: 'HEFI, HENI, HSR, FCS, Environmental, Dietary pattern, with more landing.' },
  { value: '2,425', label: 'Environmental inventory entries', sub: 'AGRIBALYSE 3.2, ADEME 2024' },
  { value: '3', label: 'Ways to read every score', sub: 'Researcher, Policy, Individual' },
];

const formatNumber = (num: number) => new Intl.NumberFormat().format(num);

export default function HomePageContent() {
  const [foodCount, setFoodCount] = useState<number | null>(null);

  useEffect(() => {
    CNFApiService.getDatabaseStatistics()
      .then((data) => setFoodCount(data.food_count))
      .catch((error) => {
        console.error('Failed to load catalogue food count:', error);
      });
  }, []);

  const stats = [
    {
      value: foodCount != null ? formatNumber(foodCount) : '—',
      label: 'Foods in catalogue',
      sub: 'Canadian Nutrient File, West African Food Composition Table, USDA FoodData Central, and ANSES CIQUAL 2025',
    },
    ...staticStats,
  ];

  return (
    <div className="min-h-screen">
      {/* Hero — research-led */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-emerald-50 py-16 sm:py-24">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-gray-900 leading-tight">
            A unified environmental&ndash;nutrition platform.
          </h1>
          <p className="mt-6 text-base sm:text-lg text-gray-700 max-w-3xl mx-auto leading-relaxed">
            Score any food, meal, or 24-hour record across every published research lens, on one
            substrate, across continents. Versioned. Citeable. Reproducible.
          </p>
          <p className="mt-4 text-sm text-gray-500 max-w-3xl mx-auto leading-relaxed">
            Published measures cover healthy eating, health impact, product stars, Food Compass,
            environmental footprint, and eating style. Each one answers a different question. We explain
            what each score means and where its limits are.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600 transition shadow-lg hover:shadow-xl"
            >
              <SparklesIcon className="mr-2 w-5 h-5" aria-hidden="true" />
              See all scores at once
              <ArrowRightIcon className="ml-2 w-5 h-5" aria-hidden="true" />
            </Link>
            <Link
              href="/research/nutrient-analysis"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition shadow-sm"
            >
              <BeakerIcon className="mr-2 w-5 h-5" aria-hidden="true" />
              Run a nutrient analysis
            </Link>
            <Link
              href="/methods"
              className="inline-flex items-center justify-center px-6 py-3 text-base font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition shadow-sm"
            >
              <BookOpenIcon className="mr-2 w-5 h-5" aria-hidden="true" />
              Read the methods
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
                <div className="text-3xl sm:text-4xl font-bold text-emerald-600 tabular-nums">
                  <span className="inline-block min-w-[3ch] text-center">{s.value}</span>
                </div>
                <div className="mt-1 text-sm font-medium text-gray-800">{s.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{s.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Published research lenses */}
      <section id="lenses" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Published research lenses</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Each measure answers a different question about the same food. No single score wins.
              The right answer depends on what you are asking. New lenses plug into the same substrate
              as they are published; the list is open, not fixed.
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
                    className="w-11 h-11 rounded-lg bg-slate-100 flex items-center justify-center"
                    aria-hidden="true"
                  >
                    <l.icon className="w-5 h-5 text-primary-700" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{l.name}</h3>
                    <p className="text-xs text-gray-600 italic">{l.tagline}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-700 leading-snug mb-2">{l.meaning}</p>
                <p className="text-[11px] text-gray-500">{l.citation}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-blue-700 group-hover:text-blue-900">
                  {l.linkLabel} <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
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
              See all lenses at once
            </Link>
          </div>
        </div>
      </section>

      {/* Built for three audiences (promoted; researcher-first ordering) */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Built for three audiences</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              Every score can be read in three ways. The numbers never change; the explanation does.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {audiences.map((a) => (
              <div key={a.name} className="rounded-2xl border border-gray-200 p-6 hover:shadow-lg transition flex flex-col">
                <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center mb-4 shadow-sm">
                  <a.icon className="w-6 h-6 text-white" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{a.name}</h3>
                <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">{a.description}</p>
                <Link
                  href={a.cta.href}
                  className="inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-900 group"
                >
                  {a.cta.label}
                  <ArrowRightIcon className="ml-1 w-4 h-4 group-hover:translate-x-0.5 transition" aria-hidden="true" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Food catalogue (multi-database substrate) */}
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
                  so the catalogue keeps growing. WAFCT 2019 landed in May 2026, USDA FoodData Central
                  in June 2026, ANSES CIQUAL 2025 also in June 2026 — and other regional databases can
                  plug in the same way. Pick any single source or search across all of them at once.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active, authoritative</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
                    <div className="text-xs text-gray-600 mt-0.5">5,993 foods, Health Canada (CNF 2026 edition).</div>
                  </div>
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active, extension</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
                    <div className="text-xs text-gray-600 mt-0.5">1,028 West African foods, Vincent 2019. Includes fonio, baobab, dawadawa, gari, egusi, and other West African staples.</div>
                  </div>
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active, extension</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">USDA FoodData Central</div>
                    <div className="text-xs text-gray-600 mt-0.5">13,620 US foods — Foundation (395 analytically derived), SR Legacy (7,793 classic SR28), and Survey FNDDS (5,432 dietary-survey foods).</div>
                  </div>
                  <div className="border border-gray-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Active, extension</div>
                    <div className="text-sm font-medium text-gray-900 mt-1">ANSES CIQUAL 2025</div>
                    <div className="text-xs text-gray-600 mt-0.5">~3,484 French foods (English release). Pairs with Agribalyse 3.2 LCA via shared Ciqual codes for nutrition + environment.</div>
                  </div>
                  <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
                    <div className="text-sm font-medium text-gray-700 mt-1">Further composition tables</div>
                    <div className="text-xs mt-0.5">EuroFIR, EFSA FoodEx2, NEVO (NL), BLS (DE), and other regional tables can plug in the same way.</div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  Each source keeps its own provenance, so differences in how foods were measured stay visible across CNF, WAFCT, FDC, and CIQUAL rows.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* For individuals (demoted from former hero; still prominent) */}
      <section className="py-14 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl bg-gradient-to-br from-rose-50 to-pink-50 border border-rose-200 p-8">
            <p className="text-xs font-semibold uppercase tracking-wide text-rose-700">For individuals</p>
            <h2 className="mt-2 text-2xl sm:text-3xl font-bold text-gray-900">
              Is this food good for you, and for the planet?
            </h2>
            <p className="mt-3 text-sm text-gray-700 max-w-3xl">
              Score a single product, a homemade dish, or a whole day of eating. Plain-language
              interpretation with the caveats that matter and no methodology jargon.
            </p>
            <div className="mt-5 flex flex-col sm:flex-row gap-3">
              <Link
                href="/scorecard"
                className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600"
              >
                <SparklesIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                See all your scores
              </Link>
              <Link
                href="/recall-24h"
                className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              >
                <CalendarDaysIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                Log a food diary day
              </Link>
              <Link
                href="/scan-product"
                className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              >
                <CameraIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                Scan a product
              </Link>
              <Link
                href="/me"
                className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium text-rose-700 hover:text-rose-900"
              >
                Open the individuals hub <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Ways to get started */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">Ways to get started</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              Different ways to bring food into the platform. However you start, it lands in the
              same food list and can be scored under any published lens.
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
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      t.highlight
                        ? 'bg-gradient-to-br from-emerald-500 to-blue-600'
                        : 'bg-gray-100'
                    }`}
                    aria-hidden="true"
                  >
                    <t.icon className={`w-5 h-5 ${t.highlight ? 'text-white' : 'text-gray-700'}`} aria-hidden="true" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">{t.name}</h3>
                </div>
                <p className="text-sm text-gray-700 leading-snug">{t.description}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-blue-700 group-hover:text-blue-900">
                  Open <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Honest framing */}
      <section className="py-14 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5" aria-hidden="true" />
              What the platform is <em>not</em>
            </h2>
            <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
              <li><strong>Not clinical advice.</strong> Scoring is population-anchored, not a personal diagnosis or prescription.</li>
              <li><strong>Not a single composite score.</strong> Each published lens answers a different question, so we report them all rather than fold disagreement into one number.</li>
              <li><strong>Not a whole-life-cycle footprint.</strong> ReCiPe and AGRIBALYSE cover the production phase. Household preparation and end-of-life are out of scope in this version.</li>
              <li><strong>Not yet Canadian-anchored everywhere.</strong> HEFI is Canadian by design. HENI uses US Global Burden of Disease epidemiology, with Canadian portability noted as future work, and Food Compass is anchored to NHANES with Canadian validation still pending.</li>
              <li><strong>No account, no health-data collection.</strong> Your recall history and active food list live in your browser only. There is no login and no personal data stored on our servers.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Primary references */}
      <section className="py-14 bg-gray-50 border-t border-gray-100">
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

      {/* Final CTA — research-led */}
      <section className="py-16 bg-gradient-to-r from-primary-600 to-accent-600">
        <div className="max-w-5xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Start analyzing</h2>
          <p className="text-base text-indigo-50 mb-8 max-w-2xl mx-auto">
            Score a meal, a 24-hour record, or a whole day across every published research lens on
            one substrate. Versioned, citeable, reproducible.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto">
            <Link
              href="/scorecard"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-indigo-700 bg-white hover:bg-gray-50 shadow"
            >
              <SparklesIcon className="mr-2 w-4 h-4" aria-hidden="true" />
              All scores
            </Link>
            <Link
              href="/research/nutrient-analysis"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-white border border-white hover:bg-white/10"
            >
              <BeakerIcon className="mr-2 w-4 h-4" aria-hidden="true" />
              Nutrient analysis
            </Link>
            <Link
              href="/methods"
              className="inline-flex items-center justify-center px-5 py-3 text-sm font-semibold rounded-lg text-white border border-white hover:bg-white/10"
            >
              <BookOpenIcon className="mr-2 w-4 h-4" aria-hidden="true" />
              Read the methods
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
