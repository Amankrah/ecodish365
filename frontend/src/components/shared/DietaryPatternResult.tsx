/**
 * DietaryPatternResult — renders a top-3 dietary-pattern resemblance
 * vector for the user's day (DIET-PATTERN-1, 2026-05-24).
 *
 * Designed to be the body of `/dietary-pattern` page. Honest framing:
 * NEVER shows a single label ("you are Mediterranean") — always shows the
 * full top-3 resemblance vector as horizontal cosine bars, with the
 * mandatory single-day caveat front-and-centre per
 * DIETARY_PATTERN_JUSTIFICATION.md and the same Brassard 2022b discipline
 * the rest of the platform uses.
 *
 * Researcher / policy mode additionally shows the per-prototype literature
 * anchor + outcome-evidence-reused citation + the per-prototype
 * "distinctive foods you ate" breakdown.
 */
'use client';

import { useState } from 'react';
import { Target, Info, AlertCircle, Sparkles, CheckCircle } from 'lucide-react';
import type {
  PatternClassifyResponse,
  PatternResemblance,
} from '@/lib/api';
import type { UserType } from './AudienceToggle';
import { SourceBadge } from './SourceBadge';

interface DietaryPatternResultProps {
  data:     PatternClassifyResponse;
  userType: UserType;
}

const CONFIDENCE_LABEL: Record<'high' | 'moderate' | 'low', { label: string; cls: string }> = {
  high:     { label: 'High confidence',     cls: 'bg-green-100  text-green-800  border-green-200' },
  moderate: { label: 'Moderate confidence', cls: 'bg-blue-100   text-blue-800   border-blue-200'  },
  low:      { label: 'Low confidence',      cls: 'bg-amber-100  text-amber-800  border-amber-200' },
};

