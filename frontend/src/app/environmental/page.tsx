/**
 * Environmental Impact Main Page - Landing and Overview
 * Comprehensive environmental analysis suite for sustainable food choices
 */

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Leaf,
  Globe,
  Calculator,
  BarChart3,
  Search,
  Droplets,
  TreePine,
  Factory,
  DollarSign,
  Users,
  BookOpen,
  Zap,
  ArrowRight,
  CheckCircle,
  Target,
  Award,
} from 'lucide-react';

export default function EnvironmentalMainPage() {
  const features = [
    {
      icon: Calculator,
      title: 'Environmental Calculator',
      description: 'Analyze your meal\'s environmental impact using comprehensive LCA methodology',
      href: '/environmental/calculate',
      color: 'from-green-500 to-emerald-500',
      benefits: ['18 Impact Categories', 'Canadian Factors', 'Economic Valuation'],
    },
    {
      icon: BarChart3,
      title: 'Food Comparison',
      description: 'Compare environmental impacts of different foods side-by-side',
      href: '/environmental/compare',
      color: 'from-blue-500 to-cyan-500',
      benefits: ['Side-by-Side Analysis', 'User-Tailored Insights', 'Best/Worst Identification'],
    },
    {
      icon: Search,
      title: 'Food Profile',
      description: 'Get detailed environmental profiles for individual foods',
      href: '/environmental/food-profile',
      color: 'from-purple-500 to-indigo-500',
      benefits: ['Comprehensive Profiling', 'Comparative Context', 'Similar Foods Analysis'],
    },
  ];

  const impactCategories = [
    {
      icon: Globe,
      name: 'Climate Change',
      description: 'Carbon footprint and global warming potential',
      unit: 'kg CO₂-eq',
      color: 'text-red-600 bg-red-100',
    },
    {
      icon: Droplets,
      name: 'Water Impact',
      description: 'Freshwater consumption and quality effects',
      unit: 'm³ / kg P-eq',
      color: 'text-blue-600 bg-blue-100',
    },
    {
      icon: TreePine,
      name: 'Land Use',
      description: 'Agricultural land occupation and transformation',
      unit: 'm²a crop-eq',
      color: 'text-green-600 bg-green-100',
    },
    {
      icon: Factory,
      name: 'Ecosystem Quality',
      description: 'Biodiversity and ecosystem health impacts',
      unit: 'species.year',
      color: 'text-purple-600 bg-purple-100',
    },
  ];

  const userTypes = [
    {
      icon: Users,
      type: 'Individual',
      description: 'Personal sustainability insights with practical recommendations',
      features: ['Easy-to-understand summaries', 'Actionable recommendations', 'Cost comparisons'],
    },
    {
      icon: BookOpen,
      type: 'Researcher',
      description: 'Detailed scientific analysis with methodological transparency',
      features: ['Complete LCA breakdown', 'Technical documentation', 'Uncertainty analysis'],
    },
    {
      icon: Target,
      type: 'Policy',
      description: 'Policy-relevant insights for decision makers and regulations',
      features: ['Population-level impacts', 'Economic valuations', 'Intervention priorities'],
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-emerald-50">
      {/* Hero Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center mb-6">
            <Leaf className="h-12 w-12 text-green-500 mr-4" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Environmental Impact Analysis
            </h1>
          </div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Comprehensive Life Cycle Assessment (LCA) suite for sustainable food choices. 
            Analyze environmental impacts using ReCiPe 2016 methodology with Canadian-specific factors 
            and economic valuation.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Badge className="bg-green-100 text-green-700 px-4 py-2 text-sm">
              <CheckCircle className="h-4 w-4 mr-2" />
              18 Impact Categories
            </Badge>
            <Badge className="bg-blue-100 text-blue-700 px-4 py-2 text-sm">
              <Globe className="h-4 w-4 mr-2" />
              Canadian Factors
            </Badge>
            <Badge className="bg-purple-100 text-purple-700 px-4 py-2 text-sm">
              <DollarSign className="h-4 w-4 mr-2" />
              Economic Valuation
            </Badge>
            <Badge className="bg-orange-100 text-orange-700 px-4 py-2 text-sm">
              <Award className="h-4 w-4 mr-2" />
              ReCiPe 2016 Standard
            </Badge>
          </div>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Comprehensive Environmental Analysis Tools</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Three powerful tools to analyze, compare, and profile the environmental impacts of your food choices
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <Card key={index} className="shadow-lg hover:shadow-xl transition-all duration-300 border-0">
                  <CardHeader className="pb-4">
                    <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4 mx-auto`}>
                      <IconComponent className="h-8 w-8 text-white" />
                    </div>
                    <CardTitle className="text-center text-xl font-bold text-gray-900">
                      {feature.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-center space-y-4">
                    <p className="text-gray-600">{feature.description}</p>
                    
                    <div className="space-y-2">
                      {feature.benefits.map((benefit, benefitIndex) => (
                        <div key={benefitIndex} className="flex items-center justify-center gap-2 text-sm">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-gray-700">{benefit}</span>
                        </div>
                      ))}
                    </div>

                    <Link href={feature.href}>
                      <Button className={`w-full bg-gradient-to-r ${feature.color} hover:opacity-90 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl`}>
                        Get Started
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Impact Categories */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Key Environmental Impact Categories</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our analysis covers 18 comprehensive impact categories using the scientifically validated ReCiPe 2016 methodology
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {impactCategories.map((category, index) => {
              const IconComponent = category.icon;
              return (
                <Card key={index} className="shadow-lg border-0">
                  <CardContent className="p-6 text-center">
                    <div className={`w-12 h-12 rounded-full ${category.color} flex items-center justify-center mb-4 mx-auto`}>
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2">{category.name}</h3>
                    <p className="text-sm text-gray-600 mb-3">{category.description}</p>
                    <Badge variant="outline" className="text-xs">
                      {category.unit}
                    </Badge>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600 mb-4">
              <strong>Complete Coverage:</strong> Plus 14 additional impact categories including toxicity, 
              resource depletion, ozone formation, and radiation exposure
            </p>
            <Badge className="bg-indigo-100 text-indigo-700">
              <Zap className="h-4 w-4 mr-2" />
              18 Total Impact Categories Analyzed
            </Badge>
          </div>
        </div>
      </section>

      {/* User Types */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Tailored for Every User</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Get personalized insights and explanations designed for your specific needs and expertise level
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {userTypes.map((user, index) => {
              const IconComponent = user.icon;
              return (
                <Card key={index} className="shadow-lg border-0">
                  <CardHeader className="pb-4">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-r from-gray-600 to-gray-800 flex items-center justify-center mb-4 mx-auto">
                      <IconComponent className="h-8 w-8 text-white" />
                    </div>
                    <CardTitle className="text-center text-xl font-bold text-gray-900">
                      {user.type}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-center space-y-4">
                    <p className="text-gray-600">{user.description}</p>
                    
                    <div className="space-y-2">
                      {user.features.map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-center justify-center gap-2 text-sm">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-gray-700">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Methodology */}
      <section className="py-16 px-6 bg-gradient-to-r from-green-500 to-blue-500">
        <div className="max-w-6xl mx-auto text-center text-white">
          <h2 className="text-3xl font-bold mb-6">Scientific Methodology</h2>
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4">LCA Framework</h3>
              <ul className="space-y-2 text-left">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  ReCiPe 2016 v1.1 Midpoint (H) methodology
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Cradle-to-gate system boundaries
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  100-year time horizon for climate impacts
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Endpoint impact characterization
                </li>
              </ul>
            </div>
            <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4">Canadian Adaptations</h3>
              <ul className="space-y-2 text-left">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Climate factors (+15% Arctic adjustment)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Water abundance factors (-30% adjustment)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Land use factors (-20% adjustment)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  CAD $185/tonne CO₂ social cost of carbon
                </li>
              </ul>
            </div>
          </div>
          <p className="text-lg opacity-90">
            Our methodology follows internationally recognized standards while incorporating 
            Canadian-specific environmental and economic factors for accurate regional assessment.
          </p>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gray-900 text-white text-center">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold mb-6">Start Your Environmental Analysis Today</h2>
          <p className="text-xl mb-8 opacity-90">
            Make informed decisions about your food choices with comprehensive environmental impact analysis
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/environmental/calculate">
              <Button size="lg" className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200">
                <Calculator className="mr-2 h-5 w-5" />
                Analyze Your Meal
              </Button>
            </Link>
            <Link href="/environmental/compare">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-gray-900 font-semibold py-3 px-8 rounded-lg transition-all duration-200">
                <BarChart3 className="mr-2 h-5 w-5" />
                Compare Foods
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}