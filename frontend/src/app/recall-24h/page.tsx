/**
 * /recall-24h — dedicated page for the 24-h dietary recall wizard (AI-MATCH-2).
 *
 * Walk users through a six-occasion 24-h recall (breakfast / AM snack /
 * lunch / PM snack / dinner / evening snack), decompose each meal into CNF
 * ingredients via the existing decomposer, aggregate into a single daily
 * list, and route to HEFI / HENI / HSR / FCS / Environmental.
 *
 * Designed to be the natural anchor for HEFI: Brassard 2022b explicitly
 * built HEFI-2019 against CCHS-Nutrition 24-h recall data, and the
 * mandatory single-day caveat (already shipped in `hefi_explanations.py`)
 * automatically surfaces when this recall routes into HEFI scoring.
 *
 * Trigger buttons on the HENI + HEFI calculate pages pre-select their
 * respective score on Step 4 via the `?then=hefi|heni` query param.
 */
'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { CalendarClock, BookOpen } from 'lucide-react';
import { AudienceToggle, type UserType } from '@/components/shared/AudienceToggle';
import { Recall24hWizard } from '@/components/shared/Recall24hWizard';

function RecallPageInner() {
  const [userType, setUserType] = useState<UserType>('individual');
  const params = useSearchParams();
  const then = params?.get('then');
  const preselect = (then === 'hefi' || then === 'heni' || then === 'hsr'
                  || then === 'fcs'  || then === 'environmental'
                  || then === 'dietary_pattern') ? then : undefined;

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="bg-white rounded-lg border p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <CalendarClock className="h-8 w-8 text-blue-700" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <h1 className="text-2xl font-bold text-gray-900">24-hour dietary recall</h1>
                <a
                  href="/recall-history"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 text-sm font-medium rounded-md whitespace-nowrap"
                >
                  <BookOpen className="h-4 w-4" aria-hidden="true" />
                  My recall history
                </a>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Walk through your day occasion-by-occasion. We&rsquo;ll decompose each meal into Canadian Nutrient File (CNF) ingredients, aggregate your full day, and let you score it against HEFI&nbsp;/&nbsp;HENI&nbsp;/&nbsp;HSR&nbsp;/&nbsp;FCS&nbsp;/&nbsp;Environmental impact.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Best for HEFI-2019 (Brassard&nbsp;2022b designed it explicitly for 24-h recall data) and HENI (sums healthy-life-minutes across the day).
                Save individual days to <a href="/recall-history" className="text-amber-800 underline">recall history</a> to score N-day-average patterns.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex justify-center">
            <AudienceToggle userType={userType} onChange={setUserType} accent="blue" />
          </div>
        </header>

        <div className="bg-white rounded-lg border p-6 shadow-sm">
          <Recall24hWizard userType={userType} preselectScore={preselect} />
        </div>
      </div>
    </main>
  );
}

export default function Recall24hPage() {
  // useSearchParams requires Suspense in the Next.js App Router.
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50" />}>
      <RecallPageInner />
    </Suspense>
  );
}
