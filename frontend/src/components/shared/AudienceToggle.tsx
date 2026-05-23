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
import { Users, Info, Globe } from 'lucide-react';

export type UserType = 'individual' | 'researcher' | 'policy';

interface AudienceToggleProps {
  userType: UserType;
  onChange: (next: UserType) => void;
  /** Optional palette override; default green matches the environmental view. */
  accent?: 'green' | 'blue' | 'purple' | 'amber';
}

const ACCENT_CLASSES: Record<NonNullable<AudienceToggleProps['accent']>, string> = {
  green:  'bg-green-100 text-green-700',
  blue:   'bg-blue-100 text-blue-700',
  purple: 'bg-purple-100 text-purple-700',
  amber:  'bg-amber-100 text-amber-700',
};

function getIcon(type: UserType) {
  switch (type) {
    case 'individual': return <Users className="h-4 w-4" />;
    case 'researcher': return <Info className="h-4 w-4" />;
    case 'policy':     return <Globe className="h-4 w-4" />;
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
}: AudienceToggleProps) {
  const activeClass = ACCENT_CLASSES[accent];
  return (
    <div className="flex justify-center">
      <div className="bg-white rounded-lg border p-1 shadow-sm">
        {(['individual', 'researcher', 'policy'] as UserType[]).map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => onChange(type)}
            title={AUDIENCE_DESCRIPTIONS[type]}
            aria-pressed={userType === type}
            aria-label={`Switch to ${type} view: ${AUDIENCE_DESCRIPTIONS[type]}`}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              userType === type
                ? `${activeClass} shadow-sm`
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {getIcon(type)}
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>
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
}

export interface ExplanationsBlock {
  score_summary?: ExplanationSection;
  methodology?: Record<string, string>;
  citations?: Record<string, string>;
  policy_context?: Record<string, string>;
  nova_explainer?: ExplanationSection;
  action_tips?: Record<string, string>;
}
