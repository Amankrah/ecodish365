'use client';

import { useState } from 'react';
import { Camera, Sparkles } from 'lucide-react';
import { AudienceToggle, type UserType } from '@/components/shared/AudienceToggle';
import { PackagedFoodScanner } from '@/components/shared/PackagedFoodScanner';
import { ImproveProductFlow } from '@/components/shared/ImproveProductFlow';

type ScanTab = 'hsr' | 'improve';

export default function ScanProductPage() {
  const [userType, setUserType] = useState<UserType>('individual');
  const [tab, setTab] = useState<ScanTab>('hsr');

  const hsrTabA11y =
    tab === 'hsr'
      ? ({ 'aria-selected': 'true' as const })
      : ({ 'aria-selected': 'false' as const });
  const improveTabA11y =
    tab === 'improve'
      ? ({ 'aria-selected': 'true' as const })
      : ({ 'aria-selected': 'false' as const });

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
              <p className="text-sm text-gray-600 mt-2">
                Photograph the nutrition label to get a Health Star Rating, or work through the
                ingredient list to explore healthier swaps for that product.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                To score a full day of eating with HEFI, HENI, or FCS, use the{' '}
                <a href="/recall-24h" className="text-blue-700 underline">24-hour dietary recall</a>.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex justify-center">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" />
          </div>
        </header>

        <div className="flex gap-1 p-1 bg-gray-100 rounded-lg" role="tablist" aria-label="Scan product mode">
          <button
            type="button"
            role="tab"
            id="scan-tab-hsr"
            {...hsrTabA11y}
            aria-controls="scan-panel-hsr"
            onClick={() => setTab('hsr')}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-md ${
              tab === 'hsr' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
            }`}
          >
            <Camera className="h-4 w-4" aria-hidden="true" />
            Health Star Rating
          </button>
          <button
            type="button"
            role="tab"
            id="scan-tab-improve"
            {...improveTabA11y}
            aria-controls="scan-panel-improve"
            onClick={() => setTab('improve')}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-md ${
              tab === 'improve' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
            }`}
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            Try healthier swaps
          </button>
        </div>

        {tab === 'hsr' && (
          <div id="scan-panel-hsr" role="tabpanel" aria-labelledby="scan-tab-hsr">
            <PackagedFoodScanner userType={userType} />
          </div>
        )}

        {tab === 'improve' && (
          <div id="scan-panel-improve" role="tabpanel" aria-labelledby="scan-tab-improve">
            <ImproveProductFlow />
          </div>
        )}
      </div>
    </main>
  );
}
