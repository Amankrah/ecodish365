/**
 * /scan-product — Phase 1 of PKG-IMG-1 (2026-05-26).
 *
 * User uploads a photo of a packaged food's Nutrition Facts panel; a
 * multimodal LLM extracts the panel into a structured JSON; user reviews
 * and confirms the extracted values; we compute Health Star Rating from
 * the (possibly-edited) panel and render an audience-aware result.
 *
 * No CNF FoodID is involved — this path is for products NOT in the
 * Canadian Nutrient File (most branded retail goods). Phase 2 will add
 * ingredient-list extraction to enable HEFI / HENI / dietary-pattern /
 * environmental scoring of the same upload.
 */
'use client';

import { useState } from 'react';
import { Camera } from 'lucide-react';
import { AudienceToggle, type UserType } from '@/components/shared/AudienceToggle';
import { PackagedFoodScanner } from '@/components/shared/PackagedFoodScanner';

export default function ScanProductPage() {
  const [userType, setUserType] = useState<UserType>('individual');

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto space-y-6">
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Camera className="h-8 w-8 text-blue-700" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">Scan a packaged food</h1>
              <p className="text-sm text-gray-600 mt-1">
                Take a photo of the Nutrition Facts panel on any packaged food and
                get its <strong>Health Star Rating</strong>. Works on Canadian
                (bilingual EN/FR), US-FDA, and European (1169/2011) labels.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Phase 1: HSR only. HEFI, HENI, dietary pattern, and environmental
                scoring need an ingredient list (coming in Phase 2).
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex justify-center">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" />
          </div>
        </header>

        <PackagedFoodScanner userType={userType} />
      </div>
    </main>
  );
}
