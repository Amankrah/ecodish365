/**
 * Cohort batch ingest page (PLATFORM-CODE-1.b, 2026-06-26).
 *
 * The first surface on the platform that lets a researcher score N
 * full-day recalls in one upload — closes the "no one publishes with
 * this tool" gap by handling NHANES What-We-Eat-in-America 2017-18
 * Day-1 / Day-2 files natively and any CSV with `food_id` + `mass_g`
 * generically.
 *
 * Flow:
 *   1. Drop a .xpt or .csv. We parse it (server-side) into Recall objects
 *      with a validation report — preview the first 50 rows + bad-row
 *      counts before committing.
 *   2. Pick which lenses to score (default: all 7).
 *   3. Run cohort scoring. The result is rendered as distribution panels
 *      + a per-respondent table + a coverage card + provenance.
 *   4. Optionally save the cohort to localStorage so you can compare it
 *      against a sibling cohort on `/research/cohort/compare`.
 *
 * Cohorts live entirely in the browser. No server-side persistence and
 * no auth changes (by design — see plan PLATFORM-CODE-1.b).
 */
'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AudienceToggle, type UserType } from '@/components/shared/AudienceToggle';
import CohortDistributionPanel from '@/components/research/CohortDistributionPanel';
import CohortRespondentTable from '@/components/research/CohortRespondentTable';
import {
  CohortApiService,
  COHORT_LENSES,
  type CohortLens,
  type CohortRecallInput,
  type CohortResult,
  type CohortIngestResponse,
  type CohortIngestFormat,
  type CohortLibraryEntry,
} from '@/lib/api';
import {
  saveCohort,
  listSavedCohorts,
  deleteCohort,
  SAVED_COHORTS_MAX,
  type SavedCohort,
} from '@/lib/savedCohorts';

const LENS_LABELS: Record<CohortLens, string> = {
  hefi:            'HEFI-2019',
  heni:            'HENI (DALY minutes)',
  hsr:             'Health Star Rating',
  fcs:             'Food Compass Score',
  env:             'Environmental impact',
  dietary_pattern: 'Dietary pattern',
  fped:            'FPED coverage',
};

const FORMAT_LABELS: Record<CohortIngestFormat, string> = {
  auto:           'Auto-detect',
  generic_csv:    'Generic CSV',
  nhanes_dr1iff:  'NHANES Day-1 XPT',
  nhanes_dr2iff:  'NHANES Day-2 XPT',
};

