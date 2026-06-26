/**
 * CohortVsNationalPanel (PLATFORM-CODE-1.m m.D, 2026-06-26).
 *
 * Renders an opt-in card on the cohort results page that compares the
 * uploaded cohort's per-food-subgroup intake distribution to the
 * published Health Canada CCHS-FCT 2015 national distribution.
 *
 * The user picks a (sex × age_band) stratum + a basis (all-person vs
 * eaters-only) + a denominator (per-person vs per-kg-bw); we POST the
 * cohort recalls to `/api/research/population-reference/canada/2015/compare-cohort/`
 * and render the per-subgroup delta table.
 *
 * Suppression-aware: cells flagged `F` by Health Canada render `—` with
 * a tooltip explaining the rule (CV > 33.3% or n_eaters < 30). Cells
 * flagged `E` render the number with an amber caution badge (CV
 * 16.6–33.3%).
 *
 * Gating: the panel only fetches when the user clicks "Compare to
 * Canadian reference". Lazy by design — we don't want a 200-row table
 * appearing automatically on every cohort run.
 */
'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  PopulationReferenceApiService,
  type CohortRecallInput,
  type CohortVsNationalResponse,
  type CohortVsNationalRow,
  type FctStratum,
} from '@/lib/api';

interface Props {
  cohortRecalls: CohortRecallInput[];
  /** Optional initial stratum; defaults to female / 31-50 Years. */
  defaultSex?: string;
  defaultAgeBand?: string;
}

// Strata we surface in the picker — the published single-stratum cells,
// not the rolled-up 1-18 / 19+ / All ages bands (those exist but are
// less interesting for cohort comparison).
const SEX_CHOICES: Array<{ value: string; label: string }> = [
  { value: 'both',   label: 'Both' },
  { value: 'male',   label: 'Male' },
  { value: 'female', label: 'Female' },
];

const AGE_BAND_CHOICES: string[] = [
  'All ages', '1-3 Years', '4-8 Years', '9-13 Years', '14-18 Years',
  '19-30 Years', '31-50 Years', '51-70 Years', '71+ Years',
  '1-18 Years', '19+ Years',
];

const BASIS_CHOICES: Array<{ value: 'eaters_only' | 'all_person'; label: string; help: string }> = [
  { value: 'eaters_only', label: 'Eaters only',
    help: 'Distribution computed across cohort members who ate this subgroup at all.' },
  { value: 'all_person',  label: 'All respondents',
    help: 'Distribution across every cohort member (zeros included for non-eaters).' },
];

function fmt(v: number | null | undefined, nd = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return Number(v).toFixed(nd);
}

function deltaCell(delta: number | null, flag: string | null): React.ReactNode {
  if (flag === 'F') {
    return (
      <span title="National cell suppressed (CV > 33.3% or n_eaters < 30); delta not computable." className="text-slate-400">—</span>
    );
  }
  if (delta === null || delta === undefined) {
    return <span className="text-slate-400">—</span>;
  }
  const sign = delta > 0 ? '+' : '';
  const tone = delta > 0 ? 'text-teal-700' : delta < 0 ? 'text-rose-700' : 'text-slate-700';
  return <span className={`tabular-nums font-medium ${tone}`}>{sign}{delta.toFixed(1)}</span>;
}

function suppressionBadge(flag: string | null) {
  if (flag === 'F') {
    return <Badge variant="secondary" title="Health Canada suppressed this cell (CV > 33.3% or n_eaters < 30).">F</Badge>;
  }
  if (flag === 'E') {
    return <Badge variant="secondary" title="Interpret with caution: CV 16.6–33.3%." className="bg-amber-100 text-amber-800">E</Badge>;
  }
  return null;
}

