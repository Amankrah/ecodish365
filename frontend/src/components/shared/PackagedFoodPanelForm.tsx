/**
 * PackagedFoodPanelForm — review-and-edit form for an extracted NF panel.
 *
 * Renders after the multimodal LLM returns a structured NFPanelExtraction.
 * Each field is editable; low-confidence fields get a yellow border; the
 * HSR category dropdown defaults to the LLM's guess (rationale shown as
 * tooltip) but the user has final say. On "Score with HSR" the parent
 * receives the (possibly-edited) panel + category for the
 * /api/hsr/calculate-from-panel/ call.
 *
 * Trust model (per user-confirmed spec): auto-extract → prefilled
 * editable form → user confirms → submit. The form NEVER silently
 * routes to scoring without the user clicking the submit button.
 */
'use client';

import { useMemo, useState } from 'react';
import type {
  NFPanelExtraction, NutrientBlock, ExtractedNumeric, HSRCategoryCode,
} from '@/lib/api';

interface Props {
  initial: NFPanelExtraction;
  busy?: boolean;
  onSubmit: (
    edited: NFPanelExtraction,
    category: HSRCategoryCode,
    consumedPortionGrams: number,
    fvnlPercent: number,
  ) => void;
  onReextract?: () => void;
  onCancel?: () => void;
}

// HSRAC v9 category labels per backend Category enum.
const CATEGORY_LABELS: Record<HSRCategoryCode, string> = {
  '1':  '1 — Beverage (non-dairy)',
  '1D': '1D — Dairy beverage',
  '2':  '2 — All other foods (most packaged products)',
  '2D': '2D — Dairy foods (yogurt, cheese, ice cream)',
  '3':  '3 — Fats / oils / nuts / seed butters',
  '3D': '3D — Dairy fats (butter, cream)',
};

// The HSR-critical nutrient fields, rendered first + always visible.
const PRIMARY_FIELDS: Array<{ key: keyof NutrientBlock; label: string; unit: string }> = [
  { key: 'energy_kcal',          label: 'Calories',         unit: 'kcal' },
  { key: 'energy_kj',            label: 'Energy',           unit: 'kJ'   },
  { key: 'fat_total_g',          label: 'Total Fat',        unit: 'g'    },
  { key: 'fat_sat_g',            label: 'Saturated Fat',    unit: 'g'    },
  { key: 'fat_trans_g',          label: 'Trans Fat',        unit: 'g'    },
  { key: 'sugars_total_g',       label: 'Total Sugars',     unit: 'g'    },
  { key: 'fibre_g',              label: 'Fibre',            unit: 'g'    },
  { key: 'protein_g',            label: 'Protein',          unit: 'g'    },
  { key: 'sodium_mg',            label: 'Sodium',           unit: 'mg'   },
];

// Less-frequently-needed fields, collapsible.
const SECONDARY_FIELDS: Array<{ key: keyof NutrientBlock; label: string; unit: string }> = [
  { key: 'carbohydrate_total_g', label: 'Total Carbohydrate', unit: 'g'  },
  { key: 'sugars_added_g',       label: 'Added Sugars',     unit: 'g'    },
  { key: 'cholesterol_mg',       label: 'Cholesterol',      unit: 'mg'   },
  { key: 'potassium_mg',         label: 'Potassium',        unit: 'mg'   },
  { key: 'calcium_mg',           label: 'Calcium',          unit: 'mg'   },
  { key: 'iron_mg',              label: 'Iron',             unit: 'mg'   },
];

function confidenceBorder(c: number): string {
  if (c >= 0.9) return 'border-emerald-300';
  if (c >= 0.7) return 'border-amber-400';
  return 'border-red-400';
}
function confidenceDot(c: number): string {
  if (c >= 0.9) return 'bg-emerald-500';
  if (c >= 0.7) return 'bg-amber-500';
  return 'bg-red-500';
}

