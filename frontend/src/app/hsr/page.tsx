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
  StarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

const hsrFeatures = [
  {
    name: 'Calculate HSR',
    description: 'Calculate Health Star Ratings for individual foods or meals with detailed nutritional analysis.',
    icon: CalculatorIcon,
    href: '/hsr/calculate',
    color: 'primary',
    features: ['Detailed score breakdown', 'Nutritional analysis', 'Health insights', 'Recommendations'],
  },
  {
    name: 'Compare Foods',
    description: 'Compare Health Star Ratings across multiple foods to make better choices.',
    icon: ScaleIcon,
    href: '/hsr/compare',
    color: 'accent',
    features: ['Side-by-side comparison', 'Ranking by HSR rating', 'Key nutrients comparison', 'Smart recommendations'],
  },
  {
    name: 'Meal Insights',
    description: 'Get comprehensive meal-level analysis and personalized recommendations.',
    icon: LightBulbIcon,
    href: '/hsr/meal-insights',
    color: 'secondary',
    features: ['Meal composition analysis', 'Nutritional balance', 'Improvement opportunities', 'Dietary goal alignment'],
  },
  {
    name: 'Food Profiles',
    description: 'Explore detailed HSR profiles for individual foods with comprehensive analysis.',
    icon: ChartBarIcon,
    href: '/hsr/food-profile',
    color: 'primary',
    features: ['Complete nutritional analysis', 'Usage recommendations', 'Healthier alternatives', 'Confidence scoring'],
  },
];

const hsrBenefits = [
  {
    title: 'Evidence-Based Rating',
    description: 'Uses the official Australian Health Star Rating system based on rigorous nutritional science.',
    icon: CheckCircleIcon,
  },
  {
    title: 'Comprehensive Analysis',
    description: 'Analyzes 7 key nutrients (energy, saturated fat, sugar, sodium, protein, fiber, FVNL) for accurate scoring.',
    icon: ChartBarIcon,
  },
  {
    title: 'Actionable Insights',
    description: 'Provides specific, actionable recommendations to help you make healthier food choices.',
    icon: LightBulbIcon,
  },
  {
    title: 'Canadian Nutrient Data',
    description: 'Based on the comprehensive Canadian Nutrient File with data for over 5,000 foods.',
    icon: InformationCircleIcon,
  },
];

const hsrLevels = [
  { level: 'Excellent', stars: 5, range: '4.5-5.0', color: 'bg-green-500', description: 'Ideal for daily consumption' },
  { level: 'Good', stars: 4, range: '3.5-4.0', color: 'bg-green-400', description: 'Great choice for regular eating' },
  { level: 'Average', stars: 3, range: '2.5-3.0', color: 'bg-yellow-400', description: 'Good as part of balanced diet' },
  { level: 'Below Average', stars: 2, range: '1.5-2.0', color: 'bg-orange-400', description: 'Consume in moderation' },
  { level: 'Poor', stars: 1, range: '0.5-1.0', color: 'bg-red-400', description: 'Limit consumption' },
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
              Health Star Rating <span className="text-blue-600">Calculator</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8 leading-relaxed">
              Make informed food choices with our comprehensive Health Star Rating system. 
              Analyze nutritional quality, compare foods, and get personalized recommendations 
              based on the Australian front-of-pack labeling system.
            </p>
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
                  {[...Array(5)].map((_, i) => (
                    <StarIcon
                      key={i}
                      className={`w-4 h-4 ${
                        i < level.stars ? 'text-yellow-400 fill-current' : 'text-gray-300'
                      }`}
                    />
                  ))}
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
                    <div className="flex">
                      {[...Array(5)].map((_, i) => (
                        <StarIcon
                          key={i}
                          className={`w-5 h-5 ${
                            i < 3.5 ? 'text-yellow-400 fill-current' : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
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