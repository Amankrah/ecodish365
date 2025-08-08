'use client';

import React from 'react';
import Link from 'next/link';
import { 
  BeakerIcon,
  CalculatorIcon,
  ChartBarIcon,
  ScaleIcon,
  UserIcon,
  BuildingOfficeIcon,
  DocumentChartBarIcon,
  SparklesIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  TrophyIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

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
            <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-6">
              Food Compass <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-green-600">2.0</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto mb-8 leading-relaxed">
              The most comprehensive nutrient profiling system validated by cutting-edge research. 
              Evaluating <strong>54 attributes</strong> across <strong>9 health-relevant domains</strong> to score foods from 1-100.
            </p>
            
            {/* Latest Research Badge */}
            <div className="inline-flex items-center bg-gradient-to-r from-blue-100 to-green-100 border border-blue-200 rounded-full px-6 py-3 mb-8">
              <TrophyIcon className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm font-semibold text-blue-900 mr-2">NEW:</span>
              <span className="text-sm text-blue-800">
                Food Compass 2.0 published in <a href="https://www.nature.com/articles/s43016-024-01053-3" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-900">Nature Food (Oct 2024)</a>
              </span>
            </div>

            {/* Key Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-sm">
                <div className="text-3xl font-bold text-blue-600 mb-2">9,273</div>
                <div className="text-sm text-gray-600">Foods & Beverages Analyzed</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-sm">
                <div className="text-3xl font-bold text-green-600 mb-2">7%</div>
                <div className="text-sm text-gray-600">Lower Mortality Risk</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-sm">
                <div className="text-3xl font-bold text-purple-600 mb-2">50,000</div>
                <div className="text-sm text-gray-600">Adults in Validation Study</div>
          </div>
        </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/fcs/calculate"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-xl text-white bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Calculate FCS Now
                <ArrowRightIcon className="ml-2 w-5 h-5" />
              </Link>
              <Link
                href="#research"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-xl text-gray-700 bg-white/80 backdrop-blur-sm hover:bg-gray-50 transition-colors duration-200 shadow-sm"
              >
                View Research
              </Link>
            </div>
          </div>
        </section>

        {/* Feature Cards */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Comprehensive Analysis Tools</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Leverage the power of Food Compass 2.0 with our suite of analytical tools
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Calculator Card */}
          <Link href="/fcs/calculate" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1">
                <div className="p-8">
                  <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    <CalculatorIcon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">FCS Calculator</h3>
                  <p className="text-gray-600 mb-4 leading-relaxed">
                    Calculate Food Compass Scores using the latest 2.0 algorithm with enhanced ingredient analysis and processing evaluation.
                  </p>
                  <div className="flex items-center text-blue-600 font-medium">
                    <span>Start Calculating</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
            </div>
          </Link>

          {/* Food Profile Card */}
          <Link href="/fcs/food-profile" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1">
                <div className="p-8">
                  <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    <BeakerIcon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">Food Profile</h3>
                  <p className="text-gray-600 mb-4 leading-relaxed">
                    Deep-dive analysis across all 9 domains with detailed breakdowns of the 54 attributes that determine food healthfulness.
                  </p>
                  <div className="flex items-center text-green-600 font-medium">
                    <span>Explore Profiles</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
            </div>
          </Link>

          {/* Comparison Card */}
          <Link href="/fcs/compare" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1">
                <div className="p-8">
                  <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl mb-6 group-hover:scale-110 transition-transform duration-300">
                    <ScaleIcon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">Compare Foods</h3>
                  <p className="text-gray-600 mb-4 leading-relaxed">
                    Side-by-side comparison of nutritional quality with detailed analysis and evidence-based recommendations.
                  </p>
                  <div className="flex items-center text-purple-600 font-medium">
                    <span>Compare Now</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </section>

        {/* Research & Validation Section */}
        <section id="research" className="mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Latest Research & Validation</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Food Compass 2.0 represents the culmination of cutting-edge nutritional science, 
              validated in the largest study of its kind
            </p>
        </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            {/* What's New in 2.0 */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mr-4">
                  <SparklesIcon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-semibold text-gray-900">What&apos;s New in Food Compass 2.0</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-start">
                  <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-gray-900">Enhanced Ingredient Analysis</div>
                    <div className="text-sm text-gray-600">Updated data on specific ingredients and emerging nutrients</div>
                  </div>
                </div>
                <div className="flex items-start">
                  <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-gray-900">Refined Processing Evaluation</div>
                    <div className="text-sm text-gray-600">Improved NOVA classification integration and processing penalties</div>
                  </div>
                </div>
                <div className="flex items-start">
                  <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-gray-900">Latest Diet-Health Evidence</div>
                    <div className="text-sm text-gray-600">Incorporates 2024 research findings on food-health relationships</div>
                  </div>
                </div>
                <div className="flex items-start">
                  <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium text-gray-900">Expanded Food Database</div>
                    <div className="text-sm text-gray-600">Analysis of 9,273 unique food and beverage items</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Key Findings */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mr-4">
                  <TrophyIcon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-semibold text-gray-900">Key Research Findings</h3>
              </div>
              <div className="space-y-6">
                <div className="bg-green-50 rounded-xl p-4">
                  <div className="text-2xl font-bold text-green-600 mb-1">7% Lower Risk</div>
                  <div className="text-sm text-green-800">All-cause mortality reduction per standard deviation increase in diet FCS</div>
                </div>
                <div className="bg-blue-50 rounded-xl p-4">
                  <div className="text-2xl font-bold text-blue-600 mb-1">Enhanced Validity</div>
                  <div className="text-sm text-blue-800">Stronger associations with health outcomes compared to other nutrient profiling systems</div>
                </div>
                <div className="bg-purple-50 rounded-xl p-4">
                  <div className="text-2xl font-bold text-purple-600 mb-1">Food Category Updates</div>
                  <div className="text-sm text-purple-800">Meaningful score improvements for seafood (+9), eggs (+8), and meat products</div>
                </div>
              </div>
            </div>
          </div>

          {/* Score Distribution */}
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center mb-6">
              <ChartBarIcon className="w-6 h-6 text-blue-600 mr-3" />
              <h3 className="text-2xl font-semibold text-gray-900">FCS 2.0 Score Distribution</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="text-center">
                <div className="bg-gradient-to-br from-green-100 to-green-200 rounded-2xl p-6 mb-4">
                  <div className="text-4xl font-bold text-green-600 mb-2">23%</div>
                  <div className="text-green-800 font-medium">Score ≥70</div>
                  <div className="text-sm text-green-600 mt-1">Encourage Daily</div>
                </div>
                <div className="text-sm text-gray-600">
                  Most seafood (82%), legumes (80%), nuts (89%), vegetables (63%), and fruits (53%)
                </div>
              </div>
              <div className="text-center">
                <div className="bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-2xl p-6 mb-4">
                  <div className="text-4xl font-bold text-yellow-600 mb-2">46%</div>
                  <div className="text-yellow-800 font-medium">Score 31-69</div>
                  <div className="text-sm text-yellow-600 mt-1">Consume in Moderation</div>
                </div>
                <div className="text-sm text-gray-600">
                  Most meat (52%), poultry (91%), eggs (89%), and dairy products (73%)
                </div>
              </div>
              <div className="text-center">
                <div className="bg-gradient-to-br from-red-100 to-red-200 rounded-2xl p-6 mb-4">
                  <div className="text-4xl font-bold text-red-600 mb-2">31%</div>
                  <div className="text-red-800 font-medium">Score ≤30</div>
                  <div className="text-sm text-red-600 mt-1">Minimize Consumption</div>
                </div>
                <div className="text-sm text-gray-600">
                  Most beverages (54%) and animal fats (92%), ultra-processed foods
                </div>
              </div>
            </div>
            <div className="bg-blue-50 rounded-xl p-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> FCS 2.0 shows enhanced differentiation compared to other systems like Health Star Rating, 
                Nutri-Score, and NOVA processing classification, providing more nuanced nutritional assessment.
              </p>
            </div>
          </div>
        </section>

        {/* User-Specific Interpretation Guide */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">FCS Interpretation by User Type</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Individuals */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <UserIcon className="w-5 h-5 text-blue-600 mr-2" />
                <h3 className="font-semibold text-blue-900">For Individuals</h3>
              </div>
              <div className="space-y-3 text-sm text-blue-800">
                <div>
                  <div className="font-medium">Daily Food Choices:</div>
                  <ul className="list-disc list-inside ml-2 space-y-1">
                    <li>Aim for foods with FCS ≥70 to comprise majority of your diet</li>
                    <li>Use FCS 31-69 foods in moderation as part of balanced meals</li>
                    <li>Limit FCS ≤30 foods to occasional treats</li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium">Health Benefits:</div>
                  <p>Higher overall diet FCS associated with 7% lower mortality risk and improved cardiometabolic markers.</p>
                </div>
              </div>
            </div>

            {/* Businesses */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <BuildingOfficeIcon className="w-5 h-5 text-green-600 mr-2" />
                <h3 className="font-semibold text-green-900">For Businesses</h3>
              </div>
              <div className="space-y-3 text-sm text-green-800">
                <div>
                  <div className="font-medium">Product Development:</div>
                  <ul className="list-disc list-inside ml-2 space-y-1">
                    <li>Target FCS ≥70 for premium health-focused products</li>
                    <li>Use FCS to optimize recipes and reformulations</li>
                    <li>Compare products against competitors scientifically</li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium">Marketing Advantages:</div>
                  <p>Evidence-based nutritional claims supported by peer-reviewed research and validated methodology.</p>
                </div>
              </div>
            </div>

            {/* Government */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <DocumentChartBarIcon className="w-5 h-5 text-purple-600 mr-2" />
                <h3 className="font-semibold text-purple-900">For Government/Policy</h3>
              </div>
              <div className="space-y-3 text-sm text-purple-800">
                <div>
                  <div className="font-medium">Policy Applications:</div>
                  <ul className="list-disc list-inside ml-2 space-y-1">
                    <li>Inform taxation policies based on nutritional quality</li>
                    <li>Establish procurement standards for public institutions</li>
                    <li>Guide front-of-pack labeling regulations</li>
                  </ul>
                </div>
                <div>
                  <div className="font-medium">Population Health:</div>
                  <p>Comprehensive tool for evaluating food environment and informing public health interventions.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Nine Domains Section */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">The Nine Health-Relevant Domains</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Food Compass 2.0 evaluates 54 attributes across nine evidence-based domains, 
              providing the most comprehensive nutritional assessment available
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { domain: "Nutrient Ratios", icon: "⚖️", description: "Balanced relationships between macronutrients, omega fatty acids, and key mineral ratios" },
              { domain: "Vitamins", icon: "🌟", description: "Essential vitamin content focusing on the top 5 most health-relevant vitamins per food category" },
              { domain: "Minerals", icon: "⛰️", description: "Critical mineral density evaluation of the top 5 most important minerals for each food type" },
              { domain: "Food Ingredients", icon: "🥬", description: "Assessment of whole food components, plant-based ingredients, and beneficial compounds" },
              { domain: "Additives", icon: "🧪", description: "Evaluation of processing additives, preservatives, and artificial ingredients impact" },
              { domain: "Processing", icon: "🏭", description: "NOVA classification integration with enhanced penalties for ultra-processed foods" },
              { domain: "Specific Lipids", icon: "🫒", description: "Detailed fatty acid profiles including omega-3, omega-6, and trans fat content" },
              { domain: "Fiber & Protein", icon: "💪", description: "Structural and functional nutrient assessment for satiety and metabolic health" },
              { domain: "Phytochemicals", icon: "🌿", description: "Plant-based bioactive compounds with proven health benefits and antioxidant properties" }
            ].map((item, index) => (
              <div key={index} className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
                <div className="text-4xl mb-4 text-center">{item.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 text-center">{item.domain}</h3>
                <p className="text-sm text-gray-600 text-center leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* NOVA Integration */}
        <section className="mb-16">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center mr-4">
                <GlobeAltIcon className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900">NOVA Processing Integration</h2>
            </div>
            <div className="mb-6">
              <p className="text-gray-600 mb-4">
                <strong>Enhanced Processing Assessment:</strong> Food Compass 2.0 integrates NOVA classification 
                into Domain 6 (Processing) with refined penalty scoring based on the latest research on ultra-processed foods.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-xl p-4">
                <h3 className="font-semibold text-green-800 mb-2">🥬 Group 1</h3>
                <h4 className="font-medium text-green-800 mb-2">Minimally Processed</h4>
                <p className="text-sm text-green-700 mb-3">Fresh fruits, vegetables, grains, meats, and dairy</p>
                <div className="bg-green-200 rounded-lg p-2">
                  <div className="text-sm font-semibold text-green-800">Score: 0 (Optimal)</div>
                </div>
              </div>
              <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 border border-yellow-200 rounded-xl p-4">
                <h3 className="font-semibold text-yellow-800 mb-2">🧈 Group 2</h3>
                <h4 className="font-medium text-yellow-800 mb-2">Culinary Ingredients</h4>
                <p className="text-sm text-yellow-700 mb-3">Oils, butter, sugar, salt for cooking</p>
                <div className="bg-yellow-200 rounded-lg p-2">
                  <div className="text-sm font-semibold text-yellow-800">Score: -6</div>
                </div>
              </div>
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200 rounded-xl p-4">
                <h3 className="font-semibold text-orange-800 mb-2">🥫 Group 3</h3>
                <h4 className="font-medium text-orange-800 mb-2">Processed Foods</h4>
                <p className="text-sm text-orange-700 mb-3">Canned vegetables, cheese, simple breads</p>
                <div className="bg-orange-200 rounded-lg p-2">
                  <div className="text-sm font-semibold text-orange-800">Score: -7.5</div>
                </div>
              </div>
              <div className="bg-gradient-to-br from-red-50 to-red-100 border border-red-200 rounded-xl p-4">
                <h3 className="font-semibold text-red-800 mb-2">🍟 Group 4</h3>
                <h4 className="font-medium text-red-800 mb-2">Ultra-Processed</h4>
                <p className="text-sm text-red-700 mb-3">Industrial formulations with additives</p>
                <div className="bg-red-200 rounded-lg p-2">
                  <div className="text-sm font-semibold text-red-800">Score: -10 (Max Penalty)</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Scientific Citation */}
        <section className="bg-gradient-to-r from-blue-900 to-green-900 rounded-2xl p-8 text-white">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Scientific Foundation</h2>
            <p className="text-blue-100 mb-6 max-w-4xl mx-auto leading-relaxed">
              Food Compass 2.0 is based on peer-reviewed research published in Nature Food, 
              one of the world&apos;s leading scientific journals. This system represents the most 
              comprehensive and validated approach to food nutritional assessment available today.
            </p>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 max-w-4xl mx-auto">
              <div className="text-sm text-blue-100 mb-2">RESEARCH CITATION</div>
              <div className="text-white font-medium mb-2">
                Barrett, E.M., Shi, P., Blumberg, J.B. et al. Food Compass 2.0 is an improved nutrient profiling system to characterize healthfulness of foods and beverages. 
              </div>
              <div className="text-blue-200 text-sm">
                <em>Nature Food</em> 5, 911–915 (2024). 
                <a 
                  href="https://www.nature.com/articles/s43016-024-01053-3" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="underline hover:text-white transition-colors ml-2"
                >
                  https://doi.org/10.1038/s43016-024-01053-3
                </a>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}