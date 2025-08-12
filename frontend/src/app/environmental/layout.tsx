/**
 * Environmental Impact Analysis Layout
 * Adds rich SEO metadata, structured data, and consistent navigation similar to FCS layout
 */

import React from 'react';
import type { Metadata } from 'next';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  applicationName: 'EcoDish365',
  title: {
    default: 'Environmental Impact Analysis Suite',
    template: '%s | Environmental Impact • EcoDish365',
  },
  description:
    'Analyze meal environmental impacts using ReCiPe 2016 with 18 impact categories, Canadian-specific factors, sustainability scoring and CAD economic valuation.',
  keywords: [
    'environmental impact',
    'environmental impacts of food',
    'life cycle assessment',
    'LCA',
    'ReCiPe 2016',
    'carbon footprint',
    'water consumption',
    'land use',
    'sustainability score',
    'food comparison',
    'meal analysis',
    'environmental cost',
    'social cost of carbon',
    'Canada',
    'Canadian factors',
  ],
  openGraph: {
    title: 'Environmental Impact Analysis Suite - EcoDish365',
    description:
      'Comprehensive LCA with 18 impact categories, Canadian regional factors, sustainability scoring, and CAD economic valuation.',
    type: 'website',
    url: '/environmental',
    siteName: 'EcoDish365',
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
      'Comprehensive meal LCA with Canadian factors, sustainability scoring and CAD economic valuation.',
    images: ['/twitter-environmental.png'],
  },
  alternates: {
    canonical: `${siteUrl.replace(/\/$/, '')}/environmental`,
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  themeColor: '#0ea5e9',
  referrer: 'origin-when-cross-origin',
  formatDetection: {
    telephone: false,
    email: false,
    address: false,
  },
};

interface EnvironmentalLayoutProps {
  children: React.ReactNode;
}

export default function EnvironmentalLayout({ children }: EnvironmentalLayoutProps) {
  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: 'Environmental Impact Analysis Suite',
    description:
      'Suite of tools for meal Life Cycle Assessment (ReCiPe 2016), Canadian regional factors, and economic valuation in CAD.',
    url: `${siteUrl.replace(/\/$/, '')}/environmental`,
    applicationCategory: 'ScienceApplication',
    operatingSystem: 'Web Browser',
    creator: {
      '@type': 'Organization',
      name: 'EcoDish365',
      url: siteUrl,
    },
    featureList: [
      '18 impact categories (ReCiPe 2016)',
      'Canadian regional correction factors',
      'Economic valuation in CAD (incl. SCC $185/tonne CO₂)',
      'Per 100 kcal normalization for comparability',
      'Reference meal comparisons',
      'Sustainability scoring with nutritional context',
    ],
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: [
        {
          '@type': 'ListItem',
          position: 1,
          name: 'Environmental Impact',
          item: `${siteUrl.replace(/\/$/, '')}/environmental`,
        },
        {
          '@type': 'ListItem',
          position: 2,
          name: 'Calculator',
          item: `${siteUrl.replace(/\/$/, '')}/environmental/calculate`,
        },
        {
          '@type': 'ListItem',
          position: 3,
          name: 'Compare Foods',
          item: `${siteUrl.replace(/\/$/, '')}/environmental/compare`,
        },
      ],
    },
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