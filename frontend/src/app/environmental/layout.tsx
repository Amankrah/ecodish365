/**
 * Environmental Impact Analysis Layout
 * Adds rich SEO metadata, structured data, and consistent navigation similar to FCS layout
 */

import React from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Environmental Impact Analysis Suite',
  description:
    'Analyze meal environmental impacts using ReCiPe 2016 with 18 impact categories, Canadian-specific factors, and CAD economic valuation.',
  keywords: [
    'environmental impact',
    'LCA',
    'ReCiPe 2016',
    'sustainability',
    'carbon footprint',
    'life cycle assessment',
    'food sustainability',
    'environmental cost',
    'Canadian factors',
  ],
  openGraph: {
    title: 'Environmental Impact Analysis Suite - EcoDish365',
    description:
      'Comprehensive LCA with 18 impact categories, Canadian regional factors, and economic valuation in CAD.',
    type: 'website',
    url: 'https://ecodish365.com/environmental',
    images: [
      {
        url: '/og-environmental.png',
        width: 1200,
        height: 630,
        alt: 'Environmental Impact Analysis',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Environmental Impact Analysis Suite',
    description:
      'Comprehensive meal LCA with Canadian factors and CAD economic valuation.',
    images: ['/twitter-environmental.png'],
  },
  alternates: {
    canonical: 'https://ecodish365.com/environmental',
  },
};

interface EnvironmentalLayoutProps {
  children: React.ReactNode;
}

export default function EnvironmentalLayout({ children }: EnvironmentalLayoutProps) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Environmental Impact Analysis Suite',
    description:
      'Suite of tools for meal Life Cycle Assessment (ReCiPe 2016), Canadian regional factors, and economic valuation in CAD.',
    url: 'https://ecodish365.com/environmental',
    applicationCategory: 'ScienceApplication',
    operatingSystem: 'Web Browser',
    creator: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: 'https://ecodish365.com',
    },
    featureList: [
      '18 impact categories (ReCiPe 2016)',
      'Canadian regional correction factors',
      'Economic valuation in CAD (incl. SCC $185/tonne CO₂)',
      'Per 100 kcal normalization for comparability',
      'Reference meal comparisons',
      'Sustainability scoring with nutritional context',
    ],
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <main>{children}</main>
    </div>
  );
}