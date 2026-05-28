/**
 * Modal editor for a saved 24-h recall day (ingredients, date, label).
 */
'use client';

import { useState } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import type { SavedRecallDay } from '@/lib/recallHistory';
import { updateDayFromEdit, QuotaExceededError } from '@/lib/recallHistory';
import { RecallIngredientPicker } from '@/components/shared/RecallIngredientPicker';
import { SourceFilter, type SourceChoice } from '@/components/shared/SourceFilter';
import { aggregatedToDirect, type RecallDirectIngredient } from '@/lib/recallDirectFood';

interface RecallDayEditModalProps {
  day: SavedRecallDay;
  onClose: () => void;
  onSaved: (updated: SavedRecallDay) => void;
}

export function RecallDayEditModal({ day, onClose, onSaved }: RecallDayEditModalProps): JSX.Element {
  const [date, setDate] = useState(day.date);
  const [label, setLabel] = useState(day.label);
  const [ingredients, setIngredients] = useState<RecallDirectIngredient[]>(
    () => aggregatedToDirect(day.aggregated_daily_ingredients),
  );
  const [source, setSource] = useState<SourceChoice>('both');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalMass = ingredients.reduce((s, i) => s + i.mass_g, 0);

  function handleSave() {
    if (ingredients.length === 0) {
      setError('Add at least one food before saving.');
      return;
    }
    if (ingredients.some(i => i.mass_g <= 0)) {
      setError('Every food needs a mass greater than 0 g.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const updated = updateDayFromEdit(day.id, { date, label, ingredients });
      if (!updated) {
        setError('This day could not be found — it may have been deleted.');
        setSaving(false);
        return;
      }
      onSaved(updated);
    } catch (e) {
      if (e instanceof QuotaExceededError) {
        setError('Recall history is full. Export and clear space before saving.');
      } else {
        setError((e as Error).message || 'Save failed.');
      }
      setSaving(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-labelledby="recall-edit-title"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between p-4 border-b sticky top-0 bg-white z-10">
          <div>
            <h2 id="recall-edit-title" className="text-lg font-semibold text-gray-900">
              Edit 24-h recall
            </h2>
            <p className="text-xs text-gray-600 mt-0.5">
              Search by name or use <strong>Find with AI</strong>. Pattern score clears until you re-view.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-[140px,1fr] gap-2 items-center">
            <label htmlFor="edit-recall-date" className="text-xs font-medium text-gray-700">
              Date
            </label>
            <input
              id="edit-recall-date"
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
            />
            <label htmlFor="edit-recall-label" className="text-xs font-medium text-gray-700">
              Label (optional)
            </label>
            <input
              id="edit-recall-label"
              type="text"
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="e.g. Day 1, weekday"
              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
            />
          </div>

          <SourceFilter source={source} onChange={setSource} accent="blue" />

          <RecallIngredientPicker
            userType={day.user_type}
            source={source}
            ingredients={ingredients}
            onChange={setIngredients}
            defaultMassG={100}
            searchPlaceholder="Search foods to add…"
            emptyHint="No foods in this day yet — search or use Find with AI."
          />

          <div className="text-xs text-gray-600 flex flex-wrap gap-x-3 gap-y-1">
            <span>{ingredients.length} foods</span>
            <span>{totalMass.toFixed(0)} g total</span>
            <span>{day.estimated_daily_kcal.toFixed(0)} kcal (from last save — re-score to refresh)</span>
          </div>

          {error && (
            <p role="alert" className="text-xs text-red-700 bg-red-50 border-l-4 border-red-400 px-2 py-1">
              {error}
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 p-4 border-t bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="px-3 py-1.5 text-sm text-gray-700 hover:text-gray-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md disabled:opacity-50"
          >
            {saving
              ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              : <Save className="h-4 w-4" aria-hidden="true" />}
            Save changes
          </button>
        </div>
      </div>
    </div>
  );
}
