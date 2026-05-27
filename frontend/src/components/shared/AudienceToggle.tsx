/**
 * AudienceToggle — reusable 3-button audience selector for nutrition + environmental views.
 *
 * Mirrors the pattern from `EnvironmentalFoodComparison.tsx` (the originating
 * implementation) and extracts it so the 4 nutrition pages (HENI / HEFI / HSR /
 * FCS) and any future audience-aware views can reuse the same UI.
 *
 * AUDIENCE-CODE-1 (2026-05-23): the backend explanation packs are gated on
 * `user_type` ∈ {individual, researcher, policy}; this toggle is the
 * frontend's mechanism for selecting which pack to render.
 */
'use client';
import { Users, Info, Globe, AlertCircle } from 'lucide-react';

export type UserType = 'individual' | 'researcher' | 'policy';

interface AudienceToggleProps {
  userType: UserType;
  onChange: (next: UserType) => void;
  /** Optional palette override; default green matches the environmental view. */
  accent?: 'green' | 'blue' | 'purple' | 'amber';
  /**
   * Set to `true` when a result is already on screen but its audience-aware
   * `explanations` block was generated under a different `userType` (i.e. the
   * user toggled the audience after calculating). Renders a small advisory
   * banner below the toggle prompting recalculation. The toggle does not
   * auto-recalculate because that would consume an extra API call on every
   * click; the hint lets the user opt in.
   */
  staleResultHint?: boolean;
}

const ACCENT_CLASSES: Record<NonNullable<AudienceToggleProps['accent']>, string> = {
  green:  'bg-green-100 text-green-700',
  blue:   'bg-blue-100 text-blue-700',
  purple: 'bg-purple-100 text-purple-700',
  amber:  'bg-amber-100 text-amber-700',
};

function getIcon(type: UserType) {
  switch (type) {
    case 'individual':
      return <Users className="h-4 w-4" aria-hidden="true" />;
    case 'researcher':
      return <Info className="h-4 w-4" aria-hidden="true" />;
    case 'policy':
      return <Globe className="h-4 w-4" aria-hidden="true" />;
  }
}

/** Human-readable description of each audience for tooltip / aria-label use. */
const AUDIENCE_DESCRIPTIONS: Record<UserType, string> = {
  individual: 'Plain-language results without exposing computational details',
  researcher: 'Full methodological breakdown with literature citations',
  policy:     'Population-level context for evidence-based policymaking',
};

export function AudienceToggle({
  userType,
  onChange,
  accent = 'green',
  staleResultHint = false,
}: AudienceToggleProps) {
  const activeClass = ACCENT_CLASSES[accent];
  return (
    <div className="flex flex-col items-center gap-2">
      <fieldset className="bg-white rounded-lg border p-1 shadow-sm m-0 min-w-0">
        <legend className="sr-only">Audience view mode</legend>
        <div className="flex flex-wrap justify-center gap-1">
        {(['individual', 'researcher', 'policy'] as UserType[]).map((type) => (
          <label
            key={type}
            title={AUDIENCE_DESCRIPTIONS[type]}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 cursor-pointer focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-gray-400 ${
              userType === type
                ? `${activeClass} shadow-sm`
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <input
              type="radio"
              name="audience-view-mode"
              value={type}
              checked={userType === type}
              onChange={() => onChange(type)}
              className="sr-only"
              aria-label={`Switch to ${type} view: ${AUDIENCE_DESCRIPTIONS[type]}`}
            />
            {getIcon(type)}
            <span>{type.charAt(0).toUpperCase() + type.slice(1)}</span>
          </label>
        ))}
        </div>
      </fieldset>
      {staleResultHint && (
        <div
          role="status"
          className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2.5 py-1"
        >
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          <span>
            View changed — recalculate to refresh the explanations for this audience.
          </span>
        </div>
      )}
    </div>
  );
}

/** Field shapes returned by the backend explanation packs (AUDIENCE-CODE-1). */
export interface ExplanationSection {
  title?: string;
  headline?: string;
  units?: string;
  interpretation?: string;
  mandatory_caveat?: string;
  description?: string;
  message?: string;
}

export interface ExplanationsBlock {
  score_summary?: ExplanationSection;
  methodology?: Record<string, string>;
  citations?: Record<string, string>;
  policy_context?: Record<string, string>;
  nova_explainer?: ExplanationSection;
  /** 24-h recall handoff caveat (HSR calculate when from_recall24h). */
  recall_context?: ExplanationSection;
  action_tips?: Record<string, string>;
}
