/**
 * ExplanationsPanel — renders the audience-aware `explanations` block returned by
 * HENI / HEFI / HSR / FCS API endpoints (AUDIENCE-CODE-1 2026-05-23).
 *
 * Field shape (mirrors backend `{heni,hefi,hsr,fcs}_explanations.py`):
 *   - score_summary: {title, headline, units, interpretation, mandatory_caveat}
 *   - methodology (researcher mode only): {key: value, ...}
 *   - citations (researcher + policy mode): {key: value, ...}
 *   - policy_context (policy mode only): {title, use_cases, ...}
 *   - nova_explainer (FCS-specific, individual mode): {title, description}
 *   - action_tips: {key: value, ...}
 *
 * Renders headline + interpretation + mandatory caveat as primary copy.
 * Methodology / citations / policy_context as collapsible accordions
 * (default-open in researcher/policy modes, hidden in individual mode).
 *
 * This component encapsulates the audience-aware rendering logic so the four
 * nutrition pages can drop it in without reimplementing the conditional
 * rendering.
 */
'use client';
import { useState } from 'react';
import { AlertTriangle, BookOpen, Info, ChevronDown, ChevronRight } from 'lucide-react';
import type { ExplanationsBlock, UserType } from './AudienceToggle';

interface ExplanationsPanelProps {
  explanations: ExplanationsBlock | undefined;
  userType: UserType;
  /** Optional CSS accent class for the headline (default green). */
  accent?: string;
}

const AUDIENCE_BANNER: Record<UserType, { label: string; bg: string; text: string }> = {
  individual: { label: 'Plain-language view', bg: 'bg-green-50',  text: 'text-green-800' },
  researcher: { label: 'Researcher view — full methodology + citations', bg: 'bg-blue-50',   text: 'text-blue-800' },
  policy:     { label: 'Policy view — population context',              bg: 'bg-purple-50', text: 'text-purple-800' },
};

export function ExplanationsPanel({
  explanations,
  userType,
  accent = 'text-green-700',
}: ExplanationsPanelProps) {
  const [methodologyOpen, setMethodologyOpen] = useState(userType !== 'individual');
  const [citationsOpen, setCitationsOpen] = useState(userType === 'researcher');
  const [policyOpen, setPolicyOpen] = useState(userType === 'policy');

  if (!explanations) {
    return null;
  }
  const summary = explanations.score_summary;
  const banner = AUDIENCE_BANNER[userType];

  return (
    <div className="space-y-4">
      {/* Audience-mode banner so users always know which view they're in */}
      <div className={`${banner.bg} ${banner.text} rounded-md px-3 py-2 text-xs font-medium border border-current/10`}>
        {banner.label}
      </div>

      {/* Primary score summary */}
      {summary && (
        <div className="bg-white rounded-lg border shadow-sm p-5 space-y-3">
          {summary.title && (
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              {summary.title}
            </h3>
          )}
          {summary.headline && (
            <p className={`text-lg font-bold ${accent}`}>{summary.headline}</p>
          )}
          {summary.units && (
            <p className="text-sm text-gray-700">{summary.units}</p>
          )}
          {summary.interpretation && (
            <p className="text-sm text-gray-700">{summary.interpretation}</p>
          )}
          {summary.mandatory_caveat && (
            <div className="bg-amber-50 border-l-4 border-amber-400 rounded-md p-3 mt-3">
              <div className="flex gap-2 items-start">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-900 font-medium leading-relaxed">
                  {summary.mandatory_caveat}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* FCS-specific NOVA explainer (individual mode) */}
      {explanations.nova_explainer && (
        <div className="bg-white rounded-lg border shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            {explanations.nova_explainer.title}
          </h3>
          <p className="text-sm text-gray-600">
            {explanations.nova_explainer.description}
          </p>
        </div>
      )}

      {/* Methodology — researcher + policy view */}
      {explanations.methodology && userType !== 'individual' && (
        <CollapsibleSection
          title="Methodology Provenance"
          icon={<Info className="h-4 w-4 text-blue-600" />}
          open={methodologyOpen}
          onToggle={() => setMethodologyOpen((x) => !x)}
        >
          <dl className="space-y-2 text-sm">
            {Object.entries(explanations.methodology).map(([k, v]) => (
              <div key={k}>
                <dt className="font-semibold text-gray-700 capitalize">{k.replace(/_/g, ' ')}</dt>
                <dd className="text-gray-600 mt-1">{v}</dd>
              </div>
            ))}
          </dl>
        </CollapsibleSection>
      )}

      {/* Policy context — policy view */}
      {explanations.policy_context && userType !== 'individual' && (
        <CollapsibleSection
          title="Policy Applications"
          icon={<Info className="h-4 w-4 text-purple-600" />}
          open={policyOpen}
          onToggle={() => setPolicyOpen((x) => !x)}
        >
          <dl className="space-y-2 text-sm">
            {Object.entries(explanations.policy_context).map(([k, v]) => {
              if (k === 'title') return null;
              return (
                <div key={k}>
                  <dt className="font-semibold text-gray-700 capitalize">{k.replace(/_/g, ' ')}</dt>
                  <dd className="text-gray-600 mt-1">{v}</dd>
                </div>
              );
            })}
          </dl>
        </CollapsibleSection>
      )}

      {/* Citations — researcher + policy view */}
      {explanations.citations && userType !== 'individual' && (
        <CollapsibleSection
          title="Literature Citations"
          icon={<BookOpen className="h-4 w-4 text-blue-600" />}
          open={citationsOpen}
          onToggle={() => setCitationsOpen((x) => !x)}
        >
          <dl className="space-y-2 text-sm">
            {Object.entries(explanations.citations).map(([k, v]) => (
              <div key={k}>
                <dt className="font-semibold text-gray-700 capitalize">{k.replace(/_/g, ' ')}</dt>
                <dd className="text-gray-600 mt-1 italic">{v}</dd>
              </div>
            ))}
          </dl>
        </CollapsibleSection>
      )}

      {/* Action tips — all modes */}
      {explanations.action_tips && (
        <div className="bg-emerald-50 rounded-lg border border-emerald-100 p-4">
          <h3 className="text-sm font-semibold text-emerald-800 mb-2">What you can do</h3>
          <div className="space-y-2 text-sm text-emerald-900">
            {Object.entries(explanations.action_tips).map(([k, v]) => (
              <p key={k}>{v}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function CollapsibleSection({ title, icon, open, onToggle, children }: CollapsibleSectionProps) {
  return (
    <div className="bg-white rounded-lg border shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-semibold text-gray-700">{title}</span>
        </div>
        {open ? (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronRight className="h-4 w-4 text-gray-500" />
        )}
      </button>
      {open && <div className="px-4 pb-4 border-t">{children}</div>}
    </div>
  );
}
