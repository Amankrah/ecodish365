'use client';

import React from 'react';
import Link from 'next/link';
import {
  Calculator,
  Building,
  Heart,
  TrendingUp,
  Shield,
  BarChart3
} from 'lucide-react';

export default function HENIHomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Hero Section */}
      <div className="relative py-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="mb-8">
            <div className="inline-flex items-center justify-center p-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-4">
              <Heart className="h-12 w-12 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              HENI Health Impact System
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Comprehensive health impact analysis using evidence-based Disability Adjusted Life Years (DALY) methodology. 
              Discover how food choices affect your health and inform policy decisions.
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <Link href="/heni/calculate" className="group">
              <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 group-hover:border-blue-200">
                <div className="inline-flex items-center justify-center p-3 bg-blue-100 rounded-full mb-4 group-hover:bg-blue-200 transition-colors">
                  <Calculator className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Individual Calculator</h3>
                <p className="text-gray-600 leading-relaxed">
                  Analyze the health impact of your meals with personalized HENI scoring, 
                  risk factor breakdown, and actionable health recommendations.
                </p>
                <div className="mt-4 text-blue-600 font-medium group-hover:text-blue-700">
                  Start Analysis →
                </div>
              </div>
            </Link>

            

            <Link href="/heni/policy-dashboard" className="group">
              <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 group-hover:border-green-200">
                <div className="inline-flex items-center justify-center p-3 bg-green-100 rounded-full mb-4 group-hover:bg-green-200 transition-colors">
                  <Building className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Policy Dashboard</h3>
                <p className="text-gray-600 leading-relaxed">
                  Population-level dietary pattern analysis for evidence-based policy making, 
                  economic impact assessment, and intervention planning.
                </p>
                <div className="mt-4 text-green-600 font-medium group-hover:text-green-700">
                  Access Dashboard →
                </div>
              </div>
            </Link>
          </div>

          {/* Key Features */}
          <div className="mt-20 bg-white rounded-2xl p-8 shadow-lg">
            <h2 className="text-2xl font-bold text-gray-900 mb-8">Evidence-Based Health Analysis</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">14</div>
                <div className="text-gray-600">Risk Factors</div>
                <div className="text-xs text-gray-500 mt-1">Food groups & nutrients</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-2">25+</div>
                <div className="text-gray-600">Disease Categories</div>
                <div className="text-xs text-gray-500 mt-1">From GBD studies</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-2">1000+</div>
                <div className="text-gray-600">Research Papers</div>
                <div className="text-xs text-gray-500 mt-1">Epidemiological evidence</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-amber-600 mb-2">195</div>
                <div className="text-gray-600">Countries</div>
                <div className="text-xs text-gray-500 mt-1">Global applicability</div>
              </div>
            </div>
          </div>

          {/* Methodology Overview */}
          <div className="mt-16 grid md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <div className="inline-flex items-center justify-center p-2 bg-blue-100 rounded-lg mb-4">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">DALY Methodology</h3>
              <p className="text-sm text-gray-600">
                Based on Global Burden of Disease studies, quantifying health impacts in 
                Disability Adjusted Life Years for precise health assessment.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <div className="inline-flex items-center justify-center p-2 bg-green-100 rounded-lg mb-4">
                <Shield className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Evidence-Based</h3>
              <p className="text-sm text-gray-600">
                All risk factor assessments grounded in peer-reviewed epidemiological 
                research and meta-analyses from leading health institutions.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <div className="inline-flex items-center justify-center p-2 bg-purple-100 rounded-lg mb-4">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Multi-Scale Analysis</h3>
              <p className="text-sm text-gray-600">
                From individual health insights to population-level policy recommendations, 
                serving diverse users with actionable intelligence.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}