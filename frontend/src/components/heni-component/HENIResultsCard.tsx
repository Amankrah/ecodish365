/**
 * HENI Results Card Component
 * Displays HENI calculation results in a visually appealing format
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  Heart,
  Shield,
  AlertTriangle,
  Info
} from 'lucide-react';
import { type HENIResult, type HENIFoodProfile } from '../../lib/api';

type HENIAnalysis = HENIResult['data'] | HENIFoodProfile['data']['heni_analysis'];
type Props = {
  results: HENIResult | HENIAnalysis;
  compact?: boolean;
  detailed?: boolean;
};

export const HENIResultsCard: React.FC<Props> = ({ results, compact = false, detailed = false }) => {
  if (!results) return null;

  // Normalize to analysis block
  const normalize = (input: Props['results']): HENIAnalysis | null => {
    if (typeof input === 'object' && input !== null) {
      const root = input as Record<string, unknown>;
      if (root.data && typeof root.data === 'object' && 'heni_scores' in (root.data as Record<string, unknown>)) {
        return root.data as HENIResult['data'];
      }
      if ('heni_scores' in root) {
        return input as HENIAnalysis;
      }
    }
    return null;
  };

  const analysis = normalize(results);
  if (!analysis) return null;

  const {
    heni_scores,
    health_impact,
    component_breakdown,
    // disease_burden_analysis,
    risk_factor_analysis,
    meal_composition
  } = analysis;

  // Determine health impact category
  const getHealthCategory = (minutes: number) => {
    if (minutes > 20) return { level: 'excellent', color: 'green', icon: TrendingUp };
    if (minutes > 5) return { level: 'good', color: 'green', icon: TrendingUp };
    if (minutes > 0) return { level: 'mild', color: 'blue', icon: TrendingUp };
    if (minutes > -5) return { level: 'neutral', color: 'gray', icon: Shield };
    if (minutes > -20) return { level: 'concerning', color: 'amber', icon: TrendingDown };
    return { level: 'poor', color: 'red', icon: TrendingDown };
  };

  const healthCategory = getHealthCategory(health_impact?.health_impact_minutes || 0);
  const HealthIcon = healthCategory.icon;

  if (compact) {
    return (
      <div className="space-y-4">
        {/* Main Score Display */}
        <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border">
          <div className="flex items-center justify-center mb-2">
            <HealthIcon className={`h-8 w-8 text-${healthCategory.color}-500 mr-2`} />
            <div className="text-3xl font-bold text-gray-800">
              {health_impact?.health_impact_minutes > 0 ? '+' : ''}
              {(health_impact?.health_impact_minutes || 0).toFixed(2)}
            </div>
          </div>
          <p className="text-lg text-gray-600">minutes of healthy life</p>
          <p className="text-sm text-gray-500 mt-1">
            HENI Score: {heni_scores?.heni_per_100_kcal?.toFixed(1) || '0.0'} μDALY/100kcal
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-white p-3 rounded border text-center">
            <div className="font-semibold text-gray-700">Energy</div>
            <div className="text-lg text-blue-600">{Math.round(meal_composition?.total_energy_kcal || 0)} kcal</div>
          </div>
          <div className="bg-white p-3 rounded border text-center">
            <div className="font-semibold text-gray-700">Weight</div>
            <div className="text-lg text-green-600">{Math.round(meal_composition?.total_weight_grams || 0)}g</div>
          </div>
        </div>
      </div>
    );
  }

  if (detailed) {
    return (
      <div className="space-y-6">
        {/* Header with Main Scores */}
        <div className="grid md:grid-cols-4 gap-4">
          <Card className="text-center">
            <CardContent className="p-4">
              <div className="flex items-center justify-center mb-2">
                <HealthIcon className={`h-6 w-6 text-${healthCategory.color}-500`} />
              </div>
              <div className="text-2xl font-bold text-gray-800">
                {health_impact?.health_impact_minutes > 0 ? '+' : ''}
                {(health_impact?.health_impact_minutes || 0).toFixed(2)}
              </div>
              <p className="text-sm text-gray-600">minutes</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="p-4">
              <Zap className="h-6 w-6 text-blue-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-800">
                {heni_scores?.heni_per_100_kcal?.toFixed(1) || '0.0'}
              </div>
              <p className="text-sm text-gray-600">μDALY/100kcal</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="p-4">
              <Clock className="h-6 w-6 text-green-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-800">
                {Math.round(meal_composition?.total_energy_kcal || 0)}
              </div>
              <p className="text-sm text-gray-600">calories</p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardContent className="p-4">
              <Heart className="h-6 w-6 text-red-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-800">
                {Object.keys(risk_factor_analysis?.risk_factors || {}).length}
              </div>
              <p className="text-sm text-gray-600">risk factors</p>
            </CardContent>
          </Card>
        </div>

        {/* Health Impact Description */}
        <Card>
          <CardContent className="p-4">
            <div className={`p-4 rounded-lg bg-${healthCategory.color}-50 border border-${healthCategory.color}-200`}>
              <div className="flex items-center gap-2 mb-2">
                <HealthIcon className={`h-5 w-5 text-${healthCategory.color}-600`} />
                <h4 className={`font-semibold text-${healthCategory.color}-800 capitalize`}>
                  {healthCategory.level} Health Impact
                </h4>
              </div>
              <p className={`text-${healthCategory.color}-700 text-sm leading-relaxed`}>
                {health_impact?.description}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Component Breakdown */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Positive Contributors */}
          {Object.keys(component_breakdown?.food_group_contributions || {}).some(key => 
            component_breakdown.food_group_contributions[key] > 0
          ) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-green-700 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Health Benefits
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(Object.entries(component_breakdown?.food_group_contributions || {}) as Array<[string, number]>)
                  .filter(([, value]) => value > 0)
                  .sort(([, a], [, b]) => b - a)
                  .map(([factor, value]) => (
                    <div key={factor} className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-gray-700 capitalize">
                          {factor.replace('_', ' ')}
                        </p>
                        <div className="w-full bg-green-100 rounded-full h-2 mt-1">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{ width: `${Math.min(100, (value / 20) * 100)}%` }}
                          />
                        </div>
                      </div>
                      <Badge className="ml-3 bg-green-100 text-green-800">
                        +{value.toFixed(1)} μDALY
                      </Badge>
                    </div>
                  ))}
              </CardContent>
            </Card>
          )}

          {/* Negative Contributors */}
          {Object.keys(component_breakdown?.food_group_contributions || {}).some(key => 
            component_breakdown.food_group_contributions[key] < 0
          ) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-amber-700 flex items-center gap-2">
                  <TrendingDown className="h-5 w-5" />
                  Health Concerns
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(Object.entries(component_breakdown?.food_group_contributions || {}) as Array<[string, number]>)
                  .filter(([, value]) => value < 0)
                  .sort(([, a], [, b]) => a - b)
                  .map(([factor, value]) => (
                    <div key={factor} className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-gray-700 capitalize">
                          {factor.replace('_', ' ')}
                        </p>
                        <div className="w-full bg-amber-100 rounded-full h-2 mt-1">
                          <div 
                            className="bg-amber-500 h-2 rounded-full" 
                            style={{ width: `${Math.min(100, (Math.abs(value) / 20) * 100)}%` }}
                          />
                        </div>
                      </div>
                      <Badge className="ml-3 bg-amber-100 text-amber-800">
                        {value.toFixed(1)} μDALY
                      </Badge>
                    </div>
                  ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Nutrient Contributions */}
        {Object.keys(component_breakdown?.nutrient_contributions || {}).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Key Nutrients Impact
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {(Object.entries(component_breakdown?.nutrient_contributions || {}) as Array<[string, number]>)
                  .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                  .map(([nutrient, value]) => (
                    <div key={nutrient} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="font-medium text-gray-700 capitalize">
                        {nutrient.replace('_', ' ')}
                      </span>
                      <Badge 
                        variant={value > 0 ? "default" : "destructive"} 
                        className={value > 0 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
                      >
                        {value > 0 ? '+' : ''}{value.toFixed(1)} μDALY
                      </Badge>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Warnings */}
        {risk_factor_analysis?.warnings?.length > 0 && (
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader>
              <CardTitle className="text-amber-700 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Important Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {risk_factor_analysis.warnings.map((warning: string, index: number) => (
                  <li key={index} className="text-amber-700 text-sm flex items-start gap-2">
                    <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    {warning}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // Default view
  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2">
            <HealthIcon className={`h-8 w-8 text-${healthCategory.color}-500`} />
            <div>
              <div className="text-3xl font-bold text-gray-800">
                {health_impact?.health_impact_minutes > 0 ? '+' : ''}
                {(health_impact?.health_impact_minutes || 0).toFixed(2)}
              </div>
              <p className="text-sm text-gray-600">minutes of healthy life</p>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-semibold text-gray-700">HENI Score</div>
              <div className="text-blue-600">{heni_scores?.heni_per_100_kcal?.toFixed(1) || '0.0'}</div>
            </div>
            <div>
              <div className="font-semibold text-gray-700">Energy</div>
              <div className="text-green-600">{Math.round(meal_composition?.total_energy_kcal || 0)} kcal</div>
            </div>
            <div>
              <div className="font-semibold text-gray-700">Weight</div>
              <div className="text-purple-600">{Math.round(meal_composition?.total_weight_grams || 0)}g</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};