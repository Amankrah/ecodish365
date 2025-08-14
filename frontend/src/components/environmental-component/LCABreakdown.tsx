'use client';
/**
 * LCA Breakdown Component - Detailed Life Cycle Assessment Results
 * Comprehensive breakdown of all 18 impact categories
 */

import React, { useState } from 'react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Globe,
  Droplets,
  TreePine,
  Factory,
  Zap,
  Wind,
  Sun,
  Skull,
  Eye,
  Mountain,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import type { EnvironmentalImpactResult, LCAResults } from '../../lib/api';

interface LCABreakdownProps {
  results: EnvironmentalImpactResult;
}

export const LCABreakdown: React.FC<LCABreakdownProps> = ({ results }) => {
  const [expandedCategory, setExpandedCategory] = useState<string | null>('Climate & Energy');
  const analysis = (results?.data?.meal_analysis || {}) as Partial<Required<EnvironmentalImpactResult>['data']['meal_analysis']>;
  const lca = (analysis?.lca_results || {}) as Partial<LCAResults>;

  // Categorize impacts with detailed information
  const impactCategories = {
    'Climate & Energy': {
      color: 'red',
      icon: Globe,
      description: 'Impacts related to climate change, energy use, and atmospheric chemistry',
      impacts: [
        {
          key: 'Global warming',
          name: 'Climate Change',
          value: lca['Global warming'] || 0,
          unit: 'kg CO₂-eq',
          description: 'Radiative forcing effects contributing to global warming over 100 years',
          icon: Globe,
        },
        {
          key: 'Stratospheric ozone depletion',
          name: 'Ozone Depletion',
          value: lca['Stratospheric ozone depletion'] || 0,
          unit: 'kg CFC11-eq',
          description: 'Depletion of stratospheric ozone layer protection',
          icon: Sun,
        },
        {
          key: 'Ozone formation, Human health',
          name: 'Photochemical Ozone (Health)',
          value: lca['Ozone formation, Human health'] || 0,
          unit: 'kg NOx-eq',
          description: 'Ground-level ozone formation affecting human health',
          icon: Wind,
        },
        {
          key: 'Ozone formation, Terrestrial ecosystems',
          name: 'Photochemical Ozone (Ecosystems)',
          value: lca['Ozone formation, Terrestrial ecosystems'] || 0,
          unit: 'kg NOx-eq',
          description: 'Ground-level ozone formation affecting plant growth',
          icon: TreePine,
        },
        {
          key: 'Fossil resource scarcity',
          name: 'Fossil Fuel Depletion',
          value: lca['Fossil resource scarcity'] || 0,
          unit: 'kg oil-eq',
          description: 'Depletion of fossil fuel resources and energy sources',
          icon: Factory,
        },
      ]
    },
    'Human Health': {
      color: 'orange',
      icon: Skull,
      description: 'Direct impacts on human health and well-being',
      impacts: [
        {
          key: 'Fine particulate matter formation',
          name: 'Particulate Matter',
          value: lca['Fine particulate matter formation'] || 0,
          unit: 'kg PM2.5-eq',
          description: 'Fine particles affecting respiratory and cardiovascular health',
          icon: Wind,
        },
        {
          key: 'Human carcinogenic toxicity',
          name: 'Cancer Risk',
          value: lca['Human carcinogenic toxicity'] || 0,
          unit: 'kg 1,4-DCB-eq',
          description: 'Exposure to carcinogenic substances increasing cancer risk',
          icon: Skull,
        },
        {
          key: 'Human non-carcinogenic toxicity',
          name: 'Toxic Effects',
          value: lca['Human non-carcinogenic toxicity'] || 0,
          unit: 'kg 1,4-DCB-eq',
          description: 'Exposure to toxic substances causing non-cancer health effects',
          icon: Eye,
        },
        {
          key: 'Ionizing radiation',
          name: 'Radiation Exposure',
          value: lca['Ionizing radiation'] || 0,
          unit: 'kBq Co-60-eq',
          description: 'Exposure to ionizing radiation affecting human health',
          icon: Zap,
        },
      ]
    },
    'Ecosystem Quality': {
      color: 'green',
      icon: TreePine,
      description: 'Impacts on natural ecosystems and biodiversity',
      impacts: [
        {
          key: 'Terrestrial acidification',
          name: 'Soil Acidification',
          value: lca['Terrestrial acidification'] || 0,
          unit: 'kg SO₂-eq',
          description: 'Acidification of soils affecting plant growth and soil organisms',
          icon: Mountain,
        },
        {
          key: 'Freshwater eutrophication',
          name: 'Freshwater Nutrients',
          value: lca['Freshwater eutrophication'] || 0,
          unit: 'kg P-eq',
          description: 'Excess nutrients in freshwater causing algae blooms and oxygen depletion',
          icon: Droplets,
        },
        {
          key: 'Marine eutrophication',
          name: 'Marine Nutrients',
          value: lca['Marine eutrophication'] || 0,
          unit: 'kg N-eq',
          description: 'Excess nutrients in marine environments affecting aquatic ecosystems',
          icon: Droplets,
        },
        {
          key: 'Terrestrial ecotoxicity',
          name: 'Land Toxicity',
          value: lca['Terrestrial ecotoxicity'] || 0,
          unit: 'kg 1,4-DCB-eq',
          description: 'Toxic effects on terrestrial organisms and ecosystems',
          icon: TreePine,
        },
        {
          key: 'Freshwater ecotoxicity',
          name: 'Freshwater Toxicity',
          value: lca['Freshwater ecotoxicity'] || 0,
          unit: 'kg 1,4-DCB-eq',
          description: 'Toxic effects on freshwater organisms and ecosystems',
          icon: Droplets,
        },
        {
          key: 'Marine ecotoxicity',
          name: 'Marine Toxicity',
          value: lca['Marine ecotoxicity'] || 0,
          unit: 'kg 1,4-DCB-eq',
          description: 'Toxic effects on marine organisms and ecosystems',
          icon: Droplets,
        },
      ]
    },
    'Resource Depletion': {
      color: 'blue',
      icon: Mountain,
      description: 'Depletion of natural resources and land use impacts',
      impacts: [
        {
          key: 'Land use',
          name: 'Land Transformation',
          value: lca['Land use'] || 0,
          unit: 'm²a crop-eq',
          description: 'Land occupation and transformation for agricultural production',
          icon: TreePine,
        },
        {
          key: 'Water consumption',
          name: 'Freshwater Use',
          value: lca['Water consumption'] || 0,
          unit: 'm³',
          description: 'Consumption of freshwater resources from natural sources',
          icon: Droplets,
        },
        {
          key: 'Mineral resource scarcity',
          name: 'Mineral Depletion',
          value: lca['Mineral resource scarcity'] || 0,
          unit: 'kg Cu-eq',
          description: 'Depletion of mineral resources and raw materials',
          icon: Mountain,
        },
      ]
    },
  };

  // Format impact values using backend's standard units; switch to scientific notation when very small
  const formatImpactValue = (value: number, unit: string): string => {
    if (!Number.isFinite(value) || value === 0) return `0 ${unit}`;

    const absVal = Math.abs(value);
    // Use standard unit as-is; only change representation for readability
    if (absVal >= 1) return `${value.toFixed(3)} ${unit}`;
    if (absVal >= 1e-3) return `${value.toFixed(6)} ${unit}`; // still readable without switching units
    // Very small: scientific notation (e.g., 3.2e-6)
    return `${value.toExponential(2)} ${unit}`;
  };

  // Get color classes based on category
  const getColorClasses = (color: string) => {
    const colorMap = {
      red: { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-200', accent: 'text-red-600' },
      orange: { bg: 'bg-orange-50', text: 'text-orange-900', border: 'border-orange-200', accent: 'text-orange-600' },
      green: { bg: 'bg-green-50', text: 'text-green-900', border: 'border-green-200', accent: 'text-green-600' },
      blue: { bg: 'bg-blue-50', text: 'text-blue-900', border: 'border-blue-200', accent: 'text-blue-600' },
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
  };

  // Monetary factors from backend monetization.py for proper normalization
  const monetaryFactors: Record<string, number> = {
    'Global warming': 221.0,  // CAD per tonne CO2-eq
    'Fine particulate matter formation': 52920.0,  // CAD per tonne PM2.5-eq
    'Human carcinogenic toxicity': 0.1029,  // CAD per kg 1,4-DCB-eq
    'Human non-carcinogenic toxicity': 0.000808,  // CAD per kg 1,4-DCB-eq
    'Ionizing radiation': 0.000056,  // CAD per kBq Co-60-eq
    'Ozone formation, Human health': 8500.0,  // CAD per tonne NOx-eq
    'Terrestrial acidification': 1985.0,  // CAD per tonne SO2-eq
    'Freshwater eutrophication': 38220.0,  // CAD per tonne P-eq
    'Marine eutrophication': 9560.0,  // CAD per tonne N-eq
    'Terrestrial ecotoxicity': 0.00081,  // CAD per kg 1,4-DCB-eq
    'Freshwater ecotoxicity': 0.00081,  // CAD per kg 1,4-DCB-eq
    'Marine ecotoxicity': 0.000081,  // CAD per kg 1,4-DCB-eq
    'Ozone formation, Terrestrial ecosystems': 2100.0,  // CAD per tonne NOx-eq
    'Stratospheric ozone depletion': 80850.0,  // CAD per tonne CFC11-eq
    'Fossil resource scarcity': 0.2205,  // CAD per kg oil-eq
    'Mineral resource scarcity': 0.0956,  // CAD per kg Cu-eq
    'Water consumption': 0.0162,  // CAD per m³
    'Land use': 0.00617,  // CAD per m²*year crop-eq
  };

  // Categories priced per tonne (need kg->tonne conversion)
  const perTonneCategories = new Set([
    'Global warming',
    'Fine particulate matter formation',
    'Terrestrial acidification',
    'Freshwater eutrophication',
    'Marine eutrophication',
    'Stratospheric ozone depletion',
    'Ozone formation, Human health',
    'Ozone formation, Terrestrial ecosystems',
  ]);

  // Calculate monetized values for all impacts
  const monetizedValues: Record<string, number> = {};

  Object.entries(lca as Record<string, number>).forEach(([key, value]) => {
    const numericValue = typeof value === 'number' ? value : 0;
    const monetaryFactor = monetaryFactors[key];
    
    if (monetaryFactor && numericValue > 0) {
      // Apply unit conversion for per-tonne categories
      const unitScale = perTonneCategories.has(key) ? 1.0 / 1000.0 : 1.0;
      const monetizedValue = (numericValue * unitScale) * monetaryFactor;
      monetizedValues[key] = monetizedValue;
    } else {
      monetizedValues[key] = 0;
    }
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Info className="h-5 w-5 text-gray-500" />
        <span className="text-sm text-gray-600">
          Complete ReCiPe 2016 midpoint impact assessment across 18 categories
        </span>
      </div>

      {Object.entries(impactCategories).map(([categoryName, category]) => {
        const isExpanded = expandedCategory === categoryName;
        const colors = getColorClasses(category.color);
        const CategoryIcon = category.icon;
        
         // Category total no longer used since comparisons are removed
        
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
                  <div className="text-sm text-gray-600">{category.description}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={colors.accent}>
                  {category.impacts.length} impacts
                </Badge>
                {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </Button>
            
            {isExpanded && (
              <div className="border-t p-4 space-y-4">
                 {category.impacts.map((impact) => {
                   const ImpactIcon = impact.icon;
                   const monetized = monetizedValues[impact.key] || 0;
                   return (
                     <div key={impact.key} className="bg-white p-3 rounded-lg border border-gray-100">
                       <div className="flex items-center justify-between mb-2">
                         <div className="flex items-center gap-2">
                           <ImpactIcon className={`h-4 w-4 ${colors.accent}`} />
                           <span className="font-medium text-gray-900">{impact.name}</span>
                         </div>
                         <div className="flex items-center gap-3">
                           <span className="font-bold text-gray-900 text-sm">
                             {formatImpactValue(impact.value, impact.unit)}
                           </span>
                           {monetized > 0 && (
                             <span className="text-xs text-gray-600">${monetized.toFixed(2)} CAD</span>
                           )}
                         </div>
                       </div>
                       <div className="text-xs text-gray-600">
                         {impact.description}
                       </div>
                       {impact.value === 0 && (
                         <div className="text-xs text-green-600 mt-1 font-medium">
                           No impact detected for this category
                         </div>
                       )}
                     </div>
                   );
                 })}
                
                {/* Removed category percentage summary to avoid cross-indicator comparisons */}
              </div>
            )}
          </div>
        );
      })}
      
      {/* Summary Information */}
      <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
        <h4 className="font-semibold text-indigo-900 mb-2">LCA Methodology Summary</h4>
        <div className="text-sm text-indigo-800 space-y-1">
          <p>
            <strong>Method:</strong> ReCiPe 2016 v1.1 Midpoint (H) with Canadian regional factors
          </p>
          <p>
            <strong>Scope:</strong> Cradle-to-gate life cycle assessment including production, processing, and distribution
          </p>
          <p>
            <strong>Time Horizon:</strong> 100-year Global Warming Potential (GWP-100) for climate impacts
          </p>
          <p>
            <strong>Regional Factors:</strong> Applied Canadian-specific characterization factors for climate (+15%), 
            water (-30%), and land use (-20%) impacts
          </p>
        </div>
      </div>
    </div>
  );
};

export default LCABreakdown;