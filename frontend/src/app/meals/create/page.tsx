'use client';

import React from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import MealCreator from '@/components/meals/MealCreator';

export default function CreateMealPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <MealCreator />
      </div>
    </ProtectedRoute>
  );
}