'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CNFApiService, type Food } from '@/lib/api';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import { FoodProfileContent } from '@/components/cnf/FoodProfileContent';

export default function CNFFoodProfilePage() {
  const params = useParams();
  const foodId = parseInt(String(params.id), 10);
  const { userType, resolveGroupName } = useCnfExplorer();
  const [food, setFood] = useState<Food | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!Number.isFinite(foodId) || foodId <= 0) {
      setError('Invalid food ID');
      setLoading(false);
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await CNFApiService.getFoodDetails(foodId);
        if (!cancelled) {
          setFood(data);
          document.title = `${data.FoodDescription} | EcoDish365`;
        }
      } catch {
        if (!cancelled) setError('Food not found in the catalogue.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [foodId]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center text-gray-600">
        Loading food profile…
      </div>
    );
  }

  if (error || !food) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Food not found</h1>
        <p className="text-gray-600 mb-6">{error ?? 'This food ID is not in the catalogue.'}</p>
        <Link href="/cnf/search" className="text-blue-700 hover:underline text-sm font-medium">
          ← Back to search
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <FoodProfileContent
          food={food}
          userType={userType}
          groupLabel={resolveGroupName(food.FoodGroupID, food.FoodGroupName)}
          variant="page"
        />
      </div>
    </div>
  );
}
