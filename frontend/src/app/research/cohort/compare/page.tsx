/**
 * Cohort comparison page (PLATFORM-CODE-1.b Phase D, 2026-06-26).
 *
 * Two-cohort selector pulled from localStorage saves. Sends both
 * per_respondent arrays to `/api/research/cohort/compare/` for
 * Mann-Whitney U + rank-biserial effect size, and renders a delta
 * table alongside twin distribution histograms.
 *
 * URL shape: `/research/cohort/compare?a=<id>&b=<id>` — both ids are
 * optional; missing ids fall back to dropdown selection.
 */
'use client';

import React, { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import CohortDistributionPanel from '@/components/research/CohortDistributionPanel';
import {
  CohortApiService,
  type CohortCompareResponse,
} from '@/lib/api';
import {
  listSavedCohorts,
  getSavedCohort,
  type SavedCohort,
} from '@/lib/savedCohorts';

function fmt(v: number | null | undefined, nd = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return Number(v).toFixed(nd);
}

function pBadge(p: number | null): { label: string; tone: 'default' | 'secondary' | 'destructive' } {
  if (p === null) return { label: 'n/a', tone: 'secondary' };
  if (p < 0.001) return { label: 'p < 0.001', tone: 'default' };
  if (p < 0.01)  return { label: `p = ${p.toFixed(3)}`, tone: 'default' };
  if (p < 0.05)  return { label: `p = ${p.toFixed(3)}`, tone: 'default' };
  return { label: `p = ${p.toFixed(3)}`, tone: 'secondary' };
}

function CompareInner() {
  const search = useSearchParams();
  const [saved, setSaved] = useState<SavedCohort[]>([]);
  const [aId, setAId] = useState<string>('');
  const [bId, setBId] = useState<string>('');
  const [result, setResult] = useState<CohortCompareResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const list = listSavedCohorts();
    setSaved(list);
    const qa = search?.get('a') ?? '';
    const qb = search?.get('b') ?? '';
    setAId(qa || list[0]?.id || '');
    setBId(qb || list[1]?.id || '');
  }, [search]);

  const aCohort = useMemo(() => (aId ? getSavedCohort(aId) : null), [aId]);
  const bCohort = useMemo(() => (bId ? getSavedCohort(bId) : null), [bId]);

  const runCompare = useCallback(async () => {
    if (!aCohort || !bCohort) return;
    setRunning(true);
    setErr(null);
    setResult(null);
    try {
      const out = await CohortApiService.compare(
        { name: aCohort.name, per_respondent: aCohort.result.per_respondent },
        { name: bCohort.name, per_respondent: bCohort.result.per_respondent },
      );
      setResult(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [aCohort, bCohort]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <div className="flex items-baseline justify-between flex-wrap gap-2 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Cohort comparison</h1>
            <p className="text-slate-600 mt-1 max-w-3xl">
              Compare two saved cohorts across every lens. Median delta + two-sided
              Mann-Whitney U + rank-biserial effect size (King &amp; Minium 2008).
            </p>
          </div>
          <Link href="/research/cohort" className="text-sm text-teal-700 hover:underline">
            ← Back to cohort upload
          </Link>
        </div>

        {saved.length < 2 ? (
          <Alert>
            <AlertDescription>
              You need at least two saved cohorts to compare. Score and save a couple from{' '}
              <Link href="/research/cohort" className="text-teal-700 hover:underline">/research/cohort</Link>.
            </AlertDescription>
          </Alert>
        ) : (
          <>
            <Card className="mb-6">
              <CardHeader><CardTitle>1 · Pick two cohorts</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="cohort-a" className="block text-sm text-slate-600 mb-1">Cohort A (baseline)</label>
                    <select
                      id="cohort-a"
                      aria-label="Cohort A (baseline)"
                      className="w-full border rounded px-2 py-1.5 text-sm"
                      value={aId}
                      onChange={(e) => setAId(e.target.value)}
                    >
                      {saved.map(c => (
                        <option key={c.id} value={c.id}>{c.name} · {c.nRecalls} recalls</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="cohort-b" className="block text-sm text-slate-600 mb-1">Cohort B (comparison)</label>
                    <select
                      id="cohort-b"
                      aria-label="Cohort B (comparison)"
                      className="w-full border rounded px-2 py-1.5 text-sm"
                      value={bId}
                      onChange={(e) => setBId(e.target.value)}
                    >
                      {saved.map(c => (
                        <option key={c.id} value={c.id}>{c.name} · {c.nRecalls} recalls</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-4">
                  <Button onClick={runCompare} disabled={!aCohort || !bCohort || aId === bId || running}>
                    {running ? 'Computing…' : 'Compare cohorts'}
                  </Button>
                  {aId === bId && (
                    <span className="ml-3 text-sm text-amber-700">Pick two different cohorts.</span>
                  )}
                </div>
                {err && <Alert className="mt-4 border-red-200 bg-red-50 text-red-800"><AlertDescription>{err}</AlertDescription></Alert>}
              </CardContent>
            </Card>

            {result && (
              <>
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>
                      2 · Per-lens delta + Mann-Whitney U
                      <span className="ml-2 text-xs font-normal text-slate-500">
                        A = {result.cohort_a.name} (n={result.cohort_a.n}) ·
                        B = {result.cohort_b.name} (n={result.cohort_b.n})
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-50 text-slate-700">
                          <tr>
                            <th className="px-3 py-2 text-left">Lens</th>
                            <th className="px-3 py-2 text-right">Median A</th>
                            <th className="px-3 py-2 text-right">Median B</th>
                            <th className="px-3 py-2 text-right">Δ median (B − A)</th>
                            <th className="px-3 py-2 text-right" title="Rank-biserial r: +1 = B uniformly higher; −1 = A uniformly higher; 0 = no rank shift.">Effect r</th>
                            <th className="px-3 py-2 text-center">p (MW)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.per_lens.map(row => {
                            const b = pBadge(row.mann_whitney.p);
                            return (
                              <tr key={row.lens} className="border-t border-slate-100">
                                <td className="px-3 py-2 font-medium">
                                  {row.lens}
                                  <div className="text-xs text-slate-500 font-normal">{row.unit}</div>
                                </td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(row.a.median)}</td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(row.b.median)}</td>
                                <td className={`px-3 py-2 text-right tabular-nums font-medium ${row.median_delta !== null && row.median_delta > 0 ? 'text-teal-700' : row.median_delta !== null && row.median_delta < 0 ? 'text-rose-700' : ''}`}>
                                  {row.median_delta === null ? '—' : (row.median_delta > 0 ? '+' : '') + row.median_delta.toFixed(2)}
                                </td>
                                <td className="px-3 py-2 text-right tabular-nums">{fmt(row.mann_whitney.effect_r, 3)}</td>
                                <td className="px-3 py-2 text-center">
                                  <Badge variant={b.tone}>{b.label}</Badge>
                                  {row.mann_whitney.note && <div className="text-xs text-slate-500 mt-1">{row.mann_whitney.note}</div>}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                    <div className="border-t border-slate-100 p-3 text-xs text-slate-500">
                      {result.method.test} · {result.method.multiple_testing_note}
                    </div>
                  </CardContent>
                </Card>

                {aCohort && bCohort && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader><CardTitle className="text-sm">{aCohort.name} distributions</CardTitle></CardHeader>
                      <CardContent><CohortDistributionPanel result={aCohort.result} audience="researcher" /></CardContent>
                    </Card>
                    <Card>
                      <CardHeader><CardTitle className="text-sm">{bCohort.name} distributions</CardTitle></CardHeader>
                      <CardContent><CohortDistributionPanel result={bCohort.result} audience="researcher" /></CardContent>
                    </Card>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="container mx-auto py-8 px-4">Loading…</div>}>
      <CompareInner />
    </Suspense>
  );
}
