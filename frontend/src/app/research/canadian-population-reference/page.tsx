/**
 * Canadian population-reference browse page (PLATFORM-CODE-1.m m.D, 2026-06-26).
 *
 * Three-pane layout:
 *   - LEFT: subgroup tree, grouped by Health Canada main food group.
 *   - TOP STRIP: (sex × age band) stratum selector + basis/denom toggles.
 *   - CENTER: populated cell — mean / P50 / P90 / P95 with SE bars,
 *     n_respondents, % eaters, body-weight reference, suppression flag,
 *     and the bridge-resolved CNF candidate list (clickable through to
 *     `/cnf/food/<id>`).
 *
 * Lets a researcher drill into any (subgroup × stratum) cell without
 * going through a cohort upload — useful for sanity-checking targets
 * before designing a study, or for pulling published Canadian intake
 * numbers into a manuscript directly.
 */
'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  PopulationReferenceApiService,
  type PopulationReferenceIndex,
  type PopulationReferenceIntakeResponse,
  type FctSubgroup,
} from '@/lib/api';

const SEX_CHOICES = [
  { value: 'both',   label: 'Both' },
  { value: 'male',   label: 'Male' },
  { value: 'female', label: 'Female' },
];

const AGE_BAND_CHOICES = [
  'All ages', '1-3 Years', '4-8 Years', '9-13 Years', '14-18 Years',
  '19-30 Years', '31-50 Years', '51-70 Years', '71+ Years',
  '1-18 Years', '19+ Years',
];

function fmt(v: number | null | undefined, nd = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return Number(v).toFixed(nd);
}

function flagBadge(flag: string | null) {
  if (flag === 'F') return <Badge variant="secondary" title="Suppressed (CV > 33.3% or n_eaters < 30).">Suppressed (F)</Badge>;
  if (flag === 'E') return <Badge variant="secondary" className="bg-amber-100 text-amber-800" title="Interpret with caution: CV 16.6–33.3%.">Caution (E)</Badge>;
  return <Badge variant="secondary" className="bg-emerald-100 text-emerald-800">Published</Badge>;
}

function groupSubgroups(subgroups: FctSubgroup[]): Record<string, FctSubgroup[]> {
  const out: Record<string, FctSubgroup[]> = {};
  for (const s of subgroups) {
    const g = s.main_group || 'Other';
    if (!out[g]) out[g] = [];
    out[g].push(s);
  }
  for (const g in out) {
    out[g].sort((a, b) => a.code.localeCompare(b.code, undefined, { numeric: true }));
  }
  return out;
}

