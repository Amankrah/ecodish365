'use client';

import React from 'react';
import Link from 'next/link';
import {
  HeartIcon,
  CalculatorIcon,
  ScaleIcon,
  ChartBarIcon,
  LightBulbIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CameraIcon,
} from '@heroicons/react/24/outline';
import StarRating from '@/components/StarRating';

const hsrFeatures = [
  {
    name: 'Scan a packaged product',
    description:
      'Take one to three photos of a label: the Nutrition Facts panel, the ingredient list, and the net weight. The app reads the panel, you confirm what it found, and the product is scored in its own category. This is the simplest way to score something straight off the shelf.',
    icon: CameraIcon,
    href: '/scan-product',
    color: 'primary',
    features: [
      'From photo to star rating',
      'Upload front, back, and side',
      'You confirm before anything is scored',
      'Best for a single packaged product',
    ],
  },
  {
    name: 'Calculate HSR',
    description:
      'Pick foods and serving sizes from our catalogue. Score one food on its own, or build a list and get an overall rating alongside a star rating for each item.',
    icon: CalculatorIcon,
    href: '/hsr/calculate',
    color: 'primary',
    features: [
      'Full score breakdown',
      'Nutrient-by-nutrient analysis',
      'A rating for each item in a list',
      'Researcher and policy views',
    ],
  },
  {
    name: 'Compare products',
    description:
      'Line up similar products side by side and rank them by stars. This is what HSR does best: which yogurt, which cereal, which loaf of bread.',
    icon: ScaleIcon,
    href: '/hsr/compare',
    color: 'accent',
    features: [
      'Compare within a category',
      'Ranked by star rating',
      'Key nutrients side by side',
      "Each product's strengths and weaknesses",
    ],
  },
  {
    name: 'All scores',
    description:
      'See the star rating next to all five other measures for the same foods: Food Compass, healthy eating, health impact, environment, and eating style, in one clear summary.',
    icon: ChartBarIcon,
    href: '/scorecard',
    color: 'primary',
    features: [
      'All six lenses at once',
      'A plain-language summary',
      'Jump straight to any calculator',
    ],
  },
];

const hsrBenefits = [
  {
    title: 'HSRAC v9 algorithm',
    description:
      'Runs the current Australian and New Zealand Health Star Rating algorithm (Implementation Guide v9, December 2025). It matches versions 6 through 8 and differs from the pre-2020 versions.',
    icon: CheckCircleIcon,
  },
  {
    title: 'Within-category comparison',
    description:
      'Every food is scored against the thresholds for its own group. HSRAC v9 has six: non-dairy beverages, dairy beverages, foods, dairy foods, fats and oils, and cheese. You compare yogurts to yogurts, not yogurts to oils.',
    icon: ChartBarIcon,
  },
  {
    title: 'Per-product, not per-day',
    description:
      'A 5-star product is not a healthy diet. For full-day diet quality, use healthy eating or Food Compass. For population-level health impact, use health impact scores.',
    icon: LightBulbIcon,
  },
  {
    title: 'Multi-database catalogue',
    description:
      'The catalogue holds 6,719 foods today: 5,691 from the Canadian Nutrient File and 1,028 West African foods from FAO/INFOODS WAFCT 2019. Each source keeps its own notes, so differences in how foods were measured stay visible, and new databases can be added the same way.',
    icon: InformationCircleIcon,
  },
];

const hsrLevels = [
  {
    stars: 4.75,
    range: '4.5–5.0',
    level: 'Excellent',
    color: 'bg-green-500',
    description: 'Among the best in its category.',
  },
  {
    stars: 3.75,
    range: '3.5–4.0',
    level: 'Good',
    color: 'bg-lime-400',
    description: 'A strong choice in its category.',
  },
  {
    stars: 2.75,
    range: '2.5–3.0',
    level: 'Average',
    color: 'bg-yellow-400',
    description: 'Middle of the pack for its category.',
  },
  {
    stars: 1.75,
    range: '1.5–2.0',
    level: 'Below average',
    color: 'bg-orange-400',
    description: 'Weaker than most in its category.',
  },
  {
    stars: 0.75,
    range: '0.5–1.0',
    level: 'Poor',
    color: 'bg-red-400',
    description: 'Among the lowest in its category.',
  },
];

