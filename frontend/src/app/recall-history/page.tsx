/**
 * /recall-history — multi-day recall persistence + research export
 * (RECALL-HISTORY-1, 2026-05-24).
 *
 * Per-browser localStorage history of saved 24-h recall days. Users can:
 *   - View per-day pattern resemblance (cached, refreshed on demand).
 *   - Score an N-day average pattern (mass-weighted concatenation routed
 *     through the existing /dietary-pattern/classify endpoint with a
 *     meta_label that triggers the softened multi-day caveat backend-side).
 *   - Export full history as JSON (versioned, round-trip) or per-ingredient
 *     CSV (one row per (day, meal, food) tuple — pandas/R-friendly).
 *   - Import a previously exported JSON file (dedupe by date+label).
 *   - Clear all (typed-confirm gated).
 *
 * Storage: localStorage only. No backend persistence; no upload unless the
 * user explicitly routes a day to a scoring endpoint. Per-IP rate limit on
 * the classifier caps cost even when re-scoring many days.
 *
 * The N-day-average pattern is volume-weighted across days (not equal-per-
 * day) — see combineDays() in recallHistory.ts for the methodological note;
 * the receiving /dietary-pattern page surfaces this honestly via the
 * softened caveat.
 */
'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  BookOpen, Download, Upload, Trash2, Sparkles, RefreshCw,
  AlertTriangle, X, ChevronRight, Loader2,
} from 'lucide-react';
import {
  listSavedDays, deleteDay, clearAllHistory, combineDays,
  exportAsJSON, exportAsCSV, importFromJSON, downloadFile,
  updateCachedPattern, subscribe, type SavedRecallDay, type ImportResult,
} from '@/lib/recallHistory';
import { CNFApiService } from '@/lib/api';
import { RecallHistoryCard } from '@/components/shared/RecallHistoryCard';
import { FpedCohortPanel } from '@/components/shared/FpedCohortPanel';

// Number of pattern-classify requests we'll issue in parallel for the
// per-day timeline refresh. Picked to stay well under the per-IP 50/hr rate
// limit and let users with 20+ saved days refresh in a few seconds without
// fanning out 20 simultaneous classifier calls (each ~700 ms server-side).
const CLASSIFY_CONCURRENCY = 3;

// How long a cached pattern is considered fresh before we re-classify.
// Prototype library is read at classify time; if it shifts (rare —
// version-controlled JSON), 30 days catches it on the next page visit
// without forcing unnecessary refreshes for stable libraries.
const PATTERN_CACHE_TTL_DAYS = 30;

function isCachedPatternFresh(d: SavedRecallDay): boolean {
  if (!d.cached_pattern) return false;
  const ageMs = Date.now() - new Date(d.cached_pattern.cached_at).getTime();
  return ageMs < PATTERN_CACHE_TTL_DAYS * 24 * 60 * 60 * 1000;
}

interface RouteMultiDayPayload {
  source: 'recall_24h';
  user_type: SavedRecallDay['user_type'];
  captured_at: string;
  target: 'dietary_pattern';
  meals_meta: Array<{ occasion: string; dish_name: string; total_mass_g: number }>;
  aggregated_daily_ingredients: SavedRecallDay['aggregated_daily_ingredients'];
  estimated_daily_kcal: number;
  multi_day: {
    n_days: number;
    first_date: string;
    last_date: string;
    label: string;
    day_ids: string[];
  };
}

