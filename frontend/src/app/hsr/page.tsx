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
} from '@heroicons/react/24/outline';
import StarRating from '@/components/StarRating';

const hsrFeatures = [
  {
    name: '📷 Scan a packaged product',
    description: 'Take 1–3 photos of the Nutrition Facts panel + ingredients + net weight. Multimodal AI extracts the panel; you confirm; HSR scores the product in its own category. The canonical single-product HSR flow.',
    icon: CalculatorIcon,
    href: '/scan-product',
    color: 'primary',
    features: ['Photo → NF panel → HSR', 'Multi-image upload (front/back/side)', 'You confirm before scoring', 'Best for single-product HSR'],
  },
  {
    name: 'Calculate HSR',
    description: 'Pick foods from the integrated catalog (CNF or WAFCT) + serving sizes. Single food = standard HSR; multi-food list = per-product summary with energy-weighted average and per-item stars.',
    icon: CalculatorIcon,
    href: '/hsr/calculate',
    color: 'primary',
    features: ['Detailed score breakdown', 'Per-component nutritional analysis', 'Per-item ratings on multi-food lists', 'Researcher / policy modes'],
  },
  {
    name: 'Compare Foods',
    description: 'Side-by-side HSR ranking for similar products — what HSR is best at. Use this for "which yogurt?" or "which cereal?" comparisons.',
    icon: ScaleIcon,
    href: '/hsr/compare',
    color: 'accent',
    features: ['Within-category compare', 'Ranking by star rating', 'Key nutrients table', 'Strongest/weakest highlights'],
  },
  {
    name: '✨ Scorecard (all metrics)',
    description: 'See HSR alongside FCS, HEFI, HENI, environmental impact, and dietary pattern for the same food list in one consumer-friendly summary.',
    icon: ChartBarIcon,
    href: '/scorecard',
    color: 'primary',
    features: ['All six metrics at once', 'Consumer-friendly summary', 'Cross-metric transfer', 'Deep links to each calculator'],
  },
];

const hsrBenefits = [
  {
    title: 'HSRAC v9 algorithm',
    description: 'Implements the current Australian / New Zealand Health Star Rating algorithm (HSRAC Implementation Guide v9, Dec 2025). Functionally equivalent to v6–v8; differs from pre-2020 versions.',
    icon: CheckCircleIcon,
  },
  {
    title: 'Within-category comparison',
    description: 'Foods are scored against thresholds for their HSR category (Cat 1/1D beverages, Cat 2/2D foods, Cat 3/3D fats & oils). Compare yogurts to yogurts — not yogurts to oils.',
    icon: ChartBarIcon,
  },
  {
    title: 'Per-product, not per-day',
    description: 'A 5-star product is not a healthy diet. For full-day diet quality use HEFI-2019 or FCS; for population-level health impact use HENI.',
    icon: LightBulbIcon,
  },
  {
    title: 'Multi-database catalog',
    description: 'Canadian Nutrient File (5,691 foods) + FAO/INFOODS WAFCT 2019 (1,028 West African foods) = 6,719 today, surfaced under a single source-tagged catalog. Per-source caveats flag analytical-method differences; further composition databases follow the same extension pattern.',
    icon: InformationCircleIcon,
  },
];

