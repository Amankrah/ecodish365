/**
 * RecipeDecomposerModal — "Score a homemade dish" workflow (AI-MATCH-1 Phase 9).
 *
 * Modal triggered from each calculate page (HENI / HEFI / HSR / FCS / Environmental). User
 * enters a dish name + total mass; the backend's two-stage decomposer
 * (LLM proposes ingredients → CNFMatcher resolves each to a CNF FoodID with
 * confidence) returns a list of ingredients. User can edit masses, remove
 * ingredients, swap one ingredient (via AIEnhancedSearch), and finally
 * "Apply" — which calls the parent's `onApply` with the final list. The
 * parent then pushes those CNF FoodIDs into its own food picker and the
 * downstream HENI/HEFI/HSR/FCS/Environmental scoring path runs unchanged.
 *
 * Audience-aware: in researcher / policy mode the per-ingredient
 * resolution_confidence + the decomposer's audit trail are visible; in
 * individual mode they're hidden.
 */
'use client';

import { useEffect, useState } from 'react';
import {
  ChefHat, Loader2, X, AlertCircle, Plus, Minus, Check, Info, Sparkles,
} from 'lucide-react';
import {
  CNFApiService,
  type CNFDecomposedRecipe,
  type CNFRecipeIngredient,
} from '@/lib/api';
import { AIEnhancedSearch } from './AIEnhancedSearch';
import type { UserType } from './AudienceToggle';

interface RecipeDecomposerModalProps {
  open: boolean;
  onClose: () => void;
  /** Called with the final ingredient list when the user clicks "Apply". */
  onApply: (ingredients: Array<{ food_id: number; food_description: string; mass_g: number }>) => void;
  userType: UserType;
  /** Default dish-mass shown when the modal opens. */
  defaultMassG?: number;
  accent?: 'blue' | 'green' | 'purple' | 'amber';
}

const ACCENT: Record<NonNullable<RecipeDecomposerModalProps['accent']>, string> = {
  blue:   'bg-blue-600 hover:bg-blue-700',
  green:  'bg-green-600 hover:bg-green-700',
  purple: 'bg-purple-600 hover:bg-purple-700',
  amber:  'bg-amber-600 hover:bg-amber-700',
};

interface ApiError { status: number; message: string }

