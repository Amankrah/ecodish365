import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import Navigation from "@/components/layout/Navigation";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "@/contexts/AuthContext";

const SITE_URL = "https://ecodish365.com";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "EcoDish365: Honest nutrition and sustainability scoring for any food",
    template: "%s | EcoDish365",
  },
  description:
    "Score any food, meal, or full day against six published research measures. Plain-language results, real uncertainty, and the limits the science actually states. 7,000+ foods, no invented grades, no single score pretending to settle it.",
  keywords: [
    "nutrition analysis", "Canadian Nutrient File", "CNF database", "food research", 
    "Health Star Rating", "HSR calculator", "Food Compass Score", "FCS calculator",
    "nutritional assessment", "food comparison", "dietary analysis", "nutrition research",
    "environmental nutrition", "food sustainability", "nutrition database",
    "food science", "dietitian tools", "nutrition professionals", "health analysis",
    "food nutrients", "calorie calculator", "macro nutrients", "micro nutrients"
  ],
  authors: [{ name: "EcoDish365 Research Team", url: "https://ecodish365.com" }],
  creator: "EcoDish365",
  publisher: "EcoDish365",
  category: "Health & Nutrition Technology",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_URL,
    siteName: "EcoDish365",
    title: "EcoDish365: Honest nutrition and sustainability scoring for any food",
    description:
      "Score any food, meal, or full day against six published research measures. Plain-language results with the limits the science states. 7,000+ foods.",
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "EcoDish365: Honest nutrition and sustainability scoring",
        type: "image/png",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "EcoDish365: Honest nutrition and sustainability scoring for any food",
    description:
      "Six published lenses. Plain-language results. No single composite score.",
    images: [`${SITE_URL}/og-image.png`],
    creator: "@ecodish365",
    site: "@ecodish365",
  },
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
  },
  other: {
    "theme-color": "#0ea5e9",
    "msapplication-TileColor": "#0ea5e9",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "EcoDish365",
    "alternateName": "EcoDish365 Nutrition Research Platform",
    "url": "https://ecodish365.com",
    "description": "Professional nutrition analysis platform with comprehensive food database and research tools",
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://ecodish365.com/cnf/search?q={search_term_string}"
      },
      "query-input": "required name=search_term_string"
    },
    "publisher": {
      "@type": "Organization",
      "name": "EcoDish365",
      "url": "https://ecodish365.com",
      "logo": {
        "@type": "ImageObject",
        "url": "https://ecodish365.com/logo.png",
        "width": 300,
        "height": 100
      },
      "sameAs": [
        "https://twitter.com/ecodish365",
        "https://linkedin.com/company/ecodish365"
      ]
    },
    "mainEntity": {
      "@type": "SoftwareApplication",
      "name": "EcoDish365 Platform",
      "applicationCategory": "HealthApplication",
      "operatingSystem": "Web Browser",
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      },
      "featureList": [
        "Canadian Nutrient File Database Access",
        "Health Star Rating Calculator",
        "Food Compass Score Calculator",
        "Nutritional Analysis Tools",
        "Food Comparison Features",
        "Environmental Impact Assessment"
      ]
    }
  };

  return (
    <html lang="en" className={inter.variable}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>
      <body className={`${inter.className} min-h-screen bg-gray-50`}>
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
            <Navigation />
            <main className="flex-1">
              {children}
            </main>
            <footer className="bg-white border-t border-gray-200 py-8">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row justify-between items-center">
                  <div className="flex items-center space-x-2 mb-4 md:mb-0">
                    <span className="text-sm text-gray-600">
                      © 2026 EcoDish365. All rights reserved.
                    </span>
                  </div>
                  <div className="flex items-center space-x-6">
                    <Link href="/privacy" className="text-sm text-gray-600 hover:text-gray-900">
                      Privacy Policy
                    </Link>
                    <Link href="/terms" className="text-sm text-gray-600 hover:text-gray-900">
                      Terms of Service
                    </Link>
                    <Link href="/documentation" className="text-sm text-gray-600 hover:text-gray-900">
                      Documentation
                    </Link>
                  </div>
                </div>
              </div>
            </footer>
          </div>
        </AuthProvider>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: "#363636",
              color: "#fff",
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: "#10b981",
                secondary: "#fff",
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: "#ef4444",
                secondary: "#fff",
              },
            },
          }}
        />
      </body>
    </html>
  );
}
