import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: "Canadian Nutrient File (CNF) Database Explorer",
  description: "Explore Canada's comprehensive nutrition database with 5000+ foods and 150+ nutrients. Search, compare, and analyze nutritional content with advanced filtering and statistical tools for research and professional use.",
  keywords: [
    "Canadian Nutrient File", "CNF database", "Canada nutrition database", 
    "food nutrients Canada", "nutritional analysis Canada", "Health Canada food data",
    "food composition database", "nutrient search tool", "nutrition research database",
    "food comparison tool", "dietary analysis", "nutrition facts Canada"
  ],
  openGraph: {
    title: "Canadian Nutrient File Database Explorer - EcoDish365",
    description: "Access Canada's official nutrition database with 5000+ foods. Advanced search, comparison, and analysis tools for nutrition professionals and researchers.",
    type: "website",
    url: "https://ecodish365.com/cnf",
    images: [
      {
        url: "/og-cnf.png",
        width: 1200,
        height: 630,
        alt: "Canadian Nutrient File Database Explorer",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Canadian Nutrient File Database Explorer",
    description: "Access Canada's comprehensive nutrition database with advanced search and analysis tools for professionals.",
    images: ["/twitter-cnf.png"],
  },
  alternates: {
    canonical: "https://ecodish365.com/cnf",
  },
};

export default function CNFLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "Canadian Nutrient File Database Explorer",
    "description": "Interactive explorer for Canada's comprehensive nutrition database containing detailed nutritional information for over 5000 foods",
    "url": "https://ecodish365.com/cnf",
    "creator": {
      "@type": "Organization",
      "name": "EcoDish365",
      "url": "https://ecodish365.com"
    },
    "publisher": {
      "@type": "Organization",
      "name": "Health Canada",
      "url": "https://www.canada.ca/en/health-canada.html"
    },
    "includedInDataCatalog": {
      "@type": "DataCatalog",
      "name": "Canadian Nutrient File",
      "publisher": {
        "@type": "Organization",
        "name": "Health Canada"
      }
    },
    "mainEntity": {
      "@type": "SoftwareApplication",
      "name": "CNF Database Explorer",
      "applicationCategory": "HealthApplication",
      "featureList": [
        "Advanced food search with filters",
        "Nutritional comparison tools", 
        "Statistical analysis features",
        "Food group analytics",
        "Nutrient density calculations",
        "Export capabilities"
      ]
    }
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