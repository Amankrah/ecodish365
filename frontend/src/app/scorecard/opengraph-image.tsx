import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 all scores — every published lens on the same food list in one view.';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'All scores at once',
      heading: 'Every published lens on the same food list.',
      sub: 'Healthy eating, health impact, stars, Food Compass, environment, and eating style — in one view. Switch the audience toggle to suit your reader.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#C2410C', // orange-700 (CTA-prominent surface)
    }),
    { ...size },
  );
}
