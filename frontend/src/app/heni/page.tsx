'use client';

import React from 'react';
import Link from 'next/link';
import {
  Calculator,
  LayoutGrid,
  Heart,
  TrendingUp,
  AlertTriangle,
  CalendarClock,
  BarChart3,
} from 'lucide-react';

// Stylianou 2021 (Nature Food 2:616-627), Suppl. Table 3 illustrative examples.
const heniExamples = [
  { food: 'Processed meat (hot dog)', minutes: -36, color: 'red' },
  { food: 'Sugar-sweetened beverage (12 oz)', minutes: -12, color: 'red' },
  { food: 'White bread (1 slice)', minutes: -1.8, color: 'amber' },
  { food: 'Egg (1, scrambled)', minutes: -0.6, color: 'amber' },
  { food: 'Chicken wing', minutes: +0.1, color: 'gray' },
  { food: 'Apple (medium)', minutes: +2.0, color: 'green' },
  { food: 'Broccoli (1 cup)', minutes: +4.9, color: 'green' },
  { food: 'Walnuts (1 oz)', minutes: +7.6, color: 'green' },
];

const colorClasses: Record<string, string> = {
  red:   'border-red-200 bg-red-50 text-red-900',
  amber: 'border-amber-200 bg-amber-50 text-amber-900',
  gray:  'border-gray-200 bg-gray-50 text-gray-800',
  green: 'border-green-200 bg-green-50 text-green-900',
};

