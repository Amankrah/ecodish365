import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 for individuals — score any food, meal, or whole day in plain language with honest caveats.';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'For individuals',
      heading: 'Is this food good for you, and for the planet?',
      sub: 'Score a single product, a homemade dish, or a whole day of eating. Plain language, honest caveats, no invented grades.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#1D4ED8', // blue-700
    }),
    { ...size },
  );
}
