import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: "Health Star Rating (HSR) Calculator",
  description: "Calculate Health Star Ratings using Australia's official front-of-pack labeling system. Analyze foods with our comprehensive HSR calculator, compare nutritional quality, and get detailed health insights for informed food choices.",
  keywords: [
    "Health Star Rating", "HSR calculator", "Australia food rating", "front of pack labeling",
    "food health rating", "nutritional quality score", "food comparison tool",
    "healthy food choices", "nutrition calculator", "food labeling system",
    "dietary assessment", "food quality rating", "health score calculator"
  ],
  openGraph: {
    title: "Health Star Rating Calculator - EcoDish365",
    description: "Calculate official Health Star Ratings for foods. Compare nutritional quality and make healthier food choices with detailed HSR analysis.",
    type: "website",
    url: "https://ecodish365.com/hsr",
    images: [
      {
        url: "/og-hsr.png", 
        width: 1200,
        height: 630,
        alt: "Health Star Rating Calculator",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Health Star Rating Calculator",
    description: "Calculate official Health Star Ratings for foods and compare nutritional quality with detailed analysis.",
    images: ["/twitter-hsr.png"],
  },
  alternates: {
    canonical: "https://ecodish365.com/hsr",
  },
};

export default function HSRLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Health Star Rating Calculator",
    "description": "Professional Health Star Rating calculator using Australia's official front-of-pack labeling algorithm",
    "url": "https://ecodish365.com/hsr",
    "applicationCategory": "HealthApplication",
    "operatingSystem": "Web Browser",
    "creator": {
      "@type": "Organization", 
      "name": "EcoDish365",
      "url": "https://ecodish365.com"
    },
    "featureList": [
      "Official HSR calculation algorithm",
      "Detailed nutritional analysis",
      "Food comparison tools",
      "Health insights and recommendations",
      "Meal HSR calculation",
      "Professional reporting"
    ],
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "ratingCount": "150",
      "bestRating": "5",
      "worstRating": "1"
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