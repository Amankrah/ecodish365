/**
 * PackagedFoodCompositionForm — editable composition table for the
 * LLM-decomposed packaged-food ingredient list (PKG-IMG-1 Phase 2).
 *
 * Renders the DecompositionResult.ingredients as rows the user can edit
 * (mass_g) or remove. Surfaces mass-conservation residual + macro
 * reconciliation prominently — the user needs to see HOW WELL the
 * inferred composition matches the NF panel before scoring with it.
 *
 * Buttons route to the five scorers (HEFI / HENI / FCS / dietary-pattern
 * / environmental) via the existing useRecall24hReceiver sessionStorage
 * handoff. Each route stamps `packaged_food.provenance =
 * 'packaged_food_inferred'` so the receiving page can forward the
 * caveat-swap flag to the backend.
 */
'use client';

import { useMemo, useState } from 'react';
import { Loader2, Trash2, AlertTriangle, ChevronRight } from 'lucide-react';
import type {
  DecomposedIngredient,
  DecompositionResult,
  NFPanelExtraction,
} from '@/lib/api';
// FOOD-LIST-PANEL (2026-05-26): persist into the cross-page active food
// list so the user can transfer this same packaged-food composition to
// other scorers without re-decomposing.
import { fromRecallAggregated, saveActiveFoodList } from '@/lib/activeFoodList';

type UserType = 'individual' | 'researcher' | 'policy';

interface Props {
  decomposition: DecompositionResult;
  panel: NFPanelExtraction;
  userType: UserType;
}

// Scoring routes. Names match Recall24hWizard's SCORE_BUTTONS for consistency.
// SCORECARD-1 (2026-05-26) tops the list with the consumer-friendly multi-metric view.
const SCORE_ROUTES: Array<{
  id: 'hefi' | 'heni' | 'fcs' | 'environmental' | 'dietary_pattern' | 'scorecard' | 'planetary';
  emoji: string;
  label: string;
  path: string;
  note: string;
}> = [
  { id: 'scorecard', emoji: '✨', label: 'Scorecard',
    path: '/scorecard',
    note: 'All six metrics at a glance, framed for a lay reader' },
  { id: 'dietary_pattern', emoji: '🎯', label: 'Dietary pattern',
    path: '/dietary-pattern',
    note: 'Which canonical pattern does this product resemble?' },
  { id: 'hefi', emoji: '🥗', label: 'HEFI-2019',
    path: '/hefi/calculate',
    note: 'Healthy Eating Food Index (Brassard 2022)' },
  { id: 'heni', emoji: '🧬', label: 'HENI',
    path: '/heni/calculate',
    note: 'Health Nutritional Index — minutes of healthy life' },
  { id: 'fcs', emoji: '🧭', label: 'FCS',
    path: '/fcs/calculate',
    note: 'Food Compass Score — Mozaffarian 2021' },
  { id: 'environmental', emoji: '🌍', label: 'Environmental',
    path: '/environmental/calculate',
    note: 'Per-100g environmental footprint (ReCiPe + AGRIBALYSE)' },
  { id: 'planetary', emoji: '🪐', label: 'Planetary boundaries',
    path: '/planetary',
    note: 'EAT-Lancet 2.0 Table 2 — % of one person\'s daily food-system budget' },
];

function confidenceColor(c: number): string {
  if (c >= 0.75) return 'bg-emerald-100 text-emerald-900 border-emerald-300';
  if (c >= 0.5)  return 'bg-amber-100 text-amber-900 border-amber-300';
  return 'bg-red-100 text-red-900 border-red-300';
}

