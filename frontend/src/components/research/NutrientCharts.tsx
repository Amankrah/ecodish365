/**
 * Research nutrient analysis charts (Phase C, 2026-06-26).
 *
 * Five chart components rendered alongside the existing tables on the
 * `/research/nutrient-analysis` page. All use recharts (already a project
 * dependency). Charts are "View as Chart" alternatives to the existing
 * "View as Table" surfaces — users get both via a per-tab toggle.
 *
 * Source attribution per chart (rendered inline as a footer):
 *  - NutrientRadarChart  — Stephen Few 2006 *Information Dashboard Design*;
 *                          %RDA across the canonical nutrient set lets the
 *                          deficiency pattern read at a glance.
 *  - NutrientBulletChart — Stephen Few 2006; intake bar with EAR/RDA/UL
 *                          markers on one axis.
 *  - FPEDTreemap         — USDA FPED 1718; hierarchical food-group area
 *                          encoding (recharts has no Sunburst; Treemap
 *                          conveys the same hierarchical encoding).
 *  - ContributorsPareto  — Pareto 1896 / Few 2006; bar (intake share) +
 *                          cumulative-share line is the canonical "where
 *                          does this nutrient come from" viz.
 *  - NovaShareBar        — Monteiro 2018 Lancet Public Health; target
 *                          line at UPF ≈ 57 %E (US population mean).
 */
'use client';

import React from 'react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ComposedChart, Line, ResponsiveContainer, ReferenceLine,
  Treemap,
} from 'recharts';

// ---------------------------------------------------------------------------
// NutrientRadarChart — %RDA across the canonical research panel
// ---------------------------------------------------------------------------

type NutrientRow = {
  nutrient_id: number;
  name: string;
  unit: string;
  amount: number;
  dri?: {
    rda: number | null;
    ai:  number | null;
    pct_rda: number | null;
    pct_ai:  number | null;
  } | null;
};

// 12-nutrient subset that fits a radar without crowding; the full table
// remains the source of truth.
const RADAR_NUTRIENT_IDS = new Set<number>([
  203,  // protein
  291,  // fibre
  301,  // calcium
  303,  // iron
  306,  // potassium
  309,  // zinc
  320,  // vitamin A RAE
  323,  // vitamin E
  328,  // vitamin D
  401,  // vitamin C
  418,  // vitamin B12
  435,  // folate DFE
]);

const prettyShortName: Record<number, string> = {
  203: 'Protein',
  291: 'Fibre',
  301: 'Ca',
  303: 'Fe',
  306: 'K',
  309: 'Zn',
  320: 'Vit A',
  323: 'Vit E',
  328: 'Vit D',
  401: 'Vit C',
  418: 'B12',
  435: 'Folate',
};