export default function CanadianPopulationReferencePage() {
  const [index, setIndex] = useState<PopulationReferenceIndex | null>(null);
  const [loadingIndex, setLoadingIndex] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filter, setFilter] = useState('');
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [sex, setSex] = useState('female');
  const [ageBand, setAgeBand] = useState('31-50 Years');
  const [basis, setBasis] = useState<'eaters_only' | 'all_person'>('eaters_only');
  const [denom, setDenom] = useState<'per_person' | 'per_kg_bw'>('per_person');

  const [cell, setCell] = useState<PopulationReferenceIntakeResponse | null>(null);
  const [loadingCell, setLoadingCell] = useState(false);

  useEffect(() => {
    setLoadingIndex(true);
    PopulationReferenceApiService.listIndex()
      .then(setIndex)
      .catch(e => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoadingIndex(false));
  }, []);

  const grouped = useMemo(() => index ? groupSubgroups(index.subgroups) : {}, [index]);

  const filtered = useMemo(() => {
    if (!filter.trim()) return grouped;
    const needle = filter.trim().toLowerCase();
    const out: Record<string, FctSubgroup[]> = {};
    for (const [group, subs] of Object.entries(grouped)) {
      const kept = subs.filter(s =>
        s.code.toLowerCase().includes(needle)
        || s.name.toLowerCase().includes(needle),
      );
      if (kept.length) out[group] = kept;
    }
    return out;
  }, [grouped, filter]);

  const fetchCell = useCallback((code: string) => {
    setLoadingCell(true);
    setCell(null);
    PopulationReferenceApiService.intakeForStratum({
      subgroup: code, sex, age_band: ageBand, basis, denom,
    })
      .then(setCell)
      .catch(e => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoadingCell(false));
  }, [sex, ageBand, basis, denom]);

  useEffect(() => {
    if (selectedCode) fetchCell(selectedCode);
  }, [selectedCode, fetchCell]);

  const onPickSubgroup = useCallback((code: string) => setSelectedCode(code), []);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900">Canadian population reference</h1>
          <p className="text-slate-600 mt-1 max-w-3xl">
            Drill into the Health Canada{' '}
            <em>Food Consumption Table 2015</em> (CCHS Nutrition 2015,
            n = 19,670). Pick any food subgroup &times; sex &times; age band cell to
            see the published Canadian intake distribution — mean, median,
            P90, P95 with bootstrap standard errors — plus the list of foods
            from our catalogue that map into it.
          </p>
          <p className="text-xs text-slate-500 mt-2 max-w-3xl">
            Food subgroups follow Health Canada&apos;s{' '}
            <span
              title="Bureau of Nutritional Sciences — the Health Canada classification that the CCHS Nutrition 2015 Food Consumption Table uses. ~180 subgroups across 10 main food groups (Grain products, Dairy, Fats, Meats, Meat alternatives, Vegetables, Fruits, Beverages, Babyfood, Miscellaneous). Codes like 1A, 2A, 10D identify a specific subgroup; codes like '1 to 8' are published OVERALL roll-ups."
              className="border-b border-dotted border-slate-400 cursor-help"
            >
              Bureau of Nutritional Sciences (BNS) coding system
            </span>
            . Cells flagged <strong>F</strong> are suppressed by Health Canada for low cell counts;
            cells flagged <strong>E</strong> have a coefficient of variation 16.6–33.3% (interpret with caution).
            {' '}
            <Link href="/research/cohort" className="text-teal-700 hover:underline">
              Score your own cohort against this reference →
            </Link>
          </p>
        </div>

        {error && (
          <Alert className="mb-4 border-red-200 bg-red-50 text-red-800">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Stratum + basis selectors — full-width strip */}
        <Card className="mb-4">
          <CardContent className="py-3 grid grid-cols-2 md:grid-cols-4 gap-3 items-end">
            <div>
              <label htmlFor="popref-sex" className="block text-xs text-slate-600 mb-1">Sex</label>
              <select id="popref-sex" aria-label="Sex stratum"
                      className="w-full border rounded px-2 py-1.5 text-sm"
                      value={sex} onChange={(e) => setSex(e.target.value)}>
                {SEX_CHOICES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="popref-age" className="block text-xs text-slate-600 mb-1">Age band</label>
              <select id="popref-age" aria-label="Age band"
                      className="w-full border rounded px-2 py-1.5 text-sm"
                      value={ageBand} onChange={(e) => setAgeBand(e.target.value)}>
                {AGE_BAND_CHOICES.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="popref-basis" className="block text-xs text-slate-600 mb-1">Basis</label>
              <select id="popref-basis" aria-label="Distribution basis"
                      className="w-full border rounded px-2 py-1.5 text-sm"
                      value={basis} onChange={(e) => setBasis(e.target.value as 'eaters_only' | 'all_person')}>
                <option value="eaters_only">Eaters only</option>
                <option value="all_person">All respondents</option>
              </select>
            </div>
            <div>
              <label htmlFor="popref-denom" className="block text-xs text-slate-600 mb-1">Denominator</label>
              <select id="popref-denom" aria-label="Denominator"
                      className="w-full border rounded px-2 py-1.5 text-sm"
                      value={denom} onChange={(e) => setDenom(e.target.value as 'per_person' | 'per_kg_bw')}>
                <option value="per_person">g / person / day</option>
                <option value="per_kg_bw">g / kg body weight / day</option>
              </select>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* LEFT: subgroup tree */}
          <Card className="md:col-span-1 h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Food subgroups</CardTitle>
              <Input
                placeholder="Filter by code or name…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="mt-2 h-8 text-sm"
              />
            </CardHeader>
            <CardContent className="text-sm max-h-[600px] overflow-y-auto">
              {loadingIndex && <div className="text-slate-500 italic">Loading index…</div>}
              {!loadingIndex && Object.entries(filtered).map(([group, subs]) => (
                <div key={group} className="mb-3">
                  <div className="font-semibold text-slate-700 mb-1">{group}</div>
                  <ul className="space-y-0.5">
                    {subs.map(s => (
                      <li key={s.code}>
                        <button
                          type="button"
                          onClick={() => onPickSubgroup(s.code)}
                          className={`text-left w-full px-2 py-1 rounded text-xs transition-colors ${
                            selectedCode === s.code
                              ? 'bg-teal-100 text-teal-900 font-medium'
                              : 'text-slate-600 hover:bg-slate-100'
                          }`}
                        >
                          <span className="font-mono mr-2">{s.code}</span>
                          {s.name}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              {!loadingIndex && Object.keys(filtered).length === 0 && (
                <div className="text-slate-500 italic">No subgroups match the filter.</div>
              )}
            </CardContent>
          </Card>

          {/* RIGHT: selected cell */}
          <div className="md:col-span-2">
            {!selectedCode && (
              <Card>
                <CardContent className="py-8 text-center text-slate-500 italic">
                  Pick a food subgroup from the left to see its published Canadian
                  intake distribution for the selected stratum.
                </CardContent>
              </Card>
            )}

            {selectedCode && loadingCell && (
              <Card><CardContent className="py-6 text-slate-500 italic">Loading cell…</CardContent></Card>
            )}

            {selectedCode && cell && !loadingCell && (
              <>
                <Card className="mb-4">
                  <CardHeader className="pb-3 flex flex-row items-start justify-between gap-3 flex-wrap">
                    <CardTitle className="text-base">
                      <span className="font-mono mr-2">{cell.cell.subgroup_code}</span>
                      {cell.cell.subgroup_name}
                      <div className="text-xs font-normal text-slate-500 mt-1">
                        {cell.cell.main_group} · {cell.cell.sex} · {cell.cell.age_band} · {cell.cell.basis.replace('_', ' ')} / {cell.cell.denom.replace('_', ' ')}
                      </div>
                    </CardTitle>
                    {flagBadge(cell.cell.suppression_flag)}
                  </CardHeader>
                  <CardContent>
                    {cell.subgroup_meta?.description && (
                      <div className="text-sm text-slate-600 mb-3 italic">
                        {cell.subgroup_meta.description}
                      </div>
                    )}
                    {cell.subgroup_meta?.notes && (
                      <div className="text-xs text-slate-500 mb-3">Note: {cell.subgroup_meta.notes}</div>
                    )}
                    {cell.not_published && (
                      <Alert className="mb-3 border-amber-200 bg-amber-50 text-amber-900">
                        <AlertDescription>
                          <strong>Health Canada did not publish a statistic for this cell.</strong>{' '}
                          Usually this means fewer than 30 eaters were observed in this
                          (sex × age band) stratum, or every statistic crossed the suppression
                          threshold (CV &gt; 33.3%). Try a broader stratum (e.g. <em>Both</em> sexes,
                          or <em>19+ Years</em>) to see whether the subgroup has releasable data.
                          The CNF candidate list below is still valid.
                        </AlertDescription>
                      </Alert>
                    )}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      <StatCell label="Mean"   value={cell.cell.mean}   se={cell.cell.se_mean}  unit={cell.cell.denom === 'per_person' ? 'g/day' : 'g/kg/day'} />
                      <StatCell label="Median" value={cell.cell.p50}    se={cell.cell.se_p50}   unit={cell.cell.denom === 'per_person' ? 'g/day' : 'g/kg/day'} />
                      <StatCell label="P90"    value={cell.cell.p90}    se={cell.cell.se_p90}   unit={cell.cell.denom === 'per_person' ? 'g/day' : 'g/kg/day'} />
                      <StatCell label="P95"    value={cell.cell.p95}    se={cell.cell.se_p95}   unit={cell.cell.denom === 'per_person' ? 'g/day' : 'g/kg/day'} />
                    </div>
                    <div className="mt-3 text-xs text-slate-600 flex flex-wrap gap-x-4 gap-y-1">
                      <div><strong>n respondents:</strong> {cell.cell.n_respondents?.toLocaleString() ?? '—'}</div>
                      <div><strong>% eaters:</strong> {fmt(cell.cell.pct_eaters, 1)}%</div>
                      {cell.body_weight && (
                        <div><strong>Stratum body weight:</strong> mean {cell.body_weight.mean_bw} kg
                          (95% CI {cell.body_weight.mean_lb}–{cell.body_weight.mean_ub})</div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">
                      Canadian Nutrient File foods in this subgroup ({cell.n_cnf_candidates})
                      <div className="text-xs font-normal text-slate-500 mt-1">
                        CNF foods that map into this Health Canada subgroup. Click any food to open its full profile.
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm">
                    {cell.cnf_candidates.length === 0 ? (
                      <div className="text-slate-500 italic">No CNF foods are currently bridged to this subgroup.</div>
                    ) : (
                      <div className="flex flex-col gap-1 max-h-96 overflow-y-auto">
                        {cell.cnf_candidates.slice(0, 200).map(c => (
                          <Link key={c.food_id} href={`/cnf/foods/${c.food_id}`} target="_blank"
                                className="text-xs px-2 py-1 rounded bg-slate-50 hover:bg-teal-50 hover:text-teal-900 border border-slate-100 flex items-baseline gap-2">
                            <span className="font-mono text-slate-500 shrink-0">{c.food_id}</span>
                            <span className="truncate">{c.description || <em className="text-slate-400">no description</em>}</span>
                          </Link>
                        ))}
                        {cell.n_cnf_candidates > 200 && (
                          <span className="text-xs text-slate-500 mt-1">…{cell.n_cnf_candidates - 200} more not shown — refine the stratum or filter to narrow down.</span>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>

        {/* Provenance footer */}
        {index?.provenance && (
          <Card className="mt-6">
            <CardContent className="py-3 text-xs text-slate-500">
              <strong>{index.provenance.source}</strong> · {index.provenance.base_data} ·
              {' '}{index.provenance.weighting} · n = {index.provenance.n_respondents_total.toLocaleString()} respondents
              · Bridge: {index.provenance.bridge.ranking_model} via {index.provenance.bridge.embedding_model},
              {' '}{index.provenance.bridge.n_bridged} CNF foods bridged
              ({index.provenance.bridge.n_manual_overrides} manual overrides),
              mean confidence {index.provenance.bridge.mean_confidence}.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function StatCell({ label, value, se, unit }: {
  label: string;
  value: number | null;
  se: number | null;
  unit: string;
}) {
  return (
    <div className="border rounded p-2 bg-white">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="font-semibold text-lg tabular-nums">
        {fmt(value)} <span className="text-xs text-slate-500 font-normal">{unit}</span>
      </div>
      {se !== null && (
        <div className="text-xs text-slate-500">SE {fmt(se, 3)}</div>
      )}
    </div>
  );
}