export function RecipeDecomposerModal({
  open,
  onClose,
  onApply,
  userType,
  defaultMassG = 250,
  accent = 'blue',
}: RecipeDecomposerModalProps) {
  const [dishName, setDishName]   = useState('');
  const [totalMass, setTotalMass] = useState(defaultMassG);
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState<CNFDecomposedRecipe | null>(null);
  const [error, setError]         = useState<ApiError | null>(null);
  // Editable copy of the ingredient list (so user can tweak before applying)
  const [editIngs, setEditIngs]   = useState<CNFRecipeIngredient[]>([]);
  // Which ingredient row is in "swap" mode (showing AIEnhancedSearch)
  const [swappingIdx, setSwappingIdx] = useState<number | null>(null);
  const [swapQuery, setSwapQuery]     = useState('');

  // Reset state when the modal opens fresh
  useEffect(() => {
    if (open) {
      setDishName('');
      setTotalMass(defaultMassG);
      setResult(null);
      setError(null);
      setEditIngs([]);
      setSwappingIdx(null);
      setSwapQuery('');
    }
  }, [open, defaultMassG]);

  async function handleDecompose() {
    if (!dishName.trim() || totalMass <= 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setEditIngs([]);
    setSwappingIdx(null);
    try {
      const r = await CNFApiService.decomposeRecipe(dishName, totalMass, { userType });
      setResult(r);
      setEditIngs(r.ingredients.map(i => ({ ...i })));     // mutable copy
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { message?: string; error?: string } } };
      setError({
        status: ax?.response?.status ?? 500,
        message: ax?.response?.data?.message
          || ax?.response?.data?.error
          || 'Recipe decomposition failed. Try a different dish name or use basic search.',
      });
    } finally {
      setLoading(false);
    }
  }

  function setIngMass(idx: number, mass: number) {
    setEditIngs(prev => prev.map((ing, i) =>
      i === idx ? { ...ing, mass_g: Math.max(0, mass) } : ing));
  }
  function removeIng(idx: number) {
    setEditIngs(prev => prev.filter((_, i) => i !== idx));
  }
  function swapIng(idx: number, picked: { food_id: number; food_description: string; food_group?: string }) {
    setEditIngs(prev => prev.map((ing, i) =>
      i === idx ? {
        ...ing,
        food_id:               picked.food_id,
        food_description:      picked.food_description,
        food_group:            picked.food_group || ing.food_group,
        rationale:             `user-swapped from "${ing.food_description}"`,
        resolution_confidence: null,   // unknown after user override
      } : ing));
    setSwappingIdx(null);
    setSwapQuery('');
  }

  function handleApply() {
    onApply(editIngs.map(i => ({
      food_id:          i.food_id,
      food_description: i.food_description,
      mass_g:           i.mass_g,
    })));
    onClose();
  }

  if (!open) return null;

  const editedTotal = editIngs.reduce((s, i) => s + (i.mass_g || 0), 0);
  const editedUnresolved = totalMass - editedTotal;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Recipe decomposer">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b">
          <div className="flex items-center gap-2">
            <ChefHat className="h-5 w-5 text-gray-700" aria-hidden="true" />
            <h2 className="text-lg font-semibold text-gray-900">Score a homemade dish</h2>
          </div>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-700" aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Inputs */}
          <p className="text-sm text-gray-600">
            Enter a dish name and total mass. The AI will decompose it into CNF ingredients
            you can edit before scoring.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-[1fr,140px] gap-3">
            <div>
              <label htmlFor="dish-name" className="block text-xs font-medium text-gray-700 mb-1">Dish name</label>
              <input
                id="dish-name"
                type="text"
                value={dishName}
                onChange={e => setDishName(e.target.value)}
                placeholder="e.g. spaghetti bolognese, chicken curry, peanut butter sandwich"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="dish-mass" className="block text-xs font-medium text-gray-700 mb-1">Total mass (g)</label>
              <input
                id="dish-mass"
                type="number"
                min="1"
                max="5000"
                step="10"
                value={totalMass}
                onChange={e => setTotalMass(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="button"
            onClick={handleDecompose}
            disabled={loading || !dishName.trim() || totalMass <= 0}
            className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium text-white
                        disabled:opacity-50 disabled:cursor-not-allowed ${ACCENT[accent]}`}
          >
            {loading
              ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              : <Sparkles className="h-4 w-4" aria-hidden="true" />}
            {loading ? 'Decomposing… (5-15 s)' : 'Decompose dish'}
          </button>

          {/* Error */}
          {error && (
            <div role="alert" className="flex items-start gap-2 p-3 rounded-md bg-red-50 border-l-4 border-red-400 text-sm">
              <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <div className="font-semibold text-red-900">
                  {error.status === 429 ? 'AI rate-limited'
                    : error.status === 503 ? 'AI temporarily unavailable'
                    : 'Decomposition failed'}
                </div>
                <div className="text-red-800 mt-0.5">{error.message}</div>
              </div>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="border rounded-lg p-3 bg-gray-50 space-y-3">
              {/* Headline */}
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    {result.matched
                      ? <Check className="h-4 w-4 text-green-600" aria-hidden="true" />
                      : <AlertCircle className="h-4 w-4 text-amber-600" aria-hidden="true" />}
                    <span className="text-sm font-semibold text-gray-900">
                      {result.matched
                        ? `Decomposed into ${result.ingredients.length} ingredients`
                        : `Partial / low-confidence decomposition`}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {result.timing_ms.toFixed(0)} ms · resolved {result.resolved_mass_g.toFixed(0)} g
                    · unresolved {result.unresolved_mass_g.toFixed(0)} g
                    {userType !== 'individual' && (
                      <> · decomposition confidence {(result.decomposition_confidence * 100).toFixed(0)}%</>
                    )}
                  </div>
                </div>
              </div>

              {/* Fallback message */}
              {!result.matched && result.fallback_reason && (
                <div className="text-xs bg-amber-50 border-l-4 border-amber-400 rounded p-2 text-amber-900">
                  <strong>Note:</strong> {result.fallback_reason}
                  {' — review the ingredient list below before applying.'}
                </div>
              )}

              {/* Editable ingredient list */}
              <ul className="space-y-2">
                {editIngs.map((ing, idx) => (
                  <li key={`${ing.food_id}-${idx}`} className="bg-white rounded border p-2 text-sm">
                    {swappingIdx === idx ? (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-600">
                          Swap <em>{ing.food_description}</em>:
                        </div>
                        <input
                          type="text"
                          autoFocus
                          value={swapQuery}
                          onChange={e => setSwapQuery(e.target.value)}
                          placeholder="Type a replacement ingredient…"
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded"
                        />
                        <AIEnhancedSearch
                          query={swapQuery}
                          userType={userType}
                          accent={accent}
                          onSelect={picked => swapIng(idx, picked)}
                        />
                        <button
                          type="button"
                          onClick={() => { setSwappingIdx(null); setSwapQuery(''); }}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 truncate">{ing.food_description}</div>
                          <div className="text-xs text-gray-500 truncate">
                            CNF {ing.food_id} · {ing.food_group}
                            {userType !== 'individual' && ing.resolution_confidence !== null && (
                              <> · resolution {(ing.resolution_confidence * 100).toFixed(0)}%</>
                            )}
                          </div>
                          {userType !== 'individual' && ing.rationale && (
                            <div className="text-[10px] italic text-gray-400 mt-0.5">{ing.rationale}</div>
                          )}
                        </div>
                        <input
                          type="number"
                          min="0"
                          step="1"
                          value={ing.mass_g}
                          onChange={e => setIngMass(idx, parseFloat(e.target.value) || 0)}
                          className="w-20 px-2 py-1 text-sm border border-gray-300 rounded text-right"
                          aria-label={`Mass for ${ing.food_description}`}
                        />
                        <span className="text-xs text-gray-500">g</span>
                        <button
                          type="button"
                          onClick={() => { setSwappingIdx(idx); setSwapQuery(ing.food_description); }}
                          className="text-xs px-2 py-1 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                          title="Swap for a different CNF food"
                        >
                          Swap
                        </button>
                        <button
                          type="button"
                          onClick={() => removeIng(idx)}
                          className="text-xs p-1 text-red-500 hover:text-red-700"
                          title="Remove this ingredient"
                          aria-label={`Remove ${ing.food_description}`}
                        >
                          <Minus className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>

              {/* Running totals */}
              <div className="text-xs text-gray-600 pt-2 border-t flex items-center justify-between">
                <span>
                  Sum: <strong>{editedTotal.toFixed(0)} g</strong> of {totalMass.toFixed(0)} g
                  {Math.abs(editedUnresolved) > totalMass * 0.05 && (
                    <span className="ml-2 text-amber-700">
                      ({editedUnresolved > 0 ? `+${editedUnresolved.toFixed(0)} g unresolved`
                        : `${editedUnresolved.toFixed(0)} g over target`})
                    </span>
                  )}
                </span>
              </div>

              {/* Researcher / policy audit trail */}
              {userType !== 'individual' && result.unresolved_ingredients_audit.length > 0 && (
                <details className="text-xs text-gray-600 pt-1 border-t">
                  <summary className="cursor-pointer hover:text-gray-900 flex items-center gap-1">
                    <Info className="h-3 w-3" aria-hidden="true" />
                    Dropped ingredients (Stage-2 audit)
                  </summary>
                  <ul className="mt-1 pl-4 space-y-1">
                    {result.unresolved_ingredients_audit.map((d, i) => (
                      <li key={i} className="italic">
                        {d.name} ({d.mass_g} g) — {d.reason}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-5 border-t bg-gray-50 rounded-b-xl">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleApply}
            disabled={editIngs.length === 0}
            className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium text-white
                        disabled:opacity-50 disabled:cursor-not-allowed ${ACCENT[accent]}`}
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Apply to calculator ({editIngs.length} ingredient{editIngs.length === 1 ? '' : 's'})
          </button>
        </div>
      </div>
    </div>
  );
}
