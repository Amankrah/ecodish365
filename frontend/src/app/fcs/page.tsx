'use client';

import React from 'react';
import Link from 'next/link';
import {
  BeakerIcon,
  CalculatorIcon,
  ChartBarIcon,
  ScaleIcon,
  UserIcon,
  BuildingOfficeIcon,
  DocumentChartBarIcon,
  SparklesIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';

export default function FCSMainPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 via-white to-green-50 rounded-3xl p-8 mb-16">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-green-500 rounded-full flex items-center justify-center">
                <SparklesIcon className="w-12 h-12 text-white" />
              </div>
            </div>
            <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-4">
              Food Compass <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-green-600">FCS-10</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-4xl mx-auto mb-6 leading-relaxed">
              An <strong>18-attribute</strong> label-grounded simplification of the original 54-attribute
              Food Compass Score, scored 1–10 per food (FCS-10) or 1–100 for a full day&apos;s
              eating (energy-weighted <strong>i.FCS</strong>).
            </p>

            {/* Honest framing banner */}
            <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-6 text-sm text-amber-900 text-left">
              <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                FCS-10 is validated <em>indirectly</em>: Spearman r = 0.93 against the
                mortality-validated full Food Compass (O&apos;Hearn 2022, NHANES). Built on
                US data — Canadian validation is pending. Does not replace clinical nutrition advice.
              </span>
            </div>

            <div className="inline-flex items-center bg-gradient-to-r from-blue-100 to-green-100 border border-blue-200 rounded-full px-6 py-3 mb-8">
              <SparklesIcon className="w-5 h-5 text-blue-600 mr-2" />
              <span className="text-sm text-blue-800">
                FCS-10 methodology:{' '}
                <a href="https://doi.org/10.1016/j.ajcnut.2024.10.020" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-900">
                  Barrett et al. 2025 (AJCN)
                </a>{' '}
                · Original Food Compass:{' '}
                <a href="https://www.nature.com/articles/s43016-021-00381-y" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-900">
                  Mozaffarian et al. 2021 (Nature Food)
                </a>
              </span>
            </div>

            {/* Score bands */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto mb-8">
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-green-200">
                <div className="text-2xl font-bold text-green-700 mb-1">Encourage</div>
                <div className="text-sm text-gray-700">FCS-10 ≥ 7 / i.FCS ≥ 70</div>
                <div className="text-xs text-gray-500 mt-1">Mostly whole vegetables, fruits, legumes, nuts, seafood, whole grains</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-amber-200">
                <div className="text-2xl font-bold text-amber-700 mb-1">Moderate</div>
                <div className="text-sm text-gray-700">FCS-10 4–6 / i.FCS 31–69</div>
                <div className="text-xs text-gray-500 mt-1">Most dairy, eggs, poultry, lightly processed staples</div>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-xl p-5 shadow-sm border border-red-200">
                <div className="text-2xl font-bold text-red-700 mb-1">Limit</div>
                <div className="text-sm text-gray-700">FCS-10 ≤ 3 / i.FCS ≤ 30</div>
                <div className="text-xs text-gray-500 mt-1">Most ultra-processed foods, sugary beverages, animal fats</div>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/fcs/calculate"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-xl text-white bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Calculate FCS now
                <ArrowRightIcon className="ml-2 w-5 h-5" />
              </Link>
              <Link
                href="/scorecard"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-xl text-gray-700 bg-white/80 backdrop-blur-sm hover:bg-gray-50 transition-colors duration-200 shadow-sm"
              >
                ✨ See FCS alongside all 6 metrics
              </Link>
            </div>
          </div>
        </section>

        {/* Feature Cards */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">FCS tools</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Score a single packaged product, an entire day&apos;s eating, or rank multiple foods side-by-side.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Scan card */}
            <Link href="/scan-product" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-amber-500 to-amber-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <SparklesIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">📷 Scan a product</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Photo of NF panel + ingredients → AI extracts → FCS-10 scores the product against its FCS-10 attribute set.
                  </p>
                  <div className="flex items-center text-amber-700 text-sm font-medium">
                    <span>Scan now</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>

            {/* Calculate card */}
            <Link href="/fcs/calculate" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <CalculatorIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">FCS Calculator</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Pick foods from the integrated catalog (CNF or WAFCT). Single food → FCS-10 (1–10); multi-food day → i.FCS (1–100, energy-weighted mean).
                  </p>
                  <div className="flex items-center text-blue-700 text-sm font-medium">
                    <span>Start calculating</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>

            {/* Food profile card */}
            <Link href="/fcs/food-profile" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <BeakerIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Single-food profile</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Deep-dive across the 9 domains for any food in the catalog — every attribute, every penalty, every NOVA tier.
                  </p>
                  <div className="flex items-center text-green-700 text-sm font-medium">
                    <span>Explore profile</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>

            {/* Compare card */}
            <Link href="/fcs/compare" className="group">
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group-hover:-translate-y-1 h-full">
                <div className="p-6">
                  <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    <ScaleIcon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Compare Foods</h3>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    Rank products side-by-side. Works across food types (unlike HSR&apos;s within-category rule).
                  </p>
                  <div className="flex items-center text-purple-700 text-sm font-medium">
                    <span>Compare</span>
                    <ArrowRightIcon className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>
          </div>
        </section>

        {/* Day-level i.FCS via recall handoff */}
        <section className="mb-16">
          <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-2xl p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Build a full day → score i.FCS
                </h2>
                <p className="text-gray-700 mb-3">
                  i.FCS (diet-level Food Compass) is an energy-weighted mean of per-food FCS-10
                  scores across a complete day. The cleanest input is a 24-h dietary recall
                  built occasion-by-occasion.
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link
                    href="/recall-24h?then=fcs"
                    className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                  >
                    Open 24-h recall wizard →
                  </Link>
                  <Link
                    href="/recall-history"
                    className="inline-flex items-center justify-center px-4 py-2 bg-white text-blue-700 text-sm font-medium rounded-md border border-blue-300 hover:bg-blue-50"
                  >
                    Or load a saved day
                  </Link>
                </div>
              </div>
              <div className="text-sm text-blue-900 space-y-1.5">
                <p><strong>Energy-weighting</strong> — a 290 g bowl of oats contributes more than a 5 g sprinkle of cocoa, proportional to kcal. Avoids the &quot;everything counts the same&quot; pitfall.</p>
                <p><strong>NOVA-aware</strong> — Domain 6 applies graded penalties (Group 1 = 0, Group 4 = −10) to flag ultra-processing.</p>
                <p><strong>Audience modes</strong> — Researcher / Policy modes expose per-attribute breakdowns and Mozaffarian 2021 methodology notes.</p>
              </div>
            </div>
          </div>
        </section>

        {/* FCS-10 attributes summary */}
        <section className="mb-16">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">9 domains · 18 attributes (FCS-10)</h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              FCS-10 simplifies the original 54-attribute Food Compass by retaining the 18
              attributes that drove ≥ 90 % of score variance across NHANES foods — making it
              tractable for label-grounded scoring while preserving the discriminative signal.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { domain: 'Nutrient ratios', icon: '⚖️', description: 'Macro balance, key omega and mineral ratios.' },
              { domain: 'Vitamins', icon: '🌟', description: 'Top vitamins per food category.' },
              { domain: 'Minerals', icon: '⛰️', description: 'Top minerals per food category.' },
              { domain: 'Food ingredients', icon: '🥬', description: 'Whole-food components and ingredient quality (first 5 on the label).' },
              { domain: 'Additives', icon: '🧪', description: 'Penalty for additives and preservatives.' },
              { domain: 'Processing (NOVA)', icon: '🏭', description: 'NOVA-classification penalty; ultra-processed foods score −10.' },
              { domain: 'Specific lipids', icon: '🫒', description: 'Fatty-acid profile (mono-, poly-, trans, omega-3/6).' },
              { domain: 'Fibre & protein', icon: '💪', description: 'Density of fibre and protein per kcal.' },
              { domain: 'Phytochemicals', icon: '🌿', description: 'Plant bioactives with documented health signals.' },
            ].map((item, index) => (
              <div key={index} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                <div className="text-3xl mb-2">{item.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{item.domain}</h3>
                <p className="text-sm text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* NOVA explainer */}
        <section className="mb-16">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center mr-4">
                <GlobeAltIcon className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900">NOVA processing tier (Domain 6)</h2>
            </div>
            <p className="text-gray-600 mb-6">
              FCS-10 inherits NOVA&apos;s 4-tier industrial-processing classification. The processing
              penalty enters the score as a graded penalty in Domain 6 — it does not replace
              the score; it adjusts it.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                <h3 className="font-semibold text-green-800 mb-1">🥬 Group 1</h3>
                <h4 className="font-medium text-green-800 text-sm">Minimally processed</h4>
                <p className="text-xs text-green-700 mt-1 mb-2">Fresh fruit, raw meat, milk, dried grains.</p>
                <div className="text-sm font-semibold text-green-900">Penalty: 0</div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <h3 className="font-semibold text-yellow-800 mb-1">🧈 Group 2</h3>
                <h4 className="font-medium text-yellow-800 text-sm">Culinary ingredients</h4>
                <p className="text-xs text-yellow-700 mt-1 mb-2">Oils, butter, sugar, salt.</p>
                <div className="text-sm font-semibold text-yellow-900">Penalty: −6</div>
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                <h3 className="font-semibold text-orange-800 mb-1">🥫 Group 3</h3>
                <h4 className="font-medium text-orange-800 text-sm">Processed foods</h4>
                <p className="text-xs text-orange-700 mt-1 mb-2">Cheese, canned vegetables, simple breads.</p>
                <div className="text-sm font-semibold text-orange-900">Penalty: −7.5</div>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <h3 className="font-semibold text-red-800 mb-1">🍟 Group 4</h3>
                <h4 className="font-medium text-red-800 text-sm">Ultra-processed</h4>
                <p className="text-xs text-red-700 mt-1 mb-2">Industrial formulations with additives.</p>
                <div className="text-sm font-semibold text-red-900">Penalty: −10 (max)</div>
              </div>
            </div>
          </div>
        </section>

        {/* User-type interpretation */}
        <section className="mb-16 bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Audience modes</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <UserIcon className="w-5 h-5 text-blue-600 mr-2" />
                <h3 className="font-semibold text-blue-900">Individual</h3>
              </div>
              <p className="text-sm text-blue-800">
                Plain-language band (encourage / moderate / limit) without methodology jargon.
                Treat it as a relative signal between products, not a personal health verdict.
              </p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <BuildingOfficeIcon className="w-5 h-5 text-green-600 mr-2" />
                <h3 className="font-semibold text-green-900">Researcher</h3>
              </div>
              <p className="text-sm text-green-800">
                Per-domain attribute breakdown, NOVA evidence, FCS-10 vs full-FCS Spearman
                concordance, Mozaffarian 2021 and Barrett 2025 methodology pointers.
              </p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <DocumentChartBarIcon className="w-5 h-5 text-purple-600 mr-2" />
                <h3 className="font-semibold text-purple-900">Policy</h3>
              </div>
              <p className="text-sm text-purple-800">
                Population framing for procurement standards, taxation analysis, and
                food-environment surveillance. Indirect-validation caveat surfaced explicitly.
              </p>
            </div>
          </div>
        </section>

        {/* Food databases */}
        <section className="mb-16">
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Food composition databases</h2>
            <p className="text-sm text-gray-700 mb-4">
              FCS-10 scores every food in our cross-database catalog. CNF + WAFCT today (6,719
              foods); the source-tagged extension architecture means additional composition
              databases plug in without re-keying scoring code.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="border border-gray-100 rounded-lg p-3">
                <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Active</div>
                <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
                <div className="text-xs text-gray-600 mt-0.5">5,691 foods · Health Canada · authoritative for Canadian context</div>
              </div>
              <div className="border border-gray-100 rounded-lg p-3">
                <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Active</div>
                <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
                <div className="text-xs text-gray-600 mt-0.5">1,028 West African foods · Vincent et al. 2019 · per-source caveat surfaces mineral-bias</div>
              </div>
              <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
                <div className="text-sm font-medium text-gray-700 mt-1">Further composition tables</div>
                <div className="text-xs mt-0.5">USDA / EuroFIR / additional regional FCTs via the same source-tagged extension pattern.</div>
              </div>
            </div>
          </div>
        </section>

        {/* What FCS-10 isn't */}
        <section className="mb-16">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              What FCS-10 is <em>not</em>
            </h2>
            <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
              <li><strong>Not a clinical diagnosis.</strong> Validated to population mortality, not individual outcomes.</li>
              <li><strong>Not directly Canadian-validated yet.</strong> Anchored to US NHANES; cross-national portability is documented future work.</li>
              <li><strong>Not a replacement for HEFI.</strong> HEFI scores adherence to Canada&apos;s Food Guide; FCS scores resemblance to longer-life food patterns. Different questions.</li>
              <li><strong>Not directly validated below the food level.</strong> Recipe-style decompositions inherit ingredient-list inference uncertainty.</li>
            </ul>
          </div>
        </section>

        {/* Citation */}
        <section className="bg-gradient-to-r from-blue-900 to-green-900 rounded-2xl p-8 text-white">
          <div className="text-center max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-4">Primary references</h2>
            <div className="space-y-3 text-sm text-blue-100 text-left">
              <p>
                <strong className="text-white">FCS-10 (the implementation):</strong>{' '}
                Barrett E.M. et al. (2025). A simplified Food Compass Score for label-grounded
                scoring. <em>American Journal of Clinical Nutrition</em>. Methods pp. 7–9.
              </p>
              <p>
                <strong className="text-white">Original Food Compass:</strong>{' '}
                Mozaffarian D. et al. (2021). Food Compass is a nutrient profiling system
                using expanded characteristics for assessing healthfulness of foods.
                <em> Nature Food</em> 2, 809–818.
              </p>
              <p>
                <strong className="text-white">Mortality validation:</strong>{' '}
                O&apos;Hearn M. et al. (2022). Incident type 2 diabetes attributable to suboptimal
                diet. <em>Nature Communications</em> 13, 7066.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
