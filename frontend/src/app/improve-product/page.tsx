'use client';

import { Sparkles } from 'lucide-react';
import { ImproveProductFlow } from '@/components/shared/ImproveProductFlow';

export default function ImproveProductPage(): JSX.Element {
  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-violet-100 p-3 rounded-lg">
              <Sparkles className="h-8 w-8 text-violet-700" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Improve a product or meal</h1>
              <p className="text-sm text-gray-600 mt-2">
                Start with something you actually eat: a packaged product from your pantry, a
                homemade dish you cook often, or a full day from your food diary. We break it
                into ingredients, suggest realistic swaps, and show how the nutrition scores
                would change if you made them.
              </p>
              <p className="text-xs text-gray-500 mt-3">
                Packaged products are estimated from the label, not measured in a lab. Swaps show
                what a reformulated version could look like in our models. Always review the
                ingredient list before applying a suggestion.
              </p>
            </div>
          </div>
        </header>

        <div className="bg-white rounded-lg border p-6 shadow-sm">
          <ImproveProductFlow />
        </div>
      </div>
    </main>
  );
}
