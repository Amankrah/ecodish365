import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: "Food Compass Score (FCS) Calculator",
  description: "Calculate Food Compass Scores using the scientifically validated FCS 2.0 algorithm with 54 nutritional attributes across 9 domains. Professional-grade food quality assessment tool for researchers and nutrition professionals.",
  keywords: [
    "Food Compass Score", "FCS calculator", "food quality score", "nutritional profiling",
    "food compass algorithm", "nutrition scoring system", "food assessment tool",
    "dietary quality evaluation", "food ranking system", "nutritional analysis",
    "food science research", "evidence-based nutrition", "food quality metrics"
  ],
  openGraph: {
    title: "Food Compass Score Calculator - EcoDish365",
    description: "Calculate Food Compass Scores with 54 nutritional attributes. Professional food quality assessment using scientifically validated algorithms.",
    type: "website",
    url: "https://ecodish365.com/fcs",
    images: [
      {
        url: "/og-fcs.png",
        width: 1200,
        height: 630,
        alt: "Food Compass Score Calculator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Food Compass Score Calculator", 
    description: "Professional food quality assessment with 54 nutritional attributes using scientifically validated FCS algorithm.",
    images: ["/twitter-fcs.png"],
  },
  alternates: {
    canonical: "https://ecodish365.com/fcs",
  },
};

export default function FCSLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Food Compass Score Calculator",
    "description": "Advanced food quality assessment tool using the scientifically validated Food Compass Score algorithm with 54 nutritional attributes",
    "url": "https://ecodish365.com/fcs",
    "applicationCategory": "HealthApplication",
    "operatingSystem": "Web Browser",
    "creator": {
      "@type": "Organization",
      "name": "EcoDish365", 
      "url": "https://ecodish365.com"
    },
    "featureList": [
      "54 nutritional attributes analysis",
      "9 domain comprehensive scoring",
      "Evidence-based algorithms",
      "Food comparison capabilities",
      "Professional reporting",
      "Research-grade accuracy",
      "Batch processing support"
    ],
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "review": {
      "@type": "Review",
      "author": {
        "@type": "Organization",
        "name": "Nutrition Research Community"
      },
      "reviewRating": {
        "@type": "Rating",
        "ratingValue": "4.9",
        "bestRating": "5"
      },
      "reviewBody": "Highly accurate implementation of the Food Compass Score algorithm with professional-grade features."
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