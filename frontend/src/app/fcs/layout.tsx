import type { Metadata } from 'next';

const SITE_URL = 'https://ecodish365.com';

export const metadata: Metadata = {
  title: 'Food Compass Calculator',
  description:
    'Score how closely a food, a meal, or a whole day of eating resembles the patterns linked to longer, healthier lives. Food Compass scores every food on a single 1 to 100 scale, calculated from label information across a 6,719-food catalogue.',
  keywords: [
    'Food Compass',
    'Food Compass Score',
    'food quality score',
    'nutritional profiling',
    'diet quality',
    'NOVA processing',
    'food comparison',
    'nutrition calculator',
  ],
  openGraph: {
    title: 'Food Compass Calculator | EcoDish365',
    description:
      'Score how closely a food, a meal, or a whole day of eating resembles the patterns linked to longer, healthier lives. A single 1 to 100 scale, the same for one food or a full day.',
    type: 'website',
    url: `${SITE_URL}/fcs`,
    images: [
      {
        url: `${SITE_URL}/og-fcs.png`,
        width: 1200,
        height: 630,
        alt: 'Food Compass Calculator',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Food Compass Calculator | EcoDish365',
    description:
      'Score how closely a food, a meal, or a whole day of eating resembles the patterns linked to longer, healthier lives.',
    images: [`${SITE_URL}/twitter-fcs.png`],
  },
  alternates: {
    canonical: `${SITE_URL}/fcs`,
  },
};

export default function FCSLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Food Compass Calculator',
    description:
      'Score how closely a food, a meal, or a whole day of eating resembles the patterns linked to longer, healthier lives using the Food Compass nutrient profiling system.',
    url: `${SITE_URL}/fcs`,
    applicationCategory: 'HealthApplication',
    operatingSystem: 'Web Browser',
    creator: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: SITE_URL,
    },
    featureList: [
      'Single 1 to 100 scale for foods, meals, and whole days',
      'Packaged product label scan',
      'Compare foods across types',
      'Nine-domain nutrition breakdown',
    ],
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      {children}
    </>
  );
}
