'use client';

/**
 * NutrientWorkbench — the full "Discover by nutrient" research surface.
 *
 * Built for dietitians / researchers screening the CNF + WAFCT catalogue: a grouped,
 * %DV-aware nutrient picker plus multi-criteria AND queries, energy-adjusted density
 * (per 100 kcal), clinical ratios (Na:K, PUFA:SFA, ...), %DV thresholds, food-group and
 * source scoping, sortable results, and CSV export. Backed by POST /api/cnf/discover/.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  BeakerIcon, MagnifyingGlassIcon, PlusIcon, XMarkIcon, ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import {
  CNFApiService,
  type Nutrient,
  type DiscoverResult,
  type DiscoverRequest,
  type DiscoverBasis,
} from '@/lib/api';
import { groupNutrients } from '@/lib/cnfNutrientGroups';
import { CNF_DAILY_VALUES, percentDV } from '@/lib/cnfDailyValues';
import {
  DISCOVER_WORKBENCH_PRESETS,
  DISCOVER_RATIO_PRESETS,
  type DiscoverWorkbenchPreset,
} from '@/lib/cnfNutrientDiscover';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { SourceBadge } from '@/components/shared/SourceBadge';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import { toCsv, downloadCsv } from '@/lib/csv';

interface CriterionRow { key: string; nutrientId: number | null; min: string; max: string; }
let _rowSeq = 0;
const newRow = (): CriterionRow => ({ key: `c${++_rowSeq}`, nutrientId: null, min: '', max: '' });

export function NutrientWorkbench({ initialFoodGroupId }: { initialFoodGroupId?: number }) {
  const { userType, foodGroups, resolveGroupName } = useCnfExplorer();
  const [nutrients, setNutrients] = useState<Nutrient[]>([]);
  const [criteria, setCriteria] = useState<CriterionRow[]>([newRow()]);
  const [basis, setBasis] = useState<DiscoverBasis>('per_100g');
  const [foodGroupId, setFoodGroupId] = useState<number | ''>(initialFoodGroupId ?? '');
  const [source, setSource] = useState<SourceChoice>('both');
  const [ratioNum, setRatioNum] = useState<number | ''>('');
  const [ratioDen, setRatioDen] = useState<number | ''>('');
  const [dvNutrient, setDvNutrient] = useState<number | ''>('');
  const [dvMinPct, setDvMinPct] = useState('');
  const [sortKey, setSortKey] = useState<string>('');     // '' = auto
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiscoverResult | null>(null);
  const [criteriaLabel, setCriteriaLabel] = useState('');

  useEffect(() => {
    CNFApiService.getNutrients().then(setNutrients).catch(() => toast.error('Failed to load nutrient list'));
  }, []);

  useEffect(() => {
    if (initialFoodGroupId != null && Number.isFinite(initialFoodGroupId)) {
      setFoodGroupId(initialFoodGroupId);
    }
  }, [initialFoodGroupId]);

  const grouped = useMemo(() => groupNutrients(nutrients), [nutrients]);
  const nutrientById = useMemo(() => {
    const m = new Map<number, Nutrient>();
    for (const n of nutrients) m.set(n.NutrientID, n);
    return m;
  }, [nutrients]);

  const unitOf = useCallback((id: number) => nutrientById.get(id)?.NutrientUnit ?? '', [nutrientById]);
  const nameOf = useCallback((id: number) => nutrientById.get(id)?.NutrientName ?? `Nutrient ${id}`, [nutrientById]);

  // Grouped <select> reused by every nutrient picker in the workbench.
  const GroupedSelect = ({ value, onChange, id, includeBlank = 'Select a nutrient…', ariaLabel }: {
    value: number | ''; onChange: (v: number | '') => void; id: string; includeBlank?: string; ariaLabel: string;
  }) => (
    <select
      id={id}
      aria-label={ariaLabel}
      value={value === '' ? '' : value}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
    >
      <option value="">{includeBlank}</option>
      {grouped.map(({ group, nutrients: ns }) => (
        <optgroup key={group.key} label={group.label}>
          {ns.map((n) => (
            <option key={n.NutrientID} value={n.NutrientID}>
              {n.NutrientName}{n.NutrientUnit ? ` (${n.NutrientUnit})` : ''}{CNF_DAILY_VALUES[n.NutrientID] ? ' · %DV' : ''}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  );

  const activeCriteria = criteria.filter((c) => c.nutrientId != null && (c.min.trim() !== '' || c.max.trim() !== ''));
  const hasRatio = ratioNum !== '' && ratioDen !== '';
  const hasDv = dvNutrient !== '' && dvMinPct.trim() !== '';

  // Sort options reflect what the current query can rank by.
  const sortOptions = useMemo(() => {
    const opts: Array<{ value: string; label: string }> = [];
    for (const c of activeCriteria) if (c.nutrientId != null) opts.push({ value: String(c.nutrientId), label: nameOf(c.nutrientId) });
    if (hasDv) opts.push({ value: String(dvNutrient), label: `${nameOf(Number(dvNutrient))} (%DV nutrient)` });
    if (hasRatio) opts.push({ value: 'ratio', label: 'Ratio' });
    opts.push({ value: 'energy', label: 'Energy (kcal)' });
    return opts;
  }, [activeCriteria, hasDv, dvNutrient, hasRatio, nameOf]);

  function setRow(key: string, patch: Partial<CriterionRow>) {
    setCriteria((prev) => prev.map((c) => (c.key === key ? { ...c, ...patch } : c)));
  }
  function addRow() { setCriteria((prev) => [...prev, newRow()]); }
  function removeRow(key: string) {
    setCriteria((prev) => (prev.length > 1 ? prev.filter((c) => c.key !== key) : [newRow()]));
  }

  const buildRequest = useCallback((): DiscoverRequest | null => {
    const crit = activeCriteria.map((c) => {
      const item: { nutrient_id: number; min?: number; max?: number } = { nutrient_id: c.nutrientId! };
      if (c.min.trim() !== '') item.min = parseFloat(c.min);
      if (c.max.trim() !== '') item.max = parseFloat(c.max);
      return item;
    });
    const ratio = hasRatio ? { numerator_id: Number(ratioNum), denominator_id: Number(ratioDen) } : null;
    const dv_threshold = hasDv ? { nutrient_id: Number(dvNutrient), min_pct: parseFloat(dvMinPct) } : null;
    if (crit.length === 0 && !ratio && !dv_threshold) {
      toast.error('Add at least one criterion, a ratio, or a %DV threshold');
      return null;
    }
    const sort = sortKey
      ? { key: (sortKey === 'ratio' || sortKey === 'energy') ? (sortKey as 'ratio' | 'energy') : Number(sortKey), direction: sortDir }
      : undefined;
    return {
      criteria: crit, basis,
      food_group_id: foodGroupId === '' ? null : Number(foodGroupId),
      source, ratio, dv_threshold, sort, limit: 100,
    };
  }, [activeCriteria, basis, foodGroupId, source, hasRatio, ratioNum, ratioDen, hasDv, dvNutrient, dvMinPct, sortKey, sortDir]);

  const run = useCallback(async (req: DiscoverRequest) => {
    setLoading(true);
    try {
      const data = await CNFApiService.discoverFoods(req);
      setResult(data);
      const parts: string[] = req.criteria.map((c) => {
        const u = unitOf(c.nutrient_id);
        const b = [];
        if (c.min != null) b.push(`≥ ${c.min}`);
        if (c.max != null) b.push(`≤ ${c.max}`);
        return `${nameOf(c.nutrient_id)} ${b.join(' ')}${u ? ` ${u}` : ''}`;
      });
      if (req.dv_threshold) parts.push(`${nameOf(req.dv_threshold.nutrient_id)} ≥ ${req.dv_threshold.min_pct}% DV`);
      if (req.ratio) parts.push(`ratio ${nameOf(req.ratio.numerator_id)} : ${nameOf(req.ratio.denominator_id)}`);
      parts.push(req.basis === 'per_100kcal' ? 'per 100 kcal' : 'per 100 g');
      setCriteriaLabel(parts.join(' · '));
    } catch {
      toast.error('Discovery query failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [nameOf, unitOf]);

  function handleRun(e: React.FormEvent) {
    e.preventDefault();
    const req = buildRequest();
    if (req) run(req);
  }

  function applyPreset(p: DiscoverWorkbenchPreset) {
    setCriteria(p.criteria.length
      ? p.criteria.map((c) => ({ key: `c${++_rowSeq}`, nutrientId: c.nutrient_id, min: c.min != null ? String(c.min) : '', max: c.max != null ? String(c.max) : '' }))
      : [newRow()]);
    setBasis(p.basis ?? 'per_100g');
    setRatioNum(p.ratio ? p.ratio.numerator_id : '');
    setRatioDen(p.ratio ? p.ratio.denominator_id : '');
    setDvNutrient(p.dv_threshold ? p.dv_threshold.nutrient_id : '');
    setDvMinPct(p.dv_threshold?.min_pct != null ? String(p.dv_threshold.min_pct) : '');
    setFoodGroupId('');
    setSortKey(p.sort ? String(p.sort.key) : '');
    setSortDir(p.sort?.direction ?? 'desc');
    run({
      criteria: p.criteria, basis: p.basis ?? 'per_100g', food_group_id: null, source: 'both',
      ratio: p.ratio ?? null, dv_threshold: p.dv_threshold ?? null, sort: p.sort ?? null, limit: 100,
    });
  }

  // --- %DV for a result cell (per-100 g amount; sums trans into saturated for 606) ---
  const cellDV = (nid: number, rowValues: Record<string, number>): number | null =>
    percentDV(nid, rowValues[String(nid)], (other) => rowValues[String(other)] ?? null);

  const involved = result?.involved_nutrient_ids ?? [];

  function exportCsv() {
    if (!result || result.foods.length === 0) return;
    const headers = ['FoodID', 'Food', 'Food group', 'Source', 'Energy (kcal/100g)'];
    for (const nid of involved) {
      headers.push(`${nameOf(nid)} (${unitOf(nid)}/100g)`);
      if (CNF_DAILY_VALUES[nid]) headers.push(`${nameOf(nid)} (%DV)`);
      if (basis === 'per_100kcal') headers.push(`${nameOf(nid)} (/100kcal)`);
    }
    if (hasRatio) headers.push('Ratio');
    const rows = result.foods.map((f) => {
      const r: unknown[] = [f.FoodID, f.FoodDescription, f.FoodGroupName, f.source, f.energy_kcal ?? ''];
      for (const nid of involved) {
        r.push(f.nutrient_values[String(nid)] ?? '');
        if (CNF_DAILY_VALUES[nid]) { const d = cellDV(nid, f.nutrient_values); r.push(d != null ? d.toFixed(1) : ''); }
        if (basis === 'per_100kcal') r.push(f.basis_values[String(nid)] ?? '');
      }
      if (hasRatio) r.push(f.ratio_value ?? '');
      return r;
    });
    downloadCsv(`cnf-discover-${Date.now()}`, toCsv(headers, rows));
  }

  return (
    <div className="space-y-5">
      {/* Research presets */}
      <div>
        <h3 className="font-semibold text-gray-900 flex items-center gap-2 text-sm mb-2">
          <BeakerIcon className="w-4 h-4 text-primary-600" aria-hidden="true" />
          Research presets
        </h3>
        <div className="flex flex-wrap gap-2">
          {DISCOVER_WORKBENCH_PRESETS.map((p) => (
            <button key={p.label} type="button" onClick={() => applyPreset(p)} title={p.description}
              className="px-3 py-1.5 text-xs font-medium rounded-full bg-gray-100 text-gray-800 hover:bg-primary-100 hover:text-primary-800 transition">
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleRun} className="space-y-4">
        {/* Criteria builder */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nutrient criteria (all must hold)</label>
          <div className="space-y-2">
            {criteria.map((c) => (
              <div key={c.key} className="grid grid-cols-1 sm:grid-cols-[1fr,110px,110px,40px] gap-2 items-center">
                <GroupedSelect id={`crit-${c.key}`} ariaLabel="Criterion nutrient" value={c.nutrientId ?? ''} onChange={(v) => setRow(c.key, { nutrientId: v === '' ? null : v })} />
                <div className="relative">
                  <input type="number" step="any" value={c.min} onChange={(e) => setRow(c.key, { min: e.target.value })}
                    placeholder="min" className="w-full px-2 py-2 border border-gray-300 rounded-lg text-sm" aria-label="Minimum" />
                  {c.nutrientId != null && unitOf(c.nutrientId) && (
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">{unitOf(c.nutrientId)}</span>
                  )}
                </div>
                <div className="relative">
                  <input type="number" step="any" value={c.max} onChange={(e) => setRow(c.key, { max: e.target.value })}
                    placeholder="max" className="w-full px-2 py-2 border border-gray-300 rounded-lg text-sm" aria-label="Maximum" />
                  {c.nutrientId != null && unitOf(c.nutrientId) && (
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">{unitOf(c.nutrientId)}</span>
                  )}
                </div>
                <button type="button" onClick={() => removeRow(c.key)} title="Remove criterion"
                  className="p-2 text-gray-400 hover:text-red-600 justify-self-center" aria-label="Remove criterion">
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <button type="button" onClick={addRow}
            className="mt-2 inline-flex items-center gap-1 text-xs px-2 py-1 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-dashed border-gray-300">
            <PlusIcon className="w-3.5 h-3.5" /> Add criterion
          </button>
          <p className="mt-1 text-xs text-gray-500">
            Thresholds are interpreted in the chosen basis. Foods missing a measurement for a criterion are excluded.
          </p>
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Basis</label>
            <div className="inline-flex rounded-lg border border-gray-300 overflow-hidden text-sm">
              {(['per_100g', 'per_100kcal'] as DiscoverBasis[]).map((b) => (
                <button key={b} type="button" onClick={() => setBasis(b)}
                  className={`px-3 py-2 ${basis === b ? 'bg-primary-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}>
                  {b === 'per_100g' ? 'per 100 g' : 'per 100 kcal'}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label htmlFor="wb-group" className="block text-xs font-medium text-gray-700 mb-1">Food group</label>
            <select id="wb-group" value={foodGroupId} onChange={(e) => setFoodGroupId(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              <option value="">All groups</option>
              {foodGroups.map((g) => <option key={g.FoodGroupID} value={g.FoodGroupID}>{g.FoodGroupName}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Source</label>
            <SourceFilter source={source} onChange={setSource} accent="blue" />
          </div>
        </div>

        {/* Advanced: ratio + %DV threshold */}
        <details className="border border-gray-200 rounded-lg p-3">
          <summary className="cursor-pointer text-sm font-medium text-gray-700">Ratios & %DV threshold</summary>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Nutrient ratio (rank by A : B)</label>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {DISCOVER_RATIO_PRESETS.map((rp) => (
                  <button key={rp.label} type="button"
                    onClick={() => { setRatioNum(rp.numerator_id); setRatioDen(rp.denominator_id); }}
                    className="px-2 py-1 text-[11px] rounded-full bg-gray-100 hover:bg-primary-100 text-gray-700">{rp.label}</button>
                ))}
                {hasRatio && (
                  <button type="button" onClick={() => { setRatioNum(''); setRatioDen(''); }}
                    className="px-2 py-1 text-[11px] rounded-full bg-red-50 text-red-600 hover:bg-red-100">clear</button>
                )}
              </div>
              <div className="grid grid-cols-[1fr,auto,1fr] gap-2 items-center">
                <GroupedSelect id="ratio-num" ariaLabel="Ratio numerator nutrient" value={ratioNum} onChange={setRatioNum} includeBlank="numerator…" />
                <span className="text-gray-400 text-sm">:</span>
                <GroupedSelect id="ratio-den" ariaLabel="Ratio denominator nutrient" value={ratioDen} onChange={setRatioDen} includeBlank="denominator…" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">% Daily Value threshold (per 100 g)</label>
              <div className="grid grid-cols-[1fr,110px] gap-2 items-center">
                <select id="wb-dv-nutrient" aria-label="Nutrient with daily value" value={dvNutrient} onChange={(e) => setDvNutrient(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
                  <option value="">Nutrient with a DV…</option>
                  {Object.keys(CNF_DAILY_VALUES).map(Number).map((nid) => (
                    <option key={nid} value={nid}>{CNF_DAILY_VALUES[nid].label}</option>
                  ))}
                </select>
                <div className="relative">
                  <input type="number" step="any" value={dvMinPct} onChange={(e) => setDvMinPct(e.target.value)}
                    placeholder="min %" className="w-full px-2 py-2 border border-gray-300 rounded-lg text-sm" aria-label="Minimum %DV" />
                  <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">% DV</span>
                </div>
              </div>
            </div>
          </div>
        </details>

        {/* Sort + run */}
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label htmlFor="wb-sort" className="block text-xs font-medium text-gray-700 mb-1">Sort by</label>
            <select id="wb-sort" value={sortKey} onChange={(e) => setSortKey(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              <option value="">Auto</option>
              {sortOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="wb-dir" className="block text-xs font-medium text-gray-700 mb-1">Direction</label>
            <select id="wb-dir" value={sortDir} onChange={(e) => setSortDir(e.target.value as 'asc' | 'desc')}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
              <option value="desc">Highest first</option>
              <option value="asc">Lowest first</option>
            </select>
          </div>
          <button type="submit" disabled={loading}
            className="btn-primary inline-flex items-center text-sm disabled:opacity-50">
            <MagnifyingGlassIcon className="w-4 h-4 mr-2" aria-hidden="true" />
            {loading ? 'Searching…' : 'Find foods'}
          </button>
        </div>
      </form>

      {/* Results */}
      {result && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 flex items-center justify-between gap-3">
            <p className="text-xs text-gray-600 min-w-0 truncate">{result.count} foods · {criteriaLabel}</p>
            <button type="button" onClick={exportCsv} disabled={result.foods.length === 0}
              className="inline-flex items-center gap-1 text-xs px-2 py-1 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-300 disabled:opacity-50 shrink-0">
              <ArrowDownTrayIcon className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          {result.foods.length === 0 ? (
            <p className="p-4 text-center text-sm text-gray-500">No foods matched all criteria.</p>
          ) : (
            <div className="overflow-x-auto max-h-[32rem]">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr className="text-left text-xs text-gray-500">
                    <th className="px-3 py-2 font-medium">Food</th>
                    <th className="px-3 py-2 font-medium text-right">Energy</th>
                    {involved.map((nid) => (
                      <th key={nid} className="px-3 py-2 font-medium text-right whitespace-nowrap">
                        {nameOf(nid)}<span className="text-gray-400"> ({unitOf(nid)})</span>
                      </th>
                    ))}
                    {hasRatio && <th className="px-3 py-2 font-medium text-right">Ratio</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {result.foods.map((f) => (
                    <tr key={f.FoodID} className="hover:bg-gray-50">
                      <td className="px-3 py-2">
                        <Link href={`/cnf/foods/${f.FoodID}`} className="font-medium text-gray-900 hover:text-primary-700">
                          {f.FoodDescription}
                        </Link>
                        <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-gray-500">
                          <SourceBadge foodId={f.FoodID} userType={userType} />
                          <span>{resolveGroupName(f.FoodGroupID ?? -1, f.FoodGroupName)}</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right text-gray-600 whitespace-nowrap">{f.energy_kcal ?? '—'}</td>
                      {involved.map((nid) => {
                        const per100 = f.nutrient_values[String(nid)];
                        const shown = basis === 'per_100kcal' ? f.basis_values[String(nid)] : per100;
                        const dv = cellDV(nid, f.nutrient_values);
                        return (
                          <td key={nid} className="px-3 py-2 text-right whitespace-nowrap">
                            <span className="text-gray-900">{shown != null ? shown : '—'}</span>
                            {dv != null && <span className="ml-1 text-[10px] text-emerald-700">{dv.toFixed(0)}%DV</span>}
                          </td>
                        );
                      })}
                      {hasRatio && <td className="px-3 py-2 text-right text-gray-900 whitespace-nowrap">{f.ratio_value ?? '—'}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="px-3 py-2 border-t border-gray-100 text-[11px] text-gray-400">
            Values per 100 g{basis === 'per_100kcal' ? ' (main figure shown per 100 kcal)' : ''}. %DV is computed per 100 g against the Health Canada Table of Daily Values.
          </div>
        </div>
      )}
    </div>
  );
}