export function PackagedFoodPanelForm({
  initial, busy, onSubmit, onReextract, onCancel,
}: Props): JSX.Element {
  // Deep-copy the initial so user edits don't mutate the caller's object.
  const [panel, setPanel] = useState<NFPanelExtraction>(
    () => JSON.parse(JSON.stringify(initial)) as NFPanelExtraction
  );
  const [category, setCategory] = useState<HSRCategoryCode>(
    initial.hsr_category_hint.guess || '2'
  );
  const [consumedPortionMode, setConsumedPortionMode] = useState<
    '0.5' | '1' | '2' | 'whole' | 'custom'
  >('1');
  const [customGrams, setCustomGrams] = useState<string>('');
  const [fvnlPercent, setFvnlPercent] = useState<string>('0');
  const [showSecondary, setShowSecondary] = useState(false);
  const [showCategoryRationale, setShowCategoryRationale] = useState(false);

  const servingGrams = useMemo(() => {
    const v = panel.serving_size.value;
    return typeof v === 'number' ? v : 0;
  }, [panel.serving_size.value]);

  const servingsPer = useMemo(() => {
    const v = panel.servings_per_container.value;
    return typeof v === 'number' && v > 0 ? v : 1;
  }, [panel.servings_per_container.value]);

  const consumedGrams = useMemo(() => {
    switch (consumedPortionMode) {
      case '0.5':   return servingGrams * 0.5;
      case '1':     return servingGrams;
      case '2':     return servingGrams * 2;
      case 'whole': return servingGrams * servingsPer;
      case 'custom': {
        const n = parseFloat(customGrams);
        return Number.isFinite(n) && n > 0 ? n : servingGrams;
      }
    }
  }, [consumedPortionMode, customGrams, servingGrams, servingsPer]);

  function setNumeric<K extends keyof NutrientBlock>(key: K, value: string) {
    setPanel(p => {
      const next = { ...p, per_serving: { ...p.per_serving } };
      const field = { ...next.per_serving[key] } as ExtractedNumeric;
      const n = value.trim() === '' ? null : parseFloat(value);
      field.value = (n !== null && Number.isFinite(n)) ? n : null;
      // Mark user-edited fields as confidence=1.0 — user override is authoritative.
      field.confidence = 1.0;
      next.per_serving[key] = field;
      return next;
    });
  }

  function setServingSize(value: string) {
    setPanel(p => {
      const n = value.trim() === '' ? null : parseFloat(value);
      return {
        ...p,
        serving_size: {
          ...p.serving_size,
          value: (n !== null && Number.isFinite(n)) ? n : null,
          confidence: 1.0,
        },
      };
    });
  }

  function setServingUnit(unit: string) {
    setPanel(p => ({
      ...p,
      serving_size: { ...p.serving_size, unit: unit || null, confidence: 1.0 },
    }));
  }

  function submit() {
    const fv = parseFloat(fvnlPercent);
    onSubmit(
      panel,
      category,
      consumedGrams,
      Number.isFinite(fv) ? Math.max(0, Math.min(100, fv)) : 0,
    );
  }

  return (
    <div className="space-y-4">
      {/* Product header — read-only display, no editing needed. */}
      <div className="text-sm text-gray-600">
        <span className="font-medium">
          {panel.product_name_visible.value || 'Unknown product'}
        </span>
        {panel.brand_visible.value && (
          <span> · {panel.brand_visible.value}</span>
        )}
        <span className="ml-2 text-xs text-gray-400">
          (panel: {panel.panel_format_detected}, language: {panel.language_detected})
        </span>
      </div>

      {/* Serving size + servings per container */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        <label className="block">
          <span className="text-gray-700 font-medium">Serving size</span>
          <div className="flex gap-1 mt-1">
            <input
              type="number" step="0.1"
              value={panel.serving_size.value ?? ''}
              onChange={e => setServingSize(e.target.value)}
              className={`flex-1 border rounded-md px-2 py-1 text-sm ${confidenceBorder(panel.serving_size.confidence)}`}
            />
            <select
              value={panel.serving_size.unit ?? 'g'}
              onChange={e => setServingUnit(e.target.value)}
              className="border border-gray-300 rounded-md px-2 py-1 text-sm"
            >
              <option value="g">g</option>
              <option value="ml">ml</option>
            </select>
          </div>
          {panel.serving_size.raw_text && (
            <span className="text-[10px] text-gray-500" title={panel.serving_size.raw_text}>
              read: &quot;{panel.serving_size.raw_text.slice(0, 40)}{panel.serving_size.raw_text.length > 40 ? '…' : ''}&quot;
            </span>
          )}
        </label>
        <label className="block">
          <span className="text-gray-700 font-medium">Servings per container</span>
          <input
            type="number" step="0.1"
            value={panel.servings_per_container.value ?? ''}
            onChange={e => {
              const n = parseFloat(e.target.value);
              setPanel(p => ({
                ...p,
                servings_per_container: {
                  ...p.servings_per_container,
                  value: Number.isFinite(n) ? n : null,
                  confidence: 1.0,
                },
              }));
            }}
            className={`mt-1 w-full border rounded-md px-2 py-1 text-sm ${confidenceBorder(panel.servings_per_container.confidence)}`}
          />
        </label>
        <label className="block">
          <span className="text-gray-700 font-medium">Net weight (optional)</span>
          <div className="flex gap-1 mt-1">
            <input
              type="number" step="1"
              value={panel.net_weight.value ?? ''}
              onChange={e => {
                const n = parseFloat(e.target.value);
                setPanel(p => ({
                  ...p,
                  net_weight: {
                    ...p.net_weight,
                    value: Number.isFinite(n) ? n : null,
                    confidence: 1.0,
                  },
                }));
              }}
              className={`flex-1 border rounded-md px-2 py-1 text-sm ${confidenceBorder(panel.net_weight.confidence)}`}
            />
            <select
              value={panel.net_weight.unit ?? 'g'}
              onChange={e => setPanel(p => ({
                ...p, net_weight: { ...p.net_weight, unit: e.target.value, confidence: 1.0 },
              }))}
              className="border border-gray-300 rounded-md px-2 py-1 text-sm"
            >
              <option value="g">g</option>
              <option value="ml">ml</option>
            </select>
          </div>
        </label>
      </div>

      {/* HSR category — pre-selected to LLM guess, with rationale + alts. */}
      <div className="border-t pt-3">
        <label className="block text-sm">
          <span className="text-gray-700 font-medium">HSR category (HSRAC v9)</span>
          <select
            value={category}
            onChange={e => setCategory(e.target.value as HSRCategoryCode)}
            className="mt-1 w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm"
          >
            {(Object.entries(CATEGORY_LABELS) as Array<[HSRCategoryCode, string]>).map(([code, label]) => (
              <option key={code} value={code}>{label}</option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="mt-1 text-xs text-blue-700 underline"
          onClick={() => setShowCategoryRationale(s => !s)}
        >
          {showCategoryRationale ? 'Hide' : 'Why this category?'}
        </button>
        {showCategoryRationale && (
          <div className="mt-1 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900 space-y-1">
            <p><strong>Suggested:</strong> {CATEGORY_LABELS[panel.hsr_category_hint.guess]} (confidence {(panel.hsr_category_hint.confidence * 100).toFixed(0)}%)</p>
            {panel.hsr_category_hint.rationale && <p>{panel.hsr_category_hint.rationale}</p>}
            {panel.hsr_category_hint.alternatives.length > 0 && (
              <div>
                <p className="font-medium">Alternatives considered:</p>
                <ul className="list-disc list-inside">
                  {panel.hsr_category_hint.alternatives.map((a, i) => (
                    <li key={i}>{CATEGORY_LABELS[a.category]}: {a.reason}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Per-serving nutrients — primary fields always visible. */}
      <div className="border-t pt-3">
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          Per-serving nutrients
          <span className="ml-2 text-xs text-gray-500 font-normal">
            (confidence dots: <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 align-middle"></span> high,{' '}
            <span className="inline-block w-2 h-2 rounded-full bg-amber-500 align-middle"></span> moderate,{' '}
            <span className="inline-block w-2 h-2 rounded-full bg-red-500 align-middle"></span> low — hover for raw text)
          </span>
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
          {PRIMARY_FIELDS.map(({ key, label, unit }) => {
            const f = panel.per_serving[key];
            return (
              <label key={key} className="block">
                <span className="flex items-center gap-1 text-gray-700">
                  <span className={`inline-block w-1.5 h-1.5 rounded-full ${confidenceDot(f.confidence)}`}
                        title={f.raw_text ? `read: "${f.raw_text}"` : `confidence ${(f.confidence * 100).toFixed(0)}%`} />
                  {label}
                </span>
                <div className="flex gap-1 mt-0.5">
                  <input
                    type="number" step="0.1"
                    value={f.value ?? ''}
                    onChange={e => setNumeric(key, e.target.value)}
                    className={`flex-1 border rounded px-1.5 py-0.5 text-sm ${confidenceBorder(f.confidence)}`}
                    title={f.raw_text || ''}
                  />
                  <span className="text-xs text-gray-500 self-center">{unit}</span>
                </div>
                {f.from_dv_percent && (
                  <span className="text-[10px] text-amber-700">⚠ from %DV</span>
                )}
                {f.from_kcal_conversion && (
                  <span className="text-[10px] text-amber-700">⚠ ×4.184 from kcal</span>
                )}
              </label>
            );
          })}
        </div>
        <button
          type="button"
          onClick={() => setShowSecondary(s => !s)}
          className="mt-2 text-xs text-blue-700 underline"
        >
          {showSecondary ? 'Hide' : 'Show'} secondary nutrients (carbs, cholesterol, micronutrients)
        </button>
        {showSecondary && (
          <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
            {SECONDARY_FIELDS.map(({ key, label, unit }) => {
              const f = panel.per_serving[key];
              return (
                <label key={key} className="block">
                  <span className="flex items-center gap-1 text-gray-700">
                    <span className={`inline-block w-1.5 h-1.5 rounded-full ${confidenceDot(f.confidence)}`} />
                    {label}
                  </span>
                  <div className="flex gap-1 mt-0.5">
                    <input
                      type="number" step="0.1"
                      value={f.value ?? ''}
                      onChange={e => setNumeric(key, e.target.value)}
                      className={`flex-1 border rounded px-1.5 py-0.5 text-sm ${confidenceBorder(f.confidence)}`}
                    />
                    <span className="text-xs text-gray-500 self-center">{unit}</span>
                  </div>
                </label>
              );
            })}
          </div>
        )}
      </div>

      {/* Consumed portion — does NOT affect HSR stars (those are per-100g)
          but is reported back as metadata for the "how much of your day"
          context that the result page renders. */}
      <div className="border-t pt-3">
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          Consumed portion
          <span className="ml-2 text-xs text-gray-500 font-normal">
            (HSR stars are per-100g regardless — this is informational)
          </span>
        </h3>
        <div className="flex flex-wrap gap-2 text-sm">
          {[
            { id: '0.5', label: '½ serving' },
            { id: '1',   label: '1 serving' },
            { id: '2',   label: '2 servings' },
            { id: 'whole', label: 'Whole container' },
            { id: 'custom', label: 'Custom (g)' },
          ].map(opt => (
            <button
              key={opt.id}
              type="button"
              onClick={() => setConsumedPortionMode(opt.id as typeof consumedPortionMode)}
              className={`px-2.5 py-1 rounded-md border text-xs ${
                consumedPortionMode === opt.id
                  ? 'bg-blue-600 text-white border-blue-700'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {opt.label}
            </button>
          ))}
          {consumedPortionMode === 'custom' && (
            <input
              type="number" step="1" min="0"
              value={customGrams}
              onChange={e => setCustomGrams(e.target.value)}
              placeholder="g"
              className="w-24 border border-gray-300 rounded-md px-2 py-1 text-sm"
            />
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          You will consume ≈ <strong>{consumedGrams.toFixed(0)}{panel.serving_size.unit || 'g'}</strong>.
        </p>
      </div>

      {/* FVNL — user-supplied since packaged-food panels don't disclose it.
          Optional; defaults 0 = treats product as having no
          fruits/vegetables/nuts/legumes content. */}
      <FvnlField
        productHints={[
          panel.product_name_visible.value || '',
          panel.brand_visible.value || '',
        ]}
        fvnlPercent={fvnlPercent}
        setFvnlPercent={setFvnlPercent}
      />

      {/* Action buttons (anchor for layout). */}
      <div className="border-t pt-3 flex flex-wrap gap-2 justify-end">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        {onReextract && (
          <button
            type="button"
            onClick={onReextract}
            disabled={busy}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            🔄 Re-extract
          </button>
        )}
        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Scoring…' : '✓ Score with HSR'}
        </button>
      </div>
    </div>
  );
}


// --- FVNL field with product-name-driven inline hint -----------------------

// Lookup table: substring → (display name, suggested low/high % range).
// Mirrors the backend fvnl_keywords map in packaged_food_views._build_result_notes.
// Frontend version fires BEFORE scoring so the user can self-correct upstream.
const FVNL_HINT_KEYWORDS: Array<[RegExp, { display: string; lo: number; hi: number }]> = [
  [/\btomate?\b|\btomato\b/i,  { display: 'tomato-based products', lo: 40, hi: 60 }],
  [/vegetable soup|minestrone|soupe.{0,5}l.gumes/i, { display: 'vegetable-based soups', lo: 40, hi: 70 }],
  [/lentil|bean\b|chickpea|pois chiche/i, { display: 'legume-based products', lo: 30, hi: 60 }],
  [/\bfruit\b/i,                { display: 'fruit-based products', lo: 50, hi: 95 }],
  [/salsa/i,                    { display: 'salsa / tomato-based', lo: 60, hi: 80 }],
  [/guacamole|avocad/i,         { display: 'avocado-based', lo: 70, hi: 90 }],
  [/hummus/i,                   { display: 'chickpea-based', lo: 50, hi: 70 }],
  [/pesto/i,                    { display: 'basil + nut based', lo: 40, hi: 60 }],
  [/almond|peanut|cashew|noix/i, { display: 'nut products', lo: 90, hi: 100 }],
];

interface FvnlFieldProps {
  productHints: string[];
  fvnlPercent: string;
  setFvnlPercent: (v: string) => void;
}

function FvnlField({ productHints, fvnlPercent, setFvnlPercent }: FvnlFieldProps): JSX.Element {
  const haystack = productHints.filter(Boolean).join(' ').toLowerCase();
  const hit = FVNL_HINT_KEYWORDS.find(([re]) => re.test(haystack));
  const current = parseFloat(fvnlPercent);
  const showHint = hit && (Number.isNaN(current) || current < hit[1].lo);

  return (
    <div className="border-t pt-3">
      <label className="block text-sm">
        <span className="text-gray-700 font-medium">
          % Fruit / Vegetable / Nut / Legume (FVNL) content (optional)
        </span>
        <input
          type="number" step="1" min="0" max="100"
          value={fvnlPercent}
          onChange={e => setFvnlPercent(e.target.value)}
          className="mt-1 w-full sm:w-32 border border-gray-300 rounded-md px-2 py-1 text-sm"
        />
        <span className="block text-xs text-gray-500 mt-1">
          HSR awards bonus points for FVNL. NF panels don&apos;t list this — your best estimate.
          Examples: 0% (cookies, sodas), 50% (vegetable soup), 95% (canned peaches).
        </span>
      </label>
      {showHint && hit && (
        <div className="mt-2 p-2.5 bg-amber-50 border border-amber-300 rounded-md text-xs text-amber-900 flex items-start gap-2">
          <span aria-hidden="true">💡</span>
          <div className="flex-1">
            <p>
              <strong>Likely too low for this product.</strong> The product name suggests{' '}
              {hit[1].display}, which typically have <strong>{hit[1].lo}–{hit[1].hi}%</strong>{' '}
              fruit / vegetable / nut / legume content. Setting FVNL too low can suppress the
              HSR star rating by 0.5–1.5 stars.
            </p>
            <button
              type="button"
              onClick={() => setFvnlPercent(String(Math.round((hit[1].lo + hit[1].hi) / 2)))}
              className="mt-1.5 px-2 py-0.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium rounded"
            >
              Use {Math.round((hit[1].lo + hit[1].hi) / 2)}% as starting estimate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
