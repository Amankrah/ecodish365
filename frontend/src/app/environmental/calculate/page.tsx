/**
 * Environmental Impact Calculator Page
 * Full-featured environmental impact analysis for meals and foods
 */

import React from 'react';
import EnvironmentalCalculator from '@/components/environmental-component/EnvironmentalCalculator';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Environmental Impact Calculator | EcoDish365',
  description: 'Analyze your meal\'s environmental impact using comprehensive Life Cycle Assessment (LCA) methodology with Canadian-specific factors and economic valuation. Get detailed insights on climate change, water use, land impact, and more.',
  keywords: 'environmental impact, LCA, life cycle assessment, carbon footprint, water footprint, sustainable food, ReCiPe 2016, Canadian environmental factors',
  openGraph: {
    title: 'Environmental Impact Calculator | EcoDish365',
    description: 'Comprehensive environmental impact analysis for your meals using scientific LCA methodology',
    type: 'website',
  },
};

export default function EnvironmentalCalculatePage() {
  return <EnvironmentalCalculator />;
}