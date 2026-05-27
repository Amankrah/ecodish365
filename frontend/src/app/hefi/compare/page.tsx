'use client';

import React, { useState } from 'react';
import {
  ChartBarIcon,
  InformationCircleIcon,
  TrophyIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { HEFIApiService, type HEFIComparison, type HEFIInterpretation } from '../../../lib/api';
import {
  ScorerFoodInput,
  type ScorerFoodPoolItem,
} from '@/components/shared/ScorerFoodInput';

type SelectedFood = { FoodID: number; FoodDescription: string; FoodCode?: string; amount_g: number };

function poolToSelected(pool: ScorerFoodPoolItem[]): SelectedFood[] {
  return pool.map(p => ({
    FoodID: p.food_id,
    FoodDescription: p.food_name,
    amount_g: p.amount_g,
  }));
}

function selectedToPool(selected: SelectedFood[]): ScorerFoodPoolItem[] {
  return selected.map(s => ({
    food_id: s.FoodID,
    food_name: s.FoodDescription,
    amount_g: s.amount_g,
  }));
}

const HEFIComparisonDisplay = ({ result }: { result: HEFIComparison }) => {
  const { data } = result;
  const { foods, comparison_insights } = data;

  return (
    <div className="space-y-8">
      {/* Comparison Summary */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Comparison Summary</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {comparison_insights.highest_score?.toFixed(1) || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Highest Score</div>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {comparison_insights.average_score?.toFixed(1) || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Average Score</div>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {comparison_insights.score_range?.toFixed(1) || 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Score Range</div>
          </div>
        </div>

        {comparison_insights.best_performing && (
          <div className="flex items-center justify-center bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <TrophyIcon className="w-6 h-6 text-yellow-600 mr-3" />
            <div>
              <div className="font-semibold text-yellow-900">Best Performing Meal</div>
              <div className="text-yellow-700">{comparison_insights.best_performing}</div>
            </div>
          </div>
        )}
      </div>

      {/* Detailed Comparison */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Detailed Results</h3>
        
        <div className="space-y-6">
          {foods.map((food, index) => {
            const interpretation: HEFIInterpretation | undefined = food.hefi_interpretation;
            const getScoreColor = () => {
              const color = interpretation?.ui_color;
              if (color === 'emerald') return 'text-emerald-700 bg-emerald-50 border-emerald-200';
              if (color === 'green') return 'text-green-700 bg-green-50 border-green-200';
              if (color === 'yellow') return 'text-yellow-700 bg-yellow-50 border-yellow-200';
              if (color === 'red') return 'text-red-700 bg-red-50 border-red-200';
              return 'text-gray-700 bg-gray-50 border-gray-200';
            };

            return (
              <div key={index} className="border border-gray-200 rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 mb-1">
                      {food.food_name}
                    </h4>
                    <div className="text-sm text-gray-500">
                      Food IDs: {food.food_ids.join(', ')}
                    </div>
                  </div>
                  
                  <div className={`px-4 py-2 rounded-lg border text-right ${getScoreColor()}`}>
                    <div className="text-2xl font-bold">
                      {food.total_score.toFixed(1)}
                    </div>
                    <div className="text-sm">
                      {food.percentage.toFixed(1)}%
                    </div>
                    {interpretation && (
                      <div className="text-xs font-semibold mt-1">{interpretation.category}</div>
                    )}
                  </div>
                </div>

                {food.error ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center text-red-700">
                      <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                      Error: {food.error}
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {Object.entries(food.components).slice(0, 10).map(([key, component]) => {
                      const percentage = (component.score / component.max_points) * 100;
                      return (
                        <div key={key} className="text-center">
                          <div className="text-sm font-medium text-gray-900 mb-1">
                            {component.name.replace('C', 'C')}
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                            <div 
                              className="bg-purple-600 h-2 rounded-full"
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-600">
                            {component.score.toFixed(1)}/{component.max_points}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Component Analysis */}
      {comparison_insights.component_analysis && (
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Component Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(comparison_insights.component_analysis).map(([key, analysis]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-4">
                <div className="font-medium text-gray-900 mb-2">
                  {analysis.component_name}
                </div>
                <div className="space-y-1 text-sm text-gray-600">
                  <div>Max: {analysis.max_score.toFixed(1)}</div>
                  <div>Min: {analysis.min_score.toFixed(1)}</div>
                  <div>Variation: {analysis.variation.toFixed(1)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default function HEFIComparePage() {
  const [selectedFoods, setSelectedFoods] = useState<SelectedFood[]>([]);
  const [meals, setMeals] = useState<Array<{ name: string; items: SelectedFood[] }>>([]);
  const [mealName, setMealName] = useState<string>('Meal 1');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<HEFIComparison | null>(null);
  const [error, setError] = useState<string>('');

  const addMealFromSelection = () => {
    if (selectedFoods.length === 0) {
      setError('Add some foods to build a meal first.');
      return;
    }
    const name = mealName?.trim() || `Meal ${meals.length + 1}`;
    setMeals(prev => [...prev, { name, items: selectedFoods }]);
    setSelectedFoods([]);
    setMealName(`Meal ${meals.length + 2}`);
  };

  const removeMeal = (index: number) => {
    setMeals(prev => prev.filter((_, i) => i !== index));
  };

  const compareHEFI = async () => {
    if (meals.length < 2) {
      setError('Please create at least 2 meals to compare.');
      return;
    }
    try {
      setIsLoading(true);
      setError('');
      const compareRequest = {
        foods: meals.map(m => ({
          food_name: m.name,
          food_items: m.items.map(it => ({ food_id: it.FoodID, amount_g: it.amount_g }))
        }))
      };
      const response = await HEFIApiService.compareFoodsHEFI(compareRequest);
      setResult(response);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string } } };
      setError(e?.response?.data?.message || 'Failed to compare HEFI scores');
      console.error('HEFI comparison error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetComparison = () => {
    setSelectedFoods([]);
    setMeals([]);
    setMealName('Meal 1');
    setResult(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HEFI Comparison</h1>
          <p className="text-lg text-gray-600">Create meal groups or day-level combinations and compare their HEFI-2019 alignment. Single-food comparisons are educational only.</p>
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0" />
              <div className="text-sm text-yellow-800">
                <p className="font-semibold">Important: HEFI-2019 measures dietary patterns</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>For valid interpretation, combine foods to represent a complete daily intake (24-hour recall).</li>
                  <li>Single-food results should not be considered a HEFI-2019 assessment.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar Configuration */}
          <aside className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Build a meal</h2>
              <p className="text-xs text-gray-600 mb-4">
                Add foods, save as a named meal, then compare 2+ meals. For a full day use{' '}
                <a href="/hefi/calculate" className="text-purple-700 underline">Calculate HEFI</a>.
              </p>
              <ScorerFoodInput
                mode="pool"
                target="hefi"
                accent="purple"
                userType="individual"
                pool={selectedToPool(selectedFoods)}
                onPoolChange={pool => setSelectedFoods(poolToSelected(pool))}
                poolSearchLabel="Search foods for the current meal"
              />
              <div className="mt-4 space-y-2">
                <div className="flex items-center gap-2">
                  <label htmlFor="meal-name" className="text-xs font-medium text-gray-600">Meal name:</label>
                  <input
                    id="meal-name"
                    type="text"
                    value={mealName}
                    onChange={(e) => setMealName(e.target.value)}
                    className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="e.g., Breakfast, Lunch, Salmon Bowl"
                  />
                </div>
                <button
                  onClick={addMealFromSelection}
                  disabled={selectedFoods.length === 0}
                  className="w-full inline-flex items-center justify-center px-4 py-2 rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
                >
                  Add Meal from Selected Foods
                </button>
              </div>
            </div>

            {/* Saved Meals */}
            {meals.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Meals to compare ({meals.length})</h3>
                <div className="space-y-2">
                  {meals.map((m, idx) => (
                    <div key={idx} className="p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{m.name}</div>
                          <div className="text-xs text-gray-500">{m.items.length} foods, {Math.round(m.items.reduce((s, it) => s + it.amount_g, 0))}g total</div>
                        </div>
                        <button
                          onClick={() => removeMeal(idx)}
                          className="text-red-500 hover:text-red-700 text-xs"
                          aria-label={`Remove ${m.name}`}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Compare Button */}
            {meals.length >= 2 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <button
                  onClick={compareHEFI}
                  disabled={isLoading}
                  className="w-full inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <ChartBarIcon className="mr-2 w-5 h-5" />
                  {isLoading ? 'Comparing...' : 'Compare Meal HEFI Scores'}
                </button>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-3" />
                  <div className="text-red-700">{error}</div>
                </div>
              </div>
            )}
          </aside>

          {/* Main Content */}
          <section className="lg:col-span-2 space-y-8">
            {result ? (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Comparison Results</h2>
                  <button
                    onClick={resetComparison}
                    className="inline-flex items-center text-purple-600 hover:text-purple-700 font-medium"
                  >
                    Start New Comparison
                  </button>
                </div>
                <HEFIComparisonDisplay result={result} />
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <InformationCircleIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
                <p className="text-gray-600 max-w-xl mx-auto">
                  Build at least two meals in the sidebar, then click &quot;Compare Meal HEFI Scores&quot; to see results here.
                </p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}