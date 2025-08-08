'use client';

import React from 'react';
import Link from 'next/link';
import { 
  BeakerIcon,
  CalculatorIcon,
  ChartBarIcon,
  ScaleIcon,
  InformationCircleIcon,
  AcademicCapIcon,
  UserIcon,
  BuildingOfficeIcon,
  DocumentChartBarIcon
} from '@heroicons/react/24/outline';

export default function FCSMainPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Food Compass Score (FCS) 2.0
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-6">
            Comprehensive nutritional analysis using the most advanced nutrient profiling algorithm. 
            FCS evaluates 54 attributes across 9 health-relevant domains to score foods from 1-100.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-2xl mx-auto">
            <div className="flex items-center justify-center mb-2">
              <AcademicCapIcon className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-blue-900">Scientific Algorithm</span>
            </div>
            <p className="text-sm text-blue-800">
              Based on validated research from Tufts University&apos;s Friedman School, 
              published in Nature Food (2024). Demonstrates significant associations 
              with mortality reduction and improved cardiometabolic health.
            </p>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {/* Calculator Card */}
          <Link href="/fcs/calculate" className="group">
            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow duration-200">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mb-4 group-hover:bg-blue-200 transition-colors">
                <CalculatorIcon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">FCS Calculator</h3>
              <p className="text-gray-600 text-sm">
                Calculate Food Compass Scores for individual foods or complete meals using the validated FCS 2.0 algorithm.
              </p>
            </div>
          </Link>

          {/* Food Profile Card */}
          <Link href="/fcs/food-profile" className="group">
            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow duration-200">
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-4 group-hover:bg-green-200 transition-colors">
                <BeakerIcon className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Food Profile</h3>
              <p className="text-gray-600 text-sm">
                Get detailed nutritional profiles with domain-by-domain breakdowns showing all 54 evaluated attributes.
              </p>
            </div>
          </Link>

          {/* Comparison Card */}
          <Link href="/fcs/compare" className="group">
            <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow duration-200">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-4 group-hover:bg-purple-200 transition-colors">
                <ScaleIcon className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Compare Foods</h3>
              <p className="text-gray-600 text-sm">
                Compare nutritional quality between multiple foods with detailed analysis and recommendations.
              </p>
            </div>
          </Link>
        </div>

        {/* FCS Information */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* What is FCS */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center mb-4">
              <InformationCircleIcon className="w-6 h-6 text-blue-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">What is Food Compass Score?</h2>
            </div>
            <div className="space-y-3 text-sm text-gray-600">
              <p>
                Food Compass Score (FCS) is a comprehensive nutrient profiling system that evaluates 
                the healthfulness of foods using 54 attributes across 9 evidence-based domains:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><strong>Nutrient Ratios:</strong> Balanced nutrient relationships</li>
                <li><strong>Vitamins:</strong> Essential vitamin content (top 5 selection)</li>
                <li><strong>Minerals:</strong> Critical mineral density (top 5 selection)</li>
                <li><strong>Food Ingredients:</strong> Whole food components</li>
                <li><strong>Additives:</strong> Processing additives assessment</li>
                <li><strong>Processing:</strong> Manufacturing and preparation methods</li>
                <li><strong>Specific Lipids:</strong> Fatty acid profiles</li>
                <li><strong>Fiber & Protein:</strong> Structural and functional nutrients</li>
                <li><strong>Phytochemicals:</strong> Plant-based bioactive compounds</li>
              </ul>
            </div>
          </div>

          {/* Score Interpretation */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center mb-4">
              <ChartBarIcon className="w-6 h-6 text-green-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Understanding FCS Scores</h2>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="bg-green-100 text-green-800 p-2 rounded text-center">
                  <div className="font-bold">≥70</div>
                  <div>Encourage</div>
                </div>
                <div className="bg-yellow-100 text-yellow-800 p-2 rounded text-center">
                  <div className="font-bold">31-69</div>
                  <div>Moderation</div>
                </div>
                <div className="bg-red-100 text-red-800 p-2 rounded text-center">
                  <div className="font-bold">≤30</div>
                  <div>Minimize</div>
                </div>
              </div>
              <div className="text-sm text-gray-600 space-y-2">
                <p>
                  <strong>Scientific Validation:</strong> Validated against health outcomes in nearly 50,000 U.S. adults, 
                  demonstrating 7% lower all-cause mortality risk per standard deviation increase.
                </p>
                <p>
                  <strong>Unique Features:</strong> Unlike other systems, FCS can evaluate all food categories 
                  from single ingredients to complex mixed meals using the same algorithmic framework.
                </p>
              </div>
            </div>
          </div>
        </div>

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

        {/* NOVA Category Information */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">NOVA Food Processing Categories in FCS</h2>
          <div className="mb-4 text-sm text-gray-600">
            <p><strong>NOVA Classification Integration:</strong> NOVA processing level contributes to Domain 6 (Processing) scoring, 
            with ultra-processed foods receiving -10 points and minimally processed foods receiving 0 points (optimal).</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div className="bg-green-50 border border-green-200 rounded p-3">
              <h3 className="font-medium text-green-800 mb-1">Group 1: Minimally Processed</h3>
              <p className="text-green-700 mb-2">Unprocessed or minimally processed foods like fresh fruits, vegetables, grains, and meats.</p>
              <div className="font-semibold text-green-800">FCS Processing Score: 0 (optimal)</div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
              <h3 className="font-medium text-yellow-800 mb-1">Group 2: Culinary Ingredients</h3>
              <p className="text-yellow-700 mb-2">Processed culinary ingredients like oils, butter, sugar, and salt used in cooking.</p>
              <div className="font-semibold text-yellow-800">FCS Processing Score: -6 (moderate penalty)</div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded p-3">
              <h3 className="font-medium text-orange-800 mb-1">Group 3: Processed Foods</h3>
              <p className="text-orange-700 mb-2">Processed foods like canned vegetables, cheese, and bread made by combining Groups 1 & 2.</p>
              <div className="font-semibold text-orange-800">FCS Processing Score: -7.5 (higher penalty)</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <h3 className="font-medium text-red-800 mb-1">Group 4: Ultra-Processed</h3>
              <p className="text-red-700 mb-2">Formulations with little or no intact Group 1 foods, often with additives and preservatives.</p>
              <div className="font-semibold text-red-800">FCS Processing Score: -10 (maximum penalty)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}