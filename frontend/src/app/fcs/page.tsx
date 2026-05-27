'use client';

import React from 'react';
import Link from 'next/link';
import {
  BeakerIcon,
  CalculatorIcon,
  ScaleIcon,
  UserIcon,
  BuildingOfficeIcon,
  DocumentChartBarIcon,
  SparklesIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
  CameraIcon,
} from '@heroicons/react/24/outline';

const fcsDomains = [
  {
    domain: 'Nutrient ratios',
    description: 'Macro balance, plus key omega and mineral ratios.',
  },
  {
    domain: 'Vitamins',
    description: 'How well the food covers the vitamins that matter most for its food group.',
  },
  {
    domain: 'Minerals',
    description: 'How well the food covers the most important minerals for its food group.',
  },
  {
    domain: 'Food ingredients',
    description: 'The quality of the main ingredients, judged from the first five on the label.',
  },
  {
    domain: 'Additives',
    description: 'A penalty for added colours, preservatives, and other industrial ingredients.',
  },
  {
    domain: 'Processing (NOVA)',
    description: 'A penalty based on how processed the food is. Ultra-processed foods take the biggest hit.',
  },
  {
    domain: 'Specific lipids',
    description: 'The fatty acid profile, looking at saturated, unsaturated, trans, and omega 3 and 6.',
  },
  {
    domain: 'Fibre and protein',
    description: 'How much fibre and protein the food carries per calorie.',
  },
  {
    domain: 'Phytochemicals',
    description: 'Plant compounds with documented health benefits.',
  },
];

const novaGroups = [
  {
    group: 'Group 1, minimally processed',
    examples: 'Fresh fruit, raw meat, milk, dried grains.',
    penalty: '0',
    color: 'green',
  },
  {
    group: 'Group 2, culinary ingredients',
    examples: 'Oils, butter, sugar, salt.',
    penalty: '−6',
    color: 'yellow',
  },
  {
    group: 'Group 3, processed foods',
    examples: 'Cheese, canned vegetables, simple breads.',
    penalty: '−7.5',
    color: 'orange',
  },
  {
    group: 'Group 4, ultra-processed',
    examples: 'Industrial formulations with additives.',
    penalty: '−10 (maximum)',
    color: 'red',
  },
];

const novaColorClasses = {
  green: 'bg-green-50 border-green-200 text-green-800',
  yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  orange: 'bg-orange-50 border-orange-200 text-orange-800',
  red: 'bg-red-50 border-red-200 text-red-800',
} as const;

