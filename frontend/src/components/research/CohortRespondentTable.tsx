/**
 * CohortRespondentTable (PLATFORM-CODE-1.b, 2026-06-26).
 *
 * Client-side sortable + filterable + paginated table of per-respondent
 * scores. CSV export streams all rows (not just the visible page) so a
 * researcher can paste the results straight into their stats package.
 *
 * In `audience='individual'` mode the respondent_id column is replaced
 * with a per-row sequential alias so a participant who shares a screenshot
 * doesn't accidentally reveal their SEQN.
 */
'use client';

import React, { useMemo, useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { CohortRespondentScore } from '@/lib/api';

type Audience = 'individual' | 'researcher' | 'policy';

interface Props {
  rows: CohortRespondentScore[];
  audience?: Audience;
  pageSize?: number;
}

type SortKey =
  | 'respondent_id' | 'day_id'
  | 'hefi_total_score' | 'heni_minutes' | 'hsr_stars' | 'fcs_score'
  | 'env_gw_per_100kcal' | 'env_sustainability' | 'env_monetized_cost'
  | 'fped_unmatched_pct';

const COLUMNS: Array<{ key: SortKey; label: string; numeric: boolean }> = [
  { key: 'respondent_id',       label: 'Respondent',                numeric: false },
  { key: 'day_id',              label: 'Day',                       numeric: false },
  { key: 'hefi_total_score',    label: 'HEFI',                      numeric: true  },
  { key: 'heni_minutes',        label: 'HENI min',                  numeric: true  },
  { key: 'hsr_stars',           label: 'HSR ★',                     numeric: true  },
  { key: 'fcs_score',           label: 'FCS',                       numeric: true  },
  { key: 'env_gw_per_100kcal',  label: 'GW kg CO₂e / 100 kcal',     numeric: true  },
  { key: 'env_sustainability',  label: 'Sustainability',            numeric: true  },
  { key: 'env_monetized_cost',  label: '$ env cost / 100 kcal',     numeric: true  },
  { key: 'fped_unmatched_pct',  label: 'Unmatched %',               numeric: true  },
];

function fmtCell(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(2);
  return String(v);
}

function rowsToCSV(rows: CohortRespondentScore[]): string {
  const headers = [
    'respondent_id', 'day_id', 'n_foods', 'total_mass_g',
    'hefi_total_score', 'heni_minutes', 'hsr_stars', 'fcs_score',
    'env_gw_per_100kcal', 'env_sustainability', 'env_monetized_cost',
    'pattern_top', 'pattern_confidence', 'fped_unmatched_pct', 'errors',
  ];
  const escape = (v: unknown): string => {
    if (v === null || v === undefined) return '';
    const s = Array.isArray(v) ? v.join('; ') : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [headers.join(',')];
  for (const r of rows) {
    lines.push(headers.map(h => escape((r as unknown as Record<string, unknown>)[h])).join(','));
  }
  return lines.join('\n');
}

function triggerDownload(filename: string, csv: string) {
  if (typeof window === 'undefined') return;
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function CohortRespondentTable({ rows, audience = 'researcher', pageSize = 50 }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('respondent_id');
  const [sortAsc, setSortAsc] = useState(true);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(0);

  // Anonymise for the individual audience: deterministic alias by index.
  const display = useMemo(() => {
    if (audience !== 'individual') return rows;
    return rows.map((r, i) => ({ ...r, respondent_id: `subject_${String(i + 1).padStart(4, '0')}` }));
  }, [rows, audience]);

  const filtered = useMemo(() => {
    if (!filter.trim()) return display;
    const needle = filter.trim().toLowerCase();
    return display.filter(r =>
      r.respondent_id.toLowerCase().includes(needle)
      || r.day_id.toLowerCase().includes(needle)
      || (r.pattern_top ?? '').toLowerCase().includes(needle),
    );
  }, [display, filter]);

  const sorted = useMemo(() => {
    const out = [...filtered];
    out.sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[sortKey];
      const bv = (b as unknown as Record<string, unknown>)[sortKey];
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av - bv : bv - av;
      return sortAsc
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return out;
  }, [filtered, sortKey, sortAsc]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const visible = sorted.slice(safePage * pageSize, (safePage + 1) * pageSize);

  function toggleSort(k: SortKey) {
    if (k === sortKey) setSortAsc(!sortAsc);
    else { setSortKey(k); setSortAsc(true); }
  }

  return (
    <Card>
      <CardHeader className="pb-3 flex flex-row items-start justify-between gap-3 flex-wrap">
        <CardTitle className="text-base">
          Per-respondent scores
          <span className="ml-2 text-xs font-normal text-slate-500">
            {sorted.length.toLocaleString()} row{sorted.length === 1 ? '' : 's'}
            {filter && ` (filtered from ${rows.length.toLocaleString()})`}
          </span>
        </CardTitle>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Filter by respondent, day, or pattern…"
            value={filter}
            onChange={(e) => { setFilter(e.target.value); setPage(0); }}
            className="w-72 h-8"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => triggerDownload(`cohort_per_respondent_${Date.now()}.csv`, rowsToCSV(sorted))}
          >
            Export CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-700">
              <tr>
                {COLUMNS.map(col => (
                  <th
                    key={col.key}
                    className={`px-3 py-2 text-left cursor-pointer select-none whitespace-nowrap ${col.numeric ? 'text-right' : ''}`}
                    onClick={() => toggleSort(col.key)}
                  >
                    {col.label}
                    {sortKey === col.key && <span className="ml-1 text-xs">{sortAsc ? '▲' : '▼'}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((r, i) => (
                <tr key={`${r.respondent_id}-${r.day_id}-${i}`} className="border-t border-slate-100 hover:bg-slate-50">
                  {COLUMNS.map(col => (
                    <td
                      key={col.key}
                      className={`px-3 py-1.5 whitespace-nowrap ${col.numeric ? 'text-right tabular-nums' : ''}`}
                    >
                      {fmtCell((r as unknown as Record<string, unknown>)[col.key])}
                    </td>
                  ))}
                </tr>
              ))}
              {visible.length === 0 && (
                <tr><td colSpan={COLUMNS.length} className="px-3 py-6 text-center text-slate-500 italic">No rows match the current filter.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-100 px-3 py-2 text-sm text-slate-600">
            <div>Page {safePage + 1} of {totalPages}</div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>Previous</Button>
              <Button variant="outline" size="sm" disabled={safePage >= totalPages - 1} onClick={() => setPage(safePage + 1)}>Next</Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
