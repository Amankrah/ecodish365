'use client';

/**
 * FpidBreakdownPanel — ingredient-level food-group attribution for ONE composite food.
 *
 * Answers "where does each food group in this dish come from?" using USDA's authoritative
 * FNDDS recipe + FPID (no LLM). Also surfaces a reconstruction QC (does the FPID ingredient
 * rollup reproduce the food's own FPED profile?) and honest coverage (ingredients with no
 * FPID row are counted as unmapped recipe mass). Fetches on mount; meant to be lazily
 * mounted only when a user expands a specific food.
 */
import { useEffect, useState } from 'react';
import { Loader2, AlertCircle, Info } from 'lucide-react';
import { FpidApiService, type FpidBreakdownResponse } from '@/lib/api';

interface FpidBreakdownPanelProps {
  foodId: number;
  massG?: number;
}

export function FpidBreakdownPanel({ foodId, massG = 100 }: FpidBreakdownPanelProps): JSX.Element {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<FpidBreakdownResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    FpidApiService.breakdown(foodId, massG)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : 'Could not load breakdown.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [foodId, massG]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 py-2 px-3">
        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        Tracing food-group sources…
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="flex items-start gap-2 text-xs text-red-800 bg-red-50 border border-red-200 rounded-md p-2 m-2">
        <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <span>{error}</span>
      </div>
    );
  }

  const breakdown = data?.breakdown ?? null;
  const reconstruction = data?.reconstruction ?? null;

  if (!breakdown) {
    return (
      <div className="flex items-start gap-2 text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-md p-2 m-2">
        <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <span>{data?.note ?? 'No ingredient-level breakdown for this food.'}</span>
      </div>
    );
  }

  const cov = breakdown.coverage;
  return (
    <div className="bg-teal-50/40 border border-teal-100 rounded-md p-3 m-2 space-y-3">
      {breakdown.by_group.length === 0 ? (
        <p className="text-xs text-gray-500">No major food groups contributed by this food.</p>
      ) : (
        <ul className="space-y-2">
          {breakdown.by_group.map((g) => (
            <li key={g.component}>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-sm font-medium text-gray-800 capitalize">{g.label}</span>
                <span className="text-sm tabular-nums text-teal-800">
                  {g.amount.toFixed(2)} <span className="text-gray-400 text-xs">{g.unit}</span>
                </span>
              </div>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {g.sources.map((s, i) => (
                  <span
                    key={`${g.component}-${i}`}
                    className="text-[11px] px-1.5 py-0.5 rounded bg-white border border-teal-200 text-gray-600"
                    title={s.sr_description}
                  >
                    {s.sr_description.length > 28 ? `${s.sr_description.slice(0, 28)}…` : s.sr_description}
                    <span className="text-teal-700 font-medium ml-1">{s.pct.toFixed(0)}%</span>
                  </span>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="text-[11px] text-gray-500 border-t border-teal-100 pt-2 space-y-0.5">
        <p>
          {cov.n_with_fpid}/{cov.n_ingredients} ingredients mapped
          {cov.unmapped_pct > 0 && <> · {cov.unmapped_pct}% of recipe mass unmapped</>}
          {' '}· analog match {(breakdown.bridge_confidence * 100).toFixed(0)}%
        </p>
        {reconstruction && reconstruction.cosine !== null && (
          <p>
            QC: ingredient rollup vs the food&apos;s known profile —{' '}
            <span className={reconstruction.plausible ? 'text-green-700' : 'text-amber-700'}>
              cosine {reconstruction.cosine.toFixed(2)}{' '}
              {reconstruction.plausible ? '(consistent)' : '(low — see coverage)'}
            </span>
          </p>
        )}
      </div>

      <p className="text-[11px] text-gray-400 leading-relaxed">{breakdown.note}</p>
    </div>
  );
}
