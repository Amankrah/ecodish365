'use client';

import React, { useState, useEffect } from 'react';
import { Metadata } from 'next';
import { 
  MagnifyingGlassIcon,
  ChartBarIcon,
  ScaleIcon,
  DocumentTextIcon,
  EyeIcon,
  ArrowTopRightOnSquareIcon,
  ClockIcon,
  CircleStackIcon,
  CubeIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';
import { CNFApiService, DatabaseStats } from '@/lib/api';
import Link from 'next/link';
import toast from 'react-hot-toast';

const quickActions = [
  {
    name: 'Discover by Nutrient',
    description: 'Find foods by iron, fibre, sodium, and other nutrient ranges',
    icon: BeakerIcon,
    href: '/cnf/discover',
    color: 'from-teal-500 to-cyan-600',
  },
  {
    name: 'Advanced Search',
    description: 'Search foods with filters and relevance scoring',
    icon: MagnifyingGlassIcon,
    href: '/cnf/search',
    color: 'from-blue-500 to-blue-600',
  },
  {
    name: 'Food Comparison',
    description: 'Compare nutritional content of multiple foods',
    icon: ScaleIcon,
    href: '/cnf/compare',
    color: 'from-green-500 to-green-600',
  },
  {
    name: 'Database Analytics',
    description: 'Explore database statistics and insights',
    icon: ChartBarIcon,
    href: '/cnf/analytics',
    color: 'from-purple-500 to-purple-600',
  },
  {
    name: 'Browse by Groups',
    description: 'Explore foods organized by food groups',
    icon: CubeIcon,
    href: '/cnf/groups',
    color: 'from-orange-500 to-orange-600',
  },
];

const features = [
  {
    title: 'Advanced Search',
    description: 'Intelligent search with relevance scoring, pagination, and comprehensive filtering options. Includes a source filter to scope to CNF only, WAFCT only, or both.',
    items: ['Text-based search', 'Source filter (CNF / WAFCT / both)', 'AI-enhanced LLM ranking', 'Nutrient + food-group filtering']
  },
  {
    title: 'Food Comparison',
    description: 'Compare nutritional profiles of multiple foods side-by-side. Cross-database comparisons (CNF vs WAFCT) surface per-source provenance badges.',
    items: ['Multi-food comparison', 'Cross-database (CNF + WAFCT)', 'Per-source provenance badges', 'Visual charts']
  },
  {
    title: 'Database Insights',
    description: 'Statistics across both food-composition databases — Health Canada CNF (5,691 foods) and FAO/INFOODS WAFCT 2019 (1,028 foods). 14 WAFCT food groups added at FoodGroupID 50-63.',
    items: ['Combined database stats', 'INFOODS↔CNF nutrient bridge (48 mappings)', 'WAFCT mineral-bias caveats in scoring', '195 canonical WAFCT recipes (sheet 09)']
  },
];

export default function CNFDashboard() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);

  useEffect(() => {
    loadDatabaseStats();
  }, []);

  const loadDatabaseStats = async () => {
    try {
      const data = await CNFApiService.getDatabaseStatistics();
      setStats(data);
    } catch (error) {
      console.error('Failed to load database statistics:', error);
      toast.error('Failed to load database statistics');
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Food Composition Database Explorer
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl">
            Explore <strong>two food-composition databases side by side</strong>: Health
            Canada&rsquo;s Canadian Nutrient File (CNF — 5,691 foods, 150+ nutrients) and
            FAO/INFOODS&rsquo; West African Food Composition Table 2019 (WAFCT — 1,028
            foods including fonio, baobab, dawadawa, gari, egusi, and other West African
            staples). Search, compare, and analyze across either or both sources.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center px-2 py-1 rounded border bg-gray-100 text-gray-700 border-gray-200 font-semibold">
              CNF — Health Canada
            </span>
            <span className="inline-flex items-center px-2 py-1 rounded border bg-amber-100 text-amber-800 border-amber-200 font-semibold">
              WAFCT — FAO/INFOODS
            </span>
            <span className="text-gray-500">
              Source filter on every search lets you scope to one database or combine both.
            </span>
          </div>
        </div>

        {/* Quick Stats */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="stat-card">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <CircleStackIcon className="w-6 h-6 text-primary-600" />
                </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(stats.food_count)}
                  </div>
                  <div className="text-sm text-gray-600">Foods</div>
                  <div className="text-xs text-gray-500">CNF + WAFCT combined</div>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <ChartBarIcon className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(stats.nutrient_types)}
                  </div>
                  <div className="text-sm text-gray-600">Nutrients</div>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <CubeIcon className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(stats.food_groups)}
                  </div>
                  <div className="text-sm text-gray-600">Food Groups</div>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <ClockIcon className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(stats.nutrient_records)}
                  </div>
                  <div className="text-sm text-gray-600">Records</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Researcher workflow */}
        <div className="mb-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Learn a food, then score it</h2>
          <p className="text-gray-600 mb-6 max-w-3xl">
            Use Researcher mode in the toolbar on any explorer page. Open a food profile to see which
            nutrients each published measure reads, then add it to all scores at your chosen portion size.
          </p>
          <ol className="grid md:grid-cols-4 gap-4 text-sm">
            <li className="border border-gray-100 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">1. Search or browse</div>
              <p className="text-gray-600">Find foods by name, group, or AI match across CNF and WAFCT.</p>
            </li>
            <li className="border border-gray-100 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">2. Open the profile</div>
              <p className="text-gray-600">Lens nutrient panels show what healthy eating, star ratings, Food Compass, and health impact draw from the catalogue.</p>
            </li>
            <li className="border border-gray-100 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">3. Compare alternatives</div>
              <p className="text-gray-600">Select up to six foods and contrast key nutrients side by side.</p>
            </li>
            <li className="border border-gray-100 rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-1">4. Score all six lenses</div>
              <p className="text-gray-600">Send foods to all scores for healthy eating, health impact, star ratings, Food Compass, environment, and eating style.</p>
            </li>
          </ol>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/cnf/search" className="btn-primary inline-flex items-center">
              Start in Search
              <MagnifyingGlassIcon className="ml-2 w-4 h-4" />
            </Link>
            <Link href="/scorecard" className="btn-outline inline-flex items-center">
              Open all scores
            </Link>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {quickActions.map((action) => (
              <Link
                key={action.name}
                href={action.href}
                className="group card hover:shadow-xl transition-all duration-200 cursor-pointer"
              >
                <div className={`w-12 h-12 bg-gradient-to-r ${action.color} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`}>
                  <action.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                  {action.name}
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {action.description}
                </p>
                <div className="mt-4 flex items-center text-primary-600 text-sm font-medium group-hover:text-primary-700">
                  Get Started
                  <ArrowTopRightOnSquareIcon className="ml-1 w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Features Overview */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Features</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card">
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 mb-4 leading-relaxed">
                  {feature.description}
                </p>
                <ul className="space-y-2">
                  {feature.items.map((item, itemIndex) => (
                    <li key={itemIndex} className="flex items-center text-sm text-gray-600">
                      <div className="w-2 h-2 bg-primary-500 rounded-full mr-3"></div>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity / Getting Started */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Getting Started */}
          <div className="card">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <DocumentTextIcon className="w-5 h-5 mr-2 text-primary-600" />
              Getting Started
            </h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">1</div>
                <div>
                  <div className="font-medium text-gray-900">Start with Search</div>
                  <div className="text-sm text-gray-600">Try searching for foods like &quot;apple&quot; or &quot;chicken breast&quot;</div>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">2</div>
                <div>
                  <div className="font-medium text-gray-900">Explore Food Details</div>
                  <div className="text-sm text-gray-600">Click on any food to see detailed nutritional information</div>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">3</div>
                <div>
                  <div className="font-medium text-gray-900">Compare Foods</div>
                  <div className="text-sm text-gray-600">Select multiple foods to compare their nutritional profiles</div>
                </div>
              </div>
            </div>
            <div className="mt-6">
              <Link
                href="/cnf/search"
                className="btn-primary inline-flex items-center"
              >
                Start Exploring
                <MagnifyingGlassIcon className="ml-2 w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Database Info */}
          <div className="card">
            <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <CircleStackIcon className="w-5 h-5 mr-2 text-primary-600" />
              Database Information
            </h3>
            <div className="space-y-4 text-sm">
              <div>
                <div className="font-medium text-gray-900 mb-1">Data Source</div>
                <div className="text-gray-600">Canadian Nutrient File (CNF) - Health Canada</div>
              </div>
              <div>
                <div className="font-medium text-gray-900 mb-1">Coverage</div>
                <div className="text-gray-600">Comprehensive nutritional data for Canadian foods</div>
              </div>
              <div>
                <div className="font-medium text-gray-900 mb-1">Last Updated</div>
                <div className="text-gray-600">
                  {stats ? new Date(stats.timestamp).toLocaleDateString() : 'Loading...'}
                </div>
              </div>
              <div>
                <div className="font-medium text-gray-900 mb-1">Quality Assurance</div>
                <div className="text-gray-600">Scientifically validated nutritional data</div>
              </div>
            </div>
            <div className="mt-6">
              <Link
                href="/cnf/analytics"
                className="btn-outline inline-flex items-center"
              >
                View Analytics
                <ChartBarIcon className="ml-2 w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="bg-gradient-to-r from-primary-600 to-accent-600 rounded-xl p-8 text-center text-white">
          <h2 className="text-2xl font-bold mb-4">Ready to Explore?</h2>
          <p className="text-primary-100 mb-6 max-w-2xl mx-auto">
            Dive into the comprehensive Canadian Nutrient File database and discover 
            detailed nutritional information for thousands of foods.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/cnf/search"
              className="inline-flex items-center justify-center px-6 py-3 bg-white text-primary-600 font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Start Searching
              <MagnifyingGlassIcon className="ml-2 w-4 h-4" />
            </Link>
            <Link
              href="/cnf/groups"
              className="inline-flex items-center justify-center px-6 py-3 border border-white text-white font-medium rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors"
            >
              Browse by Groups
              <EyeIcon className="ml-2 w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
} 