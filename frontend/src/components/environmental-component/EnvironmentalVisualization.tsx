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
  Factory,
  Zap,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import type { EnvironmentalImpactResult, LCAResults, EndpointImpacts, SustainabilityScore } from '../../lib/api';

interface EnvironmentalVisualizationProps {
  results: EnvironmentalImpactResult;
}

export const EnvironmentalVisualization: React.FC<EnvironmentalVisualizationProps> = ({ results }) => {
  type MealAnalysis = Required<EnvironmentalImpactResult>['data']['meal_analysis'];
  const analysis = (results?.data?.meal_analysis || {}) as Partial<MealAnalysis>;
  const lca = (analysis?.lca_results || {}) as Partial<LCAResults>;
  const endpoints = (analysis?.endpoint_impacts || {}) as Partial<EndpointImpacts>;
  const sustainability = (analysis?.sustainability_score || {}) as Partial<SustainabilityScore>;

  // Define impact categories with their icons and colors
  const keyImpacts = [
    {
      key: 'Global warming',
      label: 'Climate Change',
      icon: Globe,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      value: lca['Global warming'] || 0,
      unit: 'kg CO₂-eq',
      description: 'Contribution to global warming and climate change'
    },
    {
      key: 'Water consumption',
      label: 'Water Usage',
      icon: Droplets,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      value: lca['Water consumption'] || 0,
      unit: 'm³',
      description: 'Freshwater consumption for production'
    },
    {
      key: 'Land use',
      label: 'Land Impact',
      icon: TreePine,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      value: lca['Land use'] || 0,
      unit: 'm²a crop-eq',
      description: 'Agricultural land transformation and occupation'
    },
    {
      key: 'Terrestrial acidification',
      label: 'Acidification',
      icon: Factory,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      value: lca['Terrestrial acidification'] || 0,
      unit: 'kg SO₂-eq',
      description: 'Impact on soil and terrestrial ecosystems'
    },
    {
      key: 'Fine particulate matter formation',
      label: 'Air Quality',
      icon: AlertTriangle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      value: lca['Fine particulate matter formation'] || 0,
      unit: 'kg PM2.5-eq',
      description: 'Impact on air quality and human respiratory health'
    },
    {
      key: 'Freshwater eutrophication',
      label: 'Water Quality',
      icon: Droplets,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-100',
      value: lca['Freshwater eutrophication'] || 0,
      unit: 'kg P-eq',
      description: 'Nutrient enrichment of freshwater ecosystems'
    }
  ];

  // Find the maximum value for scaling bars
  const maxValue = Math.max(...keyImpacts.map(impact => impact.value || 0));

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

  // Get impact level indicator
  const getImpactLevel = (value: number, maxVal: number) => {
    const percentage = (value / maxVal) * 100;
    if (percentage >= 80) return { level: 'Very High', color: 'text-red-600', icon: TrendingUp };
    if (percentage >= 60) return { level: 'High', color: 'text-orange-600', icon: TrendingUp };
    if (percentage >= 40) return { level: 'Medium', color: 'text-yellow-600', icon: TrendingUp };
    if (percentage >= 20) return { level: 'Low', color: 'text-blue-600', icon: TrendingDown };
    return { level: 'Very Low', color: 'text-green-600', icon: TrendingDown };
  };

  return (
    <div className="space-y-6">
      {/* Impact Categories Bar Chart */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Environmental Impact Categories
        </h4>
        <div className="space-y-3">
          {keyImpacts.map((impact) => {
            const IconComponent = impact.icon;
            const percentage = maxValue > 0 ? (impact.value / maxValue) * 100 : 0;
            const impactLevel = getImpactLevel(impact.value, maxValue);
            const LevelIcon = impactLevel.icon;

            return (
              <div key={impact.key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <IconComponent className={`h-4 w-4 ${impact.color}`} />
                    <span className="text-sm font-medium text-gray-900">
                      {impact.label}
                    </span>
                    <LevelIcon className={`h-3 w-3 ${impactLevel.color}`} />
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={`text-xs ${impactLevel.color}`}>
                      {impactLevel.level}
                    </Badge>
                    <span className="text-sm font-bold text-gray-900">
                      {formatImpactValue(impact.value, impact.unit)}
                    </span>
                  </div>
                </div>
                
                <div className="relative">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${impact.bgColor.replace('bg-', 'bg-gradient-to-r from-').replace('-100', '-300 to-').replace('to-', impact.color.replace('text-', 'to-'))}`}
                      style={{ width: `${Math.max(2, percentage)}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {impact.description}
                  </div>
                </div>
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
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-red-900">Human Health Impact</span>
              <span className="text-sm font-bold text-red-900">
                {formatEndpointValue(endpoints?.['Human Health'] ?? 0, 'DALY')}
              </span>
            </div>
            <Progress 
              value={Math.min(100, ((endpoints?.['Human Health'] ?? 0) as number) * 1000000)} 
              className="h-2"
            />
            <div className="text-xs text-red-700 mt-1">
              Disability Adjusted Life Years - Health burden from environmental impacts
            </div>
          </div>

          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-green-900">Ecosystem Quality Impact</span>
              <span className="text-sm font-bold text-green-900">
                {formatEndpointValue(endpoints?.['Ecosystems'] ?? 0, 'sp.year')}
              </span>
            </div>
            <Progress 
              value={Math.min(100, ((endpoints?.['Ecosystems'] ?? 0) as number) * 1000000)} 
              className="h-2"
            />
            <div className="text-xs text-green-700 mt-1">
              Species extinction years - Biodiversity loss from environmental damage
            </div>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-900">Resource Scarcity Impact</span>
              <span className="text-sm font-bold text-blue-900">
                {formatEndpointValue(endpoints?.['Resources'] ?? 0, 'USD')}
              </span>
            </div>
            <Progress 
              value={Math.min(100, ((endpoints?.['Resources'] ?? 0) as number) * 10)} 
              className="h-2"
            />
            <div className="text-xs text-blue-700 mt-1">
              Economic value of resource depletion impacts
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
          <p>
            <strong>Top Impact:</strong> {keyImpacts.reduce((max, impact) => 
              impact.value > max.value ? impact : max, keyImpacts[0]).label} 
            is the primary environmental concern for this meal
          </p>
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