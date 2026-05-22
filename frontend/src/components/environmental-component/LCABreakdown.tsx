'use client';
/**
 * LCABreakdown — v1 trimmed LCA display.
 *
 * v1 scope (manuscript §7.5; backend `_calculate_midpoint_impacts`):
 *   - 3 ReCiPe 2016 H midpoint categories with literature-anchored centrals
 *     and worst/best-case uncertainty envelopes: Global warming, Land use,
 *     Water consumption. All anchored to Poore & Nemecek 2018 (GW + Land)
 *     and Mekonnen & Hoekstra 2011/2012 blue-water-only (Water).
 *   - Resources endpoint is NOT estimable in v1 (both fossil + mineral
 *     scarcity midpoints excluded from the consumed vector).
 *   - 15 other ReCiPe midpoints not consumed; collapsed behind a
 *     methodology accordion that explains the v1 scope decision and the
 *     v2 path (TODO-CODE-LCA-2 licensed AGRIBALYSE-LCI re-scoring).
 */

import React, { useState } from 'react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Globe, Droplets, TreePine, ChevronDown, ChevronUp, Info, AlertCircle,
} from 'lucide-react';
import type {
  EnvironmentalImpactResult, LCAResults, LCABands, EndpointImpacts, EndpointBands,
} from '../../lib/api';
import { UncertaintyBandBar } from './UncertaintyBandBar';

interface LCABreakdownProps {
  results: EnvironmentalImpactResult;
}

// Literature anchors per category. Per-100-kcal would require knowing the
// meal's kcal, so we anchor on the per-serving / per-kg published values
// most commonly cited; the band-bracketing call-out in §7.5 still applies
// even though the units differ from the API output (per 100 kcal).
// For now we show no inline anchor in the breakdown (the smoke test
// `_smoke_api_vs_literature.py` is where the bracketing claim is verified).
const CONSUMED_CATEGORIES = [
  {
    key: 'Global warming' as const,
    name: 'Climate Change',
    unit: 'kg CO₂-eq',
    color: 'rose' as const,
    icon: Globe,
    description:
      'IPCC AR5 100-year global warming potential. Anchored to Poore & Nemecek 2018 ' +
      'Fig. 1 per-food-group means; cross-checked against Stylianou et al. 2021 ' +
      '(IMPACT World+) per-serving averages.',
  },
  {
    key: 'Land use' as const,
    name: 'Land Use',
    unit: 'm²a crop-eq',
    color: 'emerald' as const,
    icon: TreePine,
    description:
      'Annual cropland equivalent occupation, ReCiPe 2016. Anchored to ' +
      'Poore & Nemecek 2018 Fig. 1 per-food-group means.',
  },
  {
    key: 'Water consumption' as const,
    name: 'Water Use',
    unit: 'm³',
    color: 'sky' as const,
    icon: Droplets,
    description:
      'Consumptive blue-water freshwater use (Hoekstra–Pfister definition, ' +
      'ReCiPe 2016 Water Consumption Potential). Anchored to Mekonnen & Hoekstra ' +
      '2011/2012 blue-water-only footprints — NOT the green+blue+grey total.',
  },
];

// Categories NOT consumed in v1; surfaced in the methodology accordion only.
const NON_CONSUMED_CATEGORIES = [
  { name: 'Terrestrial acidification', why: 'P&N reports SO₂-aggregate, not unit-compatible with ReCiPe' },
  { name: 'Freshwater eutrophication', why: 'P&N reports PO₄-aggregate, not unit-compatible with ReCiPe' },
  { name: 'Marine eutrophication',     why: 'Same as above' },
  { name: 'Fine particulate matter formation', why: 'No per-food-group numerical literature target' },
  { name: 'Stratospheric ozone depletion', why: 'Dekker 2020 flags LCI as incomplete for this category' },
  { name: 'Ionizing radiation',         why: 'Dekker 2020 flags LCI as incomplete' },
  { name: 'Ozone formation (Human health)', why: 'No per-food-group target; Dekker 2020 LCI incomplete' },
  { name: 'Ozone formation (Terrestrial ecosystems)', why: 'No per-food-group target' },
  { name: 'Human carcinogenic toxicity', why: 'RIVM 2017 flags as low-confidence; no per-food target' },
  { name: 'Human non-carcinogenic toxicity', why: 'RIVM 2017 flags as low-confidence' },
  { name: 'Terrestrial ecotoxicity',    why: 'RIVM 2017 flags as low-confidence' },
  { name: 'Freshwater ecotoxicity',     why: 'RIVM 2017 flags as low-confidence' },
  { name: 'Marine ecotoxicity',         why: 'RIVM 2017 flags as low-confidence' },
  { name: 'Mineral resource scarcity',  why: 'No per-food-group literature target' },
  { name: 'Fossil resource scarcity',   why: 'No per-food-group literature target' },
];

