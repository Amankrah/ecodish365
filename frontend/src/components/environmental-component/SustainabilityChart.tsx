'use client';
/**
 * Sustainability Chart Component - Comprehensive Sustainability Assessment Visualization
 */

import React from 'react';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import {
  Leaf,
  Apple,
  Factory,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertTriangle,
  Info,
} from 'lucide-react';
import type { EnvironmentalImpactResult, SustainabilityScore, MealComposition as EMealComposition } from '../../lib/api';

interface SustainabilityChartProps {
  results: EnvironmentalImpactResult;
}

export const SustainabilityChart: React.FC<SustainabilityChartProps> = ({ results }) => {
  type MealAnalysis = Required<EnvironmentalImpactResult>['data']['meal_analysis'];
  const analysis = (results?.data?.meal_analysis || {}) as Partial<MealAnalysis>;
  const sustainability = (analysis?.sustainability_score || {}) as Partial<SustainabilityScore>;
  const composition = (analysis?.meal_composition || {}) as Partial<EMealComposition>;

  // Get sustainability level info
  const getSustainabilityLevel = (score: number) => {
    if (score >= 80) return { 
      level: 'Excellent', 
      color: 'text-green-600', 
      bgColor: 'bg-green-100', 
      borderColor: 'border-green-300',
      icon: CheckCircle, 
      description: 'Outstanding sustainability performance across all dimensions' 
    };
    if (score >= 60) return { 
      level: 'Good', 
      color: 'text-blue-600', 
      bgColor: 'bg-blue-100', 
      borderColor: 'border-blue-300',
      icon: TrendingUp, 
      description: 'Good sustainability with room for improvement' 
    };
    if (score >= 40) return { 
      level: 'Fair', 
      color: 'text-yellow-600', 
      bgColor: 'bg-yellow-100', 
      borderColor: 'border-yellow-300',
      icon: Info, 
      description: 'Average sustainability with significant improvement opportunities' 
    };
    if (score >= 20) return { 
      level: 'Poor', 
      color: 'text-orange-600', 
      bgColor: 'bg-orange-100', 
      borderColor: 'border-orange-300',
      icon: TrendingDown, 
      description: 'Below-average sustainability requiring attention' 
    };
    return { 
      level: 'Very Poor', 
      color: 'text-red-600', 
      bgColor: 'bg-red-100', 
      borderColor: 'border-red-300',
      icon: AlertTriangle, 
      description: 'Poor sustainability performance across multiple dimensions' 
    };
  };

  const overallScore = sustainability.overall_sustainability_score ?? 0;
  const envScore = sustainability.environmental_score ?? 0;
  const nutritionScore = sustainability.nutritional_score ?? 0;
  const processingScore = sustainability.processing_score ?? 0;

  const overallLevel = getSustainabilityLevel(overallScore);
  const envLevel = getSustainabilityLevel(envScore);
  const nutritionLevel = getSustainabilityLevel(nutritionScore);
  const processingLevel = getSustainabilityLevel(processingScore);

  // Component scores breakdown
  const componentScores = [
    {
      name: 'Environmental Impact',
      score: envScore,
      level: envLevel,
      icon: Leaf,
      description: 'LCA-based environmental performance assessment',
      details: 'Based on 18 impact categories including climate, water, land use, and biodiversity',
    },
    {
      name: 'Nutritional Quality',
      score: nutritionScore,
      level: nutritionLevel,
      icon: Apple,
      description: 'Nutrient density and dietary quality assessment',
      details: 'Considers macro/micronutrient profile, dietary fiber, and beneficial compounds',
    },
    {
      name: 'Processing Level',
      score: processingScore,
      level: processingLevel,
      icon: Factory,
      description: 'Food processing intensity and naturalness',
      details: 'Evaluates degree of processing, additives, and preservation methods',
    },
  ];

  // Category-specific scores if available
  const categoryScores = Object.entries((sustainability.category_scores || {}) as Record<string, number>);

  return (
    <div className="space-y-6">
      {/* Overall Score Display */}
      <div className={`p-6 rounded-lg border-2 ${overallLevel.borderColor} ${overallLevel.bgColor}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {(() => { const OverallIcon = overallLevel.icon; return <OverallIcon className={`h-8 w-8 ${overallLevel.color}`} />; })()}
            <div>
              <h3 className="text-xl font-bold text-gray-900">Overall Sustainability</h3>
              <p className="text-sm text-gray-600">{overallLevel.description}</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${overallLevel.color}`}>
              {overallScore.toFixed(0)}
            </div>
            <div className="text-sm text-gray-600">out of 100</div>
          </div>
        </div>
        
        <div className="relative mb-2">
          <Progress value={overallScore} className="h-4" />
          <div className="absolute inset-0 flex items-center">
            <div className="flex justify-between w-full px-2 text-xs font-medium text-white drop-shadow">
              <span>0</span>
              <Badge className={`${overallLevel.color} bg-white bg-opacity-20`}>
                {overallLevel.level}
              </Badge>
              <span>100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Component Scores */}
      <div>
        <h4 className="font-semibold text-gray-900 mb-4">Component Assessment</h4>
        <div className="space-y-4">
          {componentScores.map((component, index) => {
            const ComponentIcon = component.icon;
            const LevelIcon = component.level.icon;
            
            return (
              <div key={index} className={`p-4 rounded-lg border ${component.level.borderColor} ${component.level.bgColor}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <ComponentIcon className={`h-5 w-5 ${component.level.color}`} />
                    <span className="font-medium text-gray-900">{component.name}</span>
                    <LevelIcon className={`h-4 w-4 ${component.level.color}`} />
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={component.level.color}>
                      {component.level.level}
                    </Badge>
                    <span className={`font-bold ${component.level.color}`}>
                      {component.score.toFixed(0)}/100
                    </span>
                  </div>
                </div>
                
                <Progress value={component.score} className="mb-2" />
                
                <div className="space-y-1">
                  <div className="text-sm text-gray-700">
                    {component.description}
                  </div>
                  <div className="text-xs text-gray-600">
                    {component.details}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Category-Specific Scores */}
      {categoryScores.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-4">Category Performance</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {categoryScores.map(([category, score]) => {
              const numericScore = typeof score === 'number' ? score : 0;
              const categoryLevel = getSustainabilityLevel(numericScore);
              
              return (
                <div key={category} className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {category.replace('_', ' ')}
                    </span>
                    <Badge variant="outline" className={categoryLevel.color}>
                      {categoryLevel.level}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress value={numericScore} className="flex-1 h-2" />
                    <span className="text-sm font-bold text-gray-900 min-w-[3rem]">
                      {numericScore.toFixed(0)}/100
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations Section */}
      {((sustainability.recommendations || []).length > 0) && (
        <div>
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Sustainability Recommendations
          </h4>
          <div className="space-y-3">
            {(sustainability.recommendations || []).slice(0, 5).map((recommendation, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="bg-green-100 rounded-full p-1 mt-0.5">
                  <Leaf className="h-3 w-3 text-green-600" />
                </div>
                <div className="flex-1">
                  <div className="text-sm text-green-800">{recommendation}</div>
                </div>
                <Badge variant="outline" className="text-green-700 text-xs">
                  {index + 1}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Meal Context */}
      <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
        <h4 className="font-semibold text-indigo-900 mb-3">Meal Context</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span
              className="text-indigo-700"
              title="Includes a 31.9% food-waste adjustment: total = entered amounts / (1 − 0.319)."
            >
              Total Weight:
            </span>
            <div className="font-semibold text-indigo-900">
              {(composition.total_weight_grams ?? 0).toFixed(0)}g
            </div>
          </div>
          <div>
            <span className="text-indigo-700">Energy Density:</span>
            <div className="font-semibold text-indigo-900">
              {(() => {
                const weight = composition.total_weight_grams ?? 0;
                const energy = composition.total_energy_kcal ?? 0;
                const val = weight > 0 ? (energy / weight) * 100 : 0;
                return val.toFixed(1);
              })()} kcal/100g
            </div>
          </div>
          <div>
            <span className="text-indigo-700">Protein:</span>
            <div className="font-semibold text-indigo-900">
              {(() => {
                const protein = composition.macronutrient_distribution?.protein_percent ?? 0;
                return protein.toFixed(1);
              })()}%
            </div>
          </div>
          <div>
            <span className="text-indigo-700">Food Items:</span>
            <div className="font-semibold text-indigo-900">
              {composition.food_count ?? 0}
            </div>
          </div>
        </div>
      </div>

      {/* Methodology Note */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
          <Info className="h-4 w-4" />
          Sustainability Assessment Methodology
        </h4>
        <div className="text-sm text-gray-700 space-y-1">
          <p>
            <strong>Environmental Score:</strong> Comprehensive LCA assessment using ReCiPe 2016 methodology 
            with Canadian regional factors across 18 impact categories
          </p>
          <p>
            <strong>Nutritional Score:</strong> Multi-dimensional analysis of nutrient density, dietary quality, 
            and health-promoting compounds based on dietary guidelines
          </p>
          <p>
            <strong>Processing Score:</strong> Assessment of food processing intensity using NOVA classification 
            and evaluation of naturalness, additives, and preservation methods
          </p>
          <p>
            <strong>Overall Score:</strong> Weighted integration of all dimensions with emphasis on environmental 
            impact (40%), nutritional quality (35%), and processing level (25%)
          </p>
        </div>
      </div>
    </div>
  );
};

export default SustainabilityChart;