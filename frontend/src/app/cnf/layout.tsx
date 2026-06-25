import type { Metadata } from 'next';
import { CnfExplorerShell } from '@/components/cnf/CnfExplorerShell';

export const metadata: Metadata = {
  title: "Food Catalogue — CNF + WAFCT + FDC",
  description: "Explore three food-composition databases side by side: Health Canada's CNF (5,993 foods, 150+ nutrients), FAO/INFOODS' WAFCT 2019 (1,028 West African foods including fonio, baobab, dawadawa), and USDA FoodData Central (13,620 US foods spanning Foundation, SR Legacy, and Survey FNDDS). Search, compare, and analyze nutritional content with advanced filtering and per-source provenance.",
  keywords: [
    "Canadian Nutrient File", "CNF database", "Canada nutrition database",
    "WAFCT", "West African Food Composition Table", "FAO INFOODS",
    "USDA FoodData Central", "FDC", "Foundation Foods", "SR Legacy", "FNDDS",
    "fonio nutrition", "baobab nutrition", "African food database",
    "food nutrients Canada", "US food nutrients", "nutritional analysis", "Health Canada food data",
    "food composition database", "nutrient search tool", "nutrition research database",
    "food comparison tool", "dietary analysis", "cross-database nutrition"
  ],
  openGraph: {
    title: "Food Composition Database Explorer (CNF + WAFCT + FDC) — EcoDish365",
    description: "Access three nutrition databases side by side: Canada's CNF (5,993 foods), FAO/INFOODS WAFCT 2019 (1,028 West African foods), and USDA FoodData Central (13,620 US foods). Advanced search, comparison, and analysis tools.",
    type: "website",
    url: "https://ecodish365.com/cnf",
    images: [
      {
        url: "/og-cnf.png",
        width: 1200,
        height: 630,
        alt: "Food Composition Database Explorer — CNF + WAFCT + FDC",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Food Composition Database Explorer (CNF + WAFCT + FDC)",
    description: "Health Canada's CNF (5,993 foods), FAO/INFOODS WAFCT 2019 (1,028 West African foods), and USDA FoodData Central (13,620 US foods) — one search, one comparison surface.",
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
    "name": "Food Composition Database Explorer (CNF + WAFCT + FDC)",
    "description": "Interactive explorer combining Health Canada's Canadian Nutrient File (5,993 foods), FAO/INFOODS' West African Food Composition Table 2019 (1,028 foods), and USDA FoodData Central (13,620 foods across Foundation, SR Legacy, and Survey FNDDS) into a single search + comparison surface.",
    "url": "https://ecodish365.com/cnf",
    "creator": {
      "@type": "Organization",
      "name": "EcoDish365",
      "url": "https://ecodish365.com"
    },
    "publisher": [
      {
        "@type": "Organization",
        "name": "Health Canada",
        "url": "https://www.canada.ca/en/health-canada.html"
      },
      {
        "@type": "Organization",
        "name": "FAO / Bioversity / CIRAD (WAFCT 2019)",
        "url": "https://www.fao.org/infoods/infoods/tables-and-databases/faoinfoods-databases/en/"
      },
      {
        "@type": "Organization",
        "name": "USDA Agricultural Research Service (FoodData Central)",
        "url": "https://fdc.nal.usda.gov/"
      }
    ],
    "includedInDataCatalog": [
      {
        "@type": "DataCatalog",
        "name": "Canadian Nutrient File",
        "publisher": { "@type": "Organization", "name": "Health Canada" }
      },
      {
        "@type": "DataCatalog",
        "name": "FAO/INFOODS West African Food Composition Table 2019",
        "publisher": { "@type": "Organization", "name": "FAO" }
      },
      {
        "@type": "DataCatalog",
        "name": "USDA FoodData Central (Foundation, SR Legacy, Survey FNDDS)",
        "publisher": { "@type": "Organization", "name": "USDA Agricultural Research Service" }
      }
    ],
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
      <CnfExplorerShell>{children}</CnfExplorerShell>
    </>
  );
}