export default function CohortVsNationalPanel({
  cohortRecalls,
  defaultSex = 'female',
  defaultAgeBand = '31-50 Years',
}: Props) {
  const [sex, setSex] = useState(defaultSex);
  const [ageBand, setAgeBand] = useState(defaultAgeBand);
  const [basis, setBasis] = useState<'eaters_only' | 'all_person'>('eaters_only');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<CohortVsNationalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hideNeutral, setHideNeutral] = useState(false);
  const [showTop, setShowTop] = useState(25);

  // Reset previous results when the cohort underneath changes (new run).
  useEffect(() => { setResult(null); setError(null); }, [cohortRecalls]);

  const run = useCallback(async () => {
    if (!cohortRecalls.length) return;
    setRunning(true);
    setError(null);
    try {
      const out = await PopulationReferenceApiService.compareCohort(
        cohortRecalls,
        { sex, age_band: ageBand },
        { basis },
      );
      setResult(out);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [cohortRecalls, sex, ageBand, basis]);

  const rows = useMemo(() => {
    if (!result) return [] as CohortVsNationalRow[];
    if (!hideNeutral) return result.per_subgroup;
    return result.per_subgroup.filter(r =>
      r.delta_median !== null && Math.abs(r.delta_median) >= 1,
    );
  }, [result, hideNeutral]);

  const visible = rows.slice(0, showTop);

  return (
    <Card className="mt-6">
      <CardHeader className="pb-3 flex flex-row items-start justify-between gap-3 flex-wrap">
        <CardTitle className="text-base">
          Compare to Canadian national reference (CCHS-FCT 2015)
          <div className="text-xs font-normal text-slate-500 mt-1">
            Survey-weighted, age × sex-stratified intake distributions from Health Canada.
            Each food in the cohort is mapped to one of ~180 Health Canada
            <span title="Bureau of Nutritional Sciences — Health Canada's food-grouping system used by the CCHS Nutrition 2015 Food Consumption Table. ~180 subgroups across 10 main food groups (Grain products, Dairy, Fats, Meats, etc.)." className="border-b border-dotted border-slate-400 cursor-help mx-1">
              BNS food subgroups
            </span>
            via an LLM bridge; see provenance for bridge confidence.
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 items-end">
          <div>
            <label htmlFor="ref-sex" className="block text-xs text-slate-600 mb-1">Sex</label>
            <select id="ref-sex" aria-label="Sex stratum"
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    value={sex} onChange={(e) => setSex(e.target.value)}>
              {SEX_CHOICES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="ref-age" className="block text-xs text-slate-600 mb-1">Age band</label>
            <select id="ref-age" aria-label="Age band stratum"
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    value={ageBand} onChange={(e) => setAgeBand(e.target.value)}>
              {AGE_BAND_CHOICES.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="ref-basis" className="block text-xs text-slate-600 mb-1">Basis</label>
            <select id="ref-basis" aria-label="Distribution basis"
                    className="w-full border rounded px-2 py-1.5 text-sm"
                    value={basis} onChange={(e) => setBasis(e.target.value as 'eaters_only' | 'all_person')}>
              {BASIS_CHOICES.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
            </select>
            <div className="text-xs text-slate-500 mt-1">
              {BASIS_CHOICES.find(b => b.value === basis)?.help}
            </div>
          </div>
          <div>
            <Button onClick={run} disabled={running || !cohortRecalls.length}>
              {running ? 'Comparing…' : 'Compare to Canadian reference'}
            </Button>
          </div>
        </div>

        {error && (
          <Alert className="mb-4 border-red-200 bg-red-50 text-red-800">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
              <div className="border rounded p-2 bg-white">
                <div className="text-xs text-slate-500">Cohort size</div>
                <div className="font-semibold tabular-nums">{result.meta.n_recalls.toLocaleString()} recalls</div>
              </div>
              <div className="border rounded p-2 bg-white">
                <div className="text-xs text-slate-500">Subgroups detected</div>
                <div className="font-semibold tabular-nums">{result.per_subgroup.length}</div>
              </div>
              <div className="border rounded p-2 bg-white">
                <div className="text-xs text-slate-500">Mean bridge coverage</div>
                <div className="font-semibold tabular-nums">{fmt(result.coverage.mean_pct_bridged)}%</div>
              </div>
              <div className="border rounded p-2 bg-white">
                <div className="text-xs text-slate-500">Recalls with unbridged mass</div>
                <div className="font-semibold tabular-nums">{result.coverage.n_recalls_with_unbridged_mass}</div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 mb-3 text-sm">
              <label className="inline-flex items-center gap-2 text-slate-700">
                <input type="checkbox" checked={hideNeutral} onChange={(e) => setHideNeutral(e.target.checked)} />
                Hide subgroups with |Δ median| &lt; 1 g
              </label>
              <label className="inline-flex items-center gap-2 text-slate-700">
                Show top
                <select aria-label="Number of rows to show"
                        className="border rounded px-1 py-0.5 text-sm"
                        value={showTop} onChange={(e) => setShowTop(Number(e.target.value))}>
                  {[10, 25, 50, 100, 250].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
                of {rows.length}
              </label>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-700">
                  <tr>
                    <th className="px-3 py-2 text-left" title="Health Canada BNS (Bureau of Nutritional Sciences) food subgroup code — the bucket used by the CCHS-FCT 2015 published intake distributions.">Subgroup code</th>
                    <th className="px-3 py-2 text-left">Subgroup</th>
                    <th className="px-3 py-2 text-left">Group</th>
                    <th className="px-3 py-2 text-right">Cohort med</th>
                    <th className="px-3 py-2 text-right">National med</th>
                    <th className="px-3 py-2 text-right">Δ median (g)</th>
                    <th className="px-3 py-2 text-right">Cohort P90</th>
                    <th className="px-3 py-2 text-right">National P90</th>
                    <th className="px-3 py-2 text-right">Δ P90 (g)</th>
                    <th className="px-3 py-2 text-center" title="Bridge confidence + Health Canada suppression flag">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map(r => (
                    <tr key={r.bns_code} className="border-t border-slate-100 hover:bg-slate-50">
                      <td className="px-3 py-1.5 font-mono text-xs">{r.bns_code}</td>
                      <td className="px-3 py-1.5">{r.subgroup_name ?? '—'}</td>
                      <td className="px-3 py-1.5 text-xs text-slate-500">{r.main_group ?? '—'}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">{fmt(r.cohort_median)}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">
                        {r.national_suppression_flag === 'F' ? <span className="text-slate-400">—</span> : fmt(r.national_median)}
                      </td>
                      <td className="px-3 py-1.5 text-right">{deltaCell(r.delta_median, r.national_suppression_flag)}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">{fmt(r.cohort_p90)}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">
                        {r.national_suppression_flag === 'F' ? <span className="text-slate-400">—</span> : fmt(r.national_p90)}
                      </td>
                      <td className="px-3 py-1.5 text-right">{deltaCell(r.delta_p90, r.national_suppression_flag)}</td>
                      <td className="px-3 py-1.5 text-center whitespace-nowrap">
                        {r.mean_bridge_confidence !== null && (
                          <span className="text-xs text-slate-500 mr-1" title="Mean bridge confidence — how confident the LLM was when mapping the cohort's foods to this Health Canada subgroup. 1.0 = manual override; 0.9 = unambiguous LLM match; below 0.5 was left unbridged.">
                            {r.mean_bridge_confidence.toFixed(2)}
                          </span>
                        )}
                        {suppressionBadge(r.national_suppression_flag)}
                      </td>
                    </tr>
                  ))}
                  {visible.length === 0 && (
                    <tr><td colSpan={10} className="px-3 py-6 text-center text-slate-500 italic">
                      No subgroups to show (cohort may be empty or filter is hiding everything).
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <details className="mt-4 text-xs text-slate-600">
              <summary className="cursor-pointer">Provenance + bridge stats</summary>
              <div className="mt-2 space-y-1">
                <div><strong>Source:</strong> {result.provenance.source}</div>
                <div><strong>Base data:</strong> {result.provenance.base_data}</div>
                <div><strong>Weighting:</strong> {result.provenance.weighting}</div>
                <div><strong>National n:</strong> {result.provenance.n_respondents_total.toLocaleString()} respondents</div>
                <div><strong>Bridge:</strong> {result.provenance.bridge.ranking_model} via {result.provenance.bridge.embedding_model};
                  built {result.provenance.bridge.built_date};
                  {result.provenance.bridge.n_bridged} bridged, {result.provenance.bridge.n_unbridged} unbridged,
                  {result.provenance.bridge.n_manual_overrides} manual overrides;
                  mean confidence {result.provenance.bridge.mean_confidence}</div>
                {result.body_weight_national && (
                  <div><strong>National body weight (stratum):</strong> mean {result.body_weight_national.mean_bw} kg
                    (95% CI {result.body_weight_national.mean_lb}–{result.body_weight_national.mean_ub}),
                    n={result.body_weight_national.n_respondents}</div>
                )}
              </div>
            </details>
          </>
        )}

        {!result && !error && (
          <div className="text-sm text-slate-500 italic">
            Pick a stratum and click <strong>Compare to Canadian reference</strong>. Compares the
            cohort&apos;s per-food-subgroup intake distribution against the Health Canada CCHS
            Nutrition 2015 published cell for that (sex × age band) stratum.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
