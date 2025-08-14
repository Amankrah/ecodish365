'use client';

import React from 'react';
import Link from 'next/link';
import { 
  ChartBarIcon,
  BeakerIcon,
  GlobeAltIcon,
  UserGroupIcon,
  ArrowRightIcon,
  ScaleIcon,
  DocumentChartBarIcon,
  HeartIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'Environmental Indicators (LCA + Monetization)',
    description: 'Run ReCiPe 2016 midpoint analysis across 18 impact categories (per 100 kcal), with Canadian regionalization and optional monetization (CAD) of impacts like carbon, water, land use, and air quality.',
    icon: GlobeAltIcon,
    href: '/environmental',
    status: 'Available',
  },
  {
    name: 'Canadian Nutrient File (CNF) Database',
    description: 'Access Canada\'s official nutrition database with 5,000+ foods and 150+ nutrients. Powerful search, filtering, comparison, and analysis — tightly integrated with environmental indicators and meal assessment.',
    icon: ChartBarIcon,
    href: '/cnf',
    status: 'Available',
  },
  {
    name: 'Health Star Rating (HSR)',
    description: 'Calculate official HSR with full scoring breakdown. Use alongside environmental indicators to evaluate both nutritional quality and environmental performance.',
    icon: DocumentChartBarIcon,
    href: '/hsr',
    status: 'Available',
  },
  {
    name: 'Food Compass Score (FCS)',
    description: 'Assess foods with FCS 2.0 across 9 domains and 54 attributes. Pair with LCA monetization (CAD) for environmental cost context.',
    icon: SparklesIcon,
    href: '/fcs',
    status: 'Available',
  },
  {
    name: 'Healthy Eating Food Index (HEFI)',
    description: 'Canadian validated dietary quality assessment (10 components). Combine with environmental indicators to guide sustainable dietary patterns.',
    icon: ScaleIcon,
    href: '/hefi',
    status: 'Available',
  },
  {
    name: 'Health and Nutritional Impact (HENI)',
    description: 'DALY-based health impact estimation from dietary factors. Complements environmental LCA for holistic “health + planet” insights.',
    icon: HeartIcon,
    href: '/heni',
    status: 'Available',
  },
  {
    name: 'Meal Creation & Sharing',
    description: 'Build meals and instantly see nutrition scores (HSR/FCS/HEFI/HENI) plus environmental indicators and monetized costs in CAD.',
    icon: UserGroupIcon,
    href: '/meals',
    status: 'Available',
  },
];

const userTypes = [
  {
    name: 'Researchers',
    description: 'Run environmental LCA (ReCiPe 2016), monetize impacts (CAD), and analyze nutrition with CNF, HSR, FCS, HEFI, and HENI for publishable, reproducible insights.',
    icon: BeakerIcon,
  },
  {
    name: 'Policy Makers',
    description: 'Use monetized environmental impacts (CAD), carbon/water/land indicators, and health metrics to inform policy, procurement, and dietary guidelines.',
    icon: UserGroupIcon,
  },
  {
    name: 'Health Professionals',
    description: 'Support counseling with combined nutrition quality and environmental performance to guide healthier, more sustainable choices.',
    icon: HeartIcon,
  },
];

const stats = [
  { label: 'Foods in CNF Database', value: '5,000+' },
  { label: 'Nutrients Tracked', value: '150+' },
  { label: 'LCA Impact Categories', value: '18' },
  { label: 'Monetized Impact Types (CAD)', value: '16+' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-accent-50 py-20 sm:py-32">
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-6xl font-bold tracking-tight">
              <span className="text-gray-900">Environmental</span>{' '}
              <span className="text-gradient">Nutrition Intelligence</span>{' '}
              <span className="text-gray-900">Platform</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Analyze food and meals through both nutritional quality and environmental performance. Run LCA across 18 categories, 
              monetize impacts in CAD, and pair with CNF, HSR, FCS, HEFI, and HENI — for decisions that are good for people and the planet.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/cnf"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-primary hover:opacity-90 transition-opacity duration-200 shadow-lg hover:shadow-xl"
              >
                Explore CNF Database
                <ArrowRightIcon className="ml-2 w-5 h-5" />
              </Link>
              <Link
                href="/environmental/calculate"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-sm"
              >
                Analyze Environmental Indicators
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold text-primary-600">
                  {stat.value}
                </div>
                <div className="mt-2 text-sm text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Integrated Environmental + Nutrition Tools
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Explore environmental indicators (ReCiPe 2016 + monetization in CAD) alongside Canada&apos;s CNF nutrition database, HSR, FCS, HEFI, and HENI.
              Professional-grade analytics for evidence-based, sustainable dietary assessment.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.name}
                className="card relative"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg flex items-center justify-center bg-gray-100">
                    <feature.icon className="w-6 h-6 text-gray-600" />
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    feature.status === 'Available' 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {feature.status}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.name}
                </h3>
                <p className="text-gray-600 mb-4 text-sm leading-relaxed">
                  {feature.description}
                </p>

                {feature.status === 'Available' ? (
                  <Link
                    href={feature.href}
                    className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium text-sm"
                  >
                    Explore Tool
                    <ArrowRightIcon className="ml-1 w-4 h-4" />
                  </Link>
                ) : (
                  <span className="text-gray-400 text-sm font-medium">
                    Coming Soon
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Target Audience Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">Built for Environmental Nutrition</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              EcoDish365 serves researchers, policy makers, and health professionals with combined environmental and nutrition analytics
              to support healthier people and a healthier planet.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {userTypes.map((userType) => (
              <div key={userType.name} className="text-center">
                <div className="w-16 h-16 bg-gradient-accent rounded-full flex items-center justify-center mx-auto mb-6">
                  <userType.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {userType.name}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {userType.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-primary">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">Start Exploring Environmental Nutrition</h2>
          <p className="text-xl text-primary-100 mb-8 leading-relaxed">
            Begin with the CNF database and our Environmental Indicators to evaluate both nutritional quality and environmental performance.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/cnf"
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-lg text-primary-600 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-lg"
            >
              <ChartBarIcon className="mr-2 w-5 h-5" />
              Launch CNF Explorer
            </Link>
            <Link
              href="/environmental/calculate"
              className="inline-flex items-center justify-center px-8 py-3 border border-white text-base font-medium rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-colors duration-200"
            >
              <GlobeAltIcon className="mr-2 w-5 h-5" />
              Analyze Environmental Indicators
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
