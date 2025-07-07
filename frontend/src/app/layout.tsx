import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/layout/Navigation";
import { Toaster } from "react-hot-toast";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "EcoDish365 - Environmental Nutrition & Health Tools",
  description: "A comprehensive platform for environmental nutrition and health tools, helping researchers, individuals, and policy makers make informed decisions.",
  keywords: ["nutrition", "environment", "health", "Canadian Nutrient File", "CNF", "food analysis"],
  authors: [{ name: "EcoDish365 Team" }],
  openGraph: {
    title: "EcoDish365 - Environmental Nutrition & Health Tools",
    description: "A comprehensive platform for environmental nutrition and health tools",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} min-h-screen bg-gray-50`}>
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
                    © 2025 EcoDish365. All rights reserved.
                  </span>
                </div>
                <div className="flex items-center space-x-6">
                  <a href="#" className="text-sm text-gray-600 hover:text-gray-900">
                    Privacy Policy
                  </a>
                  <a href="#" className="text-sm text-gray-600 hover:text-gray-900">
                    Terms of Service
                  </a>
                  <a href="#" className="text-sm text-gray-600 hover:text-gray-900">
                    Documentation
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>
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
