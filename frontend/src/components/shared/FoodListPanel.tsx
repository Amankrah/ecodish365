/**
 * FoodListPanel — collapsible, editable, transferable food-list widget that
 * renders at the top of every scorer page so the user can:
 *
 *   • see the current list (food_description + grams, with packaged-food
 *     provenance badge if applicable),
 *   • edit masses inline / remove individual foods,
 *   • export the list to a JSON file (food_id + mass_g) and re-import later,
 *   • transfer the same list to another scoring metric without re-decomposing
 *     (re-stashes via the same `recall_24h_payload` sessionStorage handoff
 *     the wizard uses, then navigates).
 *
 * The list lives in localStorage (`lib/activeFoodList`) so it survives page
 * reloads and cross-page navigation. The receiver hook
 * (`useRecall24hReceiver`) auto-saves to the active list whenever a recall
 * arrives, so the panel is populated transparently.
 *
 * Edits inside the panel emit via the optional `onChange` prop so the host
 * scorer page can keep its local `selectedFoods` state in sync.
 */
'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ChevronDown, ChevronUp, Download, Upload, Trash2, Send,
  Package, Info, AlertCircle, Check, Scale,
  Sparkles, Salad, Dna, Compass, Target,
} from 'lucide-react';
import { StarIcon, GlobeAltIcon, GlobeAmericasIcon } from '@heroicons/react/24/outline';
import type { ComponentType, SVGProps } from 'react';

type IconType = ComponentType<SVGProps<SVGSVGElement>>;
import {
  type ActiveFoodList,
  loadActiveFoodList,
  saveActiveFoodList,
  clearActiveFoodList,
  updateIngredientMass,
  removeIngredient,
  exportToJSONString,
  exportFilename,
  importFromJSONString,
  loadPanelCollapsed,
  savePanelCollapsed,
  ACTIVE_FOOD_LIST_EVENT,
} from '@/lib/activeFoodList';
import { provenanceLabel } from '@/lib/scorecardProvenance';
import { SourceBadge } from '@/components/shared/SourceBadge';
import type { UserType } from '@/components/shared/AudienceToggle';

export type ScoreTargetId =
  | 'hefi' | 'heni' | 'hsr' | 'fcs' | 'environmental' | 'dietary_pattern'
  | 'scorecard' | 'planetary';

interface ScoreTarget {
  id: ScoreTargetId;
  label: string;
  icon: IconType;
  path: string;
}

const SCORE_TARGETS: ScoreTarget[] = [
  { id: 'scorecard',       label: 'All scores',        icon: Sparkles,          path: '/scorecard' },
  { id: 'hefi',            label: 'Healthy eating',    icon: Salad,             path: '/hefi/calculate' },
  { id: 'heni',            label: 'Health impact',     icon: Dna,               path: '/heni/calculate' },
  { id: 'fcs',             label: 'Food Compass',      icon: Compass,           path: '/fcs/calculate' },
  { id: 'hsr',             label: 'Star rating',       icon: StarIcon,          path: '/hsr/calculate' },
  { id: 'environmental',   label: 'Environment',       icon: GlobeAltIcon,      path: '/environmental/calculate' },
  { id: 'dietary_pattern', label: 'Eating style',      icon: Target,            path: '/dietary-pattern' },
  { id: 'planetary',       label: 'Planet budget',     icon: GlobeAmericasIcon, path: '/planetary' },
];

const COMPACT_TRANSFER_IDS: ScoreTargetId[] = ['hefi', 'environmental', 'hsr'];

interface Props {
  /** The metric this page represents. The matching transfer button is
   *  rendered as the disabled "you're here" indicator. */
  currentTarget: ScoreTargetId;
  /** Called with the active list (or null if cleared) whenever it changes
   *  via this panel. Use it to keep the host page's local food state in sync.
   *  Also called once on mount with the loaded list (or null). */
  onChange?: (list: ActiveFoodList | null) => void;
  /** Scorecard: let user include/exclude foods from a scoring run without removing them. */
  selectable?: boolean;
  selectedFoodIds?: Set<number>;
  onSelectionChange?: (ids: Set<number>) => void;
  /** Scorecard layout: richer rows + compact metric transfers. */
  variant?: 'default' | 'scorecard';
  userType?: UserType;
  transferMode?: 'all' | 'compact' | 'hidden';
  /** Per-food kcal for portion (optional enrichment). */
  energyKcalByFoodId?: Record<number, number>;
}