const hsrLevels = [
  { level: 'Excellent', stars: 5, range: '4.5-5.0', color: 'bg-green-500', description: 'Ideal for daily consumption' },
  { level: 'Very Good', stars: 4.5, range: '4.0-4.5', color: 'bg-green-400', description: 'Very good choice for regular eating' },
  { level: 'Good', stars: 4, range: '3.5-4.0', color: 'bg-green-400', description: 'Great choice for regular eating' },
  { level: 'Average', stars: 3, range: '2.5-3.0', color: 'bg-yellow-400', description: 'Good as part of balanced diet' },
  { level: 'Below Average', stars: 2, range: '1.5-2.0', color: 'bg-orange-400', description: 'Consume in moderation' },
  { level: 'Poor', stars: 0.5, range: '0.5-1.0', color: 'bg-red-400', description: 'Limit consumption' },
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
              Rate a packaged product 0.5–5 stars within its own HSR category — the Australian /
              New Zealand front-of-pack rule for nutrient profiling, applied across our
              integrated food composition catalog (Canadian Nutrient File + FAO/INFOODS WAFCT
              today, with additional databases planned). HSR is per-product, designed to help
              shoppers pick between similar items (yogurt vs yogurt, cereal vs cereal).
            </p>
            <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-8 text-sm text-amber-900">
              <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Per-product, not per-day.</strong> A 5-star product is not a healthy diet.
                For full-day diet quality see{' '}
                <Link href="/hefi" className="underline">HEFI-2019</Link> or{' '}
                <Link href="/fcs" className="underline">FCS</Link>;
                for all metrics at once use the{' '}
                <Link href="/scorecard" className="underline font-medium">✨ Scorecard</Link>.
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
              The Health Star Rating system rates foods from 0.5 to 5 stars based on their nutritional profile.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            {hsrLevels.map((level) => (
              <div key={level.level} className="text-center">
                <div className={`w-16 h-16 ${level.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <span className="text-white font-bold text-lg">{level.stars}</span>
                </div>
                <div className="flex justify-center mb-2">
                  <StarRating rating={level.stars} size="sm" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{level.level}</h3>
                <p className="text-sm text-gray-500 mb-2">{level.range} stars</p>
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
              Comprehensive HSR Analysis Tools
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Choose from our suite of tools to analyze food nutritional quality and make healthier choices.
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
                    Launch Tool
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
              Why Use Health Star Ratings?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our HSR system provides evidence-based nutritional assessment to help you make informed food choices.
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
              How Health Star Rating Works
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              The HSR system evaluates foods based on key nutrients that impact health, 
              providing a simple star rating from 0.5 to 5 stars.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="flex items-start">
                <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Risk Nutrients (Negative Points)</h3>
                  <p className="text-gray-600">Energy, saturated fat, sugar, and sodium content contribute to baseline points that lower the rating.</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Beneficial Nutrients (Positive Points)</h3>
                  <p className="text-gray-600">Protein, fiber, and fruits/vegetables/nuts/legumes content provide modifying points that improve the rating.</p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <CalculatorIcon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Final Calculation</h3>
                  <p className="text-gray-600">The final score subtracts modifying points from baseline points, then converts to a 0.5-5 star rating.</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">Sample HSR Calculation</h3>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Baseline Points (Risk)</span>
                  <span className="font-semibold text-red-600">+8</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Modifying Points (Beneficial)</span>
                  <span className="font-semibold text-green-600">-3</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b-2 border-gray-200">
                  <span className="text-gray-600">Final Score</span>
                  <span className="font-semibold">5</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-lg font-semibold text-gray-900">HSR Rating</span>
                  <div className="flex items-center">
                    <span className="text-lg font-bold text-blue-600 mr-2">3.5</span>
                                          <StarRating rating={3.5} size="md" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Citations + audience modes */}
      <section className="py-12 bg-white border-t border-gray-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-2 gap-8 text-sm text-gray-700">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Audience modes</h3>
            <p>
              Every HSR calculation toggles between three explanation packs (AUDIENCE-CODE-1):
              <strong> Individual</strong> (plain-language interpretation, no jargon),
              <strong> Researcher</strong> (full HSRAC v9 methodology, category-determination
              audit trail, FVNL imputation notes), and
              <strong> Policy</strong> (population framing for procurement and labeling regulation).
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Primary references</h3>
            <ul className="space-y-1 list-disc list-inside text-gray-600">
              <li>HSRAC, <em>Health Star Rating System Implementation Guide v9</em> (Dec 2025).</li>
              <li>
                Shahid M. et al. (2020). The Australian Health Star Rating System
                — applicability for nutrient profiling.{' '}
                <em>Nutrients</em> 12, 1791.
              </li>
              <li>HSR v9 is functionally equivalent to v6–v8 and differs from pre-2020 versions.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-green-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Analyze Your Food Choices?
          </h2>
          <p className="text-xl text-blue-100 mb-8 leading-relaxed">
            Start using our comprehensive HSR tools to make healthier, more informed food decisions today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/hsr/calculate"
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-blue-600 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-lg"
            >
              <CalculatorIcon className="mr-2 w-5 h-5" />
              Calculate HSR Now
            </Link>
            <Link
              href="/hsr/compare"
              className="inline-flex items-center justify-center px-8 py-3 border border-white text-base font-medium rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-colors duration-200"
            >
              Compare Foods
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
} 