export function PackagedFoodCompositionForm({
  decomposition, panel, userType,
}: Props): JSX.Element {
  const [rows, setRows] = useState<DecomposedIngredient[]>(
    () => decomposition.ingredients.map(i => ({ ...i })),
  );
  const [routing, setRouting] = useState<string | null>(null);

  const totalMass = useMemo(
    () => rows.reduce((s, r) => s + (r.mass_g || 0), 0),
    [rows],
  );
  const residual = totalMass - decomposition.net_weight_g_assumed;
  const residualPct = decomposition.net_weight_g_assumed > 0
    ? Math.abs(residual) / decomposition.net_weight_g_assumed * 100
    : 0;
  const conservationOk = residualPct <= 5;

  function setMass(idx: number, value: string): void {
    const n = parseFloat(value);
    setRows(r => {
      const next = [...r];
      next[idx] = { ...next[idx], mass_g: Number.isFinite(n) && n >= 0 ? n : 0 };
      return next;
    });
  }

  function removeRow(idx: number): void {
    setRows(r => r.filter((_, i) => i !== idx));
  }

  function routeTo(route: typeof SCORE_ROUTES[number]): void {
    setRouting(route.id);
    // Build the payload once; reuse for both the sessionStorage handoff
    // (consumed by the destination's useRecall24hReceiver) and the cross-page
    // active food list (consumed by FoodListPanel everywhere else).
    const payload = {
      source: 'recall_24h' as const,
      user_type: userType,
      captured_at: new Date().toISOString(),
      target: route.id,
      meals_meta: [{
        occasion: 'packaged_food',
        dish_name: panel.product_name_visible.value || 'Packaged food',
        total_mass_g: totalMass,
      }],
      aggregated_daily_ingredients: rows.map(r => ({
        food_id: r.food_id,
        food_description: r.food_description,
        food_group: r.food_group || '',
        mass_g: r.mass_g,
        occasions: { packaged_food: r.mass_g },
      })),
      // Heuristic energy_per_serving estimate; not load-bearing for scoring,
      // just informational. The actual per-meal kcal is computed downstream
      // via CNF lookups on each FoodID.
      estimated_daily_kcal: 0,
      packaged_food: {
        provenance: 'packaged_food_inferred' as const,
        product_name: panel.product_name_visible.value || null,
        brand: panel.brand_visible.value || null,
        net_weight_g: decomposition.net_weight_g_assumed,
        decomposition_confidence: decomposition.decomposition_confidence,
        image_sha256: panel.extraction_metadata.image_sha256 || '',
      },
    };
    try {
      sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
    } catch {
      // sessionStorage may fail in private mode — target page renders empty
    }
    try {
      saveActiveFoodList(fromRecallAggregated(payload.aggregated_daily_ingredients, {
        user_type: userType,
        estimated_daily_kcal: payload.estimated_daily_kcal,
        meals_meta: payload.meals_meta,
        packaged_food: payload.packaged_food,
      }));
    } catch { /* localStorage unavailable — non-fatal */ }
    window.location.href = route.path + '?from=recall24h';
  }

  // Decomposition confidence pill colour
  const confBand = decomposition.decomposition_confidence >= 0.7 ? 'high'
                  : decomposition.decomposition_confidence >= 0.5 ? 'moderate'
                  : 'low';

  return (
    <div className="space-y-4">
      {/* Honest framing banner — this is the MOST IMPORTANT thing on the screen */}
      <div className="bg-amber-50 border border-amber-300 rounded-md p-3 flex items-start gap-2">
        <AlertTriangle className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div className="flex-1 text-sm text-amber-900">
          <p className="font-semibold">This composition is INFERRED, not measured.</p>
          <p className="mt-1">
            Regulation only requires ingredients to be listed in descending mass order — actual
            percentages are rarely on the label. The AI estimated each mass by combining the
            ingredient order with the Nutrition Facts panel macros. Treat the result as
            DIRECTIONAL only, and feel free to correct any obviously wrong masses below
            before scoring.
          </p>
        </div>
      </div>

      {/* Decomposition health: confidence, mass conservation, macro reconciliation */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="border rounded-md p-3 bg-white">
          <p className="text-xs text-gray-600 uppercase tracking-wide">Decomposition confidence</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {(decomposition.decomposition_confidence * 100).toFixed(0)}%
          </p>
          <p className={`text-xs mt-0.5 px-1.5 py-0.5 inline-block rounded ${
            confBand === 'high' ? 'bg-emerald-100 text-emerald-800'
            : confBand === 'moderate' ? 'bg-amber-100 text-amber-800'
            : 'bg-red-100 text-red-800'
          }`}>{confBand}</p>
        </div>
        <div className="border rounded-md p-3 bg-white">
          <p className="text-xs text-gray-600 uppercase tracking-wide">Mass conservation</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {totalMass.toFixed(0)} / {decomposition.net_weight_g_assumed.toFixed(0)} g
          </p>
          <p className={`text-xs mt-0.5 px-1.5 py-0.5 inline-block rounded ${
            conservationOk ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
          }`}>
            {residual >= 0 ? '+' : ''}{residual.toFixed(0)} g ({residualPct.toFixed(1)}%)
          </p>
        </div>
        <div className="border rounded-md p-3 bg-white">
          <p className="text-xs text-gray-600 uppercase tracking-wide">Ingredients</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{rows.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            CNF-mapped from {decomposition.ingredients.length} label items
          </p>
        </div>
      </div>

      {/* Decomposition warnings if any */}
      {decomposition.decomposition_warnings.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm">
          <p className="font-semibold text-red-900">Decomposition warnings</p>
          <ul className="mt-1 list-disc list-inside text-red-800 space-y-0.5">
            {decomposition.decomposition_warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* Editable composition table */}
      <div className="border rounded-md bg-white overflow-hidden">
        <div className="px-3 py-2 bg-gray-50 border-b text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Inferred composition — edit any mass you think is wrong
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600">
            <tr>
              <th className="px-2 py-1.5 text-left w-8">#</th>
              <th className="px-2 py-1.5 text-left">Label ingredient → CNF food</th>
              <th className="px-2 py-1.5 text-right w-24">Mass (g)</th>
              <th className="px-2 py-1.5 text-right w-20">% total</th>
              <th className="px-2 py-1.5 text-center w-16">Conf.</th>
              <th className="px-2 py-1.5 text-right w-12"><span className="sr-only">Remove</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={idx} className="border-t hover:bg-gray-50">
                <td className="px-2 py-1.5 text-gray-500">{r.position}</td>
                <td className="px-2 py-1.5">
                  <p className="text-gray-900">{r.label_name}</p>
                  <p className="text-xs text-gray-500">
                    → {r.food_description}
                    {' '}<span className="text-[10px] text-gray-400">[food_id {r.food_id}]</span>
                  </p>
                  {userType === 'researcher' && (
                    <span className="inline-block mt-0.5 text-[10px] text-gray-500">
                      mass source: <code>{r.mass_source}</code>
                    </span>
                  )}
                </td>
                <td className="px-2 py-1.5 text-right">
                  <input
                    type="number" step="1" min="0"
                    value={r.mass_g}
                    onChange={e => setMass(idx, e.target.value)}
                    aria-label={`Mass in grams for ${r.label_name}`}
                    title={`Mass in grams for ${r.label_name}`}
                    className="w-20 border border-gray-300 rounded px-1.5 py-0.5 text-sm text-right"
                  />
                </td>
                <td className="px-2 py-1.5 text-right text-xs text-gray-600">
                  {totalMass > 0 ? ((r.mass_g / totalMass) * 100).toFixed(1) : '0'}%
                </td>
                <td className="px-2 py-1.5 text-center">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${confidenceColor(r.confidence)}`}>
                    {(r.confidence * 100).toFixed(0)}
                  </span>
                </td>
                <td className="px-2 py-1.5 text-right">
                  <button
                    type="button"
                    onClick={() => removeRow(idx)}
                    aria-label={`Remove ${r.label_name}`}
                    className="text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-500 text-sm">
                All ingredients removed.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Macro reconciliation (researcher mode only — too dense for individual) */}
      {userType !== 'individual' && Object.keys(decomposition.macro_reconciliation).length > 0 && (
        <details className="border rounded-md bg-white text-xs">
          <summary className="cursor-pointer px-3 py-2 bg-gray-50 font-semibold text-gray-700 uppercase tracking-wide">
            Macro reconciliation (panel vs decomposition)
          </summary>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-600">
              <tr>
                <th className="px-2 py-1.5 text-left">Macro</th>
                <th className="px-2 py-1.5 text-right">Panel /100g</th>
                <th className="px-2 py-1.5 text-right">Inferred /100g</th>
                <th className="px-2 py-1.5 text-right">Δ</th>
                <th className="px-2 py-1.5 text-right">Within ±10%</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(decomposition.macro_reconciliation).map(([k, v]) => (
                <tr key={k} className="border-t">
                  <td className="px-2 py-1.5 text-gray-700">{k}</td>
                  <td className="px-2 py-1.5 text-right">{v.panel_per_100g}</td>
                  <td className="px-2 py-1.5 text-right">{v.inferred_per_100g}</td>
                  <td className={`px-2 py-1.5 text-right ${v.within_tolerance ? 'text-gray-700' : 'text-red-700'}`}>
                    {v.diff >= 0 ? '+' : ''}{v.diff} ({v.rel_diff_pct.toFixed(0)}%)
                  </td>
                  <td className="px-2 py-1.5 text-right">{v.within_tolerance ? '✓' : '✗'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}

      {/* Route-to-scorer buttons */}
      <div className="border-t pt-3">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Score this composition with…</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {SCORE_ROUTES.map(route => (
            <button
              key={route.id}
              type="button"
              onClick={() => routeTo(route)}
              disabled={routing !== null || rows.length === 0}
              className="flex items-start gap-2 p-3 border border-gray-300 rounded-md hover:bg-blue-50 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed text-left"
            >
              <span className="text-xl flex-shrink-0" aria-hidden="true">{route.emoji}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {route.label}
                  {routing === route.id && (
                    <Loader2 className="inline-block ml-1.5 h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  )}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">{route.note}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Each scorer opens in its own page. The receiving page will show an
          &ldquo;inferred composition&rdquo; caveat so you (and any researcher
          reading your results later) know the source isn&apos;t a measured intake.
        </p>
      </div>
    </div>
  );
}