function ResemblanceBar({
  r,
  isTop,
  userType,
}: {
  r:        PatternResemblance;
  isTop:    boolean;
  userType: UserType;
}) {
  const [open, setOpen] = useState(false);
  const widthPct = Math.max(2, Math.round(r.cosine * 100));
  const barCls = isTop ? 'bg-blue-500' : 'bg-gray-400';
  return (
    <li className="space-y-1">
      <div className="flex items-center gap-2 text-sm">
        <span className={`font-medium ${isTop ? 'text-blue-900' : 'text-gray-800'} min-w-[140px]`}>
          {r.display_name}
        </span>
        <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 ${barCls} transition-all`}
            style={{ width: `${widthPct}%` }}
            aria-label={`${r.display_name} resemblance ${widthPct}%`}
          />
        </div>
        <span className="text-xs tabular-nums text-gray-600 min-w-[50px] text-right">
          {(r.cosine * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-xs text-gray-500 pl-[148px]">{r.individual_mode_blurb}</p>
      {userType !== 'individual' && (r.literature_anchor || r.distinctive_user_foods.length > 0) && (
        <div className="pl-[148px]">
          <button
            type="button"
            onClick={() => setOpen(v => !v)}
            className="text-xs text-blue-700 hover:text-blue-900 hover:underline"
          >
            {open ? '▾ Hide' : '▸ Show'} researcher detail
          </button>
          {open && (
            <div className="mt-1 p-2 bg-gray-50 border rounded text-xs space-y-1">
              {r.literature_anchor && (
                <div>
                  <strong>Literature anchor:</strong> {r.literature_anchor}
                </div>
              )}
              {r.outcome_evidence_reused && (
                <div>
                  <strong>Reused outcome evidence:</strong> {r.outcome_evidence_reused}
                </div>
              )}
              {r.distinctive_user_foods.length > 0 && (
                <div>
                  <strong>Distinctive foods in your day:</strong>
                  <ul className="mt-1 pl-4 list-disc">
                    {r.distinctive_user_foods.map(f => (
                      <li key={f.food_id} className="flex items-center gap-1">
                        <span>{f.mass_g.toFixed(0)}g — CNF/WAFCT FoodID {f.food_id}</span>
                        <SourceBadge foodId={f.food_id} userType={userType} />
                        <span className="text-gray-500">(contribution {f.contribution.toFixed(1)})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </li>
  );
}

export function DietaryPatternResult({ data, userType }: DietaryPatternResultProps) {
  const { result, explanations } = data;

  if (!result.matched) {
    return (
      <div className="p-4 rounded-md bg-amber-50 border-l-4 border-amber-400 text-sm">
        <div className="flex items-start gap-2">
          <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div>
            <p className="font-semibold text-amber-900">
              Couldn&rsquo;t score this day&rsquo;s pattern.
            </p>
            <p className="text-amber-800 mt-1">
              {result.fallback_reason || 'No foods were resolvable in the food-composition corpus.'}
              {result.n_foods_unresolved > 0 && (
                <> {result.n_foods_unresolved} food(s) were not in the embedding corpus.</>
              )}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const topRes = result.resemblances[0];
  const conf = CONFIDENCE_LABEL[result.top_pattern_confidence];

  return (
    <div className="space-y-6">
      {/* Headline card */}
      <div className="bg-white rounded-lg border p-5 shadow-sm space-y-3">
        <div className="flex items-start gap-3">
          <div className="bg-blue-100 p-2 rounded">
            <Target className="h-6 w-6 text-blue-700" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">
              Today&rsquo;s food choices most closely resemble{' '}
              <span className="text-blue-700">{topRes.display_name}</span>
            </h2>
            <div className="flex items-center gap-2 mt-1 text-sm">
              <span className={`px-2 py-0.5 rounded-full border text-xs font-medium ${conf.cls}`}>
                {conf.label}
              </span>
              <span className="text-gray-600">
                {(topRes.cosine * 100).toFixed(0)}% similarity
              </span>
              {result.co_leading.length > 0 && (
                <span className="text-gray-600">
                  · co-leading with {result.co_leading.join(', ')}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* LLM narrative if present */}
        {explanations.narrative && (
          <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded text-sm text-blue-900">
            <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
            <p>{explanations.narrative.message}</p>
          </div>
        )}

        {/* Mandatory caveat — ALWAYS visible */}
        {explanations.mandatory_caveat && (
          <div className="flex items-start gap-2 p-3 bg-amber-50 border-l-4 border-amber-400 text-sm">
            <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
            <div>
              <p className="font-semibold text-amber-900">{explanations.mandatory_caveat.title}</p>
              <p className="text-amber-800 mt-0.5">{explanations.mandatory_caveat.message}</p>
            </div>
          </div>
        )}

        {/* Day summary */}
        <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t">
          <span><CheckCircle className="inline h-3 w-3 mr-0.5" /> {result.n_foods} foods scored</span>
          {result.n_foods_unresolved > 0 && (
            <span className="text-amber-700">{result.n_foods_unresolved} skipped (not in corpus)</span>
          )}
          <span>· {result.total_mass_g.toFixed(0)} g total</span>
          <span>· {result.timing_ms.toFixed(0)} ms</span>
        </div>
      </div>

      {/* Full top-N resemblance vector */}
      <div className="bg-white rounded-lg border p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Pattern resemblance breakdown
        </h3>
        <ul className="space-y-3">
          {result.resemblances.map((r, i) => (
            <ResemblanceBar
              key={r.pattern_id}
              r={r}
              isTop={i === 0}
              userType={userType}
            />
          ))}
        </ul>
      </div>

      {/* FPED-1: food-group drivers — makes the embedding resemblance explainable.
          "Most like DASH because: more refined grains, less whole grains vs the
          prototype day." Shown to every audience. */}
      {explanations.fped_drivers && explanations.fped_drivers.drivers.length > 0 && (
        <div className="bg-teal-50 rounded-lg border border-teal-200 p-4">
          <p className="font-medium text-teal-900 text-sm">{explanations.fped_drivers.title}</p>
          <ul className="mt-2 space-y-1">
            {explanations.fped_drivers.drivers.map((d) => (
              <li key={d.component} className="flex items-center gap-2 text-sm text-gray-800">
                <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                  d.direction === 'more'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {d.direction === 'more' ? '▲ more' : '▼ less'}
                </span>
                <span>{Math.abs(d.delta)} {d.unit} {d.label}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-gray-500">{explanations.fped_drivers.caveat}</p>
        </div>
      )}

      {/* Researcher-mode methodology block */}
      {userType !== 'individual' && explanations.methodology && (
        <details className="bg-gray-50 rounded-lg border p-4 text-sm">
          <summary className="cursor-pointer font-medium text-gray-700 flex items-center gap-1">
            <Info className="h-4 w-4" aria-hidden="true" />
            {explanations.methodology.title}
          </summary>
          <p className="mt-2 text-gray-700">{explanations.methodology.message}</p>
        </details>
      )}
    </div>
  );
}
