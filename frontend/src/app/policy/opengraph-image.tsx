import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 for policy makers — population-level framing for procurement, taxation, labelling, and surveillance.';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'For policy makers',
      heading: 'Population-level framing for the food system.',
      sub: 'Versioned numbers, plain explanations. EAT-Lancet 2.0 share, monetised social-cost overlay where the evidence supports it.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#1D4ED8', // blue-700
    }),
    { ...size },
  );
}
