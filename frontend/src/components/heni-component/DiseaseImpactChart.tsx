/**
 * Disease Impact Chart Component
 * Visualizes HENI health impacts by disease category using charts and infographics
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { type HENIResult, type HENIFoodProfile } from '../../lib/api';
import {
  Heart,
  Activity,
  Brain,
  Bone,
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Info,
  BarChart3,
  PieChart
} from 'lucide-react';

type HENIAnalysis = HENIResult['data'] | HENIFoodProfile['data']['heni_analysis'];
type DiseaseImpactChartProps = {
  results: HENIResult | HENIAnalysis | HENIFoodProfile['data'];
};

export const DiseaseImpactChart: React.FC<DiseaseImpactChartProps> = ({ results }) => {
  const [chartType, setChartType] = useState<'category' | 'timeline' | 'comparison'>('category');

  // Type guards to normalize input to a HENI analysis block without using 'any'
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


  if (!analysis?.risk_factor_analysis && !analysis?.disease_burden_analysis) return null;

  const riskFactors: Record<string, number> = analysis.risk_factor_analysis?.risk_factors || {};
  const healthImpact = analysis.health_impact || {};

  // Disease category mapping based on HENI methodology
  type DiseaseCategory = {
    name: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    percentage: number;
    conditions: string[];
    riskFactors: string[];
    protectiveFactors: string[];
  };

  const diseaseCategories: Record<string, DiseaseCategory> = {
    cardiovascular: {
      name: 'Cardiovascular Disease',
      icon: Heart,
      color: 'red',
      percentage: 45, // % of total DALY burden
      conditions: ['Ischemic heart disease', 'Stroke', 'Hypertension', 'Heart failure'],
      riskFactors: ['sodium', 'trans_fat', 'red_meat', 'processed_meat'],
      protectiveFactors: ['fruits', 'vegetables', 'omega_3', 'polyunsaturated_fatty_acids']
    },
    cancer: {
      name: 'Cancer',
      icon: Shield,
      color: 'purple',
      percentage: 25,
      conditions: ['Colorectal cancer', 'Stomach cancer', 'Breast cancer', 'Lung cancer'],
      riskFactors: ['processed_meat', 'red_meat', 'sodium'],
      protectiveFactors: ['fruits', 'vegetables', 'fiber', 'calcium']
    },
    metabolic: {
      name: 'Metabolic Disorders',
      icon: Activity,
      color: 'orange',
      percentage: 20,
      conditions: ['Type 2 diabetes', 'Obesity', 'Metabolic syndrome'],
      riskFactors: ['sugar_sweetened_beverages', 'trans_fat', 'processed_meat'],
      protectiveFactors: ['whole_grains', 'fiber', 'nuts_seeds']
    },
    neurological: {
      name: 'Neurological',
      icon: Brain,
      color: 'blue',
      percentage: 6,
      conditions: ['Alzheimer\'s disease', 'Depression', 'Cognitive decline'],
      riskFactors: ['trans_fat', 'processed_meat'],
      protectiveFactors: ['omega_3', 'fruits', 'vegetables']
    },
    musculoskeletal: {
      name: 'Bone Health',
      icon: Bone,
      color: 'amber',
      percentage: 4,
      conditions: ['Osteoporosis', 'Fractures'],
      riskFactors: ['sodium'],
      protectiveFactors: ['calcium', 'milk']
    }
  };

  // Calculate impact by disease category
  const calculateCategoryImpacts = () => {
    const impacts: Record<string, DiseaseCategory & {
      totalImpact: number;
      riskContribution: number;
      protectiveContribution: number;
      netBenefit: number;
    }> = {};
    
    Object.entries(diseaseCategories).forEach(([key, category]) => {
      let totalImpact: number = 0;
      let riskContribution: number = 0;
      let protectiveContribution: number = 0;
      
      // Sum risk factors
      category.riskFactors.forEach(factor => {
        if (riskFactors[factor]) {
          // Risk factors reduce health (treat as negative)
          const impact = -Math.abs(riskFactors[factor]) * (category.percentage / 100);
          totalImpact += impact;
          riskContribution += Math.abs(impact);
        }
      });
      
      // Sum protective factors
      category.protectiveFactors.forEach(factor => {
        if (riskFactors[factor]) {
          // Protective factors improve health (treat as positive)
          const impact = Math.abs(riskFactors[factor]) * (category.percentage / 100);
          totalImpact += impact;
          protectiveContribution += Math.max(0, impact);
        }
      });
      
      impacts[key] = {
        ...category,
        totalImpact,
        riskContribution,
        protectiveContribution,
        netBenefit: protectiveContribution - riskContribution
      };
    });
    
    return impacts;
  };

  const categoryImpacts = calculateCategoryImpacts();

  // Sort categories by absolute impact
  type DiseaseCategoryWithImpact = DiseaseCategory & {
    totalImpact: number;
    riskContribution: number;
    protectiveContribution: number;
    netBenefit: number;
  };
  const sortedCategories = (Object.entries(categoryImpacts) as Array<[string, DiseaseCategoryWithImpact]>)
    .sort(([, a], [, b]) => Math.abs(b.totalImpact) - Math.abs(a.totalImpact));

  // Get overall health trend
  const totalImpact = (Object.values(categoryImpacts) as DiseaseCategoryWithImpact[])
    .reduce((sum: number, cat: DiseaseCategoryWithImpact) => sum + cat.totalImpact, 0);

  const getImpactStatus = (impact: number) => {
    if (impact > 5) return { level: 'Strongly Protective', color: 'green', icon: TrendingUp };
    if (impact > 0) return { level: 'Protective', color: 'green', icon: TrendingUp };
    if (impact > -5) return { level: 'Neutral', color: 'gray', icon: Shield };
    if (impact > -10) return { level: 'Elevated Risk', color: 'amber', icon: TrendingDown };
    return { level: 'High Risk', color: 'red', icon: AlertTriangle };
  };

  return (
    <div className="space-y-6">
      {/* Chart Type Toggle */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={chartType === 'category' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setChartType('category')}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          By Disease
        </Button>
        <Button
          variant={chartType === 'timeline' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setChartType('timeline')}
        >
          <TrendingUp className="h-4 w-4 mr-2" />
          Timeline
        </Button>
        <Button
          variant={chartType === 'comparison' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setChartType('comparison')}
        >
          <PieChart className="h-4 w-4 mr-2" />
          Risk vs Benefit
        </Button>
      </div>

      {chartType === 'category' && (
        <div className="space-y-4">
          {/* Overall Health Impact */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full bg-${getImpactStatus(totalImpact).color}-100`}>
                    {React.createElement(getImpactStatus(totalImpact).icon, { 
                      className: `h-5 w-5 text-${getImpactStatus(totalImpact).color}-600` 
                    })}
                  </div>
                  <div>
                    <h3 className="font-semibold">Overall Disease Risk Profile</h3>
                    <p className="text-sm text-gray-600">{getImpactStatus(totalImpact).level}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold text-${getImpactStatus(totalImpact).color}-600`}>
                    {totalImpact > 0 ? '+' : ''}{totalImpact.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">μDALY Total</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Disease Categories */}
          {sortedCategories.map(([key, category]) => {
            const IconComponent = category.icon as React.ComponentType<{ className?: string }>;
            const status = getImpactStatus(category.totalImpact);
            
            return (
              <Card key={key}>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <IconComponent className={`h-5 w-5 text-${category.color}-500`} />
                      <span className="text-base">{category.name}</span>
                      <Badge 
                        variant="secondary" 
                        className={`bg-${status.color}-100 text-${status.color}-800`}
                      >
                        {status.level}
                      </Badge>
                    </div>
                    <div className="text-right">
                       <div className={`text-lg font-bold text-${status.color}-600`}>
                        {category.totalImpact > 0 ? '+' : ''}{category.totalImpact.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">μDALY</div>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  {/* Impact Breakdown */}
                   <div className="grid md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-600">Risk Factors</span>
                        <span className="text-sm font-medium text-red-600">
                          -{category.riskContribution.toFixed(1)} μDALY
                        </span>
                      </div>
                        <Progress 
                        value={Math.min(100, category.riskContribution * 10)} 
                        className="h-2 bg-red-100" 
                      />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-600">Protective Factors</span>
                        <span className="text-sm font-medium text-green-600">
                          +{category.protectiveContribution.toFixed(1)} μDALY
                        </span>
                      </div>
                        <Progress 
                        value={Math.min(100, category.protectiveContribution * 10)} 
                        className="h-2 bg-green-100" 
                      />
                    </div>
                  </div>

                  {/* Conditions */}
                   <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700">Key Conditions ({category.percentage}% of total burden)</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {category.conditions.map((condition, idx) => (
                        <div key={idx} className="text-xs text-gray-600 flex items-center gap-2">
                          <div className="w-1 h-1 bg-gray-400 rounded-full" />
                          {condition}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {chartType === 'timeline' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Disease Development Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Short Term (Days to Weeks) */}
                <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-lg">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm font-medium text-blue-700">Days</div>
                    <div className="text-xs text-blue-600">1-30</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-800">Acute Metabolic Changes</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Blood glucose, lipids, inflammation markers, blood pressure
                    </p>
                    <div className="flex gap-2 mt-2">
                      {['sugar_sweetened_beverages', 'trans_fat', 'sodium'].map(factor => (
                        riskFactors[factor] && (
                          <Badge key={factor} variant="secondary" className="text-xs bg-red-100 text-red-700">
                            {factor.replace('_', ' ')}
                          </Badge>
                        )
                      ))}
                    </div>
                  </div>
                </div>

                {/* Medium Term (Months) */}
                <div className="flex items-start gap-4 p-4 bg-amber-50 rounded-lg">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm font-medium text-amber-700">Months</div>
                    <div className="text-xs text-amber-600">1-12</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-amber-800">Intermediate Risk Factors</h4>
                    <p className="text-sm text-amber-700 mt-1">
                      Chronic inflammation, insulin resistance, arterial stiffness
                    </p>
                    <div className="flex gap-2 mt-2">
                      {['processed_meat', 'red_meat'].map(factor => (
                        riskFactors[factor] && (
                          <Badge key={factor} variant="secondary" className="text-xs bg-amber-100 text-amber-700">
                            {factor.replace('_', ' ')}
                          </Badge>
                        )
                      ))}
                    </div>
                  </div>
                </div>

                {/* Long Term (Years) */}
                <div className="flex items-start gap-4 p-4 bg-red-50 rounded-lg">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm font-medium text-red-700">Years</div>
                    <div className="text-xs text-red-600">5-20+</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-red-800">Chronic Disease Manifestation</h4>
                    <p className="text-sm text-red-700 mt-1">
                      Heart disease, diabetes, cancer, stroke, dementia
                    </p>
                    <div className="text-lg font-bold text-red-700 mt-2">
                      {healthImpact.health_impact_minutes > 0 ? '+' : ''}
                      {(healthImpact.health_impact_minutes || 0).toFixed(2)} minutes
                    </div>
                    <div className="text-xs text-red-600">Expected healthy life impact</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {chartType === 'comparison' && (
        <div className="grid md:grid-cols-2 gap-6">
           {/* Risk Factors */}
          <Card>
            <CardHeader>
              <CardTitle className="text-red-700 flex items-center gap-2">
                <TrendingDown className="h-5 w-5" />
                Disease Risk Factors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(riskFactors)
                  .filter(([factor]) => (['red_meat','processed_meat','sugar_sweetened_beverages','trans_fat','sodium'].includes(factor)))
                  .sort(([,a], [,b]) => a - b)
                  .slice(0, 5)
                  .map(([factor, value]) => (
                    <div key={factor} className="flex items-center justify-between p-2 bg-red-50 rounded">
                      <span className="text-sm capitalize">{factor.replace('_', ' ')}</span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={Math.min(100, Math.abs(value) * 10)} 
                          className="w-16 h-2 bg-red-200" 
                        />
                        <span className="text-sm font-medium text-red-700 min-w-[50px] text-right">
                          -{Math.abs(value).toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Protective Factors */}
          <Card>
            <CardHeader>
              <CardTitle className="text-green-700 flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Protective Factors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(riskFactors)
                  .filter(([factor]) => !(['red_meat','processed_meat','sugar_sweetened_beverages','trans_fat','sodium'].includes(factor)))
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 5)
                  .map(([factor, value]) => (
                    <div key={factor} className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm capitalize">{factor.replace('_', ' ')}</span>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={Math.min(100, value * 10)} 
                          className="w-16 h-2 bg-green-200" 
                        />
                        <span className="text-sm font-medium text-green-700 min-w-[50px] text-right">
                          +{value.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Key Insights */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Disease Impact Insights</h4>
              <ul className="space-y-1 text-sm text-blue-700">
                <li>• HENI analysis covers {Object.keys(diseaseCategories).length} major disease categories</li>
                <li>• Cardiovascular disease represents the largest burden (45% of total DALYs)</li>
                <li>• Your food choices show a {totalImpact > 0 ? 'net protective' : 'net risk'} profile</li>
                <li>• Long-term impact: {Math.abs(healthImpact.health_impact_minutes || 0).toFixed(2)} minutes of {healthImpact.health_impact_minutes > 0 ? 'gained' : 'lost'} healthy life</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};