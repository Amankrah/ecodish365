'use client';
/**
 * Monetization Breakdown Component - Economic Valuation of Environmental Impacts
 * Detailed breakdown of environmental costs using Canadian economic factors
 */

import React, { useState } from 'react';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import {
  DollarSign,
  TrendingUp,
  PieChart,
  BarChart3,
  Info,
  ChevronDown,
  ChevronUp,
  Globe,
  Droplets,
  TreePine,
  Factory,
  Wind,
} from 'lucide-react';
import type {
  EnvironmentalImpactResult, EnvironmentalMonetization,
  EnvironmentalValueSource, MealComposition as EMealComposition,
} from '../../lib/api';
import type { UserType } from '../shared/AudienceToggle';

interface MonetizationBreakdownProps {
  results: EnvironmentalImpactResult;
  /** Audience-aware rendering. Defaults to 'individual'. */
  userType?: UserType;
}

// CODE-4 source attribution popover. Icon-only trigger; on click reveals the
// page-anchored source citation. Researcher / policy also see the page anchor
// + sensitivity range + methodological note + last-verified date.
const ValueSourceInfo: React.FC<{
  source?: EnvironmentalValueSource;
  userType: UserType;
}> = ({ source, userType }) => {
  const [open, setOpen] = useState<boolean>(false);
  if (!source) return null;
  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="ml-1 inline-flex items-center text-gray-400 hover:text-indigo-600 focus:outline-none"
        aria-label="Show monetary value source"
        title={source.source}
      >
        <Info className="h-3.5 w-3.5" />
      </button>
      {open && (
        <div
          className="absolute right-0 top-5 z-20 w-72 p-3 bg-white border border-gray-200 rounded-md shadow-lg text-[11px] text-gray-700 space-y-1"
          role="dialog"
        >
          <div className="font-semibold text-gray-900 text-xs">Source</div>
          <p>{source.source}</p>
          <div className="flex flex-wrap gap-2 text-[10px] text-gray-500">
            {source.currency_year && <span>currency: {source.currency_year}</span>}
            {source.last_verified && <span>last verified: {source.last_verified}</span>}
            {source.status === 'pending_page_citation' && (
              <Badge variant="outline" className="text-[10px]">pending page citation</Badge>
            )}
          </div>
          {userType !== 'individual' && (
            <>
              {source.page_anchor && (
                <div className="text-[10px] text-gray-600">
                  <span className="font-semibold">Anchor: </span>{source.page_anchor}
                </div>
              )}
              {source.sensitivity_range_2026 && (
                <div className="text-[10px] text-gray-600">
                  <span className="font-semibold">Sensitivity: </span>{source.sensitivity_range_2026}
                </div>
              )}
              {source.methodological_note && (
                <p className="text-[10px] italic text-gray-600 pt-1 border-t border-gray-100">
                  {source.methodological_note}
                </p>
              )}
            </>
          )}
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-[10px] text-indigo-600 hover:text-indigo-800 underline pt-1"
          >
            Close
          </button>
        </div>
      )}
    </span>
  );
};

