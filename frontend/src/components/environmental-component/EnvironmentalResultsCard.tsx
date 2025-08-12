'use client';
/**
 * Environmental Results Card - Core Results Display Component
 * Displays comprehensive environmental impact analysis results
 */

import React from 'react';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import {
  Globe,
  Droplets,
  TreePine,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Leaf,
  AlertTriangle,
  CheckCircle,
  Factory,
  Zap,
} from 'lucide-react';
import type { EnvironmentalImpactResult } from '../../lib/api';

interface EnvironmentalResultsCardProps {
  results: EnvironmentalImpactResult;
  compact?: boolean;
  detailed?: boolean;
}

export const EnvironmentalResultsCard: React.FC<EnvironmentalResultsCardProps> = ({
  results,
  compact = false,
  detailed = false
}) => {
  const analysis = results?.data?.meal_analysis || {};
  const lca = analysis?.lca_results || {};
  const monetization = analysis?.monetization || {};
  const sustainability = analysis?.sustainability_score || { overall_sustainability_score: 0 };
  const composition = analysis?.meal_composition || { total_energy_kcal: 0, total_weight_grams: 0 };

  // Get sustainability color and icon
  const getSustainabilityInfo = (score: number) => {
    if (score >= 80) return { color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle, label: 'Excellent' };
    if (score >= 60) return { color: 'text-blue-600', bgColor: 'bg-blue-100', icon: TrendingUp, label: 'Good' };
    if (score >= 40) return { color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: TrendingUp, label: 'Fair' };
    if (score >= 20) return { color: 'text-orange-600', bgColor: 'bg-orange-100', icon: TrendingDown, label: 'Poor' };
    return { color: 'text-red-600', bgColor: 'bg-red-100', icon: AlertTriangle, label: 'Very Poor' };
  };

  const sustainabilityInfo = getSustainabilityInfo(sustainability?.overall_sustainability_score || 0);
  const SustainabilityIcon = sustainabilityInfo.icon;

  // Format impact values using backend-provided units; scientific notation for tiny values
  const formatImpactValue = (value: number, unit: string): string => {
    if (!Number.isFinite(value) || value === 0) return `0 ${unit}`;
    const absVal = Math.abs(value);
    if (absVal >= 1) return `${value.toFixed(3)} ${unit}`;
    if (absVal >= 1e-3) return `${value.toFixed(6)} ${unit}`;
    return `${value.toExponential(2)} ${unit}`;
  };

  // Format endpoint impacts (DALY, sp.year, USD) with e-notation for very small values
  const formatEndpointValue = (value: number, unit: string): string => {
    if (!Number.isFinite(value) || value === 0) return `0 ${unit}`;
    const absVal = Math.abs(value);
    if (absVal < 1e-6) return `${value.toExponential(2)} ${unit}`;
    if (absVal < 1e-3) return `${value.toExponential(2)} ${unit}`;
    if (absVal < 1) return `${value.toFixed(6)} ${unit}`;
    return `${value.toFixed(3)} ${unit}`;
  };

  if (compact) {
    return (
      <div className="space-y-4">
        {/* Quick Impact Overview */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Globe className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Carbon Footprint</span>
            </div>
            <div className="text-lg font-bold text-blue-900">
              {formatImpactValue(lca?.['Global warming'] || 0, 'kg CO₂-eq')}
            </div>
          </div>

          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-green-900">Environmental Cost</span>
            </div>
            <div className="text-lg font-bold text-green-900">
              CAD ${(monetization?.total_cost || 0).toFixed(3)}
            </div>
          </div>
        </div>

        {/* Sustainability Score */}
        <div className={`p-4 rounded-lg ${sustainabilityInfo.bgColor}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <SustainabilityIcon className={`h-5 w-5 ${sustainabilityInfo.color}`} />
              <span className="font-medium">Sustainability Score</span>
            </div>
            <Badge className={sustainabilityInfo.color}>
              {sustainabilityInfo.label}
            </Badge>
          </div>
          <div className="flex items-center gap-3">
            <Progress 
              value={sustainability?.overall_sustainability_score || 0} 
              className="flex-1" 
            />
            <span className={`font-bold ${sustainabilityInfo.color}`}>
              {(sustainability?.overall_sustainability_score || 0).toFixed(0)}/100
            </span>
          </div>
        </div>

        {/* Key Impacts */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Water Use:</span>
            <span className="font-medium">{formatImpactValue(lca?.['Water consumption'] || 0, 'm³')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Land Use:</span>
            <span className="font-medium">{formatImpactValue(lca?.['Land use'] || 0, 'm²a')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Per Calorie:</span>
            <span className="font-medium">CAD {(monetization?.cost_per_calorie || 0).toFixed(5)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Single Score:</span>
            <span className="font-medium">{(analysis?.single_score || 0).toFixed(4)} pts</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Meal Overview */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-3">Meal Composition</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span
              className="text-gray-600"
              title="Includes a 31.9% food-waste adjustment: total = entered amounts / (1 − 0.319)."
            >
              Total Weight:
            </span>
            <div className="font-semibold">{(composition?.total_weight_grams || 0).toFixed(0)}g</div>
          </div>
          <div>
            <span className="text-gray-600">Total Energy:</span>
            <div className="font-semibold">{(composition?.total_energy_kcal || 0).toFixed(0)} kcal</div>
          </div>
          <div>
            <span className="text-gray-600">Foods Count:</span>
            <div className="font-semibold">{composition?.food_count || 0}</div>
          </div>
          <div>
            <span className="text-gray-600">Protein:</span>
            <div className="font-semibold">{(composition?.macronutrient_distribution?.protein_percent || 0).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Core Environmental Impacts */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Globe className="h-5 w-5" />
          Key Environmental Impacts
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-900">Climate Impact</span>
            </div>
            <div className="text-2xl font-bold text-blue-900">
              {formatImpactValue(lca?.['Global warming'] || 0, 'kg CO₂-eq')}
            </div>
            <div className="text-sm text-blue-700 mt-1">
              Global Warming Potential
            </div>
          </div>

          <div className="bg-cyan-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Droplets className="h-5 w-5 text-cyan-600" />
              <span className="font-medium text-cyan-900">Water Impact</span>
            </div>
            <div className="text-2xl font-bold text-cyan-900">
              {formatImpactValue(lca?.['Water consumption'] || 0, 'm³')}
            </div>
            <div className="text-sm text-cyan-700 mt-1">
              Freshwater Consumption
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <TreePine className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-900">Land Impact</span>
            </div>
            <div className="text-2xl font-bold text-green-900">
              {formatImpactValue(lca?.['Land use'] || 0, 'm²a crop-eq')}
            </div>
            <div className="text-sm text-green-700 mt-1">
              Agricultural Land Use
            </div>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Factory className="h-5 w-5 text-purple-600" />
              <span className="font-medium text-purple-900">Ecosystem Impact</span>
            </div>
            <div className="text-2xl font-bold text-purple-900">
              {formatImpactValue(lca?.['Terrestrial acidification'] || 0, 'kg SO₂-eq')}
            </div>
            <div className="text-sm text-purple-700 mt-1">
              Terrestrial Acidification
            </div>
          </div>
        </div>
      </div>

      {/* Economic Impact */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <DollarSign className="h-5 w-5" />
          Economic Valuation
        </h3>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-yellow-700">Total Cost:</span>
              <div className="text-xl font-bold text-yellow-900">
                CAD ${(monetization?.total_cost || 0).toFixed(3)}
              </div>
            </div>
            <div>
              <span className="text-sm text-yellow-700">Per Calorie:</span>
              <div className="text-xl font-bold text-yellow-900">
                CAD ${(monetization?.cost_per_calorie || 0).toFixed(5)}
              </div>
            </div>
            <div>
              <span className="text-sm text-yellow-700">Per Protein:</span>
              <div className="text-xl font-bold text-yellow-900">
                CAD ${(monetization?.cost_per_protein || 0).toFixed(5)}
              </div>
            </div>
            <div>
              <span className="text-sm text-yellow-700">Top Driver:</span>
              <div className="text-sm font-bold text-yellow-900">
                  {monetization?.top_cost_drivers?.[0]?.impact_category || 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sustainability Assessment */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Leaf className="h-5 w-5" />
          Sustainability Assessment
        </h3>
        <div className={`p-4 rounded-lg ${sustainabilityInfo.bgColor}`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <SustainabilityIcon className={`h-6 w-6 ${sustainabilityInfo.color}`} />
              <span className="text-lg font-semibold">Overall Score</span>
            </div>
            <Badge className={`text-lg px-3 py-1 ${sustainabilityInfo.color}`}>
              {(sustainability?.overall_sustainability_score || 0).toFixed(0)}/100
            </Badge>
          </div>

          <Progress 
            value={sustainability?.overall_sustainability_score || 0} 
            className="mb-4" 
          />

          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Environmental:</span>
              <div className="font-semibold">{(sustainability?.environmental_score || 0).toFixed(0)}/100</div>
              <Progress value={sustainability?.environmental_score || 0} className="h-1 mt-1" />
            </div>
            <div>
              <span className="text-gray-600">Nutritional:</span>
              <div className="font-semibold">{(sustainability?.nutritional_score || 0).toFixed(0)}/100</div>
              <Progress value={sustainability?.nutritional_score || 0} className="h-1 mt-1" />
            </div>
            <div>
              <span className="text-gray-600">Processing:</span>
              <div className="font-semibold">{(sustainability?.processing_score || 0).toFixed(0)}/100</div>
              <Progress value={sustainability?.processing_score || 0} className="h-1 mt-1" />
            </div>
          </div>
        </div>
      </div>

      {/* Additional Endpoint Impacts */}
      {detailed && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Endpoint Impact Categories
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-red-900">Human Health</span>
              </div>
              <div className="text-lg font-bold text-red-900">
                {formatEndpointValue(analysis?.endpoint_impacts?.['Human Health'] ?? 0, 'DALY')}
              </div>
              <div className="text-sm text-red-700 mt-1">
                Disability Adjusted Life Years
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-green-900">Ecosystem Quality</span>
              </div>
              <div className="text-lg font-bold text-green-900">
                {formatEndpointValue(analysis?.endpoint_impacts?.['Ecosystems'] ?? 0, 'sp.year')}
              </div>
              <div className="text-sm text-green-700 mt-1">
                Species Extinction Years
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-blue-900">Resource Scarcity</span>
              </div>
              <div className="text-lg font-bold text-blue-900">
                {formatEndpointValue(analysis?.endpoint_impacts?.['Resources'] ?? 0, 'USD')}
              </div>
              <div className="text-sm text-blue-700 mt-1">
                Resource Depletion Cost
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Recommendations */}
      {(sustainability?.recommendations?.length || 0) > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Key Recommendations
          </h3>
          <div className="space-y-2">
            {(sustainability?.recommendations || []).slice(0, 3).map((recommendation, index) => (
              <div key={index} className="flex items-start gap-2 p-3 bg-green-50 rounded-lg">
                <Leaf className="h-4 w-4 text-green-600 mt-0.5" />
                <p className="text-sm text-green-800">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Single Score Summary */}
      <div className="bg-indigo-50 p-4 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm text-indigo-700">ReCiPe Single Score</span>
            <div className="text-2xl font-bold text-indigo-900">
              {(analysis?.single_score ?? 0).toFixed(2)} points
            </div>
            <div className="text-xs text-indigo-600 mt-1">
              Lower scores indicate better environmental performance
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-indigo-700">Rating</div>
            <Badge className="text-indigo-700">
              {sustainability?.sustainability_rating || 'Unknown'}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnvironmentalResultsCard;