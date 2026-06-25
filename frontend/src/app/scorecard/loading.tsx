// Route-transition skeleton for /scorecard. Reuses the existing
// MetricSkeleton component for the metric grid so the empty grid matches
// the rendered state. Header skeleton mirrors the page's actual layout.
//
// Per-metric loading during the in-page "Score all" action is handled
// inside the page itself by streaming MetricSkeleton -> MetricCard as
// each scorer resolves. This file only handles the route-transition
// flash before the page mounts.
//
// 'use client' is required because we pass icon component references
// (Salad, Dna, etc.) as props to <MetricSkeleton/>. Component types
// cannot serialize across the Server -> Client boundary in Next.js 15,
// so this file has to render on the client.
'use client';

import { MetricSkeleton } from '@/components/scorecard/MetricSkeleton';
import { Salad, Dna, Compass, Target } from 'lucide-react';
import { StarIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import type { IconType } from '@/components/scorecard/metricAdapters';

const METRIC_PREVIEW: Array<{ key: string; icon: IconType; title: string }> = [
  { key: 'hefi',            icon: Salad,        title: 'Healthy eating' },
  { key: 'heni',            icon: Dna,          title: 'Health impact' },
  { key: 'hsr',             icon: StarIcon,     title: 'Product rating' },
  { key: 'fcs',             icon: Compass,      title: 'Food Compass' },
  { key: 'environmental',   icon: GlobeAltIcon, title: 'Environment' },
  { key: 'dietary_pattern', icon: Target,       title: 'Eating style' },
];

export default function ScorecardLoading() {
  return (
    <div
      className="max-w-7xl mx-auto px-4 py-6 space-y-6"
      role="status"
      aria-busy="true"
      aria-label="Loading scorecard"
    >
      {/* Header skeleton */}
      <header className="bg-white rounded-lg shadow-sm p-6 animate-pulse">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-lg bg-gray-200 flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-6 w-56 bg-gray-200 rounded" />
            <div className="h-3 w-full max-w-md bg-gray-100 rounded" />
            <div className="h-3 w-3/4 max-w-md bg-gray-100 rounded" />
          </div>
        </div>
        <div className="mt-4 pt-4 border-t flex items-center justify-between gap-3 flex-wrap">
          <div className="h-8 w-48 bg-gray-100 rounded" />
          <div className="h-9 w-24 bg-gray-100 rounded" />
        </div>
      </header>

      {/* Food list panel skeleton */}
      <div className="bg-white rounded-lg shadow-sm p-4 animate-pulse">
        <div className="h-4 w-32 bg-gray-200 rounded mb-3" />
        <div className="space-y-2">
          <div className="h-10 w-full bg-gray-100 rounded" />
          <div className="h-10 w-full bg-gray-100 rounded" />
          <div className="h-10 w-full bg-gray-100 rounded" />
        </div>
      </div>

      {/* Metric grid skeleton — reuses the in-page skeleton for visual continuity */}
      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {METRIC_PREVIEW.map((m) => (
          <MetricSkeleton key={m.key} icon={m.icon} title={m.title} />
        ))}
      </section>

      <span className="sr-only">Loading the scorecard…</span>
    </div>
  );
}
