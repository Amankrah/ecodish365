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
  CubeIcon,
  DocumentChartBarIcon,
  HeartIcon
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'CNF Database Explorer',
    description: 'Comprehensive exploration of the Canadian Nutrient File with advanced search, comparison, and analytics capabilities.',
    icon: ChartBarIcon,
    href: '/cnf',
    status: 'Available',
    highlight: true,
  },
  {
    name: 'Health Star Rating (HSR)',
    description: 'Calculate and analyze Health Star Ratings for foods using the Australian front-of-pack labeling system.',
    icon: HeartIcon,
    href: '/hsr',
    status: 'Available',
  },
  {
    name: 'Food Classification System (FCS)',
    description: 'Advanced food classification based on processing levels and nutritional profiles.',
    icon: CubeIcon,
    href: '/calculators/fcs',
    status: 'Coming Soon',
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
    name: 'Policy Analytics',
    description: 'Advanced analytics and reporting tools for policy makers and public health officials.',
    icon: DocumentChartBarIcon,
    href: '/analytics',
    status: 'Coming Soon',
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
              <span className="text-gray-900">Environmental</span>{' '}
              <span className="text-gradient">Nutrition</span>{' '}
              <span className="text-gray-900">& Health Tools</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              A comprehensive platform empowering researchers, individuals, and policy makers 
              with advanced nutritional analysis, environmental impact assessment, and health evaluation tools.
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
              Comprehensive Research Tools
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Access a suite of advanced tools designed for nutritional research, 
              health assessment, and environmental impact analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.name}
                className={`card relative ${
                  feature.highlight ? 'ring-2 ring-primary-200 bg-gradient-to-br from-primary-5 to-white' : ''
                }`}
              >
                {feature.highlight && (
                  <div className="absolute -top-3 left-6">
                    <span className="bg-primary-600 text-white px-3 py-1 text-xs font-medium rounded-full">
                      Featured
                    </span>
                  </div>
                )}
                
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    feature.highlight ? 'bg-primary-600' : 'bg-gray-100'
                  }`}>
                    <feature.icon className={`w-6 h-6 ${
                      feature.highlight ? 'text-white' : 'text-gray-600'
                    }`} />
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
              href="/analytics"
              className="inline-flex items-center justify-center px-8 py-3 border border-white text-base font-medium rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-colors duration-200"
            >
              View Analytics
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