export default function HENIHomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="relative py-12 max-w-7xl mx-auto px-6">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-4">
            <Heart className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
            Health Nutritional Index (HENI)
          </h1>
          <p className="text-lg text-gray-700 max-w-3xl mx-auto leading-relaxed">
            Net <strong>minutes of healthy life</strong> a food adds or subtracts per serving —
            computed from <strong>15 GBD dietary risk factors</strong> via Disability-Adjusted Life
            Year (DALY) loss attributable to US adult diet, then converted to time.
          </p>
          <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mt-5 text-sm text-amber-900 text-left">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Population-marginal estimate, not a personal prediction.</strong> Assumes
              each food&apos;s effect is independent and multiplicative; US-anchored
              epidemiology (Canadian portability is documented future work). For day-level
              guideline adherence see <Link href="/hefi" className="underline">HEFI-2019</Link>.
            </span>
          </div>
        </div>

        {/* Primary CTAs */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-12">
          <Link href="/heni/calculate" className="group">
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 group-hover:border-blue-200 h-full">
              <div className="inline-flex items-center justify-center p-3 bg-blue-100 rounded-full mb-3 group-hover:bg-blue-200 transition-colors">
                <Calculator className="h-7 w-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">HENI Calculator</h3>
              <p className="text-gray-600 leading-relaxed text-sm">
                Score a meal or full day with healthy-life minutes, risk-factor breakdown,
                and audience-aware explanations (individual, researcher, or policy).
              </p>
              <div className="mt-3 text-blue-700 font-medium group-hover:text-blue-800 text-sm">
                Start analysis →
              </div>
            </div>
          </Link>

          <Link href="/scorecard" className="group">
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 group-hover:border-purple-200 h-full">
              <div className="inline-flex items-center justify-center p-3 bg-purple-100 rounded-full mb-3 group-hover:bg-purple-200 transition-colors">
                <LayoutGrid className="h-7 w-7 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">✨ Multi-metric Scorecard</h3>
              <p className="text-gray-600 leading-relaxed text-sm">
                Combine HENI with HEFI, FCS, HSR, environmental impact, and dietary pattern on one
                panel. Toggle <em>Policy</em> audience mode for procurement and briefing context.
              </p>
              <div className="mt-3 text-purple-700 font-medium group-hover:text-purple-800 text-sm">
                Open Scorecard →
              </div>
            </div>
          </Link>
        </div>

        {/* Secondary CTAs */}
        <div className="grid md:grid-cols-2 gap-4 max-w-4xl mx-auto mb-12">
          <Link
            href="/recall-24h?then=heni"
            className="bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-md transition flex items-center gap-3"
          >
            <CalendarClock className="h-6 w-6 text-blue-700 flex-shrink-0" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-gray-900">Build a 24-h recall → HENI</div>
              <div className="text-xs text-gray-600">
                Aggregate occasion-by-occasion eating, then sum HENI minutes across the day.
              </div>
            </div>
          </Link>
          <Link
            href="/heni/policy-dashboard"
            className="bg-white border border-gray-200 rounded-xl p-4 hover:border-purple-300 hover:shadow-md transition flex items-center gap-3"
          >
            <BarChart3 className="h-6 w-6 text-purple-700 flex-shrink-0" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-gray-900">Policy dashboard</div>
              <div className="text-xs text-gray-600">
                Population-level framing for procurement, taxation, and food-environment analysis.
              </div>
            </div>
          </Link>
        </div>

        {/* Worked examples */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-1">What does &quot;minutes of healthy life&quot; mean?</h2>
          <p className="text-sm text-gray-600 mb-4">
            Illustrative per-serving values from Stylianou et&nbsp;al.&nbsp;2021 (Nature Food, Suppl.&nbsp;Table 3).
            Positive = adds time; negative = subtracts time. The signal is small per serving and
            adds up across a day or year of eating.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {heniExamples.map((ex) => (
              <div
                key={ex.food}
                className={`border rounded-lg p-3 ${colorClasses[ex.color]}`}
              >
                <div className="text-2xl font-bold leading-tight">
                  {ex.minutes >= 0 ? '+' : '−'}{Math.abs(ex.minutes).toFixed(ex.minutes < 1 && ex.minutes > -1 ? 1 : 0)} min
                </div>
                <div className="text-xs mt-1">{ex.food}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Methodology summary */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">How HENI is computed</h2>
          <ol className="space-y-4 text-sm text-gray-700 list-decimal list-inside">
            <li>
              <strong className="text-gray-900">15 GBD dietary risk factors.</strong> For each food,
              identify which Global Burden of Disease 2017 dietary risks it contributes to
              (fruits, vegetables, nuts, whole grains, legumes, milk, processed meat, red meat,
              sugar-sweetened beverages, sodium, trans fat, fibre and sources, cholesterol,
              polyunsaturated fat, alcohol).
            </li>
            <li>
              <strong className="text-gray-900">DALY-loss attribution.</strong> Use risk-outcome
              dose-response functions from the GBD 2017 Diet Collaborators to compute the change in
              DALYs (micro-units) per serving for the US adult diet population.
            </li>
            <li>
              <strong className="text-gray-900">Convert DALYs → minutes.</strong> Multiply by the
              published constant <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">−0.5256 min / μDALY</code>{' '}
              (Stylianou&nbsp;2021), with sign convention so positive minutes = healthy life added.
            </li>
            <li>
              <strong className="text-gray-900">Aggregate across foods.</strong> Sum per-food minutes
              for a meal or full day. The 24-h recall handoff above is the cleanest input.
            </li>
          </ol>
        </div>

        {/* Stats */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-5">Scope</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-1">15</div>
              <div className="text-sm text-gray-700 font-medium">GBD dietary risk factors</div>
              <div className="text-xs text-gray-500 mt-1">Stylianou 2021 Table 1</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-1">6,719</div>
              <div className="text-sm text-gray-700 font-medium">Foods in catalog</div>
              <div className="text-xs text-gray-500 mt-1">CNF 5,691 + WAFCT 1,028</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-1">−0.526</div>
              <div className="text-sm text-gray-700 font-medium">min / μDALY conversion</div>
              <div className="text-xs text-gray-500 mt-1">Published constant</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-600 mb-1">GBD 2017</div>
              <div className="text-sm text-gray-700 font-medium">Epidemiology vintage</div>
              <div className="text-xs text-gray-500 mt-1">Lancet 392:1958</div>
            </div>
          </div>
        </div>

        {/* Food databases */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Food composition databases</h2>
          <p className="text-sm text-gray-700 mb-4">
            HENI is computed on every food in our cross-database catalog. The 15 GBD dietary risk
            factors are mapped to CNF + WAFCT food groups via the same pipeline used for HEFI / HSR / FCS.
            WAFCT&apos;s phytate / IP3-6 columns (which would matter for iron / zinc bioavailability)
            are not yet wired into HENI scoring — a researcher-mode caveat surfaces when a WAFCT food
            is present.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="border border-gray-100 rounded-lg p-3">
              <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Active</div>
              <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
              <div className="text-xs text-gray-600 mt-0.5">5,691 foods · Health Canada</div>
            </div>
            <div className="border border-gray-100 rounded-lg p-3">
              <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Active</div>
              <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
              <div className="text-xs text-gray-600 mt-0.5">1,028 West African foods · researcher caveat for HENI</div>
            </div>
            <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
              <div className="text-sm font-medium text-gray-700 mt-1">Further composition tables</div>
              <div className="text-xs mt-0.5">Additional regional FCTs + Canadian-anchored GBD risk-factor recalibration.</div>
            </div>
          </div>
        </div>

        {/* What HENI isn't */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 mb-12">
          <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            What HENI is <em>not</em>
          </h2>
          <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
            <li><strong>Not a personal life-expectancy prediction.</strong> HENI is the population-marginal effect; your individual outcome depends on factors HENI doesn&apos;t model.</li>
            <li><strong>Not applicable to radical diet restructuring.</strong> Assumes small substitutions; the multiplicative-independence assumption breaks under wholesale change.</li>
            <li><strong>Not Canadian-validated.</strong> Built on US epidemiology; Canadian portability is documented future work in the manuscript.</li>
            <li><strong>Limited GBD scope.</strong> Excludes saturated fat (modelled indirectly via cholesterol), vitamin D, ultra-processing, cooking methods, and bioavailability.</li>
          </ul>
        </div>

        {/* Audience modes + citations */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="inline-flex items-center justify-center p-2 bg-blue-100 rounded-lg mb-3">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Audience modes</h3>
            <p className="text-sm text-gray-600">
              Three explanation packs (AUDIENCE-CODE-1):
              <strong> Individual</strong> (plain-English minutes-of-life framing),
              <strong> Researcher</strong> (per-risk-factor breakdown, GBD 2017
              dose-response provenance, conversion-constant audit), and
              <strong> Policy</strong> (population framing for procurement &
              substitution analyses).
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="inline-flex items-center justify-center p-2 bg-green-100 rounded-lg mb-3">
              <BarChart3 className="h-5 w-5 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Pair with other lenses</h3>
            <p className="text-sm text-gray-600">
              HENI answers <em>&quot;how many minutes?&quot;</em>; HEFI answers <em>&quot;does this
              align with the Food Guide?&quot;</em>; HSR answers <em>&quot;is this product
              better than its peers?&quot;</em> — different questions about the same foods.
              The <Link href="/scorecard" className="text-blue-700 underline">Scorecard</Link> runs all six in parallel.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="inline-flex items-center justify-center p-2 bg-purple-100 rounded-lg mb-3">
              <Heart className="h-5 w-5 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Primary references</h3>
            <ul className="text-xs text-gray-700 space-y-1 list-disc list-inside">
              <li>Stylianou K. S. et al. (2021). HENI framework. <em>Nature Food</em> 2, 616–627.</li>
              <li>Stylianou K. S. et al. (2016). LCA × nutrition method. <em>Int J LCA</em> 21, 734–746.</li>
              <li>GBD 2017 Diet Collaborators. <em>Lancet</em> 393, 1958–1972.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