export default function RecallHistoryPage() {
  // The page is purely client-side (localStorage gates the whole experience),
  // so we ignore the server-render pass and let useEffect populate state on
  // mount. `hydrated` is the explicit gate the JSX uses.
  const [hydrated, setHydrated]   = useState(false);
  const [days, setDays]           = useState<SavedRecallDay[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [classifying, setClassifying] = useState<Set<string>>(new Set());
  const [importOpen, setImportOpen]   = useState(false);
  const [clearOpen,  setClearOpen]    = useState(false);
  const [importBusy, setImportBusy]   = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importText,   setImportText]   = useState('');
  const [clearConfirm, setClearConfirm] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- hydration + cross-tab sync ------------------------------------------

  const refresh = useCallback(() => {
    setDays(listSavedDays());
  }, []);

  useEffect(() => {
    refresh();
    setHydrated(true);
    const unsubscribe = subscribe(refresh);
    return unsubscribe;
  }, [refresh]);

  // Auto-clear toast after a few seconds so the page stays tidy.
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(t);
  }, [toast]);

  // --- derived ------------------------------------------------------------

  const selectedDays = useMemo(
    () => days.filter(d => selectedIds.has(d.id)),
    [days, selectedIds],
  );

  // Cohort food-group exposure operates on the selected days (or all days if none
  // selected): one recall per day, each its aggregated daily ingredients.
  const cohortTargetDays = selectedDays.length > 0 ? selectedDays : days;
  const cohortRecalls = useMemo(
    () => cohortTargetDays.map(d =>
      d.aggregated_daily_ingredients.map(i => ({ food_id: i.food_id, mass_g: i.mass_g }))),
    [cohortTargetDays],
  );
  const cohortUserType = cohortTargetDays[0]?.user_type ?? 'individual';

  const totalKcal = useMemo(
    () => days.reduce((s, d) => s + d.estimated_daily_kcal, 0),
    [days],
  );

  const dateRange = useMemo(() => {
    if (days.length === 0) return null;
    const sorted = [...days].map(d => d.date).sort();
    return { first: sorted[0], last: sorted[sorted.length - 1] };
  }, [days]);

  // Pattern distribution across all saved days (counts top patterns).
  const patternDist = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const d of days) {
      if (d.cached_pattern) {
        const p = d.cached_pattern.top_pattern;
        counts[p] = (counts[p] || 0) + 1;
      }
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [days]);

  const staleCount = useMemo(
    () => days.filter(d => !isCachedPatternFresh(d)).length,
    [days],
  );

  // --- selection helpers --------------------------------------------------

  function toggleSelect(id: string, checked: boolean) {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (checked) next.add(id); else next.delete(id);
      return next;
    });
  }

  function selectAll(checked: boolean) {
    setSelectedIds(checked ? new Set(days.map(d => d.id)) : new Set());
  }

  // --- per-day actions ----------------------------------------------------

  function handleDelete(id: string) {
    // No confirm for per-day delete — it's recoverable via import if the
    // user has an export, and the bulk Clear All is the destructive lever.
    deleteDay(id);
    refresh();
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    setToast('Day deleted.');
  }

  // --- bulk actions -------------------------------------------------------

  function handleScoreNDayAverage() {
    const target = selectedDays.length > 0 ? selectedDays : days;
    if (target.length === 0) return;
    if (target.length === 1) {
      // Single-day average is just the single day — route as a normal
      // single-day classify (no multi-day badge).
      const day = target[0];
      const payload = {
        source: 'recall_24h' as const,
        user_type: day.user_type,
        captured_at: new Date().toISOString(),
        target: 'dietary_pattern' as const,
        meals_meta: day.meals.map(m => ({
          occasion: m.occasion,
          dish_name: m.decomposition.dish_name,
          total_mass_g: m.decomposition.total_mass_g,
        })),
        aggregated_daily_ingredients: day.aggregated_daily_ingredients,
        estimated_daily_kcal: day.estimated_daily_kcal,
      };
      try { sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload)); } catch {}
      window.location.href = '/dietary-pattern?from=recall24h';
      return;
    }
    const sortedByDate = [...target].sort((a, b) => a.date.localeCompare(b.date));
    const first = sortedByDate[0].date;
    const last  = sortedByDate[sortedByDate.length - 1].date;
    const combined = combineDays(target);
    const kcal = target.reduce((s, d) => s + d.estimated_daily_kcal, 0);
    // Concatenate all meals across days for traceability — the
    // /dietary-pattern page doesn't use this except for display, but
    // preserving it round-trips cleanly if the user navigates back.
    const meals_meta = target.flatMap(d => d.meals.map(m => ({
      occasion: m.occasion,
      dish_name: m.decomposition.dish_name,
      total_mass_g: m.decomposition.total_mass_g,
    })));
    // Use the first day's user_type — they're typically the same; if not,
    // the receiver page can re-toggle. Researchers using mixed audiences
    // is an unusual case.
    const userType = target[0].user_type;
    const payload: RouteMultiDayPayload = {
      source: 'recall_24h',
      user_type: userType,
      captured_at: new Date().toISOString(),
      target: 'dietary_pattern',
      meals_meta,
      aggregated_daily_ingredients: combined,
      estimated_daily_kcal: kcal / target.length,  // mean per-day kcal
      multi_day: {
        n_days: target.length,
        first_date: first,
        last_date: last,
        label: `${target.length}-day average, ${first} to ${last}`,
        day_ids: target.map(d => d.id),
      },
    };
    try { sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload)); } catch {
      // sessionStorage may be unavailable; the dietary-pattern page will
      // show its empty state — acceptable graceful degradation.
    }
    window.location.href = '/dietary-pattern?from=recall24h';
  }

  function handleExportJSON() {
    if (days.length === 0) return;
    const content = exportAsJSON();
    const today = new Date().toISOString().slice(0, 10);
    downloadFile(content, `recall_history_${today}.json`, 'application/json');
    setToast(`Exported ${days.length} days as JSON.`);
  }

  function handleExportCSV() {
    if (days.length === 0) return;
    const content = exportAsCSV();
    const today = new Date().toISOString().slice(0, 10);
    downloadFile(content, `recall_history_${today}.csv`, 'text/csv;charset=utf-8');
    setToast(`Exported ${days.length} days as CSV (one row per ingredient).`);
  }

  // --- import dialog ------------------------------------------------------

  function handleImportRun() {
    setImportBusy(true);
    const result = importFromJSON(importText);
    setImportResult(result);
    setImportBusy(false);
    if (result.added > 0) refresh();
  }

  function handleFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setImportText(String(reader.result || ''));
    };
    reader.readAsText(file);
  }

  function resetImportDialog() {
    setImportOpen(false);
    setImportText('');
    setImportResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  // --- clear-all dialog ---------------------------------------------------

  function handleClearAll() {
    clearAllHistory();
    refresh();
    setSelectedIds(new Set());
    setClearOpen(false);
    setClearConfirm('');
    setToast('All history cleared.');
  }

  // --- per-day timeline classification ------------------------------------

  /** Re-classify every saved day whose cached_pattern is missing or stale.
   *  Capped to CLASSIFY_CONCURRENCY parallel requests to avoid bursting
   *  past the per-IP rate limit on the classifier endpoint. */
  const refreshTimeline = useCallback(async () => {
    const targets = days.filter(d => !isCachedPatternFresh(d));
    if (targets.length === 0) return;
    setClassifying(new Set(targets.map(d => d.id)));
    let cursor = 0;
    async function worker() {
      while (cursor < targets.length) {
        const my = cursor++;
        const day = targets[my];
        try {
          const foods = day.aggregated_daily_ingredients.map(i => ({
            food_id: i.food_id, mass_g: i.mass_g,
          }));
          const r = await CNFApiService.classifyDietaryPattern(foods, {
            userType: day.user_type, includeNarrative: false,
          });
          if (r.result.matched && r.result.top_pattern) {
            updateCachedPattern(day.id, {
              top_pattern: r.result.top_pattern,
              top_pattern_confidence: r.result.top_pattern_confidence,
              cached_at: new Date().toISOString(),
            });
          }
        } catch {
          // Per-day failure is non-fatal — the card surfaces "not yet
          // scored" and the user can retry. Don't block the rest of the
          // batch on a transient error.
        } finally {
          setClassifying(prev => {
            const next = new Set(prev);
            next.delete(day.id);
            return next;
          });
        }
      }
    }
    const workers = Array.from(
      { length: Math.min(CLASSIFY_CONCURRENCY, targets.length) },
      () => worker(),
    );
    await Promise.allSettled(workers);
    refresh();
  }, [days, refresh]);

  // --- render -------------------------------------------------------------

  if (!hydrated) {
    return (
      <main className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg border p-6 shadow-sm flex items-center gap-3 text-sm text-gray-700">
            <Loader2 className="h-5 w-5 animate-spin text-blue-700" aria-hidden="true" />
            Loading your recall history&hellip;
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-amber-100 p-3 rounded-lg">
              <BookOpen className="h-8 w-8 text-amber-800" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Recall history</h1>
              <p className="text-sm text-gray-600 mt-1">
                All your saved 24-h recall days. Stored only in this browser
                (4 MB cap, ~1000 days). Export as JSON / CSV for offline analysis
                or to transfer between devices.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Privacy: nothing leaves your browser unless you explicitly
                score a day or export a file. No accounts, no server-side
                storage.
              </p>
            </div>
          </div>
        </header>

        {/* Empty state */}
        {days.length === 0 && (
          <div className="bg-white rounded-lg border p-6 shadow-sm text-sm text-gray-700 space-y-3">
            <p className="font-medium text-gray-900">No recall days saved yet.</p>
            <ol className="list-decimal list-inside space-y-1 text-gray-600">
              <li>Go to the <a href="/recall-24h" className="text-blue-700 underline">24-h dietary recall wizard</a>.</li>
              <li>Log your day occasion-by-occasion.</li>
              <li>On Step 3 (Review), open <span className="font-medium">&ldquo;💾 Save this day&rdquo;</span> and click Save.</li>
              <li>Come back here to view, average, or export.</li>
            </ol>
            <div className="pt-2">
              <a
                href="/recall-24h"
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md"
              >
                Start a recall <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </a>
            </div>
            {/* Import-only path: a returning user with a previously exported
                JSON file should be able to restore even with zero saved days. */}
            <div className="pt-3 border-t">
              <button
                type="button"
                onClick={() => setImportOpen(true)}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium border border-gray-300 rounded-md"
              >
                <Upload className="h-4 w-4" aria-hidden="true" />
                Import from a previous export
              </button>
            </div>
          </div>
        )}

        {/* Summary + toolbar (visible only with ≥1 day) */}
        {days.length > 0 && (
          <>
            <section className="bg-white rounded-lg border p-4 shadow-sm space-y-3">
              <div className="text-sm text-gray-700">
                <strong>{days.length}</strong> saved day{days.length === 1 ? '' : 's'}
                {dateRange && (
                  <> &middot; <span className="text-gray-600">{dateRange.first} → {dateRange.last}</span></>
                )}
                {' '}&middot; total {totalKcal.toFixed(0)} kcal across the history
              </div>

              {/* Pattern timeline (≥1 cached pattern) */}
              {patternDist.length > 0 && (
                <div className="pt-2 border-t">
                  <p className="text-xs font-medium text-gray-700 mb-1.5">
                    Pattern distribution across {days.length} day{days.length === 1 ? '' : 's'}:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {patternDist.map(([p, n]) => (
                      <span
                        key={p}
                        className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-900 border border-blue-200"
                      >
                        {p} &times;{n}
                      </span>
                    ))}
                  </div>
                  {/* Confidence-band legend. The per-day card surfaces the
                      top-pattern pill with a high / moderate / low sub-pill;
                      this one-liner decodes what those bands mean so users
                      don't have to hover for the tooltip. */}
                  <p className="text-[11px] text-gray-500 mt-2">
                    Confidence bands on each day&rsquo;s pattern pill:{' '}
                    <span className="font-medium text-emerald-800">high</span> (top cosine ≥ 0.75, clear lead) &middot;{' '}
                    <span className="font-medium text-amber-800">moderate</span> (top cosine 0.60–0.75, or a runner-up within 0.05) &middot;{' '}
                    <span className="font-medium text-gray-700">low</span> (top cosine &lt; 0.60 — log more days). Hover the band for details.
                  </p>
                </div>
              )}

              {staleCount > 0 && (
                <div className="pt-2 border-t flex items-center justify-between gap-3">
                  <p className="text-xs text-gray-600">
                    {staleCount} day{staleCount === 1 ? '' : 's'} not yet scored
                    {' '}or with stale cached pattern (older than {PATTERN_CACHE_TTL_DAYS} days).
                  </p>
                  <button
                    type="button"
                    onClick={refreshTimeline}
                    disabled={classifying.size > 0}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium rounded-md"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${classifying.size > 0 ? 'animate-spin' : ''}`} aria-hidden="true" />
                    Refresh {staleCount} pattern{staleCount === 1 ? '' : 's'} ({staleCount}¢)
                  </button>
                </div>
              )}
            </section>

            {/* Bulk toolbar */}
            <section className="bg-white rounded-lg border p-4 shadow-sm space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <label className="inline-flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={selectedIds.size === days.length && days.length > 0}
                    onChange={e => selectAll(e.target.checked)}
                    className="h-4 w-4"
                  />
                  Select all
                </label>
                <span className="text-xs text-gray-500">
                  {selectedIds.size} of {days.length} selected
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleScoreNDayAverage}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md"
                >
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  📊 Score {selectedDays.length > 0
                    ? `${selectedDays.length}-day average`
                    : `${days.length}-day average (all)`}
                </button>
                <button
                  type="button"
                  onClick={handleExportJSON}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium border border-gray-300 rounded-md"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Export JSON
                </button>
                <button
                  type="button"
                  onClick={handleExportCSV}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium border border-gray-300 rounded-md"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Export CSV
                </button>
                <button
                  type="button"
                  onClick={() => setImportOpen(true)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium border border-gray-300 rounded-md"
                >
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  Import
                </button>
                <span className="flex-1" />
                <button
                  type="button"
                  onClick={() => setClearOpen(true)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-300 text-sm font-medium rounded-md"
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                  Clear all
                </button>
              </div>

              <p className="text-xs text-gray-500">
                Tip: select 2+ days then click <strong>Score N-day average</strong>{' '}
                to see the combined pattern across those days, with a softened
                multi-day caveat in place of the single-day disclaimer.
              </p>
            </section>

            {/* Food-group exposure across days (FPED cohort) */}
            <FpedCohortPanel recalls={cohortRecalls} userType={cohortUserType} />

            {/* Cards */}
            <section className="space-y-3">
              {days.map(d => (
                <RecallHistoryCard
                  key={d.id}
                  day={d}
                  selected={selectedIds.has(d.id)}
                  onSelectChange={chk => toggleSelect(d.id, chk)}
                  onDelete={() => handleDelete(d.id)}
                  classifying={classifying.has(d.id)}
                />
              ))}
            </section>
          </>
        )}

        {/* CSV-handling warning for researchers */}
        {days.length > 0 && (
          <aside className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <p>
              <strong>Research use:</strong> exported recall data may identify
              individuals. Handle per your IRB / data-handling protocol —
              don&rsquo;t email or upload to non-compliant cloud storage.
            </p>
          </aside>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-4 py-2 rounded-md shadow-lg"
        >
          {toast}
        </div>
      )}

      {/* Import dialog */}
      {importOpen && (
        <div
          role="dialog"
          aria-labelledby="import-dialog-title"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between p-4 border-b">
              <h2 id="import-dialog-title" className="text-lg font-semibold text-gray-900">
                Import recall history (JSON)
              </h2>
              <button
                type="button"
                onClick={resetImportDialog}
                aria-label="Close"
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <div className="p-4 space-y-3">
              <p className="text-sm text-gray-700">
                Paste a previously exported JSON, or pick a file. Days with the
                same date + label as an existing day are skipped (not overwritten).
              </p>
              <div>
                <label className="text-sm font-medium text-gray-800" htmlFor="import-file">
                  Pick a JSON file
                </label>
                <input
                  id="import-file"
                  ref={fileInputRef}
                  type="file"
                  accept="application/json,.json"
                  onChange={handleFilePicked}
                  className="block mt-1 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-800" htmlFor="import-textarea">
                  …or paste JSON
                </label>
                <textarea
                  id="import-textarea"
                  value={importText}
                  onChange={e => setImportText(e.target.value)}
                  rows={8}
                  spellCheck={false}
                  placeholder='{"version": 1, "exported_from": "ecodish365", "days": [...]}'
                  className="block mt-1 w-full font-mono text-xs border border-gray-300 rounded-md p-2"
                />
              </div>
              {importResult && (
                <div className={`p-3 rounded-md border text-sm ${
                  importResult.errors.length > 0
                    ? 'bg-red-50 border-red-300 text-red-900'
                    : 'bg-emerald-50 border-emerald-300 text-emerald-900'
                }`}>
                  <p className="font-medium">
                    Added {importResult.added}, skipped {importResult.skipped}.
                  </p>
                  {importResult.errors.length > 0 && (
                    <ul className="mt-1 list-disc list-inside text-xs">
                      {importResult.errors.slice(0, 5).map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                      {importResult.errors.length > 5 && (
                        <li>(+{importResult.errors.length - 5} more)</li>
                      )}
                    </ul>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 p-4 border-t">
              <button
                type="button"
                onClick={resetImportDialog}
                className="px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium border border-gray-300 rounded-md"
              >
                {importResult && importResult.added > 0 ? 'Done' : 'Cancel'}
              </button>
              <button
                type="button"
                onClick={handleImportRun}
                disabled={importBusy || importText.trim().length === 0}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-md"
              >
                {importBusy ? (
                  <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />Importing&hellip;</>
                ) : (
                  <><Upload className="h-4 w-4" aria-hidden="true" />Import</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear-all confirm */}
      {clearOpen && (
        <div
          role="dialog"
          aria-labelledby="clear-dialog-title"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-start justify-between p-4 border-b">
              <h2 id="clear-dialog-title" className="text-lg font-semibold text-red-900">
                Clear all recall history?
              </h2>
              <button
                type="button"
                onClick={() => { setClearOpen(false); setClearConfirm(''); }}
                aria-label="Close"
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <div className="p-4 space-y-3 text-sm">
              <p className="text-gray-800">
                This will permanently delete all <strong>{days.length}</strong>{' '}
                saved day{days.length === 1 ? '' : 's'} from this browser.
                You can&rsquo;t undo this. Consider <strong>Export JSON</strong> first.
              </p>
              <p className="text-gray-700">
                Type <code className="px-1 bg-gray-100 rounded">CLEAR</code> to enable the button:
              </p>
              <input
                type="text"
                value={clearConfirm}
                onChange={e => setClearConfirm(e.target.value)}
                placeholder="CLEAR"
                className="block w-full border border-gray-300 rounded-md p-2 text-sm"
              />
            </div>
            <div className="flex items-center justify-end gap-2 p-4 border-t">
              <button
                type="button"
                onClick={() => { setClearOpen(false); setClearConfirm(''); }}
                className="px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-800 text-sm font-medium border border-gray-300 rounded-md"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleClearAll}
                disabled={clearConfirm !== 'CLEAR'}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md"
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
                Clear all
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
