import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'HENI - Health Nutritional Impact Analysis | DISH Research',
  description: 'Comprehensive health impact analysis using evidence-based DALY methodology. Analyze how food choices affect your health with HENI scoring.',
  keywords: 'HENI, health impact, nutritional analysis, DALY, food health, evidence-based nutrition, health assessment',
  openGraph: {
    title: 'HENI - Health Nutritional Impact Analysis',
    description: 'Evidence-based health impact analysis using DALY methodology for individuals, researchers, and policy makers.',
    type: 'website',
    siteName: 'DISH Research Tools',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'HENI - Health Nutritional Impact Analysis',
    description: 'Evidence-based health impact analysis using DALY methodology.',
  }
};

export default function HENILayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="heni-layout">
      {children}
    </div>
  );
}