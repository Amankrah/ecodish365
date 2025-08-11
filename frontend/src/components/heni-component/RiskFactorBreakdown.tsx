/**
 * Risk Factor Breakdown Component
 * Detailed analysis of HENI's 14 risk factors with scientific context
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import {
  TrendingUp,
  TrendingDown,
  Shield,
  Heart,
  Bone,
  Info,
  ChevronRight,
  ChevronDown,
  AlertTriangle
} from 'lucide-react';
import { type HENIResult, type HENIFoodProfile } from '../../lib/api';

type HENIAnalysis = HENIResult['data'] | HENIFoodProfile['data']['heni_analysis'];
type Props = { results: HENIResult | HENIAnalysis | HENIFoodProfile['data'] };

export const RiskFactorBreakdown: React.FC<Props> = ({ results }) => {
  const [expandedFactor, setExpandedFactor] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'impact' | 'scientific'>('impact');

  // Normalize inputs to a HENI analysis block
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

  if (!analysis?.risk_factor_analysis?.risk_factors) {
    return null;
  }

  const riskFactors: Record<string, number> = analysis.risk_factor_analysis.risk_factors;

  // Risk factor categories and metadata
  type RiskInfo = {
    category: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    description: string;
    diseases: string[];
    mechanism: string;
    evidenceLevel: string;
    dalysAttribute: string;
  };

  const riskFactorInfo: Record<string, RiskInfo> = {
    // Food Groups
    'fruits': {
      category: 'Protective Foods',
      icon: TrendingUp,
      color: 'green',
      description: 'Fresh, dried, or minimally processed fruits',
      diseases: ['Cardiovascular disease', 'Stroke', 'Type 2 diabetes'],
      mechanism: 'Antioxidants, fiber, potassium reduce inflammation and improve vascular health',
      evidenceLevel: 'High',
      dalysAttribute: '65% cardiovascular, 20% cancer, 15% metabolic'
    },
    'vegetables': {
      category: 'Protective Foods',
      icon: TrendingUp,
      color: 'green',
      description: 'Fresh, frozen, or minimally processed vegetables',
      diseases: ['Cardiovascular disease', 'Colorectal cancer', 'Stroke'],
      mechanism: 'Phytochemicals, fiber, folate support cellular health and reduce oxidative stress',
      evidenceLevel: 'High',
      dalysAttribute: '60% cardiovascular, 25% cancer, 15% other'
    },
    'whole_grains': {
      category: 'Protective Foods',
      icon: TrendingUp,
      color: 'green',
      description: 'Whole grain cereals, bread, and pasta',
      diseases: ['Type 2 diabetes', 'Cardiovascular disease', 'Colorectal cancer'],
      mechanism: 'Fiber, B-vitamins, minerals improve glucose metabolism and gut health',
      evidenceLevel: 'High',
      dalysAttribute: '45% diabetes, 35% cardiovascular, 20% cancer'
    },
    'nuts_seeds': {
      category: 'Protective Foods',
      icon: TrendingUp,
      color: 'green',
      description: 'Tree nuts, peanuts, and seeds',
      diseases: ['Cardiovascular disease', 'Type 2 diabetes'],
      mechanism: 'Healthy fats, protein, magnesium support heart and metabolic health',
      evidenceLevel: 'High',
      dalysAttribute: '70% cardiovascular, 30% metabolic'
    },
    'milk': {
      category: 'Neutral Foods',
      icon: Shield,
      color: 'blue',
      description: 'Dairy products including milk, yogurt, cheese',
      diseases: ['Colorectal cancer (protective)', 'Prostate cancer (risk)'],
      mechanism: 'Calcium, protein beneficial; saturated fat may increase some risks',
      evidenceLevel: 'Moderate',
      dalysAttribute: 'Net neutral with opposing effects'
    },

    // Risk Foods
    'red_meat': {
      category: 'Risk Foods',
      icon: TrendingDown,
      color: 'red',
      description: 'Unprocessed beef, pork, lamb, and goat',
      diseases: ['Colorectal cancer', 'Cardiovascular disease', 'Type 2 diabetes'],
      mechanism: 'Heme iron, saturated fat, and cooking compounds increase inflammation',
      evidenceLevel: 'Moderate',
      dalysAttribute: '50% cancer, 30% cardiovascular, 20% diabetes'
    },
    'processed_meat': {
      category: 'Risk Foods',
      icon: TrendingDown,
      color: 'red',
      description: 'Bacon, sausage, ham, deli meats, hot dogs',
      diseases: ['Colorectal cancer', 'Stomach cancer', 'Cardiovascular disease'],
      mechanism: 'Nitrates, sodium, advanced glycation end-products increase cancer risk',
      evidenceLevel: 'High',
      dalysAttribute: '60% cancer, 25% cardiovascular, 15% other'
    },
    'sugar_sweetened_beverages': {
      category: 'Risk Foods',
      icon: TrendingDown,
      color: 'red',
      description: 'Sodas, fruit drinks with added sugar, energy drinks',
      diseases: ['Type 2 diabetes', 'Obesity', 'Cardiovascular disease'],
      mechanism: 'Rapid glucose spikes, empty calories contribute to metabolic dysfunction',
      evidenceLevel: 'High',
      dalysAttribute: '50% diabetes, 30% cardiovascular, 20% obesity-related'
    },

    // Nutrients
    'omega_3': {
      category: 'Protective Nutrients',
      icon: TrendingUp,
      color: 'blue',
      description: 'EPA, DHA from fish; ALA from plants',
      diseases: ['Cardiovascular disease', 'Stroke', 'Depression'],
      mechanism: 'Anti-inflammatory effects, improve membrane function, reduce arrhythmias',
      evidenceLevel: 'High',
      dalysAttribute: '80% cardiovascular, 20% neurological'
    },
    'fiber': {
      category: 'Protective Nutrients',
      icon: TrendingUp,
      color: 'green',
      description: 'Insoluble and soluble dietary fiber',
      diseases: ['Colorectal cancer', 'Type 2 diabetes', 'Cardiovascular disease'],
      mechanism: 'Improved gut microbiome, glucose control, cholesterol reduction',
      evidenceLevel: 'High',
      dalysAttribute: '40% cancer, 35% diabetes, 25% cardiovascular'
    },
    'calcium': {
      category: 'Protective Nutrients',
      icon: TrendingUp,
      color: 'blue',
      description: 'Essential mineral for bone and cellular health',
      diseases: ['Colorectal cancer', 'Osteoporotic fractures'],
      mechanism: 'Cellular signaling, bone mineralization, possible tumor suppression',
      evidenceLevel: 'Moderate',
      dalysAttribute: '60% cancer, 40% bone health'
    },
    'polyunsaturated_fatty_acids': {
      category: 'Protective Nutrients',
      icon: TrendingUp,
      color: 'blue',
      description: 'PUFA from vegetable oils, nuts, fish',
      diseases: ['Cardiovascular disease'],
      mechanism: 'Replace saturated fats, improve lipid profiles, reduce inflammation',
      evidenceLevel: 'High',
      dalysAttribute: '90% cardiovascular, 10% other'
    },
    'trans_fat': {
      category: 'Risk Nutrients',
      icon: TrendingDown,
      color: 'red',
      description: 'Artificially hydrogenated oils in processed foods',
      diseases: ['Cardiovascular disease', 'Type 2 diabetes'],
      mechanism: 'Increase LDL, decrease HDL, promote inflammation and insulin resistance',
      evidenceLevel: 'High',
      dalysAttribute: '80% cardiovascular, 20% diabetes'
    },
    'sodium': {
      category: 'Risk Nutrients',
      icon: TrendingDown,
      color: 'amber',
      description: 'Salt content in processed and prepared foods',
      diseases: ['Hypertension', 'Stroke', 'Stomach cancer'],
      mechanism: 'Increases blood pressure, fluid retention, may damage gastric mucosa',
      evidenceLevel: 'High',
      dalysAttribute: '60% cardiovascular, 25% stroke, 15% cancer'
    }
  };

  // Separate positive and negative factors, then sort by impact magnitude
  const isRiskFactorName = (factor: string): boolean => {
    const info = riskFactorInfo[factor as keyof typeof riskFactorInfo];
    if (!info) return false;
    return info.category.toLowerCase().startsWith('risk');
  };

  const allFactors = Object.entries(riskFactors) as Array<[string, number]>;
  const positiveFactors = allFactors
    .filter(([factor]) => !isRiskFactorName(factor))
    .sort(([, a], [, b]) => b - a);
  const negativeFactors = allFactors
    .filter(([factor]) => isRiskFactorName(factor))
    .sort(([, a], [, b]) => b - a);
  // const sortedFactors = allFactors.sort(([, a], [, b]) => Math.abs(b) - Math.abs(a));

  const getImpactLevel = (value: number) => {
    const abs = Math.abs(value);
    if (abs >= 10) return 'High';
    if (abs >= 5) return 'Moderate';
    if (abs >= 1) return 'Low';
    return 'Minimal';
  };

  const getHealthIcon = (factor: string) => {
    const info = riskFactorInfo[factor as keyof typeof riskFactorInfo];
    if (!info) return Shield;
    
    if (info.diseases.some((d: string) => d.includes('Cardiovascular'))) return Heart;
    if (info.diseases.some((d: string) => d.includes('cancer'))) return AlertTriangle;
    if (info.diseases.some((d: string) => d.includes('diabetes'))) return TrendingDown;
    if (info.diseases.some((d: string) => d.includes('bone'))) return Bone;
    return info.icon;
  };

  return (
    <div className="space-y-4">
      {/* View Mode Toggle */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={viewMode === 'impact' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setViewMode('impact')}
        >
          Impact View
        </Button>
        <Button
          variant={viewMode === 'scientific' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setViewMode('scientific')}
        >
          Scientific View
        </Button>
      </div>

      {/* Render different content based on view mode */}
      {viewMode === 'impact' ? (
        /* IMPACT VIEW - Benefits and Risks separated */
        <>
          {/* Benefits Section */}
          {positiveFactors.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <h3 className="text-lg font-semibold text-green-700">Health Benefits ({positiveFactors.length})</h3>
              </div>
              <div className="space-y-2">
                {positiveFactors.map(([factor, value]) => {
          const info: RiskInfo = riskFactorInfo[factor as keyof typeof riskFactorInfo] || { 
            category: 'Unknown', 
            icon: Shield, 
            color: 'gray',
            description: factor.replace('_', ' '),
            diseases: ['Various conditions'],
            mechanism: 'Mechanism not specified',
            evidenceLevel: 'Unknown',
            dalysAttribute: 'Attribution not specified'
          };
          
          const isExpanded = expandedFactor === factor;
          const isPositive = !isRiskFactorName(factor);
           const impactLevel = getImpactLevel(value);
          const HealthIcon = getHealthIcon(factor);

          return (
            <Card key={factor} className="overflow-hidden border-green-100">
              <CardContent className="p-0">
                {/* Main Row */}
                <div 
                  className="flex items-center p-4 cursor-pointer hover:bg-green-50"
                  onClick={() => setExpandedFactor(isExpanded ? null : factor)}
                >
                  <div className="flex items-center gap-3 flex-1">
                    <HealthIcon className={`h-5 w-5 text-${info.color}-500`} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium capitalize">
                          {factor.replace('_', ' ')}
                        </h4>
                        <Badge 
                          variant="secondary"
                          className="text-xs bg-green-100 text-green-800"
                        >
                             {getImpactLevel(value)}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">{info.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className={`text-lg font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {isPositive ? '+' : '-'}{Math.abs(value).toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">μDALY</div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t bg-green-50">
                    <div className="p-4 space-y-4">
                      {/* Impact Details */}
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <h5 className="font-semibold text-gray-700 mb-2">Health Impact</h5>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm">Impact Level:</span>
                              <Badge className={`${isPositive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                {impactLevel}
                              </Badge>
                            </div>
                             <div className="flex justify-between">
                              <span className="text-sm">Time Equivalent:</span>
                              <span className="text-sm font-medium">
                                {(Math.abs(value) * 0.5256).toFixed(1)} minutes
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm">Category:</span>
                              <span className="text-sm">{info.category}</span>
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <h5 className="font-semibold text-gray-700 mb-2">Associated Diseases</h5>
                          <ul className="space-y-1">
                            {info.diseases.slice(0, 3).map((disease: string, idx: number) => (
                              <li key={idx} className="text-sm text-gray-600 flex items-center gap-2">
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
                                {disease}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* Visual Impact Bar */}
                      <div>
                        <h5 className="font-semibold text-gray-700 mb-2">Impact Magnitude</h5>
                        <div className="relative">
                          <Progress 
                            value={Math.min(100, Math.abs(value) * 5)} 
                            className={`h-3 ${isPositive ? 'bg-green-100' : 'bg-red-100'}`}
                          />
                          <div className="text-xs text-gray-600 mt-1">
                            {Math.abs(value).toFixed(1)} μDALY per serving
                          </div>
                        </div>
                      </div>

                      {/* Additional context for high-impact factors */}
                      {Math.abs(value) >= 5 && (
                        <div className={`p-3 rounded ${isPositive ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                          <div className="flex items-start gap-2">
                            <Info className={`h-4 w-4 ${isPositive ? 'text-green-600' : 'text-red-600'} mt-0.5 flex-shrink-0`} />
                            <div className={`text-sm ${isPositive ? 'text-green-800' : 'text-red-800'}`}>
                              <strong>High Impact Factor:</strong> This factor has a substantial influence on your health outcome. 
                              {isPositive 
                                ? ' Consider maintaining or increasing this beneficial component in your diet.'
                                : ' Consider reducing this risk factor for better health outcomes.'
                              }
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
            })}
          </div>
        </div>
      )}

      {/* Risks Section */}
      {negativeFactors.length > 0 && (
        <div className="space-y-3 mt-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="h-5 w-5 text-red-600" />
            <h3 className="text-lg font-semibold text-red-700">Health Risks ({negativeFactors.length})</h3>
          </div>
          <div className="space-y-2">
            {negativeFactors.map(([factor, value]) => {
              const info: RiskInfo = riskFactorInfo[factor as keyof typeof riskFactorInfo] || { 
                category: 'Unknown', 
                icon: Shield, 
                color: 'gray',
                description: factor.replace('_', ' '),
                diseases: ['Various conditions'],
                mechanism: 'Mechanism not specified',
                evidenceLevel: 'Unknown',
                dalysAttribute: 'Attribution not specified'
              };
              
              const isExpanded = expandedFactor === factor;
              const HealthIcon = getHealthIcon(factor);

              return (
                <Card key={factor} className="overflow-hidden border-red-100">
                  <CardContent className="p-0">
                    {/* Main Row */}
                    <div 
                      className="flex items-center p-4 cursor-pointer hover:bg-red-50"
                      onClick={() => setExpandedFactor(isExpanded ? null : factor)}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <HealthIcon className={`h-5 w-5 text-${info.color}-500`} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium capitalize">
                              {factor.replace('_', ' ')}
                            </h4>
                            <Badge 
                              variant="secondary"
                              className="text-xs bg-red-100 text-red-800"
                            >
                              {getImpactLevel(value)}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <p className="text-sm text-gray-600 capitalize">
                              {info.category} • {info.evidenceLevel} Evidence
                            </p>
                            <div className="flex items-center gap-2">
                              <Badge className="bg-red-100 text-red-800">
                                -{Math.abs(value).toFixed(1)} μDALY
                              </Badge>
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4 text-gray-400" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-gray-400" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="px-4 pb-4 border-t bg-red-50">
                        <div className="grid md:grid-cols-2 gap-4 pt-4">
                          <div>
                            <h5 className="font-semibold text-gray-700 mb-2">Health Impact</h5>
                            <p className="text-sm text-gray-600 mb-2">
                              {info.description}
                            </p>
                            <div className="text-xs text-gray-500">
                              {Math.abs(value).toFixed(1)} μDALY per serving
                              {' '}({Math.abs(value * 0.5256).toFixed(2)} minutes)
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            <div>
                              <h5 className="font-semibold text-gray-700 mb-2">Biological Mechanism</h5>
                              <p className="text-sm text-gray-600">{info.mechanism}</p>
                            </div>
                            
                            <div>
                              <h5 className="font-semibold text-gray-700 mb-2">Associated Diseases</h5>
                              <ul className="text-sm text-gray-600 space-y-1">
                                {info.diseases.slice(0, 3).map((disease: string, idx: number) => (
                                  <li key={idx}>• {disease}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                        
                        
                        
                        <div className="mt-4 text-sm text-gray-600 bg-white p-3 rounded border">
                          <strong>Recommendation:</strong>
                          {' Consider reducing this risk factor for better health outcomes.'}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
          </div>
        
      )}
      </>
      ) : (
        /* SCIENTIFIC VIEW - All factors with scientific details */
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {allFactors.map(([factor, value]) => {
              const info: RiskInfo = riskFactorInfo[factor as keyof typeof riskFactorInfo] || { 
                category: 'Unknown', 
                icon: Shield, 
                color: 'gray',
                description: factor.replace('_', ' '),
                diseases: ['Various conditions'],
                mechanism: 'Mechanism not specified',
                evidenceLevel: 'Unknown',
                dalysAttribute: 'Attribution not specified'
              };
              
              const isPositive = value > 0;
              const HealthIcon = getHealthIcon(factor);

              return (
                <Card key={factor} className={`p-4 ${isPositive ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <HealthIcon className={`h-5 w-5 text-${info.color}-600`} />
                        <h4 className="font-semibold capitalize text-sm">
                          {factor.replace('_', ' ')}
                        </h4>
                      </div>
                      <Badge 
                        variant={isPositive ? "default" : "destructive"}
                        className={`text-xs ${isPositive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                      >
                        {value > 0 ? '+' : ''}{value.toFixed(1)} μDALY
                      </Badge>
                    </div>
                    
                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="font-medium">Category:</span> {info.category}
                      </div>
                      <div>
                        <span className="font-medium">Evidence:</span> {info.evidenceLevel}
                      </div>
                      <div>
                        <span className="font-medium">Mechanism:</span>
                        <p className="mt-1 text-gray-600">{info.mechanism}</p>
                      </div>
                      <div>
                        <span className="font-medium">Disease Attribution:</span>
                        <p className="mt-1 text-gray-600">{info.dalysAttribute}</p>
                      </div>
                      <div>
                        <span className="font-medium">Associated Diseases:</span>
                        <ul className="mt-1 text-gray-600">
                          {info.diseases.slice(0, 2).map((disease: string, idx: number) => (
                            <li key={idx}>• {disease}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Risk Factor Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-lg font-bold text-green-600">
                {Object.keys(riskFactors).filter(f => !isRiskFactorName(f)).length}
              </div>
              <div className="text-xs text-gray-500">Protective Factors</div>
            </div>
            <div>
              <div className="text-lg font-bold text-red-600">
                {Object.keys(riskFactors).filter(f => isRiskFactorName(f)).length}
              </div>
              <div className="text-xs text-gray-500">Risk Factors</div>
            </div>
            <div>
              <div className="text-lg font-bold text-blue-600">
                {Object.values(riskFactors).filter(v => Math.abs(v) >= 5).length}
              </div>
              <div className="text-xs text-gray-500">High Impact</div>
            </div>
            <div>
              <div className="text-lg font-bold text-gray-600">
                {Object.keys(riskFactors).length}
              </div>
              <div className="text-xs text-gray-500">Total Analyzed</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};