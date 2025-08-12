/**
 * Environmental Food Profile Page
 * Detailed environmental profile analysis for individual foods
 */

import React from 'react';
import EnvironmentalFoodProfile from '@/components/environmental-component/EnvironmentalFoodProfile';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Food Environmental Profile | EcoDish365',
  description: 'Get detailed environmental profiles for individual foods with comprehensive LCA analysis, comparative context, and sustainability assessment.',
  keywords: 'food profile, environmental profile, food LCA, individual food analysis, sustainability assessment, food environmental impact',
  openGraph: {
    title: 'Food Environmental Profile | EcoDish365',
    description: 'Comprehensive environmental profiling for individual foods with detailed analysis and context',
    type: 'website',
  },
};

export default function FoodProfilePage() {
  return <EnvironmentalFoodProfile />;
}