export default function FCSMainPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 via-white to-green-50 rounded-3xl p-8 mb-16">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-green-500 rounded-full flex items-center justify-center">
                <SparklesIcon className="w-12 h-12 text-white" />
              </div>
            </div>
            <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-4">
              Food Compass
            </h1>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto mb-6 leading-relaxed">
              How closely does a food, a meal, or a whole day of eating resemble the kinds of
              foods linked to longer, healthier lives in research studies? Food Compass scores
              every food on a single scale from 1 to 100, where higher is better. It looks at
              nine areas of nutrition all at once, so a sugary breakfast cereal with added
              vitamins lands in a very different place from a bowl of plain oats.
            </p>

            <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-6 text-sm text-amber-900 text-left">
              <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                <strong>If you live in Canada:</strong> the link between this score and
                health outcomes was tested in US data. We have not yet retested it in Canadian
                populations. Use it as a useful signal, not as clinical advice.
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto mb-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-green-200 text-left">
                <div className="text-2xl font-bold text-green-700 mb-1">Encourage</div>
                <div className="text-sm text-gray-700">Score of 70 or more</div>
                <div className="text-xs text-gray-500 mt-1">
                  Mostly whole vegetables, fruits, legumes, nuts, seafood, and whole grains.
                </div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-amber-200 text-left">
                <div className="text-2xl font-bold text-amber-700 mb-1">Moderate</div>
                <div className="text-sm text-gray-700">Score of 31 to 69</div>
                <div className="text-xs text-gray-500 mt-1">
                  Most dairy, eggs, poultry, and lightly processed staples.
                </div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-red-200 text-left">
                <div className="text-2xl font-bold text-red-700 mb-1">Limit</div>
                <div className="text-sm text-gray-700">Score of 30 or less</div>
                <div className="text-xs text-gray-500 mt-1">
                  Most ultra-processed foods, sugary drinks, and animal fats.
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/fcs/calculate"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-xl text-white bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Calculate now
                <ArrowRightIcon className="ml-2 w-5 h-5" />
              </Link>
              <Link
                href="/scorecard"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-xl text-gray-700 bg-white/80 backdrop-blur-sm hover:bg-gray-50 transition-colors duration-200 shadow-sm"
              >
                See Food Compass alongside all 6 metrics
              </Link>
            </div>
          </div>
        </section>

        {/* FCS tools */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">What you can do</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Score a single packaged product, a whole day of eating, or rank several foods side by side.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Link href="/scan-product" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-amber-500 to-amber-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <CameraIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Scan a product</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Take a photo of the Nutrition Facts panel and ingredient list. The app reads
                    it for you and scores the product.
                  </p>
                  <div className="flex items-center text-amber-700 text-sm font-medium">
                    <span>Scan now</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>

            <Link href="/fcs/calculate" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <CalculatorIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Calculator</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Pick foods and serving sizes from our catalogue. Score one food on its own
                    or build a list and score the lot together.
                  </p>
                  <div className="flex items-center text-blue-700 text-sm font-medium">
                    <span>Start calculating</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>

            <Link href="/fcs/food-profile" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <BeakerIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Single-food profile</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    See how any food in the catalogue scores in each of the nine areas, plus its
                    processing penalty and NOVA group.
                  </p>
                  <div className="flex items-center text-green-700 text-sm font-medium">
                    <span>Explore profile</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>

            <Link href="/fcs/compare" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <ScaleIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Compare foods</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Rank foods side by side. This works across food types, so you can hold a
                    snack bar up against an apple.
                  </p>
                  <div className="flex items-center text-purple-700 text-sm font-medium">
                    <span>Compare</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </section>

        {/* Build a full day */}
        <section className="mb-16">
          <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-2xl p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Build a full day, then score it
                </h2>
                <p className="text-gray-700 mb-3">
                  The easiest way to score a whole day is to walk through it occasion by
                  occasion in the 24-hour recall wizard. Each meal contributes to the day&apos;s
                  overall score in proportion to how many calories it adds, so a big bowl of
                  oats counts for more than a small sprinkle of cocoa.
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link
                    href="/recall-24h?then=fcs"
                    className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                  >
                    Open the 24-h recall wizard
                  </Link>
                  <Link
                    href="/recall-history"
                    className="inline-flex items-center justify-center px-4 py-2 bg-white text-blue-700 text-sm font-medium rounded-md border border-blue-300 hover:bg-blue-50"
                  >
                    Or load a saved day
                  </Link>
                </div>
              </div>
              <div className="text-sm text-blue-900 space-y-3">
                <p>
                  <strong>Calorie-weighted.</strong> Foods with more calories pull the day&apos;s
                  score around more than tiny garnishes, so a single bite of cake will not
                  ruin a healthy day.
                </p>
                <p>
                  <strong>Processing-aware.</strong> Heavily processed foods take a built-in
                  penalty, with the size of the penalty rising as the level of processing rises.
                </p>
                <p>
                  <strong>Three ways to read it.</strong> Researcher and policy views open up the
                  detail behind each domain and the methodology behind the score.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 9 domains */}
        <section className="mb-16">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Nine areas, looked at together</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              The score is not built from one number on the label. It pulls together nine
              different areas of nutrition, weighing the helpful parts against the harmful
              ones, so the final number reflects the whole food rather than any single ingredient.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {fcsDomains.map((item) => (
              <div key={item.domain} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{item.domain}</h3>
                <p className="text-sm text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How processing affects the score */}
        <section className="mb-16">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center mr-4">
                <GlobeAltIcon className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900">
                How processing affects the score
              </h2>
            </div>
            <p className="text-gray-600 mb-6">
              Foods are sorted into four NOVA groups based on how industrially processed they
              are. Processing on its own does not set the score. It nudges the score down by a
              fixed penalty, and the more processed the food, the larger the penalty.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {novaGroups.map((item) => (
                <div
                  key={item.group}
                  className={`border rounded-xl p-4 ${novaColorClasses[item.color as keyof typeof novaColorClasses]}`}
                >
                  <h3 className="font-semibold mb-1">{item.group}</h3>
                  <p className="text-xs mt-1 mb-2 opacity-90">{item.examples}</p>
                  <div className="text-sm font-semibold">Penalty: {item.penalty}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Audience modes */}
        <section className="mb-16 bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Three ways to read every result
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <UserIcon className="w-5 h-5 text-blue-600 mr-2" />
                <h3 className="font-semibold text-blue-900">Individual</h3>
              </div>
              <p className="text-sm text-blue-800">
                A plain-language band, with no methodology jargon. Read it as a comparison
                between products, not as a personal health verdict.
              </p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <BuildingOfficeIcon className="w-5 h-5 text-green-600 mr-2" />
                <h3 className="font-semibold text-green-900">Researcher</h3>
              </div>
              <p className="text-sm text-green-800">
                The full breakdown for each of the nine areas, the processing penalty, and
                pointers to the methodology behind the score.
              </p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <DocumentChartBarIcon className="w-5 h-5 text-purple-600 mr-2" />
                <h3 className="font-semibold text-purple-900">Policy</h3>
              </div>
              <p className="text-sm text-purple-800">
                Population-level framing for procurement standards, taxation analysis, and
                food-environment work, with the limits of the underlying study stated plainly.
              </p>
            </div>
          </div>
        </section>

        {/* Food composition databases */}
        <section className="mb-16">
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Which foods we can score</h2>
            <p className="text-sm text-gray-700 mb-4">
              The catalogue holds 6,719 foods today, drawn from the Canadian Nutrient File and
              the West African Food Composition Table. Each source keeps its own notes, so any
              known differences in how foods were measured stay visible. New food composition
              databases can be added without changing how the scoring works.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="border border-gray-100 rounded-lg p-3">
                <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Active</div>
                <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
                <div className="text-xs text-gray-600 mt-0.5">
                  5,691 foods from Health Canada, the authoritative source for the Canadian context.
                </div>
              </div>
              <div className="border border-gray-100 rounded-lg p-3">
                <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Active</div>
                <div className="text-sm font-medium text-gray-900 mt-1">WAFCT 2019</div>
                <div className="text-xs text-gray-600 mt-0.5">
                  1,028 West African foods. Known differences in how minerals were measured
                  show up in researcher view.
                </div>
              </div>
              <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
                <div className="text-sm font-medium text-gray-700 mt-1">More to come</div>
                <div className="text-xs mt-0.5">
                  Other regional food composition tables can plug in the same way.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* What it isn't */}
        <section className="mb-16">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              What this score is <em>not</em>
            </h2>
            <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
              <li>
                <strong>Not clinical advice.</strong> It was tested at the level of populations,
                not for individual diagnosis or prescription.
              </li>
              <li>
                <strong>Not yet retested for people in Canada.</strong> The link between the
                score and health outcomes comes from US adults. A Canadian validation has not
                been done yet.
              </li>
              <li>
                <strong>Not a replacement for the Canadian Food Guide score.</strong> HEFI tells
                you how well you follow Canada&apos;s Food Guide. Food Compass tells you how
                closely your food resembles eating patterns linked to longer life. Two
                different questions.
              </li>
              <li>
                <strong>Not perfectly precise for homemade recipes.</strong> Breaking a recipe
                into ingredients involves some guesswork, so a homemade dish carries more
                uncertainty than a packaged one.
              </li>
            </ul>
          </div>
        </section>

        {/* Where the science comes from */}
        <section className="py-12 bg-white border border-gray-200 rounded-2xl">
          <div className="max-w-4xl mx-auto px-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Where the science comes from</h2>
            <p className="text-sm text-gray-700 mb-4 leading-relaxed">
              Food Compass was first published in <em>Nature Food</em> in 2021 by a team led by
              Dariush Mozaffarian. It pulled together evidence on which foods tend to support
              long-term health and which tend not to, and turned that into a single score.
              A follow-up paper in 2022 in <em>Nature Communications</em> showed that adults in
              the US who ate higher-scoring diets had lower rates of all-cause mortality,
              which is the strongest evidence that the score reflects something meaningful
              about long-term health.
            </p>
            <p className="text-sm text-gray-700 leading-relaxed">
              Researcher view links out to both papers if you want to read the original work.
            </p>
            <ul className="space-y-3 text-sm text-gray-600 list-disc list-inside mt-4">
              <li>
                <strong className="text-gray-900">The system itself:</strong>{' '}
                Mozaffarian et al. (2021), <em>Nature Food</em> 2, 809–818.{' '}
                <a
                  href="https://doi.org/10.1038/s43016-021-00381-y"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 underline hover:text-blue-800"
                >
                  doi:10.1038/s43016-021-00381-y
                </a>
              </li>
              <li>
                <strong className="text-gray-900">Link to mortality in US adults:</strong>{' '}
                O&apos;Hearn et al. (2022), <em>Nature Communications</em> 13, 7066.{' '}
                <a
                  href="https://doi.org/10.1038/s41467-022-34195-8"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 underline hover:text-blue-800"
                >
                  doi:10.1038/s41467-022-34195-8
                </a>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
