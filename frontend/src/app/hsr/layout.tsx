import type { Metadata } from 'next';

const SITE_URL = 'https://ecodish365.com';

export const metadata: Metadata = {
  title: 'Health Star Rating (HSR) Calculator',
  description:
    'Rate any packaged product from 0.5 to 5 stars with the Australian and New Zealand Health Star Rating system, applied to a 6,719-food catalogue. Built for comparing similar products: which yogurt, which cereal, which loaf of bread.',
  keywords: [
    'Health Star Rating',
    'HSR calculator',
    'Australia food rating',
    'New Zealand food rating',
    'front of pack labeling',
    'food health rating',
    'nutritional quality score',
    'compare products',
    'healthy food choices',
    'nutrition calculator',
    'HSRAC v9',
  ],
  openGraph: {
    title: 'Health Star Rating (HSR) Calculator | EcoDish365',
    description:
      'Rate any packaged product from 0.5 to 5 stars with the Australian and New Zealand Health Star Rating system, applied to a 6,719-food catalogue.',
    type: 'website',
    url: `${SITE_URL}/hsr`,
    images: [
      {
        url: `${SITE_URL}/og-hsr.png`,
        width: 1200,
        height: 630,
        alt: 'Health Star Rating Calculator',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Health Star Rating (HSR) Calculator | EcoDish365',
    description:
      'Rate any packaged product from 0.5 to 5 stars. Built for comparing similar products: which yogurt, which cereal, which loaf of bread.',
    images: [`${SITE_URL}/twitter-hsr.png`],
  },
  alternates: {
    canonical: `${SITE_URL}/hsr`,
  },
};

export default function HSRLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Health Star Rating Calculator',
    description:
      'Rate packaged products from 0.5 to 5 stars using the Australian and New Zealand Health Star Rating system (HSRAC v9).',
    url: `${SITE_URL}/hsr`,
    applicationCategory: 'HealthApplication',
    operatingSystem: 'Web Browser',
    creator: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: SITE_URL,
    },
    featureList: [
      'HSRAC v9 star rating',
      'Packaged product label scan',
      'Catalogue food scoring',
      'Compare products side by side',
      'Scorecard across all metrics',
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
