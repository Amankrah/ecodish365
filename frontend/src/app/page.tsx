import type { Metadata } from 'next';
import HomePageContent from '@/components/home/HomePageContent';

export const metadata: Metadata = {
  title: 'EcoDish365: Honest nutrition and sustainability scoring for any food',
  description:
    'Score any food, meal, or full day against six published research measures. Plain-language results, real uncertainty, and the limits the science actually states. 7,000+ foods, no invented grades, no single score pretending to settle it.',
  openGraph: {
    title: 'EcoDish365: Honest nutrition and sustainability scoring for any food',
    description:
      'Score any food, meal, or full day against six published research measures. Plain-language results with the limits the science states.',
  },
  twitter: {
    title: 'EcoDish365: Honest nutrition and sustainability scoring for any food',
    description:
      'Six published lenses. Plain-language results. No single composite score.',
  },
};

export default function HomePage() {
  return <HomePageContent />;
}