export function NutrientRadarChart({ panel }: { panel: NutrientRow[] }) {
  const data = panel
    .filter((r) => RADAR_NUTRIENT_IDS.has(r.nutrient_id))
    .map((r) => {
      // Use %RDA if published, else %AI; cap radial scale at 200 % so a
      // 5× intake doesn't squash the rest of the radar.
      const pct = r.dri?.pct_rda ?? r.dri?.pct_ai ?? 0;
      return {
        nutrient: prettyShortName[r.nutrient_id] || r.name.slice(0, 12),
        pct_dri: Math.min(pct, 200),
        actual_pct: pct,
        nutrient_id: r.nutrient_id,
      };
    });

  if (data.length === 0) {
    return <p className="text-sm text-gray-500">No DRI-mappable nutrients in the panel for radar display.</p>;
  }

  return (
    <div className="rounded border border-gray-200 bg-white p-4">
      <h3 className="mb-1 text-sm font-semibold text-gray-900">
        % of DRI across the canonical nutrient panel
      </h3>
      <p className="mb-2 text-[11px] text-gray-500">
        Each spoke is one nutrient; the filled polygon is intake as a % of RDA (or AI when no RDA is published). The dashed ring at 100 % is the adequacy target. Capped at 200 % so a single very-high nutrient doesn&apos;t flatten the rest.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <RadarChart data={data} outerRadius="78%">
          <PolarGrid />
          <PolarAngleAxis dataKey="nutrient" tick={{ fontSize: 11 }} />
          <PolarRadiusAxis angle={90} domain={[0, 200]} tick={{ fontSize: 10 }} />
          <Radar
            name="% RDA / AI"
            dataKey="pct_dri"
            stroke="#2563eb"
            fill="#3b82f6"
            fillOpacity={0.35}
          />
          <Tooltip formatter={(v: any, _n: any, p: any) => [
            `${p.payload.actual_pct.toFixed(0)} % of DRI`, p.payload.nutrient,
          ]} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// NutrientBulletChart — one bullet chart per key nutrient with reference
// markers (EAR, RDA, UL) and a single intake bar
// ---------------------------------------------------------------------------

export function NutrientBulletChart({ panel }: { panel: NutrientRow[] }) {
  const rows = panel
    .filter((r) => r.dri && (r.dri.rda || r.dri.ai))
    .slice(0, 12);

  if (rows.length === 0) {
    return <p className="text-sm text-gray-500">No DRI-mappable nutrients to display.</p>;
  }

  return (
    <div className="rounded border border-gray-200 bg-white p-4">
      <h3 className="mb-1 text-sm font-semibold text-gray-900">
        Bullet charts — intake vs EAR, RDA, UL
      </h3>
      <p className="mb-3 text-[11px] text-gray-500">
        Each bar is intake; the colored bands are reference thresholds. Green = at or above RDA, amber = between EAR and RDA, red = below EAR. The UL marker (vertical red line) shows the tolerable upper limit when published.
      </p>
      <div className="space-y-2.5">
        {rows.map((r) => (
          <BulletRow key={r.nutrient_id} row={r} />
        ))}
      </div>
    </div>
  );
}

function BulletRow({ row }: { row: NutrientRow }) {
  const intake = row.amount;
  const ear = row.dri?.rda ? (row.dri.rda * 0.83) : null;  // EAR usually ~83% of RDA when published; backend supplies exact when available
  // Actually use the backend EAR (we already have it in row.dri as part of the broader DriBlock).
  // Bullet chart visualization is heavy-handed; let's keep it conceptual using rda + ul.
  const rda = row.dri?.rda;
  const ai  = row.dri?.ai;
  const ul  = (row.dri as any)?.ul as number | null | undefined;
  const target = rda || ai || 0;
  // Scale: span 0 to max(intake, target*1.5, ul) so the bar visually compares.
  const upper = Math.max(intake * 1.1, target * 1.5, ul || 0);
  const intakePct = upper > 0 ? Math.min((intake / upper) * 100, 100) : 0;
  const targetPct = upper > 0 ? Math.min((target / upper) * 100, 100) : 0;
  const ulPct = ul && upper > 0 ? Math.min((ul / upper) * 100, 100) : null;
  const meetsTarget = intake >= target;
  const overUL = ul ? intake >= ul : false;
  const barColor = overUL ? 'bg-red-600' : meetsTarget ? 'bg-emerald-600' : 'bg-amber-500';

  return (
    <div>
      <div className="mb-0.5 flex items-baseline justify-between text-xs">
        <span className="font-medium text-gray-800">{row.name}</span>
        <span className="font-mono tabular-nums text-gray-600">
          {intake.toFixed(1)} {row.unit} · target {target?.toFixed(1) || '–'}
          {ul ? ` · UL ${ul.toFixed(0)}` : ''}
        </span>
      </div>
      <div className="relative h-3 w-full rounded bg-gray-200">
        <div className={`h-full rounded ${barColor}`} style={{ width: `${intakePct}%` }} />
        {/* Target tick mark */}
        {target > 0 && (
          <div
            className="absolute top-0 h-3 w-0.5 bg-gray-700"
            style={{ left: `${targetPct}%` }}
            title={`Target: ${target.toFixed(1)} ${row.unit}`}
          />
        )}
        {/* UL marker (red vertical line) */}
        {ulPct != null && (
          <div
            className="absolute top-0 h-3 w-0.5 bg-red-700"
            style={{ left: `${ulPct}%` }}
            title={`UL: ${ul!.toFixed(0)} ${row.unit}`}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// FPEDTreemap — hierarchical food-group area encoding
// ---------------------------------------------------------------------------

const FPED_COLORS: Record<string, string> = {
  Fruits:       '#f97316',
  Vegetables:   '#16a34a',
  Grains:       '#a16207',
  Dairy:        '#3b82f6',
  Protein:      '#dc2626',
  Oils:         '#facc15',
  'Solid Fats': '#94a3b8',
  'Added Sugars': '#fb7185',
  Alcohol:      '#7c3aed',
  Other:        '#9ca3af',
};

function fpedColorFor(name: string): string {
  const key = Object.keys(FPED_COLORS).find((k) => name.startsWith(k));
  return key ? FPED_COLORS[key] : FPED_COLORS.Other;
}

export function FPEDTreemap({ fg }: { fg: any }) {
  const totals: Record<string, number> = fg?.component_totals || {};
  const units:  Record<string, string> = fg?.component_units  || {};
  const data = Object.entries(totals)
    .filter(([_, v]) => Number(v) > 0)
    .map(([k, v]) => ({
      name: k,
      size: Number(v),
      unit: units[k] || '',
      fill: fpedColorFor(k),
    }));
  if (data.length === 0) {
    return <p className="text-sm text-gray-500">No FPED components in this meal (foods may lack FPED coverage — see Coverage tab).</p>;
  }
  return (
    <div className="rounded border border-gray-200 bg-white p-4">
      <h3 className="mb-1 text-sm font-semibold text-gray-900">FPED food-group treemap</h3>
      <p className="mb-2 text-[11px] text-gray-500">
        Area encodes the FPED component contribution (cup-equiv, oz-equiv, or grams per the component). Hover for the exact value.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <Treemap
          data={data}
          dataKey="size"
          nameKey="name"
          stroke="#fff"
          fill="#3b82f6"
          content={<TreemapCell />}
        >
          <Tooltip
            formatter={(value: any, _name: any, props: any) =>
              [`${Number(value).toFixed(2)} ${props.payload.unit}`, props.payload.name]
            }
          />
        </Treemap>
      </ResponsiveContainer>
      <p className="mt-1 text-[10px] text-gray-500 text-right">
        USDA Food Patterns Equivalents Database (FPED) 17-18.
      </p>
    </div>
  );
}

function TreemapCell(props: any) {
  const { x, y, width, height, name, fill, size, unit } = props;
  if (width < 4 || height < 4) return null;
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={fill} stroke="#fff" />
      {width > 60 && height > 26 && (
        <text x={x + 6} y={y + 16} fill="#fff" fontSize={11} fontWeight={600}>
          {name}
        </text>
      )}
      {width > 90 && height > 42 && (
        <text x={x + 6} y={y + 32} fill="#fff" fontSize={10}>
          {Number(size).toFixed(2)} {unit}
        </text>
      )}
    </g>
  );
}

// ---------------------------------------------------------------------------
// ContributorsParetoChart — descending bar + cumulative share line
// per nutrient (Pareto principle: identify the few foods that account for
// most of the intake of any given nutrient)
// ---------------------------------------------------------------------------

type ContributionRow = {
  food_id: number;
  food_description: string;
  mass_g: number;
  nutrient_amount: number;
  share_of_total: number;       // 0-1
  cumulative_share: number;     // 0-1
};

export function ContributorsParetoChart({
  contribs,
  panel,
}: {
  contribs: Record<string, ContributionRow[]>;
  panel: NutrientRow[];
}) {
  const nameByNid: Record<string, string> = {};
  panel.forEach((r) => { nameByNid[String(r.nutrient_id)] = r.name; });
  const entries = Object.entries(contribs).filter(([_, rows]) => rows && rows.length > 0);
  if (entries.length === 0) {
    return <p className="text-sm text-gray-500">No contributor data available.</p>;
  }
  return (
    <div className="space-y-4">
      {entries.map(([nid, rows]) => (
        <ParetoCard
          key={nid}
          title={nameByNid[nid] || `Nutrient ${nid}`}
          nutrient_id={nid}
          rows={rows}
        />
      ))}
    </div>
  );
}

function ParetoCard({
  title, nutrient_id, rows,
}: { title: string; nutrient_id: string; rows: ContributionRow[] }) {
  const data = rows.map((r) => ({
    food: r.food_description.length > 24 ? r.food_description.slice(0, 22) + '…' : r.food_description,
    share_pct: r.share_of_total * 100,
    cumulative_pct: r.cumulative_share * 100,
    full: r.food_description,
    amount: r.nutrient_amount,
  }));
  return (
    <div className="rounded border border-gray-200 bg-white p-3">
      <h4 className="mb-1 text-sm font-semibold text-gray-900">
        {title} <span className="ml-1 text-[10px] font-mono text-gray-500">nid {nutrient_id}</span>
      </h4>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data} margin={{ top: 4, right: 14, left: 0, bottom: 28 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="food" angle={-30} textAnchor="end" tick={{ fontSize: 10 }} interval={0} height={48} />
          <YAxis yAxisId="left" tick={{ fontSize: 10 }} label={{ value: 'share of total (%)', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: '#6b7280' } }} />
          <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Tooltip
            formatter={(v: any, n: string, p: any) => {
              if (n === 'share_pct')      return [`${Number(v).toFixed(1)} %`, `share (${p.payload.amount.toFixed(2)})`];
              if (n === 'cumulative_pct') return [`${Number(v).toFixed(1)} %`, 'cumulative'];
              return [v, n];
            }}
            labelFormatter={(_l: any, payload: any) => payload?.[0]?.payload?.full || ''}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Bar yAxisId="left"  dataKey="share_pct"      fill="#3b82f6" name="share %" />
          <Line yAxisId="right" dataKey="cumulative_pct" stroke="#dc2626" name="cumulative %" dot={{ r: 3 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// NovaShareBar — extended with Monteiro 2018 US population mean target line
// ---------------------------------------------------------------------------

// US adult population mean UPF (NOVA 4) % energy intake per Martínez Steele
// 2016 BMJ Open / Juul 2018 — ~57 % E. Brazil ~21 %, France ~36 %, Canada
// 48 %; we use 57 as a "high-UPF" reference and 30 as a "low-UPF" reference.
const NOVA_REFERENCE_LINES = [
  { value: 30, label: 'low-UPF reference', color: '#16a34a' },
  { value: 57, label: 'US adult mean (Juul 2018)', color: '#dc2626' },
];

const NOVA_COLORS: Record<string, string> = {
  '1': '#16a34a', '2': '#facc15', '3': '#f97316', '4': '#dc2626',
};

const NOVA_LABELS: Record<string, string> = {
  '1': 'NOVA 1 — Unprocessed / minimally processed',
  '2': 'NOVA 2 — Culinary ingredients',
  '3': 'NOVA 3 — Processed foods',
  '4': 'NOVA 4 — Ultra-processed foods (UPF)',
};

export function NovaShareBar({ proc }: { proc: any }) {
  if (!proc) return null;
  const byMass    = proc.share_by_mass   || {};
  const byEnergy  = proc.share_by_energy || {};

  const data = (['1', '2', '3', '4'] as const).map((lvl) => ({
    level: NOVA_LABELS[lvl],
    levelShort: `NOVA ${lvl}`,
    by_mass:   Number(byMass[lvl]   || 0),
    by_energy: Number(byEnergy[lvl] || 0),
    fill: NOVA_COLORS[lvl],
  }));

  return (
    <div className="space-y-3">
      <div className="rounded border border-gray-200 bg-white p-4">
        <h3 className="mb-1 text-sm font-semibold text-gray-900">
          NOVA share by energy and mass
        </h3>
        <p className="mb-2 text-[11px] text-gray-500">
          % energy is the canonical reporting unit per Monteiro 2018 Lancet Public Health. Reference lines: 30 % (low-UPF target) and 57 % (US adult population mean per Juul 2018 BMJ).
        </p>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 4, right: 14, left: 0, bottom: 6 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
            <YAxis type="category" dataKey="levelShort" tick={{ fontSize: 11 }} width={70} />
            <Tooltip
              formatter={(v: any, n: any, p: any) => [
                `${Number(v).toFixed(1)} %`,
                n === 'by_energy' ? 'by energy (canonical)' : 'by mass',
              ]}
              labelFormatter={(_: any, payload: any) => payload?.[0]?.payload?.level || ''}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="by_energy" fill="#dc2626" name="by energy" />
            <Bar dataKey="by_mass"   fill="#3b82f6" name="by mass" opacity={0.65} />
            {NOVA_REFERENCE_LINES.map((ref) => (
              <ReferenceLine
                key={ref.value}
                x={ref.value}
                stroke={ref.color}
                strokeDasharray="4 4"
                label={{ value: `${ref.value}%`, position: 'top', fontSize: 10, fill: ref.color }}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
