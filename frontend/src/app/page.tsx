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
    name: 'Canadian Nutrient File (CNF) Database',
    description: 'Access Canada\'s official nutrition database with 5000+ foods and 150+ nutrients. Advanced search, filtering, comparison, and statistical analysis tools for professional nutrition research.',
    icon: ChartBarIcon,
    href: '/cnf',
    status: 'Available',
  },
  {
    name: 'Health Star Rating Calculator',
    description: 'Calculate official Health Star Ratings using Australia\'s validated front-of-pack labeling algorithm. Compare nutritional quality across foods with detailed scoring breakdowns.',
    icon: HeartIcon,
    href: '/hsr',
    status: 'Available',
  },
  {
    name: 'Food Compass Score Calculator',
    description: 'Professional food quality assessment using the scientifically validated FCS 2.0 algorithm. Analyze 54 nutritional attributes across 9 domains for comprehensive food evaluation.',
    icon: SparklesIcon,
    href: '/fcs',
    status: 'Available',
  },
  {
    name: 'Healthy Eating Index (HENI)',
    description: 'Assess diet quality using various healthy eating indices and nutritional guidelines.',
    icon: ScaleIcon,
    href: '/calculators/heni',
    status: 'Coming Soon',
  },
  {
    name: 'Environmental Impact',
    description: 'Analyze the environmental footprint of foods including carbon, water, and land use.',
    icon: GlobeAltIcon,
    href: '/calculators/environmental',
    status: 'Coming Soon',
  },
  {
    name: 'HEFI Score',
    description: 'Healthy Eating Food Index scoring system for comprehensive dietary quality assessment.',
    icon: DocumentChartBarIcon,
    href: '/hefi',
    status: 'Available',
  },
];

const userTypes = [
  {
    name: 'Researchers',
    description: 'Access comprehensive nutritional databases and analytical tools for food and nutrition research.',
    icon: BeakerIcon,
  },
  {
    name: 'Policy Makers',
    description: 'Make informed decisions with evidence-based nutritional data and environmental impact assessments.',
    icon: UserGroupIcon,
  },
  {
    name: 'Health Professionals',
    description: 'Utilize advanced nutritional analysis tools to support patient care and dietary recommendations.',
    icon: HeartIcon,
  },
];

const stats = [
  { label: 'Foods in CNF Database', value: '5,000+' },
  { label: 'Nutrients Tracked', value: '150+' },
  { label: 'Food Groups', value: '20+' },
  { label: 'Research Tools', value: '6+' },
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
              <span className="text-gray-900">Professional</span>{' '}
              <span className="text-gradient">Nutrition Analysis</span>{' '}
              <span className="text-gray-900">& Food Research Platform</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Advanced nutrition analysis platform with Canadian Nutrient File database, Health Star Rating calculator, 
              Food Compass Score assessment, and environmental impact tools. Trusted by researchers, dietitians, 
              and health professionals worldwide for evidence-based nutrition research and food quality analysis.
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
                href="#features"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors duration-200 shadow-sm"
              >
                Learn More
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
              Professional Nutrition Analysis Tools
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Access Canada&apos;s most comprehensive nutrition database with 5000+ foods, calculate Health Star Ratings, 
              Food Compass Scores, and assess environmental impact. Professional-grade tools for accurate 
              nutritional research and evidence-based dietary analysis.
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
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Built for Professionals
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              EcoDish365 serves researchers, policy makers, and health professionals 
              with the tools they need to make informed decisions.
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
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Start Exploring Nutritional Data Today
          </h2>
          <p className="text-xl text-primary-100 mb-8 leading-relaxed">
            Begin with our comprehensive Canadian Nutrient File database explorer 
            and discover insights from over 5,000 foods and 150+ nutrients.
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
              href="/fcs"
              className="inline-flex items-center justify-center px-8 py-3 border border-white text-base font-medium rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-colors duration-200"
            >
              <SparklesIcon className="mr-2 w-5 h-5" />
              Try FCS Calculator
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