export default function HSRDashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 via-white to-green-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-green-500 rounded-full flex items-center justify-center">
                <HeartIcon className="w-12 h-12 text-white" />
              </div>
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              Health Star Rating <span className="text-blue-600">(HSRAC v9)</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8 leading-relaxed">
              Rate a packaged product from 0.5 to 5 stars against others in its own category.
              The Health Star Rating is the front-of-pack system used across Australia and New
              Zealand, and here it runs on our full food catalogue: the Canadian Nutrient File
              and the West African Food Composition Table, with more to come. It scores one
              product at a time, which is what makes it useful at the shelf. This yogurt or
              that one. This cereal or that one.
            </p>
            <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-8 text-sm text-amber-900 text-left">
              <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Per-product, not per-day.</strong> A 5-star product is not a healthy diet.
                For full-day diet quality see{' '}
                <Link href="/hefi" className="underline">healthy eating</Link> or{' '}
                <Link href="/fcs" className="underline">Food Compass</Link>.
                For all metrics at once, use{' '}
                <Link href="/scorecard" className="underline font-medium">all scores</Link>.
              </span>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/hsr/calculate"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Start Calculating
                <ArrowRightIcon className="ml-2 w-5 h-5" />
              </Link>
              <Link
                href="#how-it-works"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-sm"
              >
                Learn How It Works
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* HSR Rating Levels */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Understanding Health Star Ratings</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              The Health Star Rating runs from 0.5 to 5 stars and reflects a product&apos;s
              nutritional profile compared with others in the same category.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {hsrLevels.map((level) => (
              <div key={level.range} className="text-center">
                <div className={`w-16 h-16 ${level.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <span className="text-white font-bold text-sm">{level.range}</span>
                </div>
                <div className="flex justify-center mb-2">
                  <StarRating rating={level.stars} size="sm" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{level.level}</h3>
                <p className="text-xs text-gray-600">{level.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Four ways to score a product
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Pick the tool that fits what you have in front of you: a packaged label, a food
              from our catalogue, two products to compare, or the full picture across every lens.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {hsrFeatures.map((feature) => (
              <div key={feature.name} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 overflow-hidden">
                <div className="p-8">
                  <div className="flex items-center mb-6">
                    <div className={`w-12 h-12 bg-gradient-to-br ${
                      feature.color === 'primary' ? 'from-blue-500 to-blue-600' :
                      feature.color === 'accent' ? 'from-purple-500 to-purple-600' :
                      'from-green-500 to-green-600'
                    } rounded-lg flex items-center justify-center`}>
                      <feature.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 ml-4">{feature.name}</h3>
                  </div>

                  <p className="text-gray-600 mb-6 leading-relaxed">{feature.description}</p>

                  <ul className="space-y-2 mb-6">
                    {feature.features.map((item) => (
                      <li key={item} className="flex items-center text-sm text-gray-600">
                        <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={feature.href}
                    className={`inline-flex items-center justify-center w-full px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r ${
                      feature.color === 'primary' ? 'from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800' :
                      feature.color === 'accent' ? 'from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800' :
                      'from-green-600 to-green-700 hover:from-green-700 hover:to-green-800'
                    } transition-all duration-200`}
                  >
                    Launch tool
                    <ArrowRightIcon className="ml-2 w-5 h-5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="how-it-works" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Why use Health Star Ratings?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              HSR is built for one job and does it well: comparing similar packaged products on
              the same evidence base.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {hsrBenefits.map((benefit) => (
              <div key={benefit.title} className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <benefit.icon className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">{benefit.title}</h3>
                <p className="text-gray-600 leading-relaxed">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              How Health Star Rating works
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              HSR weighs the nutrients that affect health and turns them into a single star
              rating from 0.5 to 5.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="flex items-start">
                <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Risk nutrients</h3>
                  <p className="text-gray-600">
                    Energy, saturated fat, sugar, and sodium add risk points. The more a product
                    has, the more risk points it carries.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Beneficial nutrients</h3>
                  <p className="text-gray-600">
                    Protein, fibre, and fruit, vegetable, nut, and legume content add beneficial
                    points that work in the product&apos;s favour.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <CalculatorIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Final calculation</h3>
                  <p className="text-gray-600">
                    The final score is the risk points minus the beneficial points. A lower final
                    score means a healthier profile, which earns more stars. Each food category has
                    its own table that converts the final score into a star rating.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">
                Sample calculation &mdash; general foods
              </h3>

              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Risk points (energy, saturated fat, sugar, sodium)</span>
                  <span className="font-semibold text-red-600">7</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Beneficial points (protein, fibre, fruit, veg, nuts, legumes)</span>
                  <span className="font-semibold text-green-600">6</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b-2 border-gray-200">
                  <span className="text-gray-600">Final score (7 minus 6)</span>
                  <span className="font-semibold">1</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-lg font-semibold text-gray-900">Stars for this category</span>
                  <div className="flex items-center">
                    <span className="text-lg font-bold text-blue-600 mr-2">3.5</span>
                    <StarRating rating={3.5} size="md" />
                  </div>
                </div>
                <p className="text-xs text-gray-500 pt-2">
                  Each category has its own conversion table. The same final score yields different
                  stars for beverages, foods, dairy products, fats and oils, and cheese.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Audience modes */}
      <section className="py-16 bg-white border-t border-gray-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Three ways to read every result</h2>
          <p className="text-gray-700 leading-relaxed">
            Every result can be read three ways. The numbers never change; the explanation does.
            Individuals get a plain-language read with no jargon. Researchers get the full HSRAC v9
            methodology, including the category-determination trail and notes on how fruit,
            vegetable, nut, and legume content was estimated. Policy makers get population-level
            framing for procurement and labelling.
          </p>
        </div>
      </section>

      {/* Primary references */}
      <section className="py-12 bg-white border-t border-gray-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="font-semibold text-gray-900 mb-2">Primary references</h3>
          <ul className="space-y-1 list-disc list-inside text-gray-600 text-sm">
            <li>HSRAC, <em>Health Star Rating System Implementation Guide v9</em> (Dec 2025).</li>
            <li>
              Shahid M. et al. (2020). The Australian Health Star Rating System: applicability
              for nutrient profiling. <em>Nutrients</em> 12, 1791.
            </li>
            <li>HSR v9 is functionally equivalent to versions 6 through 8 and differs from pre-2020 versions.</li>
          </ul>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-green-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to rate a product?
          </h2>
          <p className="text-xl text-blue-100 mb-8 leading-relaxed">
            Score what&apos;s in your hand, or compare two products side by side.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/hsr/calculate"
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-blue-600 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-lg"
            >
              <CalculatorIcon className="mr-2 w-5 h-5" />
              Calculate HSR
            </Link>
            <Link
              href="/hsr/compare"
              className="inline-flex items-center justify-center px-8 py-3 border border-white text-base font-medium rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-colors duration-200"
            >
              Compare products
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
