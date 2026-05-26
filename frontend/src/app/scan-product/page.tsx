/**
 * /scan-product — HSR scoring from a packaged-food Nutrition Facts photo.
 *
 * User uploads a photo of a Nutrition Facts panel; a multimodal LLM extracts
 * structured values; the user confirms; we compute Health Star Rating.
 *
 * HEFI / HENI / FCS use the 24-h recall wizard (/recall-24h) with per-occasion
 * packaged-food scanning instead.
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
                For HEFI, HENI, or FCS, use the{' '}
                <a href="/recall-24h" className="text-blue-700 underline">24-hour dietary recall</a>
                {' '}and scan packaged foods per occasion (breakfast, snack, etc.).
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
