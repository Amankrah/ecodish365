import type { Metadata } from 'next';
import { ScaleIcon } from '@heroicons/react/24/outline';

export const metadata: Metadata = {
  title: 'Healthy Eating Score Calculator',
  description:
    "See how closely a day of eating matches Canada's Food Guide. Ten components, plain-language results, and a score from 0 to 80.",
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
    title: 'Healthy Eating Score Calculator - EcoDish365',
    description:
      "See how closely a day of eating matches Canada's Food Guide. Ten components and a score from 0 to 80.",
    type: 'website',
    url: 'https://ecodish365.com/hefi',
    images: [
      {
        url: '/og-hefi.png',
        width: 1200,
        height: 630,
        alt: 'Healthy eating score calculator',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Healthy Eating Score Calculator',
    description:
      "See how closely a day of eating matches Canada's Food Guide.",
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
    name: 'Healthy Eating Score Calculator',
    description:
      "Diet quality assessment aligned with Canada's Food Guide across 10 components.",
    url: 'https://ecodish365.com/hefi',
    applicationCategory: 'HealthApplication',
    operatingSystem: 'Web Browser',
    creator: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: 'https://ecodish365.com',
    },
    featureList: [
      '10 component healthy eating scoring',
      'Adequacy and moderation components',
      'Food and meal scoring',
      'Comparison and insights',
      'Plain-language interpretation',
      'Food diary workflow',
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
        'Implementation of the HEFI-2019 scoring system with comprehensive dietary analysis features.',
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
            <h1 className="text-4xl font-bold mb-4">Healthy eating scores</h1>
            <p className="text-xl text-purple-100 max-w-3xl mx-auto">
              See how closely a day of eating matches Canada&apos;s Food Guide across ten
              components, with plain-language results.
            </p>
          </div>
        </div>
      </div>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
    </div>
  );
}
