/**
 * Health Impact Visualization Component
 * Visual representation of HENI health impacts using charts and graphics
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import {
  TrendingUp,
  TrendingDown,
  Heart,
  Shield,
  Clock,
  AlertTriangle,
  Target,
  Activity
} from 'lucide-react';
import { type HENIResult, type HENIFoodProfile } from '../../lib/api';

type HENIAnalysis = HENIResult['data'] | HENIFoodProfile['data']['heni_analysis'];
type Props = { results: HENIResult | HENIAnalysis | HENIFoodProfile['data'] };

export const HealthImpactVisualization: React.FC<Props> = ({ results }) => {
  // Normalize input to a HENI analysis block
  const hasDataWithHeniScores = (obj: unknown): obj is { data: HENIAnalysis } => {
    if (!obj || typeof obj !== 'object') return false;
    const root = obj as Record<string, unknown>;
    const data = root['data'] as unknown;
    return !!(data && typeof data === 'object' && 'heni_scores' in (data as Record<string, unknown>));
  };
  const hasHeniAnalysis = (obj: unknown): obj is { heni_analysis: HENIAnalysis } => {
    if (!obj || typeof obj !== 'object') return false;
    const root = obj as Record<string, unknown>;
    const ha = root['heni_analysis'] as unknown;
    return !!(ha && typeof ha === 'object' && 'heni_scores' in (ha as Record<string, unknown>));
  };
  const hasHeniScores = (obj: unknown): obj is HENIAnalysis => {
    return !!(obj && typeof obj === 'object' && 'heni_scores' in (obj as Record<string, unknown>));
  };

  const analysis: HENIAnalysis | null = hasDataWithHeniScores(results)
    ? results.data
    : hasHeniAnalysis(results)
      ? results.heni_analysis
      : hasHeniScores(results)
        ? (results as HENIAnalysis)
        : null;

  if (!analysis?.health_impact) return null;

  const {
    health_impact,
    heni_scores,
    component_breakdown,
    risk_factor_analysis
  } = analysis;

  const healthMinutes = health_impact.health_impact_minutes || 0;
  const heniPerKcal = heni_scores?.heni_per_100_kcal || 0;

  // Calculate health impact scale (-100 to +100 minutes range)
  const impactScale = Math.max(-100, Math.min(100, healthMinutes));
  const impactPercentage = ((impactScale + 100) / 200) * 100;

  // Determine health status
  const getHealthStatus = (minutes: number) => {
    if (minutes > 20) return { level: 'Excellent', color: 'emerald', bgColor: 'emerald-500', icon: TrendingUp };
    if (minutes > 5) return { level: 'Good', color: 'green', bgColor: 'green-500', icon: TrendingUp };
    if (minutes > 0) return { level: 'Mild Benefit', color: 'blue', bgColor: 'blue-500', icon: Shield };
    if (minutes > -5) return { level: 'Neutral', color: 'gray', bgColor: 'gray-500', icon: Shield };
    if (minutes > -20) return { level: 'Concerning', color: 'amber', bgColor: 'amber-500', icon: TrendingDown };
    return { level: 'Poor', color: 'red', bgColor: 'red-500', icon: TrendingDown };
  };

  const healthStatus = getHealthStatus(healthMinutes);
  const StatusIcon = healthStatus.icon;

  // FIX (audit follow-up): merge food_group + nutrient contributions. Many CNF
  // foods (e.g. Beef stew canned 4964) emit only nutrient_contributions, so a
  // food-group-only view collapses to nothing. Also flip sign convention to
  // match the rest of the page: negative μDALY = beneficial, positive = harmful.
  const contribFG = component_breakdown?.food_group_contributions || {};
  const contribN  = component_breakdown?.nutrient_contributions || {};
  const contributors: Record<string, number> = { ...contribFG, ...contribN };
  for (const k of Object.keys(contributors)) {
    if (k.startsWith('__') || contributors[k] === 0) delete contributors[k];
  }
  const positiveContributors = (Object.entries(contributors) as Array<[string, number]>)
    .filter(([, value]) => value < 0)              // beneficial μDALY
    .sort(([, a], [, b]) => a - b)                 // most-beneficial first
    .slice(0, 3);

  const negativeContributors = (Object.entries(contributors) as Array<[string, number]>)
    .filter(([, value]) => value > 0)              // harmful μDALY
    .sort(([, a], [, b]) => b - a)                 // most-harmful first
    .slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Main Health Impact Meter */}
      <Card className="overflow-hidden">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Heart className="h-5 w-5 text-red-500" />
            Health Impact Meter
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-6">
          {/* Circular Progress Indicator */}
          <div className="relative w-32 h-32 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full bg-gray-200">
              <div 
                className={`absolute inset-0 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500`}
                style={{
                  background: `conic-gradient(from 0deg, #ef4444 0deg, #f59e0b 120deg, #10b981 180deg, #10b981 360deg)`,
                  mask: `conic-gradient(from 0deg, transparent 0deg, black ${impactPercentage * 3.6}deg, transparent ${impactPercentage * 3.6}deg)`
                }}
              />
            </div>
            <div className="absolute inset-2 rounded-full bg-white flex items-center justify-center">
              <div className="text-center">
                <StatusIcon className={`h-6 w-6 text-${healthStatus.color}-500 mx-auto mb-1`} />
                <div className="font-bold text-lg">
                  {healthMinutes > 0 ? '+' : ''}{healthMinutes.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500">min</div>
              </div>
            </div>
          </div>

          {/* Status Badge */}
          <div className="text-center">
            <Badge className={`bg-${healthStatus.color}-100 text-${healthStatus.color}-800 text-sm px-3 py-1`}>
              {healthStatus.level}
            </Badge>
            <p className="text-sm text-gray-600 mt-2">
              {health_impact.description || 'Health impact based on DALY methodology'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Impact Breakdown */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Positive Contributors */}
        {positiveContributors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-green-700 text-sm flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Health Benefits
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {positiveContributors.map(([factor, value]) => (
                <div key={factor} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium capitalize">
                      {factor.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-green-600">
                      {value.toFixed(1)} μDALY
                    </span>
                  </div>
                  <Progress
                    value={Math.min(100, (Math.abs(value) / 20) * 100)}
                    className="h-2 bg-green-100"
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Negative Contributors */}
        {negativeContributors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-amber-700 text-sm flex items-center gap-2">
                <TrendingDown className="h-4 w-4" />
                Health Concerns
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {negativeContributors.map(([factor, value]) => (
                <div key={factor} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium capitalize">
                      {factor.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-amber-600">
                      +{value.toFixed(1)} μDALY
                    </span>
                  </div>
                  <Progress
                    value={Math.min(100, (Math.abs(value) / 20) * 100)}
                    className="h-2 bg-amber-100"
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card className="text-center">
          <CardContent className="p-4">
            <Target className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-800">
              {Math.abs(heniPerKcal).toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">HENI Score/100kcal</div>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="p-4">
            <Clock className="h-6 w-6 text-green-500 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-800">
              {Math.abs(healthMinutes).toFixed(2)}
            </div>
            <div className="text-xs text-gray-500">Minutes Impact</div>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="p-4">
            <Activity className="h-6 w-6 text-purple-500 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-800">
              {/* Match HENIResultsCard counter: drop zero-valued rows
                  (heni_calculator_methods.py:222 defaults trans_fat = 0.0)
                  and internal __audit__ keys, so the two counters agree. */}
              {Object.entries(risk_factor_analysis?.risk_factors || {})
                .filter(([k, v]) => !k.startsWith('__') && Number(v) !== 0)
                .length}
            </div>
            <div className="text-xs text-gray-500">Risk Factors</div>
          </CardContent>
        </Card>
      </div>

      {/* Health Impact Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Estimated Health Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Immediate (Hours) */}
            <div className="flex items-center gap-4">
              <div className="w-20 text-sm text-gray-500">Hours</div>
              <div className="flex-1">
                <div className="text-sm font-medium">Metabolic Response</div>
                <div className="text-xs text-gray-600">
                  Initial nutrient absorption and metabolic processing
                </div>
              </div>
              <Badge variant="secondary" className="text-xs">
                Immediate
              </Badge>
            </div>

            {/* Days */}
            <div className="flex items-center gap-4">
              <div className="w-20 text-sm text-gray-500">Days</div>
              <div className="flex-1">
                <div className="text-sm font-medium">Biomarker Changes</div>
                <div className="text-xs text-gray-600">
                  Blood lipids, inflammation markers, blood pressure effects
                </div>
              </div>
              <Badge 
                variant="secondary" 
                className={`text-xs ${healthMinutes > 0 ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}
              >
                {healthMinutes > 0 ? 'Beneficial' : 'Risk'}
              </Badge>
            </div>

            {/* Years — FIX (audit bug #5): the previous copy asserted
                definitive "Increased risk of cardiovascular disease, diabetes,
                certain cancers" outcomes for any negative-minutes meal,
                including Neutral-classified ones. Stylianou 2021 (Discussion
                p. 622) is explicit that the HENI marginal framework is NOT
                applicable to chronic-disease incidence forecasting for a
                single eating occasion. */}
            <div className="flex items-center gap-4">
              <div className="w-20 text-sm text-gray-500">Years</div>
              <div className="flex-1">
                <div className="text-sm font-medium">Marginal Population Effect</div>
                <div className="text-xs text-gray-600">
                  {healthMinutes > 0
                    ? 'Marginal contribution toward beneficial population-level GBD outcomes (Stylianou 2021)'
                    : 'Marginal contribution toward adverse population-level GBD outcomes — not a personal disease-risk projection (Stylianou 2021 marginality caveat)'
                  }
                </div>
              </div>
              <Badge
                variant="secondary"
                className={`text-xs ${healthMinutes > 0 ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}
              >
                {healthMinutes > 0 ? '+' : ''}{healthMinutes.toFixed(2)} min
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Warnings */}
      {risk_factor_analysis?.warnings?.length > 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-amber-800 mb-2">Important Notes</h4>
                <ul className="space-y-1">
                  {risk_factor_analysis.warnings.map((warning: string, index: number) => (
                    <li key={index} className="text-sm text-amber-700">
                      • {warning}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};