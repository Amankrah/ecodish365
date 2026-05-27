/**
 * MetricSkeleton — loading-state placeholder rendered in place of
 * MetricCard while the orchestrator is in flight.
 */
'use client';

interface Props {
  emoji: string;
  title: string;
}

export function MetricSkeleton({ emoji, title }: Props): JSX.Element {
  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col gap-2 animate-pulse"
      aria-busy="true"
      aria-label={`${title} score loading`}
    >
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-500">
          <span aria-hidden="true">{emoji}</span>
          {title}
        </span>
      </div>
      <div className="h-6 w-32 bg-gray-200 rounded" />
      <div className="h-3 w-44 bg-gray-100 rounded" />
      <div className="h-3 w-full bg-gray-100 rounded" />
      <div className="h-3 w-3/4 bg-gray-100 rounded" />
      <div className="h-3 w-20 bg-gray-100 rounded mt-auto" />
    </div>
  );
}
