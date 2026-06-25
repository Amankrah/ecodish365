// Shared layout helper for per-route opengraph-image.tsx files. Returns
// the JSX consumed by `next/og`'s `ImageResponse`. ImageResponse renders
// a constrained CSS subset (no Tailwind, no external fonts unless fetched
// explicitly, every parent of multiple children needs `display: 'flex'`),
// so all styling is inline objects with hex colors.
//
// Each opengraph-image.tsx supplies its own copy + accent palette; the
// shape of the card is identical across the platform.

import React from 'react';

export const OG_SIZE = { width: 1200, height: 630 } as const;
export const OG_CONTENT_TYPE = 'image/png' as const;

type OgCardProps = {
  /** Small uppercase line above the heading (e.g. "For researchers"). */
  eyebrow: string;
  /** Page-specific large heading. Keep under ~60 chars. */
  heading: string;
  /** One-line subheading. Keep under ~120 chars. */
  sub: string;
  /** Hex color for the top-left gradient stop (e.g. "#EEF2FF"). */
  accentFrom: string;
  /** Hex color for the bottom-right gradient stop (e.g. "#EFF6FF"). */
  accentTo: string;
  /** Hex color for the eyebrow text (typically a -700 from the same family). */
  eyebrowColor: string;
};

export function ogCardJsx({
  eyebrow,
  heading,
  sub,
  accentFrom,
  accentTo,
  eyebrowColor,
}: OgCardProps): React.ReactElement {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        width: '100%',
        height: '100%',
        padding: '64px',
        paddingTop: '52px',
        background: `linear-gradient(135deg, ${accentFrom} 0%, #FFFFFF 50%, ${accentTo} 100%)`,
        fontFamily: 'system-ui, sans-serif',
        borderTop: '12px solid #F97316',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div
          style={{
            fontSize: '22px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: eyebrowColor,
            marginBottom: '24px',
          }}
        >
          {eyebrow}
        </div>
        <div
          style={{
            fontSize: '76px',
            fontWeight: 700,
            color: '#111827',
            lineHeight: 1.1,
            marginBottom: '32px',
            maxWidth: '1000px',
          }}
        >
          {heading}
        </div>
        <div
          style={{
            fontSize: '30px',
            color: '#374151',
            lineHeight: 1.4,
            maxWidth: '1000px',
          }}
        >
          {sub}
        </div>
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          fontSize: '22px',
          color: '#475569',
        }}
      >
        <div style={{ fontWeight: 700, color: '#111827' }}>ecodish365</div>
        <div style={{ color: '#CBD5E1' }}>·</div>
        <div>Unified environmental–nutrition platform</div>
      </div>
    </div>
  );
}
