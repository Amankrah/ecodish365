/**
 * Environmental Food Comparison Page
 * Side-by-side environmental impact comparison of multiple foods
 */

import React from 'react';
import EnvironmentalFoodComparison from '@/components/environmental-component/EnvironmentalFoodComparison';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Environmental Food Comparison | EcoDish365',
  description: 'Compare the environmental impacts of different foods side-by-side using comprehensive LCA methodology. Identify the most sustainable food choices for your diet.',
  keywords: 'food comparison, environmental comparison, carbon footprint comparison, sustainable food choices, LCA comparison, food environmental impact',
  openGraph: {
    title: 'Environmental Food Comparison | EcoDish365',
    description: 'Side-by-side environmental impact comparison of multiple foods with detailed analysis',
    type: 'website',
  },
};

export default function EnvironmentalComparePage() {
  return <EnvironmentalFoodComparison />;
}