export default function CohortPage() {
  const [audience, setAudience] = useState<UserType>('researcher');
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<CohortIngestFormat>('auto');
  const [ingest, setIngest] = useState<CohortIngestResponse | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  const [lenses, setLenses] = useState<CohortLens[]>([...COHORT_LENSES]);
  const [scoring, setScoring] = useState(false);
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [result, setResult] = useState<CohortResult | null>(null);

  const [cohortName, setCohortName] = useState('');
  const [saved, setSaved] = useState<SavedCohort[]>([]);

  const [library, setLibrary] = useState<CohortLibraryEntry[]>([]);
  const [librarySampleN, setLibrarySampleN] = useState(200);
  const [loadingLibrary, setLoadingLibrary] = useState<string | null>(null);

  useEffect(() => { setSaved(listSavedCohorts()); }, []);

  useEffect(() => {
    CohortApiService.listLibrary()
      .then(setLibrary)
      .catch(() => setLibrary([]));   // graceful — panel hides on failure
  }, []);

  const loadFromLibrary = useCallback(async (entry: CohortLibraryEntry) => {
    setLoadingLibrary(entry.id);
    setIngestError(null);
    setIngest(null);
    setResult(null);
    setFile(null);
    try {
      const resp = await CohortApiService.loadLibrary(entry.id, librarySampleN);
      // The library endpoint returns the same shape as /ingest/, so we can
      // feed it straight into the existing preview state.
      setIngest({
        format_detected:   resp.format_detected,
        validation_report: resp.validation_report,
        recalls_preview:   resp.recalls_preview,
        n_total_recalls:   resp.n_total_recalls,
        recalls:           resp.recalls,
      });
      setCohortName(`${entry.name} (n=${resp.n_total_recalls})`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setIngestError(`Failed to load ${entry.name}: ${msg}`);
    } finally {
      setLoadingLibrary(null);
    }
  }, [librarySampleN]);

  const onDrop = useCallback((evt: React.DragEvent<HTMLDivElement>) => {
    evt.preventDefault();
    const f = evt.dataTransfer.files?.[0];
    if (f) { setFile(f); setIngest(null); setResult(null); }
  }, []);

  const onPick = useCallback((evt: React.ChangeEvent<HTMLInputElement>) => {
    const f = evt.target.files?.[0];
    if (f) { setFile(f); setIngest(null); setResult(null); }
  }, []);

  const runIngest = useCallback(async () => {
    if (!file) return;
    setIngesting(true);
    setIngestError(null);
    try {
      const resp = await CohortApiService.ingest(file, format, 50);
      setIngest(resp);
      if (resp.n_total_recalls === 0) {
        setIngestError('No valid recalls parsed. Check the validation report below for the dropped rows.');
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setIngestError(`Upload failed: ${msg}`);
    } finally {
      setIngesting(false);
    }
  }, [file, format]);

  const runScoring = useCallback(async () => {
    if (!ingest || ingest.n_total_recalls === 0) return;
    setScoring(true);
    setScoreError(null);
    setResult(null);
    try {
      const recalls: CohortRecallInput[] = ingest.recalls;
      const r = await CohortApiService.runCohort(recalls, lenses, {
        parallelism: 4,
        anonymize: audience === 'individual',
      });
      setResult(r);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setScoreError(`Scoring failed: ${msg}`);
    } finally {
      setScoring(false);
    }
  }, [ingest, lenses, audience]);

  const onSave = useCallback(() => {
    if (!result || !ingest) return;
    const name = cohortName.trim() || `${ingest.format_detected} cohort · ${new Date().toLocaleString()}`;
    const out = saveCohort({
      name,
      source: file?.name ?? 'unknown source',
      formatDetected: ingest.format_detected,
      lensesRun: result.meta.lenses_run,
      result,
      recalls: ingest.recalls,
    });
    if (out) {
      setSaved(listSavedCohorts());
      setCohortName('');
    } else {
      alert('Could not save cohort — your browser storage may be full. Try removing an older saved cohort first.');
    }
  }, [result, ingest, file, cohortName]);

  const onDeleteSaved = useCallback((id: string) => {
    deleteCohort(id);
    setSaved(listSavedCohorts());
  }, []);

  const toggleLens = useCallback((l: CohortLens) => {
    setLenses(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l]);
  }, []);

  const previewRows = useMemo(() => ingest?.recalls_preview ?? [], [ingest]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        {/* Header */}
        <div className="flex flex-col gap-3 mb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Cohort upload</h1>
            <p className="text-slate-600 mt-1 max-w-3xl">
              Upload N recalls (NHANES What-We-Eat-in-America .xpt or a CSV with{' '}
              <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">food_id, mass_g</code>) and score
              the whole cohort across every lens in one pass. Distribution stats,
              per-respondent rows, and CSV export — without writing a line of API client code.
            </p>
          </div>
          <AudienceToggle userType={audience} onChange={setAudience} accent="blue" />
        </div>

        {/* Saved cohorts strip */}
        {saved.length > 0 && (
          <Card className="mb-6">
            <CardHeader className="pb-2 flex-row items-baseline justify-between flex">
              <CardTitle className="text-sm">
                Saved cohorts ({saved.length}/{SAVED_COHORTS_MAX})
              </CardTitle>
              {saved.length >= 2 && (
                <Link href={`/research/cohort/compare?a=${saved[0].id}&b=${saved[1].id}`} className="text-sm text-teal-700 hover:underline">
                  Compare top two →
                </Link>
              )}
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {saved.map(c => (
                  <div key={c.id} className="flex items-center gap-2 bg-slate-100 rounded px-3 py-1.5 text-sm">
                    <span className="font-medium">{c.name}</span>
                    <span className="text-slate-500 text-xs">{c.nRecalls} recalls · {c.nRespondents} respondents</span>
                    <button type="button" className="text-slate-400 hover:text-red-500" onClick={() => onDeleteSaved(c.id)} aria-label="delete">×</button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Built-in cohorts — primary path; load NHANES etc. without re-uploading */}
        {library.length > 0 && (
          <Card className="mb-6">
            <CardHeader className="pb-3 flex flex-row items-baseline justify-between gap-3 flex-wrap">
              <CardTitle>
                Built-in cohorts
                <span className="ml-2 text-sm font-normal text-slate-500">
                  Public national-nutrition surveys shipped with the platform — no upload required.
                </span>
              </CardTitle>
              <div className="flex items-center gap-2 text-sm">
                <label htmlFor="lib-sample" className="text-slate-600">Sample size:</label>
                <select
                  id="lib-sample"
                  aria-label="Sample size when loading a built-in cohort"
                  className="border rounded px-2 py-1"
                  value={librarySampleN}
                  onChange={(e) => setLibrarySampleN(Number(e.target.value))}
                >
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                  <option value={500}>500</option>
                  <option value={1000}>1,000</option>
                  <option value={5000}>5,000 (max)</option>
                </select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {library.map(entry => {
                  const isLoading = loadingLibrary === entry.id;
                  const disabled = !entry.file_present || isLoading;
                  return (
                    <div
                      key={entry.id}
                      className={`border rounded-lg p-3 flex flex-col gap-2 ${entry.file_present ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-200 opacity-60'}`}
                    >
                      <div className="flex items-baseline justify-between gap-2 flex-wrap">
                        <div className="font-medium text-slate-900">{entry.name}</div>
                        <span className="text-xs text-slate-500">{entry.country} · {entry.year}</span>
                      </div>
                      <div className="text-xs text-slate-600">{entry.description}</div>
                      <div className="flex flex-wrap gap-1 text-xs text-slate-500">
                        <Badge variant="secondary" className="font-normal">~{entry.expected_recalls.toLocaleString()} recalls</Badge>
                        {entry.coverage_note && (
                          <Badge variant="secondary" className="font-normal" title={entry.coverage_note}>coverage caveat</Badge>
                        )}
                        {entry.survey_weight_note && (
                          <Badge variant="secondary" className="font-normal" title={entry.survey_weight_note}>unweighted</Badge>
                        )}
                      </div>
                      <div className="text-xs text-slate-500">
                        Source: <a href={entry.source_url} target="_blank" rel="noopener noreferrer" className="text-teal-700 hover:underline">{entry.source}</a>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => loadFromLibrary(entry)}
                        disabled={disabled}
                      >
                        {isLoading
                          ? 'Loading…'
                          : entry.file_present
                            ? `Load ${librarySampleN.toLocaleString()} recalls`
                            : 'Not available on this deployment'}
                      </Button>
                    </div>
                  );
                })}
              </div>
              <div className="text-xs text-slate-500 mt-3">
                Want CCHS-Nutrition, INCA3, NDNS, KNHANES, or another national survey added here?
                Track progress under <code className="bg-slate-100 px-1 rounded">PLATFORM-CODE-1.k</code> in <code className="bg-slate-100 px-1 rounded">code_action_items.md</code>.
              </div>
            </CardContent>
          </Card>
        )}

        {/* Or: upload your own */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{library.length > 0 ? 'Or upload your own cohort' : '1 · Upload a cohort'}</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              onDrop={onDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-teal-400 transition-colors"
            >
              <input
                type="file"
                id="cohort-file"
                accept=".csv,.xpt,.txt"
                className="hidden"
                onChange={onPick}
              />
              <label htmlFor="cohort-file" className="cursor-pointer block">
                <div className="text-slate-600">
                  {file ? (
                    <>
                      <div className="font-medium">{file.name}</div>
                      <div className="text-sm text-slate-500 mt-1">
                        {(file.size / (1024 * 1024)).toFixed(1)} MB · click to choose a different file
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="font-medium">Drop a .csv or .xpt file here</div>
                      <div className="text-sm text-slate-500 mt-1">or click to browse · up to ~100 MB</div>
                    </>
                  )}
                </div>
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-3 mt-4">
              <label htmlFor="cohort-format" className="text-sm text-slate-700">Format:</label>
              <select
                id="cohort-format"
                aria-label="Upload format"
                className="text-sm border rounded px-2 py-1"
                value={format}
                onChange={(e) => setFormat(e.target.value as CohortIngestFormat)}
              >
                {(Object.keys(FORMAT_LABELS) as CohortIngestFormat[]).map(k => (
                  <option key={k} value={k}>{FORMAT_LABELS[k]}</option>
                ))}
              </select>
              <Button onClick={runIngest} disabled={!file || ingesting}>
                {ingesting ? 'Parsing…' : 'Parse upload'}
              </Button>
            </div>

            {ingestError && (
              <Alert className="mt-4 border-red-200 bg-red-50 text-red-800">
                <AlertDescription>{ingestError}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Step 2: Preview + lens picker */}
        {ingest && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>
                2 · Review parsed cohort
                <span className="ml-2 text-sm font-normal text-slate-500">
                  {ingest.n_total_recalls.toLocaleString()} recalls · format {ingest.format_detected}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <Stat label="Rows read"        value={ingest.validation_report.n_rows_read} />
                <Stat label="Rows dropped"     value={ingest.validation_report.n_rows_dropped}
                      tone={ingest.validation_report.n_rows_dropped > 0 ? 'warn' : 'ok'} />
                <Stat label="Recalls built"    value={ingest.validation_report.n_recalls_built} />
                <Stat label="Respondents"      value={ingest.validation_report.n_respondents} />
              </div>

              {Object.keys(ingest.validation_report.drop_reasons).length > 0 && (
                <div className="text-sm text-slate-600 mb-4">
                  Dropped row reasons:
                  <span className="ml-2 inline-flex flex-wrap gap-1">
                    {Object.entries(ingest.validation_report.drop_reasons).map(([reason, n]) => (
                      <Badge key={reason} variant="secondary" className="font-normal">{reason}: {n}</Badge>
                    ))}
                  </span>
                </div>
              )}

              {previewRows.length > 0 && (
                <div className="overflow-x-auto mb-4">
                  <table className="text-xs">
                    <thead className="bg-slate-50 text-slate-700">
                      <tr>
                        <th className="px-2 py-1 text-left">Respondent</th>
                        <th className="px-2 py-1 text-left">Day</th>
                        <th className="px-2 py-1 text-right">Foods</th>
                        <th className="px-2 py-1 text-left">First 5 foods (food_id × mass_g)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.slice(0, 12).map((r, i) => (
                        <tr key={i} className="border-t border-slate-100">
                          <td className="px-2 py-1 font-medium">{r.respondent_id}</td>
                          <td className="px-2 py-1">{r.day_id}</td>
                          <td className="px-2 py-1 text-right">{r.n_foods}</td>
                          <td className="px-2 py-1 text-slate-500">
                            {r.foods.slice(0, 5).map(f => `${f.food_id} × ${f.mass_g.toFixed(0)}g`).join(', ')}
                            {r.foods.length > 5 && '…'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {previewRows.length > 12 && (
                    <div className="text-xs text-slate-500 mt-1">…{previewRows.length - 12} more in preview</div>
                  )}
                </div>
              )}

              <div className="border-t border-slate-100 pt-4">
                <div className="text-sm font-medium text-slate-700 mb-2">Choose lenses to score:</div>
                <div className="flex flex-wrap gap-2">
                  {COHORT_LENSES.map(l => (
                    <button
                      key={l}
                      type="button"
                      onClick={() => toggleLens(l)}
                      className={`text-sm px-3 py-1.5 rounded border transition-colors ${
                        lenses.includes(l)
                          ? 'bg-teal-600 text-white border-teal-600'
                          : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400'
                      }`}
                    >
                      {LENS_LABELS[l]}
                    </button>
                  ))}
                </div>
                <div className="mt-4">
                  <Button
                    onClick={runScoring}
                    disabled={scoring || ingest.n_total_recalls === 0 || lenses.length === 0}
                  >
                    {scoring
                      ? `Scoring ${ingest.n_total_recalls.toLocaleString()} recalls…`
                      : `Run cohort analysis (${ingest.n_total_recalls.toLocaleString()} × ${lenses.length} lenses)`}
                  </Button>
                  {ingest.n_total_recalls > 5000 && (
                    <span className="ml-3 text-sm text-amber-700">
                      Note: the backend caps at 5,000 recalls per request. Trim or batch.
                    </span>
                  )}
                </div>
              </div>

              {scoring && (
                <div className="mt-3">
                  <Progress value={undefined} className="h-2" />
                  <div className="text-xs text-slate-500 mt-1">
                    Each lens runs in parallel against every recall. Expect ~30–60 s for 200 recalls × 7 lenses.
                  </div>
                </div>
              )}

              {scoreError && (
                <Alert className="mt-4 border-red-200 bg-red-50 text-red-800">
                  <AlertDescription>{scoreError}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 3: Results */}
        {result && (
          <>
            <Card className="mb-6">
              <CardHeader className="pb-3 flex-row items-start justify-between flex flex-wrap gap-2">
                <CardTitle className="text-base">
                  3 · Distribution by lens
                  <span className="ml-2 text-xs font-normal text-slate-500">
                    {result.meta.n_recalls} recalls · {result.meta.n_respondents} respondents · {result.meta.runtime_s}s
                  </span>
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="Cohort name to save…"
                    value={cohortName}
                    onChange={(e) => setCohortName(e.target.value)}
                    className="h-8 w-64"
                  />
                  <Button size="sm" variant="outline" onClick={onSave}>Save cohort</Button>
                </div>
              </CardHeader>
              <CardContent>
                <CohortDistributionPanel result={result} audience={audience} />
              </CardContent>
            </Card>

            <CohortRespondentTable rows={result.per_respondent} audience={audience} />

            <Card className="mt-6">
              <CardHeader className="pb-2"><CardTitle className="text-sm">Coverage & provenance</CardTitle></CardHeader>
              <CardContent className="text-sm text-slate-700 space-y-2">
                <div>Recalls scored: <strong>{result.coverage.n_recalls_total}</strong>
                  {' · '}with errors: <strong>{result.coverage.n_recalls_with_errors}</strong>
                  {' · '}distinct respondents: <strong>{result.coverage.n_distinct_respondents}</strong></div>
                {audience !== 'individual' && (
                  <details className="text-xs text-slate-600">
                    <summary className="cursor-pointer">Lens versions ({Object.keys(result.provenance.lens_versions).length})</summary>
                    <ul className="mt-2 space-y-1">
                      {Object.entries(result.provenance.lens_versions).map(([k, v]) => (
                        <li key={k}><span className="font-medium">{k}:</span> {v}</li>
                      ))}
                    </ul>
                    <div className="mt-2">Substrate: {result.provenance.platform_substrate}</div>
                  </details>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: 'ok' | 'warn' }) {
  return (
    <div className={`rounded border p-2 ${tone === 'warn' ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-white'}`}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-lg font-semibold tabular-nums">{value.toLocaleString()}</div>
    </div>
  );
}
