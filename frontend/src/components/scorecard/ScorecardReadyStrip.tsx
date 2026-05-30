'use client';

import { Sparkles, Info } from 'lucide-react';

interface ScorecardReadyStripProps {
  nFoods: number;
  nTotalFoods: number;
  totalMassG: number;
  dailyKcal?: number;
  isSmallSample: boolean;
  hasPartialSelection: boolean;
  onScore: () => void;
  scoring: boolean;
}

export function ScorecardReadyStrip({
  nFoods,
  nTotalFoods,
  totalMassG,
  dailyKcal,
  isSmallSample,
  hasPartialSelection,
  onScore,
  scoring,
}: ScorecardReadyStripProps) {
  if (nFoods === 0) return null;

  return (
    <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-start gap-2 min-w-0">
        <Sparkles className="h-5 w-5 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
        <div className="text-sm text-emerald-950">
          <strong>Ready to score</strong>
          {' · '}
          {hasPartialSelection
            ? `${nFoods} of ${nTotalFoods} foods selected`
            : `${nFoods} food${nFoods === 1 ? '' : 's'}`}
          {' · '}{totalMassG.toFixed(0)} g
          {typeof dailyKcal === 'number' && dailyKcal > 0 && ` · ~${dailyKcal.toFixed(0)} kcal`}
          {isSmallSample && (
            <span className="block text-xs text-emerald-800 mt-0.5">
              Small sample — treat results as a preview, not a full-day diagnosis.
            </span>
          )}
        </div>
      </div>
      <button
        type="button"
        onClick={onScore}
        disabled={scoring}
        className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 disabled:opacity-60 shrink-0"
      >
        <Sparkles className="h-4 w-4" aria-hidden="true" />
        {scoring ? 'Scoring…' : `Score ${hasPartialSelection ? 'selected' : 'all'}`}
      </button>
    </div>
  );
}

interface ScorecardStickyBarProps {
  visible: boolean;
  label: string;
  onScore: () => void;
  scoring: boolean;
  isStale: boolean;
  disabled: boolean;
}

export function ScorecardStickyBar({
  visible,
  label,
  onScore,
  scoring,
  isStale,
  disabled,
}: ScorecardStickyBarProps) {
  if (!visible) return null;

  return (
    <div className="fixed bottom-0 inset-x-0 z-40 border-t border-gray-200 bg-white/95 backdrop-blur px-4 py-3 shadow-lg">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-3">
        <p className="text-sm text-gray-700 truncate flex items-center gap-1.5">
          <Info className="h-4 w-4 text-gray-400 shrink-0" aria-hidden="true" />
          {label}
        </p>
        <button
          type="button"
          onClick={onScore}
          disabled={disabled || scoring}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500 shrink-0"
        >
          <Sparkles className={`h-4 w-4 ${scoring ? 'animate-pulse' : ''}`} aria-hidden="true" />
          {scoring ? 'Scoring…' : isStale ? 'Re-score' : label}
        </button>
      </div>
    </div>
  );
}