export function FoodListPanel({
  currentTarget,
  onChange,
  selectable = false,
  selectedFoodIds,
  onSelectionChange,
  variant = 'default',
  userType = 'individual',
  transferMode = 'all',
  energyKcalByFoodId,
}: Props): JSX.Element | null {
  const [list, setList] = useState<ActiveFoodList | null>(() => null);
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [showAllTransfers, setShowAllTransfers] = useState(false);

  // Hydrate from localStorage after mount (SSR-safe).
  useEffect(() => {
    setList(loadActiveFoodList());
    setCollapsed(loadPanelCollapsed());
    setHydrated(true);
  }, []);

  // Listen for cross-component changes (other tabs / the receiver hook /
  // the wizard's handleRoute). The detail is the new list (or null).
  useEffect(() => {
    function handler(e: Event) {
      const ce = e as CustomEvent<ActiveFoodList | null>;
      setList(ce.detail ?? loadActiveFoodList());
    }
    window.addEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
    // Also listen to native storage event for cross-tab updates.
    function storageHandler(e: StorageEvent) {
      if (e.key === null || e.key.startsWith('active_food_list')) {
        setList(loadActiveFoodList());
      }
    }
    window.addEventListener('storage', storageHandler);
    return () => {
      window.removeEventListener(ACTIVE_FOOD_LIST_EVENT, handler);
      window.removeEventListener('storage', storageHandler);
    };
  }, []);

  // Notify parent whenever our local mirror changes. Including on first hydrate.
  useEffect(() => {
    if (!hydrated) return;
    onChange?.(list);
  // We intentionally don't depend on onChange identity (parents often pass
  // an inline callback) — call on every list change.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list, hydrated]);

  const totalMass = useMemo(
    () => list?.ingredients.reduce((s, i) => s + i.mass_g, 0) ?? 0,
    [list],
  );

  const selectedCount = useMemo(() => {
    if (!selectable || !selectedFoodIds || !list) return list?.ingredients.length ?? 0;
    return list.ingredients.filter(i => selectedFoodIds.has(i.food_id)).length;
  }, [selectable, selectedFoodIds, list]);

  const transferTargets = useMemo(() => {
    if (transferMode === 'hidden') return [];
    if (transferMode === 'compact' && !showAllTransfers) {
      return SCORE_TARGETS.filter(t => COMPACT_TRANSFER_IDS.includes(t.id) || t.id === currentTarget);
    }
    return SCORE_TARGETS;
  }, [transferMode, showAllTransfers, currentTarget]);

  const compareUrl = useMemo(() => {
    const ids = list?.ingredients.map(i => i.food_id).slice(0, 6) ?? [];
    return ids.length > 0 ? `/cnf/compare?foods=${ids.join(',')}` : '/cnf/compare';
  }, [list?.ingredients]);

  function toggleFoodSelection(food_id: number): void {
    if (!onSelectionChange || !selectedFoodIds) return;
    const next = new Set(selectedFoodIds);
    if (next.has(food_id)) next.delete(food_id);
    else next.add(food_id);
    onSelectionChange(next);
  }

  function selectAllFoods(): void {
    if (!onSelectionChange || !list) return;
    onSelectionChange(new Set(list.ingredients.map(i => i.food_id)));
  }

  function deselectAllFoods(): void {
    onSelectionChange?.(new Set());
  }

  function handleEditMass(food_id: number, mass_g: number): void {
    if (!Number.isFinite(mass_g) || mass_g < 0) return;
    const next = updateIngredientMass(food_id, mass_g);
    setList(next);
  }

  function handleRemove(food_id: number): void {
    const next = removeIngredient(food_id);
    setList(next);
  }

  function handleClear(): void {
    clearActiveFoodList();
    setList(null);
  }

  function handleExport(): void {
    if (!list) return;
    const text = exportToJSONString(list);
    const blob = new Blob([text], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exportFilename(list);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function handleImport(file: File): void {
    setImportError(null);
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const result = importFromJSONString(text);
      if (!result.ok || !result.list) {
        setImportError(result.error || 'Import failed.');
        return;
      }
      saveActiveFoodList(result.list);
      setList(result.list);
    };
    reader.onerror = () => setImportError('Could not read the file.');
    reader.readAsText(file);
  }

  function handleTransfer(target: ScoreTarget): void {
    if (!list) return;
    // Re-stash in the same shape `useRecall24hReceiver` expects so the
    // destination scorer page picks the foods up automatically.
    try {
      const payload = {
        source: 'recall_24h' as const,
        user_type: list.user_type ?? 'individual',
        captured_at: new Date().toISOString(),
        target: target.id,
        meals_meta: list.meals_meta ?? [],
        aggregated_daily_ingredients: list.ingredients.map(i => ({
          food_id: i.food_id,
          food_description: i.food_description,
          food_group: i.food_group ?? '',
          mass_g: i.mass_g,
          occasions: {},
        })),
        estimated_daily_kcal: list.estimated_daily_kcal ?? 0,
        ...(list.packaged_food ? { packaged_food: list.packaged_food } : {}),
        ...(list.packaged_food_occasions
          ? { packaged_food_occasions: list.packaged_food_occasions } : {}),
        ...(list.multi_day ? { multi_day: list.multi_day } : {}),
      };
      sessionStorage.setItem('recall_24h_payload', JSON.stringify(payload));
    } catch { /* private mode — destination still loads from active list */ }
    window.location.href = `${target.path}?from=recall24h`;
  }

  // Don't render anything until hydrated to avoid SSR/client mismatch.
  if (!hydrated) return null;

  if (!list || list.ingredients.length === 0) {
    return (
      <details
        className="border border-gray-200 bg-gray-50 rounded-lg"
        open={!collapsed}
        onToggle={e => {
          const open = (e.target as HTMLDetailsElement).open;
          setCollapsed(!open);
          savePanelCollapsed(!open);
        }}
      >
        <summary className="cursor-pointer list-none px-3 py-2 flex items-center gap-2 text-xs text-gray-700">
          <Info className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span className="flex-1">
            <strong>Saved food list</strong> is empty. Log a food diary day or scan a product to fill it,
            or import a list you saved before.
          </span>
          <ChevronDown className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
        </summary>
        <div className="border-t border-gray-200 px-3 py-2 flex items-center gap-2">
          <label className="cursor-pointer inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-700 border border-gray-300 bg-white rounded-md hover:bg-gray-50">
            <Upload className="h-3.5 w-3.5" aria-hidden="true" />
            Import JSON
            <input
              type="file"
              accept="application/json,.json"
              className="hidden"
              onChange={e => {
                const f = e.target.files?.[0];
                if (f) handleImport(f);
                e.target.value = '';
              }}
            />
          </label>
          {importError && (
            <span className="text-[11px] text-red-700 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" aria-hidden="true" />
              {importError}
            </span>
          )}
        </div>
      </details>
    );
  }

  const isPackaged = list?.source === 'packaged_food_inferred';
  const isMultiDay = !!list?.multi_day;
  const provLabel = list ? provenanceLabel(list) : '';

  const isOpen = hydrated ? !collapsed : true;

  const handlePanelToggle = (e: React.SyntheticEvent<HTMLDetailsElement>) => {
    const open = e.currentTarget.open;
    setCollapsed(!open);
    savePanelCollapsed(!open);
  };

  return (
    <details
      className={`border rounded-lg ${
        isPackaged ? 'border-amber-300 bg-amber-50/60'
        : isMultiDay ? 'border-violet-300 bg-violet-50/60'
        : 'border-blue-300 bg-blue-50/60'
      }`}
      open={isOpen}
      onToggle={handlePanelToggle}
    >
      <summary className="w-full flex items-center gap-2 px-3 py-2 text-left cursor-pointer list-none [&::-webkit-details-marker]:hidden">
        {isPackaged
          ? <Package className="h-4 w-4 text-amber-700 flex-shrink-0" aria-hidden="true" />
          : <Check className="h-4 w-4 text-blue-700 flex-shrink-0" aria-hidden="true" />}
        <span className="flex-1 text-sm font-semibold text-gray-900">
          Saved food list
          <span className="ml-2 text-xs font-normal text-gray-600">
            {list.ingredients.length} food{list.ingredients.length === 1 ? '' : 's'} ·
            {' '}{totalMass.toFixed(0)} g total
            {list.estimated_daily_kcal ? ` · ${list.estimated_daily_kcal.toFixed(0)} kcal` : ''}
            {' · '}<em>{provLabel}</em>
          </span>
        </span>
        {isOpen
          ? <ChevronUp className="h-4 w-4 text-gray-600" aria-hidden="true" />
          : <ChevronDown className="h-4 w-4 text-gray-600" aria-hidden="true" />}
      </summary>

      <div className="border-t px-3 py-3 space-y-3">
          {isPackaged && list.packaged_food && (
            <div className="text-[11px] text-amber-900 bg-amber-100/70 border border-amber-200 rounded px-2 py-1.5">
              <strong>{list.packaged_food.product_name ?? 'Packaged product'}</strong>
              {list.packaged_food.brand ? ` · ${list.packaged_food.brand}` : ''}
              {' · '}net {list.packaged_food.net_weight_g.toFixed(0)} g
              {' · '}inferred composition (confidence{' '}
              {(list.packaged_food.decomposition_confidence * 100).toFixed(0)}%).
              Scoring uses inferred masses, not measured intake.
            </div>
          )}

          {selectable && onSelectionChange && selectedFoodIds && (
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="text-gray-600">
                <strong>{selectedCount}</strong> of {list.ingredients.length} selected for scoring
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={selectAllFoods}
                  className="text-blue-700 hover:text-blue-900 font-medium"
                >
                  Select all
                </button>
                <button
                  type="button"
                  onClick={deselectAllFoods}
                  className="text-gray-600 hover:text-gray-900 font-medium"
                >
                  Deselect all
                </button>
              </div>
            </div>
          )}

          <ul className="divide-y divide-gray-200 bg-white border border-gray-200 rounded">
            {list.ingredients.map(ing => {
              const isSelected = !selectable || !selectedFoodIds || selectedFoodIds.has(ing.food_id);
              const kcalPer100 = energyKcalByFoodId?.[ing.food_id];
              const portionKcal = kcalPer100 != null ? (kcalPer100 * ing.mass_g) / 100 : null;
              return (
              <li
                key={ing.food_id}
                className={`flex items-center gap-2 px-2 py-2 text-xs ${!isSelected ? 'opacity-50 bg-gray-50' : ''}`}
              >
                {selectable && selectedFoodIds && onSelectionChange && (
                  <input
                    type="checkbox"
                    checked={selectedFoodIds.has(ing.food_id)}
                    onChange={() => toggleFoodSelection(ing.food_id)}
                    aria-label={`Include ${ing.food_description} in scoring`}
                    className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded flex-shrink-0"
                  />
                )}
                <span className="flex-1 min-w-0">
                  {variant === 'scorecard' ? (
                    <>
                      <span className="flex flex-wrap items-center gap-1.5">
                        <Link
                          href={`/cnf/foods/${ing.food_id}`}
                          className="text-gray-900 font-medium hover:text-blue-700 truncate max-w-full"
                          title={ing.food_description}
                        >
                          {ing.food_description}
                        </Link>
                        <SourceBadge foodId={ing.food_id} userType={userType} />
                      </span>
                      <span className="text-[10px] text-gray-500 flex flex-wrap gap-x-2">
                        {ing.food_group && <span>{ing.food_group}</span>}
                        {portionKcal != null && (
                          <span className="text-emerald-700 tabular-nums">≈ {portionKcal.toFixed(0)} kcal</span>
                        )}
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="text-gray-900 truncate block">{ing.food_description}</span>
                      <span className="text-[10px] text-gray-500">
                        Food ID {ing.food_id}{ing.food_group ? ` · ${ing.food_group}` : ''}
                      </span>
                    </>
                  )}
                </span>
                <label className="flex items-center gap-1 shrink-0">
                  <input
                    type="number"
                    min={0}
                    step={1}
                    value={ing.mass_g}
                    onChange={e => handleEditMass(ing.food_id, parseFloat(e.target.value) || 0)}
                    aria-label={`Mass in grams for ${ing.food_description}`}
                    title={`Mass in grams for ${ing.food_description}`}
                    className="w-20 px-1.5 py-0.5 border border-gray-300 rounded text-right"
                  />
                  <span className="text-gray-500">g</span>
                </label>
                <button
                  type="button"
                  onClick={() => handleRemove(ing.food_id)}
                  aria-label={`Remove ${ing.food_description}`}
                  title={`Remove ${ing.food_description}`}
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </li>
            );})}
          </ul>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleExport}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-700 border border-gray-300 bg-white rounded-md hover:bg-gray-50"
            >
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
              Export JSON
            </button>
            <label className="cursor-pointer inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-700 border border-gray-300 bg-white rounded-md hover:bg-gray-50">
              <Upload className="h-3.5 w-3.5" aria-hidden="true" />
              Replace from JSON
              <input
                type="file"
                accept="application/json,.json"
                className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0];
                  if (f) handleImport(f);
                  e.target.value = '';
                }}
              />
            </label>
            <button
              type="button"
              onClick={handleClear}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-red-700 border border-red-300 bg-white rounded-md hover:bg-red-50"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              Clear list
            </button>
            {variant === 'scorecard' && list.ingredients.length >= 2 && list.ingredients.length <= 6 && (
              <Link
                href={compareUrl}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-700 border border-blue-300 bg-white rounded-md hover:bg-blue-50"
              >
                <Scale className="h-3.5 w-3.5" aria-hidden="true" />
                Compare in catalogue
              </Link>
            )}
          </div>

          {importError && (
            <div role="alert" className="flex items-start gap-1.5 text-[11px] text-red-800 bg-red-50 border border-red-200 rounded px-2 py-1">
              <AlertCircle className="h-3 w-3 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <span>{importError}</span>
            </div>
          )}

          {transferMode !== 'hidden' && transferTargets.length > 0 && (
          <div>
            <p className="text-[11px] text-gray-600 mb-1">
              {transferMode === 'compact' ? 'Open in a dedicated scorer:' : 'Score this list with another metric:'}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {transferTargets.map(target => {
                const isCurrent = target.id === currentTarget;
                return (
                  <button
                    key={target.id}
                    type="button"
                    onClick={() => handleTransfer(target)}
                    disabled={isCurrent}
                    aria-label={`Send to ${target.label}`}
                    className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border ${
                      isCurrent
                        ? 'bg-gray-100 border-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-white border-blue-300 text-blue-800 hover:bg-blue-100'
                    }`}
                    title={isCurrent
                      ? `You are on the ${target.label} scorer`
                      : `Score this list with ${target.label}`}
                  >
                    <target.icon className="w-3.5 h-3.5" aria-hidden="true" />
                    <span>{target.label}</span>
                    {!isCurrent && <Send className="h-3 w-3" aria-hidden="true" />}
                    {isCurrent && <span className="text-[10px]">(current)</span>}
                  </button>
                );
              })}
              {transferMode === 'compact' && !showAllTransfers && (
                <button
                  type="button"
                  onClick={() => setShowAllTransfers(true)}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border border-gray-300 text-gray-700 bg-white hover:bg-gray-50"
                >
                  More metrics…
                </button>
              )}
            </div>
          </div>
          )}
        </div>
    </details>
  );
}
