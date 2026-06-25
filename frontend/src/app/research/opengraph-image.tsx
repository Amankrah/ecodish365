import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 for researchers — one substrate, every published lens, cross-continent, reproducible.';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'For researchers',
      heading: 'One substrate. Every published lens.',
      sub: 'Cross-continent, reproducible. The platform behind the Nature Food submission.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#1D4ED8', // blue-700
    }),
    { ...size },
  );
}