export const MonetizationBreakdown: React.FC<MonetizationBreakdownProps> = ({
  results,
  userType = 'individual',
}) => {
  const [viewMode, setViewMode] = useState<'category' | 'individual'>('category');
  const [expandedCategory, setExpandedCategory] = useState<string | null>('Climate & Energy');

  type MealAnalysis = Required<EnvironmentalImpactResult>['data']['meal_analysis'];
  const analysis = (results?.data?.meal_analysis || {}) as Partial<MealAnalysis>;
  const monetization = (analysis?.monetization || {}) as Partial<EnvironmentalMonetization>;
  const composition = (analysis?.meal_composition || {}) as Partial<EMealComposition>;
  // CODE-4: per-category source attribution. Maps a midpoint category name
  // to its monetary value source dict.
  const valueSources: Record<string, EnvironmentalValueSource> = (
    monetization.value_sources || {}
  ) as Record<string, EnvironmentalValueSource>;

  // UI config for categories
  type CategoryColor = 'red' | 'orange' | 'green' | 'blue';
  interface CategoryUIConfig {
    icon: React.ElementType;
    color: CategoryColor;
    description: string;
    impacts: string[];
  }

  const categoryConfigMap: Record<string, CategoryUIConfig> = {
    'Climate & Energy': {
      icon: Globe,
      color: 'red',
      description: 'Costs from climate change, energy use, and atmospheric impacts',
      impacts: ['Global warming', 'Fossil resource scarcity', 'Stratospheric ozone depletion', 'Ozone formation, Human health', 'Ozone formation, Terrestrial ecosystems']
    },
    'Human Health': {
      icon: Wind,
      color: 'orange', 
      description: 'Health-related costs from air pollution and toxic exposures',
      impacts: ['Fine particulate matter formation', 'Human carcinogenic toxicity', 'Human non-carcinogenic toxicity', 'Ionizing radiation']
    },
    'Ecosystem Quality': {
      icon: TreePine,
      color: 'green',
      description: 'Costs from ecosystem damage and biodiversity loss',
      impacts: ['Terrestrial acidification', 'Freshwater eutrophication', 'Marine eutrophication', 'Terrestrial ecotoxicity', 'Freshwater ecotoxicity', 'Marine ecotoxicity']
    },
    'Resource Depletion': {
      icon: Droplets,
      color: 'blue',
      description: 'Costs from natural resource consumption and depletion',
      impacts: ['Water consumption', 'Land use', 'Mineral resource scarcity']
    }
  };

  // Format currency values
  const formatCurrency = (value: number): string => {
    if (value === 0) return 'CAD $0.000';
    if (value < 0.001) return `CAD $${(value * 1000).toFixed(3)}μ`;
    if (value < 1) return `CAD $${value.toFixed(3)}`;
    if (value < 1000) return `CAD $${value.toFixed(2)}`;
    if (value < 1000000) return `CAD $${(value / 1000).toFixed(1)}k`;
    return `CAD $${(value / 1000000).toFixed(1)}M`;
  };

  // Calculate per-unit costs
  const totalCost = monetization.total_cost ?? 0;
  const costPerCalorie = monetization.cost_per_calorie ?? 0;
  const totalWeight = composition.total_weight_grams ?? 0;
  const costPerGram = totalWeight > 0 ? totalCost / totalWeight : 0;
  const costPerProteinGram = monetization.cost_per_protein ?? 0;

  // Get color classes
  const getColorClasses = (color: string) => {
    const colorMap = {
      red: { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-200', accent: 'text-red-600', progress: 'bg-red-500' },
      orange: { bg: 'bg-orange-50', text: 'text-orange-900', border: 'border-orange-200', accent: 'text-orange-600', progress: 'bg-orange-500' },
      green: { bg: 'bg-green-50', text: 'text-green-900', border: 'border-green-200', accent: 'text-green-600', progress: 'bg-green-500' },
      blue: { bg: 'bg-blue-50', text: 'text-blue-900', border: 'border-blue-200', accent: 'text-blue-600', progress: 'bg-blue-500' },
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
  };

  return (
    <div className="space-y-6">
      {/* Header with Total Cost */}
      <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-lg border border-yellow-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <DollarSign className="h-8 w-8 text-yellow-600" />
            <div>
              <h3 className="text-xl font-bold text-gray-900">Total Environmental Cost</h3>
              <p className="text-sm text-gray-600">Economic valuation using Canadian factors</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-yellow-900">
              {formatCurrency(totalCost)}
            </div>
            <div className="text-sm text-yellow-700">per meal</div>
          </div>
        </div>

        {/* Quick Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-3 rounded-lg border border-yellow-200">
            <div className="text-sm text-gray-600">Per Calorie</div>
            <div className="text-lg font-bold text-gray-900">{formatCurrency(costPerCalorie)}</div>
          </div>
          <div className="bg-white p-3 rounded-lg border border-yellow-200">
            <div className="text-sm text-gray-600">Per Gram</div>
            <div className="text-lg font-bold text-gray-900">{formatCurrency(costPerGram)}</div>
          </div>
          <div className="bg-white p-3 rounded-lg border border-yellow-200">
            <div className="text-sm text-gray-600">Per Protein (g)</div>
            <div className="text-lg font-bold text-gray-900">{formatCurrency(costPerProteinGram)}</div>
          </div>
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm font-medium text-gray-700">View:</span>
        <div className="bg-gray-100 rounded-md p-1 flex">
          <Button
            variant={viewMode === 'category' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('category')}
            className="flex items-center gap-2"
          >
            <PieChart className="h-4 w-4" />
            By Category
          </Button>
          <Button
            variant={viewMode === 'individual' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('individual')}
            className="flex items-center gap-2"
          >
            <BarChart3 className="h-4 w-4" />
            Individual Impacts
          </Button>
        </div>
      </div>

      {/* Category View */}
      {viewMode === 'category' && (
        <div className="space-y-4">
          {Object.entries((monetization.cost_breakdown_by_category || {}) as Record<string, { total_cost: number; percentage_of_total: number; individual_impacts: Record<string, number> }> ).map(([categoryName, categoryInfo]) => {
            const isExpanded = expandedCategory === categoryName;
            const uiConfig = categoryConfigMap[categoryName] || { icon: Factory, color: 'blue' as CategoryColor, description: '', impacts: [] };
            const colors = getColorClasses(uiConfig.color);
            const CategoryIcon = uiConfig.icon;
            
            return (
              <div key={categoryName} className={`border rounded-lg ${colors.border}`}>
                <Button
                  variant="ghost"
                  onClick={() => setExpandedCategory(isExpanded ? null : categoryName)}
                  className={`w-full justify-between p-4 h-auto ${colors.bg} hover:${colors.bg}`}
                >
                  <div className="flex items-center gap-3">
                    <CategoryIcon className={`h-5 w-5 ${colors.accent}`} />
                    <div className="text-left">
                      <div className={`font-semibold ${colors.text}`}>{categoryName}</div>
                      <div className="text-sm text-gray-600">
                        {formatCurrency(categoryInfo.total_cost || 0)} ({(categoryInfo.percentage_of_total ?? 0).toFixed(1)}%)
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress 
                      value={categoryInfo.percentage_of_total} 
                      className="w-20 h-2" 
                    />
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </div>
                </Button>
                
                {isExpanded && (
                  <div className="border-t p-4 space-y-3">
                    {Object.entries(categoryInfo.individual_impacts || {}).map(([impactName, cost]) => (
                      <div key={impactName} className="bg-white p-3 rounded-lg border border-gray-100">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900 flex items-center">
                            {impactName}
                            <ValueSourceInfo
                              source={valueSources[impactName]}
                              userType={userType}
                            />
                          </span>
                          <span className="font-bold text-gray-900">
                            {formatCurrency((cost as number) || 0)}
                          </span>
                        </div>
                        <div className="mb-2">
                          <Progress 
                            value={(() => { const denom = categoryInfo.total_cost || 0; return Math.max(0, Math.min(100, denom > 0 ? ((cost as number) / denom) * 100 : 0)); })()} 
                            className="h-2" 
                          />
                        </div>
                        <div className="text-xs text-gray-600">
                          {(() => { const denom = totalCost; const pct = denom > 0 ? (((cost as number) / denom) * 100) : 0; return pct.toFixed(2); })()}% of total cost
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Individual Impacts View */}
      {viewMode === 'individual' && (
        <div className="space-y-3">
          <h4 className="font-semibold text-gray-900 mb-4">Top Cost Drivers</h4>
          {(monetization.top_cost_drivers || []).map((driver) => (
            <div key={driver.impact_category} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    #{driver.rank}
                  </Badge>
                  <span className="font-medium text-gray-900">{driver.impact_category}</span>
                </div>
                <div className="text-right">
                  <div className="font-bold text-gray-900">{formatCurrency(driver.cost || 0)}</div>
                  <div className="text-sm text-gray-600">{(driver.percentage_of_total ?? 0).toFixed(1)}%</div>
                </div>
              </div>
              <Progress value={driver.percentage_of_total ?? 0} className="h-3" />
            </div>
          ))}
        </div>
      )}

      {/* Cost Context */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Cost Efficiency */}
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Cost Efficiency Metrics
          </h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-blue-700">Environmental cost per 100 kcal:</span>
              <span className="font-bold text-blue-900">
                {formatCurrency(costPerCalorie * 100)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Environmental cost per 100g:</span>
              <span className="font-bold text-blue-900">
                {formatCurrency(costPerGram * 100)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Cost per gram of protein:</span>
              <span className="font-bold text-blue-900">
                {formatCurrency(costPerProteinGram)}
              </span>
            </div>
          </div>
        </div>

        {/* Economic Context */}
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <Info className="h-5 w-5" />
            Economic Valuation Context
          </h4>
          <div className="space-y-2 text-sm text-green-800">
            <p><strong>Social Cost of Carbon:</strong> CAD $185/tonne CO₂-eq (Environment Canada 2024)</p>
            <p><strong>Regional Adjustments:</strong> Canadian-specific factors applied</p>
            <p><strong>Methodology:</strong> Damage-cost approach with current economic valuations</p>
            <p><strong>Scope:</strong> External environmental costs not reflected in market prices</p>
          </div>
        </div>
      </div>

      {/* All Monetized Impacts */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Complete Monetization Breakdown
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
          {Object.entries((monetization.monetized_impacts || {}) as Record<string, number>).map(([impact, cost]) => {
            const costValue = cost as number;
            const percentage = totalCost > 0 ? (costValue / totalCost) * 100 : 0;
            
            return (
              <div key={impact} className="bg-white p-3 rounded-lg border border-gray-200">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-gray-700 text-xs font-medium leading-tight flex items-start">
                    <span>{impact}</span>
                    <ValueSourceInfo
                      source={valueSources[impact]}
                      userType={userType}
                    />
                  </span>
                  <span className="text-gray-900 font-bold text-xs">
                    {formatCurrency(costValue)}
                  </span>
                </div>
                <div className="mb-1">
                  <Progress value={Math.max(0.5, percentage)} className="h-1" />
                </div>
                <div className="text-xs text-gray-500">
                  {percentage.toFixed(2)}%
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Methodology Note */}
      <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
        <h4 className="font-semibold text-indigo-900 mb-2">Monetization Methodology</h4>
        <div className="text-sm text-indigo-800 space-y-1">
          <p>
            <strong>Approach:</strong> Damage-cost methodology using current Canadian economic factors
          </p>
          <p>
            <strong>Currency:</strong> Canadian Dollars (CAD) adjusted for inflation to 2024 values
          </p>
          <p>
            <strong>Regional Factors:</strong> Applied Canadian-specific adjustments for climate (+15%), 
            water (-30%), and land use (-20%) impacts
          </p>
          <p>
            <strong>Key Rate:</strong> Social Cost of Carbon at CAD $185 per tonne CO₂-eq 
            (Environment and Climate Change Canada, 2024)
          </p>
          <p>
            <strong>Limitation:</strong> Represents external environmental costs not captured in market prices
          </p>
        </div>
      </div>
    </div>
  );
};

export default MonetizationBreakdown;