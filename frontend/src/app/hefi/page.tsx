'use client';

import React from 'react';
import Link from 'next/link';
import { 
  CalculatorIcon,
  ChartBarIcon,
  UserIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'Calculate HEFI Score',
    description: 'Calculate comprehensive HEFI scores for individual foods or food combinations using Canada\'s validated algorithm.',
    icon: CalculatorIcon,
    href: '/hefi/calculate',
    color: 'bg-blue-500',
  },
  {
    name: 'Compare Foods',
    description: 'Compare HEFI scores across multiple foods to identify healthier options and dietary patterns.',
    icon: ChartBarIcon,
    href: '/hefi/compare',
    color: 'bg-green-500',
  },
  {
    name: 'Food Profile',
    description: 'Get detailed HEFI analysis for individual foods with component breakdowns and recommendations.',
    icon: UserIcon,
    href: '/hefi/food-profile',
    color: 'bg-purple-500',
  },
];

const hefiComponents = [
  { name: 'Vegetables and Fruits', description: 'Adequate intake of vegetables and fruits', maxScore: 10 },
  { name: 'Whole Grains', description: 'Proportion of whole grain foods', maxScore: 5 },
  { name: 'Grain Products Ratio', description: 'Ratio of whole grains to total grains', maxScore: 5 },
  { name: 'Protein Foods', description: 'Adequate protein food intake', maxScore: 5 },
  { name: 'Plant Protein', description: 'Proportion of plant-based proteins', maxScore: 5 },
  { name: 'Beverages', description: 'Recommended beverage choices', maxScore: 10 },
  { name: 'Fatty Acids', description: 'Ratio of unsaturated to saturated fats', maxScore: 10 },
  { name: 'Saturated Fats', description: 'Limitation of saturated fat intake', maxScore: 10 },
  { name: 'Free Sugars', description: 'Limitation of free sugar intake', maxScore: 10 },
  { name: 'Sodium', description: 'Limitation of sodium intake', maxScore: 10 },
];

export default function HEFIPage() {
  return (
    <div className="space-y-12">
      {/* Tools Section */}
      <section>
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            HEFI Analysis Tools
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Choose from our comprehensive HEFI analysis tools to assess dietary quality 
            and make informed nutrition decisions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature) => (
            <Link
              key={feature.name}
              href={feature.href}
              className="card hover:scale-105 transition-all duration-200 group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-lg ${feature.color} flex items-center justify-center group-hover:scale-110 transition-transform duration-200`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <ArrowRightIcon className="w-5 h-5 text-gray-400 group-hover:text-purple-600 transition-colors duration-200" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-purple-600 transition-colors duration-200">
                {feature.name}
              </h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                {feature.description}
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* HEFI Components */}
      <section>
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            HEFI Components
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            The Healthy Eating Food Index evaluates diet quality across 10 key components, 
            with a maximum total score of 80 points.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {hefiComponents.map((component, index) => (
            <div key={component.name} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="text-sm font-semibold text-purple-600 bg-purple-100 px-2 py-1 rounded-full mr-3">
                      C{index + 1}
                    </span>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {component.name}
                    </h3>
                  </div>
                  <p className="text-gray-600 text-sm mb-3">
                    {component.description}
                  </p>
                </div>
                <div className="text-right ml-4">
                  <div className="text-2xl font-bold text-purple-600">
                    {component.maxScore}
                  </div>
                  <div className="text-xs text-gray-500">max points</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-8">
          <div className="inline-flex items-center bg-purple-50 border border-purple-200 rounded-lg px-6 py-4">
            <CheckCircleIcon className="w-6 h-6 text-purple-600 mr-3" />
            <div className="text-left">
              <div className="text-lg font-semibold text-purple-900">
                Maximum HEFI Score: 80 Points
              </div>
              <div className="text-sm text-purple-700">
                Higher scores indicate better alignment with Canada&apos;s Food Guide
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* About HEFI */}
      <section className="bg-white rounded-2xl border border-gray-200 p-8">
        <div className="flex items-start mb-6">
          <InformationCircleIcon className="w-6 h-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              About the Healthy Eating Food Index (HEFI)
            </h2>
            <div className="space-y-4 text-gray-600">
              <p>
                The Healthy Eating Food Index (HEFI-2019) is a validated tool developed by Health Canada 
                to assess how well dietary patterns align with Canada&apos;s Food Guide recommendations.
              </p>
              <p>
                HEFI evaluates diet quality across 10 components that reflect key recommendations from 
                the 2019 Canada&apos;s Food Guide, including adequate consumption of nutritious foods and 
                moderation of nutrients of public health concern.
              </p>
              <p>
                This tool is valuable for researchers, dietitians, and health professionals working 
                to assess and improve dietary quality in Canadian populations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Ready to Start?
        </h2>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/hefi/calculate"
            className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            <CalculatorIcon className="mr-2 w-5 h-5" />
            Calculate HEFI Score
          </Link>
          <Link
            href="/hefi/compare"
            className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-sm"
          >
            <ChartBarIcon className="mr-2 w-5 h-5" />
            Compare Foods
          </Link>
        </div>
      </section>
    </div>
  );
}