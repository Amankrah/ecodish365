'use client';
/**
 * Environmental Visualization - Core Visual Component
 * Interactive charts and visualizations for environmental impact data
 */

import React from 'react';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import {
  Globe,
  Droplets,
  TreePine,
  Zap,
  AlertTriangle,
} from 'lucide-react';
import type { EnvironmentalImpactResult, LCAResults, EndpointImpacts, SustainabilityScore, LCABands } from '../../lib/api';
import { UncertaintyBandBar } from './UncertaintyBandBar';

interface EnvironmentalVisualizationProps {
  results: EnvironmentalImpactResult;
}

export const EnvironmentalVisualization: React.FC<EnvironmentalVisualizationProps> = ({ results }) => {
  type MealAnalysis = Required<EnvironmentalImpactResult>['data']['meal_analysis'];
  const analysis = (results?.data?.meal_analysis || {}) as Partial<MealAnalysis>;
  const lca = (analysis?.lca_results || {}) as Partial<LCAResults>;
  const bands: LCABands = (analysis?.lca_results_bands as LCABands) || {};
  const endpoints = (analysis?.endpoint_impacts || {}) as Partial<EndpointImpacts>;
  const sustainability = (analysis?.sustainability_score || {}) as Partial<SustainabilityScore>;

  // v1 scope trim: only the 3 literature-anchored midpoint categories are
  // consumed. Acidification, fine PM, eutrophication and the other 12 used
  // to be visualised here but were silently 0 after the trim — removed
  // entirely; the full methodology + reasoning lives in the LCABreakdown
  // accordion.
  const keyImpacts = [
    {
      key: 'Global warming' as const,
      label: 'Climate Change',
      icon: Globe,
      color: 'text-red-600',
      bandColor: 'rose' as const,
      value: lca['Global warming'] || 0,
      band: bands['Global warming'],
      unit: 'kg CO₂-eq',
      description: 'IPCC AR5 100-year global warming potential, per 100 kcal of meal'
    },
    {
      key: 'Land use' as const,
      label: 'Land Use',
      icon: TreePine,
      color: 'text-green-600',
      bandColor: 'emerald' as const,
      value: lca['Land use'] || 0,
      band: bands['Land use'],
      unit: 'm²a crop-eq',
      description: 'Agricultural land transformation and occupation, per 100 kcal'
    },
    {
      key: 'Water consumption' as const,
      label: 'Water Use',
      icon: Droplets,
      color: 'text-blue-600',
      bandColor: 'sky' as const,
      value: lca['Water consumption'] || 0,
      band: bands['Water consumption'],
      unit: 'm³',
      description: 'Blue-water consumptive use (Mekonnen & Hoekstra), per 100 kcal'
    },
  ];

  // Removed cross-indicator scaling; display absolute values only

  // Format impact values using backend units; scientific notation for tiny values
  const formatImpactValue = (value: number, unit: string): string => {
    if (!Number.isFinite(value) || value === 0) return `0 ${unit}`;
    const absVal = Math.abs(value);
    if (absVal >= 1) return `${value.toFixed(3)} ${unit}`;
    if (absVal >= 1e-3) return `${value.toFixed(6)} ${unit}`;
    return `${value.toExponential(2)} ${unit}`;
  };

  // Format endpoint impacts with scientific notation for very small values
  const formatEndpointValue = (value: number, unit: string): string => {
    if (!Number.isFinite(value) || value === 0) return `0 ${unit}`;
    const absVal = Math.abs(value);
    if (absVal < 1e-6) return `${value.toExponential(2)} ${unit}`;
    if (absVal < 1e-3) return `${value.toExponential(2)} ${unit}`;
    if (absVal < 1) return `${value.toFixed(6)} ${unit}`;
    return `${value.toFixed(3)} ${unit}`;
  };

  // Removed relative impact level logic

  return (
    <div className="space-y-6">
      {/* Impact Categories Bar Chart */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Environmental Impact Categories
        </h4>
        <div className="space-y-4">
          {keyImpacts.map((impact) => {
            const IconComponent = impact.icon;
            return (
              <div key={impact.key} className="space-y-2 border-b border-gray-100 pb-3 last:border-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <IconComponent className={`h-4 w-4 ${impact.color}`} />
                    <span className="text-sm font-medium text-gray-900">
                      {impact.label}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-gray-900 tabular-nums">
                    {formatImpactValue(impact.value, impact.unit)}
                  </span>
                </div>
                <div className="text-xs text-gray-600">
                  {impact.description}
                </div>
                {impact.band && (
                  <UncertaintyBandBar band={impact.band} unit={impact.unit} color={impact.bandColor} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Endpoint Impact Summary */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-4">Endpoint Impact Summary</h4>
        <div className="grid grid-cols-1 gap-3">
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-red-900">Human Health Impact</span>
              <span className="text-sm font-bold text-red-900">
                {formatEndpointValue(endpoints?.['Human Health'] ?? 0, 'DALY')}
              </span>
            </div>
            <div className="text-xs text-red-700 mt-1">
              Disability Adjusted Life Years - Health burden from environmental impacts
            </div>
          </div>

          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-green-900">Ecosystem Quality Impact</span>
              <span className="text-sm font-bold text-green-900">
                {formatEndpointValue(endpoints?.['Ecosystems'] ?? 0, 'sp.year')}
              </span>
            </div>
            <div className="text-xs text-green-700 mt-1">
              Species extinction years - Biodiversity loss from environmental damage
            </div>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-900">Resource Scarcity Impact</span>
              <span className="text-xs font-medium text-orange-700">Not estimable in v1</span>
            </div>
            <div className="text-xs text-gray-600 mt-1">
              Both Fossil and Mineral resource scarcity midpoints are excluded from the v1
              consumed vector (no per-food-group literature grounding). Restored when
              licensed AGRIBALYSE-LCI re-scoring lands.
            </div>
          </div>
        </div>
      </div>

      {/* Sustainability Score Breakdown */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-4">Sustainability Score Components</h4>
        <div className="space-y-3">
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-green-900">Environmental Performance</span>
              <span className="text-sm font-bold text-green-900">
                {(sustainability.environmental_score ?? 0).toFixed(0)}/100
              </span>
            </div>
            <Progress value={sustainability.environmental_score ?? 0} className="h-2" />
            <div className="text-xs text-green-700 mt-1">
              LCA impact assessment across all environmental categories
            </div>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-900">Nutritional Quality</span>
              <span className="text-sm font-bold text-blue-900">
                {(sustainability.nutritional_score ?? 0).toFixed(0)}/100
              </span>
            </div>
            <Progress value={sustainability.nutritional_score ?? 0} className="h-2" />
            <div className="text-xs text-blue-700 mt-1">
              Nutrient density and nutritional value assessment
            </div>
          </div>

          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-purple-900">Processing Level</span>
              <span className="text-sm font-bold text-purple-900">
                {(sustainability.processing_score ?? 0).toFixed(0)}/100
              </span>
            </div>
            <Progress value={sustainability.processing_score ?? 0} className="h-2" />
            <div className="text-xs text-purple-700 mt-1">
              Food processing intensity and naturalness assessment
            </div>
          </div>
        </div>
      </div>

      {/* Overall Sustainability Visualization */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-gray-900">Overall Sustainability Rating</h4>
          <Badge 
            className={`text-lg px-3 py-1 ${
              (sustainability.overall_sustainability_score ?? 0) >= 80 ? 'text-green-600' :
              (sustainability.overall_sustainability_score ?? 0) >= 60 ? 'text-blue-600' :
              (sustainability.overall_sustainability_score ?? 0) >= 40 ? 'text-yellow-600' :
              (sustainability.overall_sustainability_score ?? 0) >= 20 ? 'text-orange-600' :
              'text-red-600'
            }`}
          >
            {sustainability.sustainability_rating || 'Unknown'}
          </Badge>
        </div>
        
        <div className="relative mb-2">
          <Progress value={sustainability.overall_sustainability_score ?? 0} className="h-4" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold text-white drop-shadow">
              {(sustainability.overall_sustainability_score ?? 0).toFixed(0)}/100
            </span>
          </div>
        </div>
        
        <div className="text-sm text-gray-600">
          Comprehensive sustainability assessment combining environmental impact, 
          nutritional quality, and processing considerations
        </div>
      </div>

      {/* Impact Interpretation */}
      <div className="bg-yellow-50 p-4 rounded-lg">
        <h4 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          Impact Interpretation
        </h4>
        <div className="space-y-2 text-sm text-yellow-800">
          <p>
            <strong>Single Score:</strong> {(analysis?.single_score ?? 0).toFixed(4)} ReCiPe points 
            (lower is better - represents combined environmental burden)
          </p>
          {/* Removed cross-category "Top Impact" comparison */}
          <p>
            <strong>Benchmark:</strong> This meal&apos;s sustainability score of{' '}
            {(sustainability.overall_sustainability_score ?? 0).toFixed(0)}/100 indicates{' '}
            {(sustainability.overall_sustainability_score ?? 0) >= 60 ? 'above-average' : 
             (sustainability.overall_sustainability_score ?? 0) >= 40 ? 'average' : 'below-average'} 
            environmental and nutritional performance
          </p>
        </div>
      </div>
    </div>
  );
};

export default EnvironmentalVisualization;