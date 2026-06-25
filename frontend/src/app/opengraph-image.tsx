import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 — A unified environmental–nutrition platform';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'EcoDish365',
      heading: 'A unified environmental–nutrition platform.',
      sub: 'Score any food, meal, or 24-hour record across every published research lens. Versioned, citeable, reproducible.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#C2410C', // orange-700 (CTA-prominent surface)
    }),
    { ...size },
  );
}
