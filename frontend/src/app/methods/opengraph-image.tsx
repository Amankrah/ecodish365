import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 methods and data — every score traces to a published factor pack.';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'Methods & data',
      heading: 'Every score traces to a published factor pack.',
      sub: 'Versioned, checksummed, citeable. CNF, WAFCT, FPED, NOVA, IOM/NASEM. Every release ships with a reproducibility manifest.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#1D4ED8', // blue-700
    }),
    { ...size },
  );
}
