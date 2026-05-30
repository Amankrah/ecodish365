'use client';

import React from 'react';
import Link from 'next/link';
import {
  CalculatorIcon,
  ChartBarIcon,
  UserIcon,
  CalendarDaysIcon,
  SparklesIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'Log a food diary day',
    description:
      "Walk through your day one meal at a time. The wizard turns each meal into the foods that make it up, then sends them here for scoring. This is the way healthy eating scores were meant to be used, and it gives you the most useful number.",
    icon: CalendarDaysIcon,
    href: '/recall-24h?then=hefi',
    color: 'bg-blue-500',
    badge: 'Recommended',
  },
  {
    name: 'Calculate a score',
    description:
      "Pick foods from our catalogue, set the serving sizes, and get a score across all ten things HEFI looks at. You can score a single meal, but a whole day is what the score is built for.",
    icon: CalculatorIcon,
    href: '/hefi/calculate',
    color: 'bg-purple-500',
  },
  {
    name: 'Compare meals',
    description:
      'Line up a few meal ideas side by side and see how they rank. Useful when you are planning a menu, swapping an ingredient, or testing a recipe change.',
    icon: ChartBarIcon,
    href: '/hefi/compare',
    color: 'bg-green-500',
  },
  {
    name: 'Single-food profile',
    description:
      "See how one food on its own would land in HEFI's ten checks. Best for understanding why a food helps or hurts a day's score, not as a standalone judgment.",
    icon: UserIcon,
    href: '/hefi/food-profile',
    color: 'bg-amber-500',
  },
];

// Brassard 2022b Table A2 (Canadian population ≥ 2 y, CCHS 2015).
// Source of truth: backend/api/views/hefi_explanations.py _POPULATION_BENCHMARKS.
const hefiBenchmarks = [
  { label: '1st percentile',  value: 22, note: 'Very low adherence' },
  { label: '25th percentile', value: 35, note: 'Below the median' },
  { label: '50th percentile', value: 43, note: 'Median Canadian' },
  { label: '75th percentile', value: 51, note: 'Above the median' },
  { label: '99th percentile', value: 63, note: 'Top of the distribution' },
];

const hefiRewards = [
  {
    name: 'Vegetables and fruit',
    description:
      'How much of what you eat is whole vegetables and fruit.',
    maxScore: 20,
  },
  {
    name: 'Whole-grain foods',
    description:
      'Whether whole-grain foods show up in the day at all.',
    maxScore: 5,
  },
  {
    name: 'Whole grains as a share of grains',
    description:
      'When you eat grains, how often they are the whole-grain kind.',
    maxScore: 5,
  },
  {
    name: 'Protein foods',
    description:
      'Whether the day includes enough foods that count as protein sources.',
    maxScore: 5,
  },
  {
    name: 'Plant proteins',
    description:
      'How often your protein comes from plants like beans, lentils, tofu, and nuts.',
    maxScore: 5,
  },
  {
    name: 'Recommended drinks',
    description:
      'Whether what you drink leans toward water, plain milk, and unsweetened plant beverages.',
    maxScore: 10,
  },
];

const hefiModerates = [
  {
    name: 'Fat balance',
    description:
      'The balance between unsaturated fats (from things like fish, nuts, and oils) and saturated fats (from butter, fatty meats, and full-fat dairy).',
    maxScore: 5,
  },
  {
    name: 'Saturated fat share',
    description:
      'How much of the day’s calories come from saturated fat.',
    maxScore: 5,
  },
  {
    name: 'Free sugars share',
    description:
      "How much of the day's calories come from sugars that were added to a food or freed up by processing, like the sugar in fruit juice or syrup.",
    maxScore: 10,
  },
  {
    name: 'Sodium relative to calories',
    description:
      'How salty the day is for the calories it provides.',
    maxScore: 10,
  },
];

