import type { Metadata } from 'next';
import Link from 'next/link';
import {
  HeartIcon,
  ArrowRightIcon,
  SparklesIcon,
  CalendarDaysIcon,
  CameraIcon,
  BookmarkIcon,
  WrenchScrewdriverIcon,
  ChartPieIcon,
  ClockIcon,
  PlusCircleIcon,
} from '@heroicons/react/24/outline';

export const metadata: Metadata = {
  title: 'For individuals',
  description:
    'Score a single product, a homemade dish, or a whole day of eating. Plain-language interpretation with honest caveats. The consumer surface of the ecodish365 platform.',
};

const liveTools = [
  {
    icon: SparklesIcon,
    name: 'All scores',
    href: '/scorecard',
    description: 'See healthy eating, health impact, stars, Food Compass, environment, and eating style for the same food list in one view.',
    primary: true,
  },
  {
    icon: CalendarDaysIcon,
    name: 'Food diary',
    href: '/recall-24h',
    description: 'Log a full day meal by meal. Each meal breaks into individual foods you can score under any published lens.',
  },
  {
    icon: CameraIcon,
    name: 'Scan a product',
    href: '/scan-product',
    description: 'Photograph a nutrition label, confirm the details, and score the product across every lens.',
  },
  {
    icon: ClockIcon,
    name: 'Saved days',
    href: '/recall-history',
    description: 'Save logged days and revisit them, or average several days together for a truer picture of how you usually eat.',
  },
  {
    icon: WrenchScrewdriverIcon,
    name: 'Improve one meal',
    href: '/improve-product',
    description: 'Get ingredient substitution suggestions to raise a meal\'s scores across multiple lenses at once.',
  },
  {
    icon: ChartPieIcon,
    name: 'Dietary pattern',
    href: '/dietary-pattern',
    description: 'Match your day to one of eight published eating styles: Mediterranean, DASH, EAT-Lancet, and more.',
  },
  {
    icon: PlusCircleIcon,
    name: 'My meals',
    href: '/meals/my-meals',
    description: 'Save the meals you eat often and re-score them under any lens whenever you like. Sign in to use.',
  },
  {
    icon: BookmarkIcon,
    name: 'Saved meals',
    href: '/meals/saved-meals',
    description: 'Bookmarked community meals you can re-score and adapt. Sign in to use.',
  },
];

const roadmap = [
  {
    name: 'Personal trends',
    anchor: 'trends',
    description: 'Track your six scores over time across saved days.',
  },
  {
    name: 'Weekly summary',
    anchor: 'weekly',
    description: 'A weekly readout of where your eating stands across each lens.',
  },
  {
    name: 'Saved analyses',
    anchor: 'saved',
    description: 'Name a scored meal, retrieve it later, share a link with a dietitian.',
  },
];

export default function IndividualsHubPage() {
  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-slate-50 py-12 sm:py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-sm flex-shrink-0">
              <HeartIcon className="w-7 h-7 text-white" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-700 mb-2">For individuals</p>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight">
                Is this food good for you, and for the planet?
              </h1>
              <p className="mt-3 text-base text-gray-700 max-w-3xl leading-relaxed">
                Score a single product, a homemade dish, or a whole day of eating. Plain-language
                interpretation with the caveats that matter and no methodology jargon. The same published lenses
                that power the research and policy surfaces, read in everyday English.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/scorecard"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600 shadow-sm"
                >
                  <SparklesIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  See all your scores
                  <ArrowRightIcon className="ml-2 w-4 h-4" aria-hidden="true" />
                </Link>
                <Link
                  href="/recall-24h"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                >
                  <CalendarDaysIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Log a food diary day
                </Link>
                <Link
                  href="/scan-product"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                >
                  <CameraIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Scan a product
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Live tools</h2>
          <p className="text-sm text-gray-600 mb-6">Everything you need to score a food, a meal, or a day, in plain language.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {liveTools.map((t) => (
              <Link
                key={t.name}
                href={t.href}
                className={`rounded-2xl p-5 border hover:shadow-lg hover:-translate-y-0.5 transition group ${
                  t.primary ? 'bg-gradient-to-br from-primary-50 to-blue-50 border-primary-300' : 'bg-white border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${t.primary ? 'bg-gradient-to-br from-primary-500 to-primary-600' : 'bg-gray-100'}`}>
                    <t.icon className={`w-5 h-5 ${t.primary ? 'text-white' : 'text-gray-700'}`} aria-hidden="true" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">{t.name}</h3>
                </div>
                <p className="text-sm text-gray-700 leading-snug line-clamp-3">{t.description}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-primary-700 group-hover:text-primary-900">
                  Open <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section id="roadmap" className="py-10 bg-gray-50 border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Roadmap</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {roadmap.map((r) => (
              <div key={r.name} id={r.anchor} className="rounded-2xl border border-dashed border-gray-300 bg-white p-4">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-gray-700">{r.name}</h3>
                  <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">Soon</span>
                </div>
                <p className="text-sm text-gray-600 leading-snug">{r.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-8 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm text-gray-500">
            Also see:
            {' '}
            <Link href="/research" className="text-primary-700 hover:underline">Researchers</Link>
            {' · '}
            <Link href="/policy" className="text-primary-700 hover:underline">Policy</Link>
            {' · '}
            <Link href="/methods" className="text-primary-700 hover:underline">Methods &amp; data</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
