import { ImageResponse } from 'next/og';
import { ogCardJsx, OG_SIZE, OG_CONTENT_TYPE } from '@/lib/og';

export const runtime = 'edge';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const alt = 'EcoDish365 nutrient analysis — composition assessment for a meal or 24-hour record.';

export default async function Image() {
  return new ImageResponse(
    ogCardJsx({
      eyebrow: 'Nutrient analysis',
      heading: 'Composition assessment for a meal or 24-hour record.',
      sub: 'Full nutrient panel against IOM DRIs by life-stage, FPED food groups, NOVA processing, and AMDR macronutrient bands. Export JSON or CSV.',
      accentFrom: '#EFF6FF', // blue-50
      accentTo: '#F8FAFC',   // slate-50
      eyebrowColor: '#1D4ED8', // blue-700
    }),
    { ...size },
  );
}