export default function HEFIPage() {
  return (
    <div className="space-y-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero */}
      <section className="text-center">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
          Healthy Eating Food Index
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-4 leading-relaxed">
          A score for how closely a day of eating lines up with <strong>Canada&apos;s Food
          Guide</strong>. Six things the Guide encourages add to your score, four nutrients
          worth moderating can pull it down. The total runs from 0 to 80.
        </p>
        <p className="text-sm text-gray-500 max-w-2xl mx-auto mb-4">
          Researchers may know this measure as HEFI-2019 (Brassard et al. 2022).
        </p>
        <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-6 text-sm text-amber-900">
          <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            HEFI is built for a full day of eating. A single meal gives a rough sense of
            direction, not a verdict on your diet. There is no pass or fail score. The number
            is most useful when you read it against the range of Canadian eaters, shown below.
          </span>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/recall-24h?then=hefi"
            className="inline-flex items-center justify-center px-6 py-3 bg-purple-600 text-white text-base font-medium rounded-lg hover:bg-purple-700"
          >
            <CalendarDaysIcon className="mr-2 w-5 h-5" />
            Log a food diary day
          </Link>
          <Link
            href="/scorecard"
            className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
          >
            <SparklesIcon className="mr-2 w-5 h-5" />
            See all six scores at once
          </Link>
        </div>
      </section>

      {/* Tools */}
      <section>
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">Four ways to get a score</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Pick the one that fits what you have in front of you, from a quick look at one
            food to a whole day of eating.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <Link
              key={feature.name}
              href={feature.href}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 group flex flex-col"
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-11 h-11 rounded-lg ${feature.color} flex items-center justify-center group-hover:scale-110 transition-transform duration-200`}>
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
                {feature.badge && (
                  <span className="text-[10px] font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-wide">
                    {feature.badge}
                  </span>
                )}
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-2 group-hover:text-purple-700">
                {feature.name}
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed flex-1">
                {feature.description}
              </p>
              <div className="flex items-center text-purple-700 text-sm font-medium mt-3">
                <span>Open</span>
                <ArrowRightIcon className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Population benchmarks */}
      <section className="bg-purple-50 border border-purple-200 rounded-2xl p-6">
        <div className="flex items-start gap-3 mb-4">
          <ChartBarIcon className="w-6 h-6 text-purple-700 flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">How to read your score</h2>
            <p className="text-sm text-gray-600 mt-1">
              There is no &ldquo;healthy&rdquo; line to clear. The score makes more sense when you
              hold it next to the range of Canadian eaters from the 2015 national survey.
              The median Canadian sits at 43, the top one percent reach 63, and almost nobody
              hits 80.
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {hefiBenchmarks.map((b) => (
            <div key={b.label} className="bg-white border border-purple-100 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-700">{b.value}</div>
              <div className="text-xs text-gray-600 font-medium">{b.label}</div>
              <div className="text-[10px] text-gray-500 mt-1">{b.note}</div>
            </div>
          ))}
        </div>
      </section>

      {/* HEFI components */}
      <section>
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">What the score looks at</h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Ten things, grouped into the six that earn points and the four that can cost
            them. Together they add up to 80.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Encourage column */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-semibold bg-green-100 text-green-700 px-2 py-0.5 rounded-full uppercase tracking-wide">
                Earns points
              </span>
              <span className="text-sm text-gray-600">Six things the Food Guide encourages</span>
            </div>
            <div className="space-y-3">
              {hefiRewards.map((c) => (
                <div key={c.name} className="bg-white border border-gray-200 rounded-xl p-4 flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-gray-900 mb-1">{c.name}</h3>
                    <p className="text-sm text-gray-600">{c.description}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-2xl font-bold text-purple-600">{c.maxScore}</div>
                    <div className="text-[10px] text-gray-500 uppercase tracking-wide">max pts</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Moderate column */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-semibold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full uppercase tracking-wide">
                Can cost points
              </span>
              <span className="text-sm text-gray-600">Four nutrients worth moderating</span>
            </div>
            <div className="space-y-3">
              {hefiModerates.map((c) => (
                <div key={c.name} className="bg-white border border-gray-200 rounded-xl p-4 flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-gray-900 mb-1">{c.name}</h3>
                    <p className="text-sm text-gray-600">{c.description}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-2xl font-bold text-purple-600">{c.maxScore}</div>
                    <div className="text-[10px] text-gray-500 uppercase tracking-wide">max pts</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="text-center mt-6">
          <div className="inline-flex items-center bg-purple-50 border border-purple-200 rounded-lg px-5 py-3">
            <CheckCircleIcon className="w-5 h-5 text-purple-600 mr-2" />
            <span className="text-sm text-purple-900">
              <strong>Total: 80 points.</strong> The top one percent of Canadians reach about 63.
            </span>
          </div>
        </div>
      </section>

      {/* Food databases */}
      <section className="bg-white rounded-2xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Where the foods come from</h2>
        <p className="text-sm text-gray-700 mb-4">
          Every food you score is drawn from a real food composition database. The Canadian
          Nutrient File is the one HEFI was built against, so it stays the home base. The
          West African Food Composition Table fills in foods the Canadian database does not
          cover. When a West African food shows up in your meal, the researcher view flags
          the small differences in how it was measured, so nothing slips by unnoticed.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Home base</div>
            <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
            <div className="text-xs text-gray-600 mt-0.5">
              5,691 foods from Health Canada. HEFI was developed and tested against the
              Canadian eating data this database supports.
            </div>
          </div>
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Extension</div>
            <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
            <div className="text-xs text-gray-600 mt-0.5">
              1,028 West African foods. Small measurement differences are shown clearly when
              one of these foods is in your meal.
            </div>
          </div>
          <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
            <div className="text-sm font-medium text-gray-700 mt-1">More regional tables</div>
            <div className="text-xs mt-0.5">
              Additional composition tables will plug in the same way.
            </div>
          </div>
        </div>
      </section>

      {/* What HEFI isn't */}
      <section className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
        <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
          <ExclamationTriangleIcon className="w-5 h-5" />
          What HEFI is not
        </h2>
        <ul className="space-y-2 text-sm text-amber-900 list-disc list-inside">
          <li>
            <strong>Not a health prediction.</strong> The score tells you how close your eating
            sits to Canada&apos;s Food Guide. It does not tell you your risk for any disease.
            For a mortality-anchored read, try <Link href="/fcs" className="underline">Food Compass</Link>.
            For a health-life-minutes read, try <Link href="/heni" className="underline">HENI</Link>.
          </li>
          <li>
            <strong>Not a single-meal verdict.</strong> A high score on one meal does not make
            for a high-scoring day, and a low-scoring meal can still fit inside a strong day.
          </li>
          <li>
            <strong>Not a pass or fail.</strong> There is no clinical cutoff. Read your score
            against the range of Canadian eaters, not against an imaginary perfect 80.
          </li>
          <li>
            <strong>Free sugars are estimated.</strong> The Canadian database tracks total
            sugars rather than free sugars, so the score uses total sugars as a stand-in. That
            tends to be hard on whole fruit, milk, and plain yogurt, where most of the sugar
            is natural to the food.
          </li>
        </ul>
      </section>

      {/* Audience modes + citations */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Three ways to read every result</h3>
          <p className="text-sm text-gray-700">
            The numbers stay the same. The explanation changes depending on who is reading.
            The everyday view gives you a plain-language read of where your day sits.
            The researcher view shows each component, the ratios behind it, and the
            references it draws on. The policy view frames the score for population
            monitoring and Food Guide implementation work.
          </p>
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Where the science comes from</h3>
          <p className="text-sm text-gray-700 leading-relaxed">
            HEFI-2019 was developed and validated by Didier Brassard and colleagues for Health
            Canada, with two companion papers in the <em>Applied Physiology, Nutrition, and
            Metabolism</em> journal in 2022. The Canadian benchmarks shown above come from
            the 2015 Canadian Community Health Survey, which is the same population the score
            was tuned against.
          </p>
        </div>
      </section>

      {/* About */}
      <section className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-start mb-3">
          <InformationCircleIcon className="w-6 h-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">About healthy eating scores</h2>
            <p className="text-sm text-gray-700">
              The Healthy Eating Food Index is the score Health Canada uses to measure how
              closely the way Canadians eat lines up with the 2019 Food Guide. It works best
              when you give it a whole day of eating, which is exactly what the 24-hour
              recall wizard above is built to help you do.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
