'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { ChevronDownIcon, ChevronUpIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import {
  CNFApiService,
  EnvironmentalImpactApiService,
  type EnvironmentalImpactResult,
} from '@/lib/api';
import type { UserType } from '@/components/shared/AudienceToggle';

interface EnvironmentalTeaserProps {
  foodId: number;
  massG: number;
  userType: UserType;
}

function formatImpact(value: number | undefined, unit: string): string {
  if (value == null || !Number.isFinite(value)) return '—';
  if (Math.abs(value) >= 100) return `${value.toFixed(1)} ${unit}`;
  if (Math.abs(value) >= 10) return `${value.toFixed(2)} ${unit}`;
  return `${value.toFixed(3)} ${unit}`;
}

export function EnvironmentalTeaser({ foodId, massG, userType }: EnvironmentalTeaserProps) {
  const [expanded, setExpanded] = useState(userType === 'researcher');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnvironmentalImpactResult | null>(null);
  const requestRef = useRef(0);

  useEffect(() => {
    if (!expanded || !Number.isFinite(massG) || massG <= 0) return;

    const requestId = ++requestRef.current;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const payload = CNFApiService.recallToEnvironmental(
          [{
            food_id: foodId,
            food_description: '',
            food_group: '',
            mass_g: massG,
            occasions: {},
          }],
          userType,
        );
        const res = await EnvironmentalImpactApiService.analyzeMealEnvironmentalImpact(payload);
        if (requestId === requestRef.current) setResult(res);
      } catch {
        if (requestId === requestRef.current) {
          setError('Environmental preview unavailable for this food.');
          setResult(null);
        }
      } finally {
        if (requestId === requestRef.current) setLoading(false);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [expanded, foodId, massG, userType]);

  const perServing = result?.data?.meal_analysis?.impacts_by_basis?.per_serving
    ?? result?.data?.meal_analysis?.lca_results;
  const per100kcal = result?.data?.meal_analysis?.lca_results;
  const bands = result?.data?.meal_analysis?.lca_results_bands;
  const explanation = result?.data?.user_explanation;

  return (
    <div className="border border-teal-200 rounded-lg overflow-hidden bg-teal-50/50">
      <button
        type="button"
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-teal-50 text-left"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-gray-900">
          <GlobeAltIcon className="w-4 h-4 text-teal-700" aria-hidden="true" />
          Environmental preview (ReCiPe 2016, production phase)
        </span>
        {expanded ? (
          <ChevronUpIcon className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDownIcon className="w-4 h-4 text-gray-500" />
        )}
      </button>

      {expanded && (
        <div className="px-3 py-3 border-t border-teal-100 bg-white">
          {loading && (
            <p className="text-sm text-gray-500">Calculating footprint for {massG} g…</p>
          )}
          {error && !loading && (
            <p className="text-sm text-amber-800">{error}</p>
          )}
          {result && !loading && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div className="rounded-lg border border-gray-100 p-2.5">
                  <div className="text-[10px] font-medium text-gray-500 uppercase">Climate</div>
                  <div className="text-sm font-semibold text-gray-900">
                    {formatImpact(perServing?.['Global warming'], 'kg CO₂-eq')}
                  </div>
                  <div className="text-[10px] text-gray-500">for this portion</div>
                </div>
                <div className="rounded-lg border border-gray-100 p-2.5">
                  <div className="text-[10px] font-medium text-gray-500 uppercase">Land</div>
                  <div className="text-sm font-semibold text-gray-900">
                    {formatImpact(perServing?.['Land use'], 'm²·yr')}
                  </div>
                </div>
                <div className="rounded-lg border border-gray-100 p-2.5">
                  <div className="text-[10px] font-medium text-gray-500 uppercase">Water</div>
                  <div className="text-sm font-semibold text-gray-900">
                    {formatImpact(perServing?.['Water consumption'], 'm³')}
                  </div>
                </div>
              </div>

              {per100kcal?.['Global warming'] != null && (
                <p className="text-xs text-gray-600">
                  Normalized: {formatImpact(per100kcal['Global warming'], 'kg CO₂-eq')} per 100 kcal
                  {bands?.['Global warming'] && userType !== 'individual' && (
                    <> (range {formatImpact(bands['Global warming'].low, 'kg')}–{formatImpact(bands['Global warming'].high, 'kg')})</>
                  )}
                </p>
              )}

              {explanation?.summary && userType === 'individual' && (
                <p className="text-xs text-gray-700">{explanation.summary}</p>
              )}
              {userType === 'researcher' && explanation?.technical_notes?.[0] && (
                <p className="text-xs text-gray-600">{explanation.technical_notes[0]}</p>
              )}

              <p className="text-[10px] text-gray-500">
                Production-stage only (AGRIBALYSE 3.2). Household preparation and end-of-life are out of scope.
              </p>
              <Link
                href="/environmental/calculate"
                className="inline-block text-xs font-medium text-teal-800 hover:text-teal-950"
              >
                Open full environmental calculator →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
