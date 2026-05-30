'use client';
/**
 * LCADataQualityReport — surfaces the backend's CODE-5 data-quality block
 * (`backend/environmental_impact_model/src/life_cycle_assessment.py:767-799`).
 *
 * Audience policy:
 *   - Individual: collapsed by default. When closed, the leading
 *     `known_issues[0]` shows as a single-line caveat so the user still sees
 *     the headline limitation. Expanding reveals the full list.
 *   - Researcher / Policy: open by default with the full sources +
 *     known_issues + recommendations vector visible.
 */

import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ChevronDown, ChevronUp, ShieldCheck, AlertTriangle } from 'lucide-react';
import type { EnvironmentalDataQuality } from '../../lib/api';
import type { UserType } from '../shared/AudienceToggle';

interface Props {
  dataQuality: EnvironmentalDataQuality;
  userType: UserType;
}

export const LCADataQualityReport: React.FC<Props> = ({ dataQuality, userType }) => {
  // Researcher / policy: open by default. Individual: collapsed.
  const [open, setOpen] = useState<boolean>(userType !== 'individual');

  const knownIssues = dataQuality.known_issues || [];
  const recommendations = dataQuality.recommendations || [];
  const sources = dataQuality.sources || [];
  const confidenceSummary = dataQuality.confidence_summary;

  return (
    <div className="border rounded-lg bg-slate-50/50">
      <Button
        variant="ghost"
        onClick={() => setOpen(v => !v)}
        className="w-full justify-between p-4 h-auto"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <ShieldCheck className="h-4 w-4 text-slate-600" />
          <span className="text-sm font-medium text-gray-900">
            Data quality &amp; methodology provenance
          </span>
          {dataQuality.methodology_version && (
            <Badge variant="outline" className="text-xs">
              {dataQuality.methodology_version}
            </Badge>
          )}
          {confidenceSummary && (
            <span className="text-xs text-gray-500">
              {confidenceSummary.high_confidence} high · {confidenceSummary.medium_confidence} med · {confidenceSummary.low_confidence} low
            </span>
          )}
        </div>
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </Button>

      {/* Collapsed-state caveat (individual only — gives a headline issue
          even when the user doesn't expand). */}
      {!open && userType === 'individual' && knownIssues.length > 0 && (
        <div className="border-t px-4 py-3 flex items-start gap-2 text-xs text-amber-900 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-700 flex-shrink-0 mt-0.5" />
          <p className="italic">{knownIssues[0]}</p>
        </div>
      )}

      {open && (
        <div className="border-t p-4 space-y-4 text-sm text-gray-700">
          {dataQuality.perspective && (
            <div className="flex flex-wrap gap-4 text-xs text-gray-600">
              <span><strong>Perspective:</strong> {dataQuality.perspective}</span>
              {dataQuality.consumer_perspective && (
                <span><strong>Consumer:</strong> {dataQuality.consumer_perspective}</span>
              )}
              {dataQuality.country && (
                <span><strong>Country:</strong> {dataQuality.country}</span>
              )}
            </div>
          )}

          {sources.length > 0 && (
            <div>
              <h5 className="font-semibold text-gray-900 mb-1 text-xs uppercase tracking-wide">
                Sources
              </h5>
              <ul className="text-xs space-y-1 list-disc list-inside text-gray-700">
                {sources.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {knownIssues.length > 0 && (
            <div>
              <h5 className="font-semibold text-gray-900 mb-1 text-xs uppercase tracking-wide flex items-center gap-1">
                <AlertTriangle className="h-3 w-3 text-amber-700" />
                Known issues &amp; scope limits
              </h5>
              <ul className="text-xs space-y-1 list-disc list-inside text-gray-700">
                {knownIssues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {recommendations.length > 0 && (
            <div>
              <h5 className="font-semibold text-gray-900 mb-1 text-xs uppercase tracking-wide">
                Recommendations
              </h5>
              <ul className="text-xs space-y-1 list-disc list-inside text-gray-700">
                {recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Researcher / policy only — raw provenance dict from the backend
              for reviewers who want to cite the exact pack version. */}
          {userType !== 'individual' && dataQuality.methodology_provenance && (
            <details className="text-xs">
              <summary className="cursor-pointer font-semibold text-gray-700">
                Methodology pack provenance
              </summary>
              <pre className="mt-2 p-2 bg-white border rounded overflow-x-auto text-[10px] text-gray-600">
                {JSON.stringify(dataQuality.methodology_provenance, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
};
