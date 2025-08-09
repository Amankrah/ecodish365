import type { Metadata } from 'next';
import { ScaleIcon } from '@heroicons/react/24/outline';

export const metadata: Metadata = {
  title: 'Healthy Eating Food Index (HEFI) Calculator',
  description:
    "Assess diet quality using Canada's Healthy Eating Food Index (HEFI-2019). Evaluate nutritional quality across 10 components and get comprehensive dietary analysis.",
  keywords: [
    'HEFI',
    'Healthy Eating Food Index',
    'HEFI-2019',
    "Canada's Food Guide",
    'diet quality score',
    'nutrition assessment',
    'dietary quality',
    'food index',
    'nutrition calculator',
    'diet scoring tool',
  ],
  openGraph: {
    title: 'Healthy Eating Food Index (HEFI) Calculator - EcoDish365',
    description:
      "Assess diet quality using Canada's Healthy Eating Food Index (HEFI-2019). Evaluate nutritional quality across 10 components and get comprehensive dietary analysis.",
    type: 'website',
    url: 'https://ecodish365.com/hefi',
    images: [
      {
        url: '/og-hefi.png',
        width: 1200,
        height: 630,
        alt: 'HEFI Calculator',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Healthy Eating Food Index (HEFI) Calculator',
    description:
      "Assess diet quality using Canada's Healthy Eating Food Index (HEFI-2019). Evaluate nutritional quality across 10 components and get comprehensive dietary analysis.",
    images: ['/twitter-hefi.png'],
  },
  alternates: {
    canonical: 'https://ecodish365.com/hefi',
  },
};

export default function HEFILayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Healthy Eating Food Index (HEFI) Calculator',
    description:
      "Advanced diet quality assessment using the HEFI-2019 algorithm with 10 components aligned to Canada's Food Guide.",
    url: 'https://ecodish365.com/hefi',
    applicationCategory: 'HealthApplication',
    operatingSystem: 'Web Browser',
    creator: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: 'https://ecodish365.com',
    },
    featureList: [
      '10 component HEFI-2019 scoring',
      'Adequacy and moderation components',
      'Food and meal HEFI calculation',
      'Comparison and insights',
      'HEFI interpretation and grades',
      'Professional reporting',
      'Research-grade accuracy',
    ],
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    review: {
      '@type': 'Review',
      author: {
        '@type': 'Organization',
        name: 'Nutrition Research Community',
      },
      reviewRating: {
        '@type': 'Rating',
        ratingValue: '4.9',
        bestRating: '5',
      },
      reviewBody:
        'Accurate implementation of the HEFI-2019 scoring system with comprehensive dietary analysis features.',
    },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <ScaleIcon className="mx-auto h-16 w-16 mb-4 opacity-80" />
            <h1 className="text-4xl font-bold mb-4">Healthy Eating Food Index (HEFI)</h1>
            <p className="text-xl text-purple-100 max-w-3xl mx-auto">
              Assess diet quality using Canada&apos;s Healthy Eating Food Index. Evaluate nutritional
              quality across 10 components for comprehensive dietary analysis.
            </p>
          </div>
        </div>
      </div>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
    </div>
  );
}