export const LCABreakdown: React.FC<LCABreakdownProps> = ({ results }) => {
  const [showMethodology, setShowMethodology] = useState(false);
  const [showEndpoints, setShowEndpoints] = useState(false);
  const analysis = (results?.data?.meal_analysis || {}) as Partial<
    Required<EnvironmentalImpactResult>['data']['meal_analysis']
  >;
  const lca: Partial<LCAResults> = analysis?.lca_results || {};
  const bands: LCABands = (analysis?.lca_results_bands as LCABands) || {};
  const endpoints: Partial<EndpointImpacts> = analysis?.endpoint_impacts || {};
  const endpointBands: EndpointBands = (analysis?.endpoint_impacts_bands as EndpointBands) || {};

  return (
    <div className="space-y-4">
      {/* Header / methodology summary */}
      <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
        <AlertCircle className="h-5 w-5 text-amber-700 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-amber-900">
          <strong>v1 scope</strong>: 3 of 18 ReCiPe 2016 midpoint categories with
          literature-anchored centrals and worst/best-case uncertainty envelopes.
          The other 15 categories are documented but not consumed —
          see <button type="button" className="underline" onClick={() => setShowMethodology(true)}>methodology</button>.
        </div>
      </div>

      {/* The 3 consumed midpoint categories with band visualisation */}
      <div className="space-y-3">
        {CONSUMED_CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const central = (lca[cat.key] ?? 0) as number;
          const band = bands[cat.key];
          const palette = {
            rose:    { card: 'border-rose-200 bg-rose-50/50',       text: 'text-rose-900',    accent: 'text-rose-700' },
            emerald: { card: 'border-emerald-200 bg-emerald-50/50', text: 'text-emerald-900', accent: 'text-emerald-700' },
            sky:     { card: 'border-sky-200 bg-sky-50/50',         text: 'text-sky-900',     accent: 'text-sky-700' },
            amber:   { card: 'border-amber-200 bg-amber-50/50',     text: 'text-amber-900',   accent: 'text-amber-700' },
          }[cat.color];
          return (
            <div key={cat.key} className={`border rounded-lg p-4 ${palette.card}`}>
              <div className="flex items-start gap-3 mb-3">
                <Icon className={`h-5 w-5 ${palette.accent} mt-0.5`} />
                <div className="flex-1">
                  <div className="flex items-baseline justify-between">
                    <h3 className={`font-semibold ${palette.text}`}>{cat.name}</h3>
                    <span className="text-xs text-gray-500">per 100 kcal of meal</span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{cat.description}</p>
                </div>
              </div>
              {band ? (
                <UncertaintyBandBar band={band} unit={cat.unit} color={cat.color} />
              ) : (
                <div className="text-sm text-gray-600">
                  Central: <span className="font-medium tabular-nums">{central.toExponential(2)} {cat.unit}</span>
                  <span className="ml-2 text-xs text-amber-700">(no band data)</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Endpoint section */}
      <div className="border rounded-lg bg-gray-50/50">
        <Button
          variant="ghost"
          onClick={() => setShowEndpoints((v) => !v)}
          className="w-full justify-between p-4 h-auto"
        >
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-900">Endpoint damages (DALY, species·yr)</span>
            <Badge variant="outline" className="text-xs">2 of 3</Badge>
          </div>
          {showEndpoints ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
        {showEndpoints && (
          <div className="border-t p-4 space-y-3">
            <EndpointRow
              name="Human Health"
              unit="DALY"
              central={endpoints['Human Health'] ?? 0}
              band={endpointBands['Human Health']}
            />
            <EndpointRow
              name="Ecosystems"
              unit="species·yr"
              central={endpoints['Ecosystems'] ?? 0}
              band={endpointBands['Ecosystems']}
            />
            {/* Resources — explicit "not estimable" instead of silent 0 */}
            <div className="text-sm text-gray-600 bg-white p-3 rounded border border-gray-200">
              <div className="flex items-baseline justify-between">
                <span className="font-medium">Resources</span>
                <span className="text-xs text-orange-700 font-medium">Not estimable in v1</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Both Fossil and Mineral resource scarcity midpoints are excluded from
                the v1 consumed vector (no per-food-group literature grounding).
                Returns when TODO-CODE-LCA-2 (licensed AGRIBALYSE-LCI re-scoring) lands.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Methodology accordion — the 15 non-consumed categories */}
      <div className="border rounded-lg bg-gray-50/50">
        <Button
          variant="ghost"
          onClick={() => setShowMethodology((v) => !v)}
          className="w-full justify-between p-4 h-auto"
        >
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-900">v1 methodology: 15 categories not assessed</span>
            <Badge variant="outline" className="text-xs">scope rationale</Badge>
          </div>
          {showMethodology ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
        {showMethodology && (
          <div className="border-t p-4 space-y-3 text-sm text-gray-700">
            <p>
              The full ReCiPe 2016 H midpoint set has 18 categories. The 15 not displayed
              above are not consumed in v1 because per-food-group numerical literature
              grounding is unavailable — shipping conservative-default point estimates
              for them would present false multidimensional rigor (manuscript §7.5).
              Group-level fallback values continue to exist in the database for legacy
              consumers but are not shown here.
            </p>
            <ul className="space-y-1 text-xs">
              {NON_CONSUMED_CATEGORIES.map((c) => (
                <li key={c.name} className="flex justify-between gap-3 border-b border-gray-100 pb-1">
                  <span className="font-medium text-gray-800">{c.name}</span>
                  <span className="text-gray-500 text-right">{c.why}</span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-gray-600 pt-2">
              <strong>v2 path:</strong> licensed AGRIBALYSE-LCI re-scored under ReCiPe
              characterisation factors closes the 12 truly-ungrounded categories;
              raw SimaPro outputs from Dekker et al. 2020 (per-food ReCiPe H midpoints)
              would close the 3 unit-incompatible ones. See `code_action_items.md`
              TODO-CODE-LCA-2 and TODO-CODE-LCA-3.
            </p>
          </div>
        )}
      </div>

      {/* Methodology summary footer */}
      <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
        <h4 className="font-semibold text-indigo-900 mb-2 text-sm">Methodology</h4>
        <div className="text-xs text-indigo-800 space-y-1">
          <p><strong>Method:</strong> ReCiPe 2016 v1.1 Hierarchist (RIVM 2017, Huijbregts et al. 2017)</p>
          <p><strong>Functional unit:</strong> per 100 kcal of meal</p>
          <p><strong>Centrals:</strong> Poore &amp; Nemecek 2018 Fig. 1 (GW + Land); Mekonnen &amp; Hoekstra 2011/2012 blue-water-only (Water)</p>
          <p><strong>Bands:</strong> worst/best-case envelope from P&amp;N 10th-percentile/mean ratios + M&amp;H spatial spread — NOT a 90 % CI</p>
          <p><strong>Regionalisation:</strong> Canadian regional multipliers applied to group-default fallback foods only (not to Agribalyse-matched values)</p>
        </div>
      </div>
    </div>
  );
};

// Small helper for endpoint rows.
const EndpointRow: React.FC<{
  name: string;
  unit: string;
  central: number;
  band?: { low: number; central: number; high: number };
}> = ({ name, unit, central, band }) => (
  <div className="bg-white p-3 rounded border border-gray-200">
    <div className="flex items-baseline justify-between mb-2">
      <span className="font-medium text-gray-900">{name}</span>
      <span className="text-sm font-medium tabular-nums">
        {central.toExponential(2)} {unit}
      </span>
    </div>
    {band && <UncertaintyBandBar band={band} unit={unit} color="amber" showScale />}
  </div>
);

export default LCABreakdown;
