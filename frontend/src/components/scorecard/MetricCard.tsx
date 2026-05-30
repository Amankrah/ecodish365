/**
 * MetricCard — generic compact card shell rendered once per metric on
 * the Scorecard page. Driven entirely by a `CardModel` produced by
 * `metricAdapters` — no per-metric branching here.
 */
'use client';

import Link from 'next/link';
import { ArrowRight, AlertCircle, Info, RefreshCw } from 'lucide-react';
import { ACCENT_CLASSES, type CardModel } from './metricAdapters';

interface Props {
  card: CardModel;
  /** Visually dim the card after the active food list has changed. */
  stale?: boolean;
  /** Called when the user clicks "Retry" on an error card. */
  onRetry?: () => void;
  /** Whether a retry is currently in flight (disables the button). */
  retrying?: boolean;
}

export function MetricCard({ card, stale, onRetry, retrying }: Props): JSX.Element {
  const accent = ACCENT_CLASSES[card.accent];
  const isError = card.status === 'error';
  const isHint = card.status === 'hint';
  const isDamped = card.status === 'damped';

  return (
    <article
      className={`bg-white border ${accent.border} rounded-lg p-4 flex flex-col gap-2 transition-opacity ${
        stale || isDamped ? 'opacity-70' : ''
      }`}
      aria-label={`${card.title} score card`}
    >
      <header className="flex items-center gap-2">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${accent.chip}`}
        >
          <span aria-hidden="true">{card.emoji}</span>
          {card.title}
        </span>
        {stale && (
          <span className="text-[10px] text-gray-500 italic ml-auto">stale</span>
        )}
      </header>

      <div>
        <p
          className={`text-xl font-bold leading-tight ${
            isError || isHint ? 'text-gray-400' : 'text-gray-900'
          }`}
        >
          {card.headline}
        </p>
        {card.subline && (
          <p className="text-xs text-gray-600 mt-0.5">{card.subline}</p>
        )}
      </div>

      {/* Error / hint state — replaces meaning + caveat with a single message */}
      {(isError || isHint) && card.hint && (
        <div
          className={`flex items-start gap-1.5 text-xs px-2 py-1.5 rounded ${
            isError
              ? 'bg-red-50 border border-red-200 text-red-900'
              : 'bg-amber-50 border border-amber-200 text-amber-900'
          }`}
        >
          {isError
            ? <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
            : <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />}
          <span>{card.hint}</span>
        </div>
      )}

      {/* Normal state — meaning + caveat */}
      {!isError && !isHint && (
        <>
          <p className="text-sm text-gray-700 leading-snug">{card.meaning}</p>
          {card.driver && (
            <p className="text-xs text-gray-600 leading-snug italic">{card.driver}</p>
          )}
          <p className="text-[11px] text-gray-500 leading-snug">Note: {card.caveat}</p>
        </>
      )}

      <footer className="flex items-center justify-between gap-2 mt-auto pt-1">
        {isError && onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            disabled={retrying}
            className="inline-flex items-center gap-1 text-xs font-medium text-red-700 hover:text-red-900 disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${retrying ? 'animate-spin' : ''}`} aria-hidden="true" />
            {retrying ? 'Retrying…' : 'Retry'}
          </button>
        ) : (
          <span />
        )}
        <Link
          href={card.ctaHref}
          className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-900"
        >
          {card.ctaLabel}
          <ArrowRight className="h-3 w-3" aria-hidden="true" />
        </Link>
      </footer>
    </article>
  );
}
