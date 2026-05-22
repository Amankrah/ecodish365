'use client';
/**
 * UncertaintyBandBar — horizontal band visualisation of a v1 uncertainty
 * envelope {low, central, high}, with optional literature-anchor marker.
 *
 * Visual layout:
 *
 *   [====|=============●=============|====]
 *    low              central             high
 *                  literature ▲
 *
 * Bar uses logarithmic spacing internally when the high/low ratio is large
 * (>5x), so wide envelopes don't collapse the central marker against one end.
 */
import React from 'react';
import type { UncertaintyBand } from '../../lib/api';

interface UncertaintyBandBarProps {
  band: UncertaintyBand;
  unit: string;
  /** Optional published literature anchor for context. */
  literature?: { value: number; source: string } | null;
  /** Tailwind color tint for the bar (e.g. 'rose', 'emerald', 'sky'). */
  color?: 'rose' | 'emerald' | 'sky' | 'amber';
  /** Show the numeric scale endpoints. Defaults to true. */
  showScale?: boolean;
}

const colorPalette: Record<NonNullable<UncertaintyBandBarProps['color']>, {
  band: string; central: string; fill: string; text: string;
}> = {
  rose:    { band: 'bg-rose-100',    central: 'bg-rose-700',    fill: 'bg-rose-400/70',    text: 'text-rose-900' },
  emerald: { band: 'bg-emerald-100', central: 'bg-emerald-700', fill: 'bg-emerald-400/70', text: 'text-emerald-900' },
  sky:     { band: 'bg-sky-100',     central: 'bg-sky-700',     fill: 'bg-sky-400/70',     text: 'text-sky-900' },
  amber:   { band: 'bg-amber-100',   central: 'bg-amber-700',   fill: 'bg-amber-400/70',   text: 'text-amber-900' },
};

const formatVal = (v: number): string => {
  if (!Number.isFinite(v)) return '—';
  if (v === 0) return '0';
  const abs = Math.abs(v);
  if (abs >= 100) return v.toFixed(0);
  if (abs >= 1)   return v.toFixed(2);
  if (abs >= 1e-3) return v.toFixed(4);
  return v.toExponential(2);
};

/** Position a value within [low, high] as a 0-100 percentage,
 *  using log scale when the dynamic range is large. */
const positionPct = (val: number, low: number, high: number): number => {
  if (high <= low) return 50;
  const useLog = high / Math.max(low, 1e-30) > 5;
  if (useLog) {
    const lo = Math.log(Math.max(low,  1e-30));
    const hi = Math.log(Math.max(high, 1e-30));
    const v  = Math.log(Math.max(val,  1e-30));
    return Math.max(0, Math.min(100, ((v - lo) / (hi - lo)) * 100));
  }
  return Math.max(0, Math.min(100, ((val - low) / (high - low)) * 100));
};

export const UncertaintyBandBar: React.FC<UncertaintyBandBarProps> = ({
  band, unit, literature, color = 'sky', showScale = true,
}) => {
  const palette = colorPalette[color];
  const { low, central, high } = band;
  const centralPct = positionPct(central, low, high);
  const litInBand = literature && literature.value >= low && literature.value <= high;
  const litPct = literature ? positionPct(literature.value, low, high) : null;

  return (
    <div className="w-full space-y-1.5">
      {/* Bar */}
      <div className={`relative h-8 rounded-md ${palette.band} overflow-visible`}>
        {/* Filled band core (the low-to-high envelope) */}
        <div className={`absolute inset-y-0 left-0 right-0 ${palette.fill} rounded-md`} />

        {/* Central marker (vertical line + dot) */}
        <div
          className="absolute inset-y-0 flex items-center"
          style={{ left: `${centralPct}%`, transform: 'translateX(-50%)' }}
        >
          <div className={`w-1 h-full ${palette.central} rounded`} />
        </div>
        <div
          className="absolute -top-1.5 flex items-center"
          style={{ left: `${centralPct}%`, transform: 'translateX(-50%)' }}
        >
          <div className={`w-3 h-3 rounded-full border-2 border-white ${palette.central}`} />
        </div>

        {/* Literature-anchor triangle (below the bar) */}
        {literature && litPct != null && (
          <div
            className="absolute -bottom-3 flex items-center"
            style={{ left: `${litPct}%`, transform: 'translateX(-50%)' }}
            title={`${literature.source}: ${formatVal(literature.value)} ${unit}`}
          >
            <div className={`w-0 h-0 border-l-[6px] border-r-[6px] border-b-[8px]
                            border-l-transparent border-r-transparent
                            ${litInBand ? 'border-b-emerald-600' : 'border-b-orange-500'}`} />
          </div>
        )}
      </div>

      {/* Scale labels */}
      {showScale && (
        <div className="flex justify-between text-[10px] text-gray-500 tabular-nums">
          <span>{formatVal(low)}</span>
          <span className={`font-medium ${palette.text}`}>{formatVal(central)} {unit}</span>
          <span>{formatVal(high)}</span>
        </div>
      )}

      {/* Literature footer */}
      {literature && (
        <div className="text-[10px] text-gray-500">
          Literature anchor: <span className="font-medium">{formatVal(literature.value)} {unit}</span>
          {' — '}
          <span className={litInBand ? 'text-emerald-700' : 'text-orange-700'}>
            {litInBand ? 'within band' : 'outside band'}
          </span>
          {' '}({literature.source})
        </div>
      )}
    </div>
  );
};

export default UncertaintyBandBar;
