'use client';

import React from 'react';
import Link from 'next/link';
import {
  CalculatorIcon,
  ChartBarIcon,
  UserIcon,
  CalendarDaysIcon,
  SparklesIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

const features = [
  {
    name: '🍽️ Build a 24-h recall',
    description: 'The HEFI-2019 algorithm was designed against 24-h recall data. Build your day occasion-by-occasion (breakfast, lunch, dinner, snacks); the wizard decomposes meals into CNF foods and routes to HEFI.',
    icon: CalendarDaysIcon,
    href: '/recall-24h?then=hefi',
    color: 'bg-blue-500',
    badge: 'Recommended',
  },
  {
    name: 'Calculate HEFI score',
    description: 'Pick foods from the integrated catalog (CNF or WAFCT) + serving sizes and compute HEFI across all 10 components. Works for single meals too — though single-meal scores are interpreted cautiously.',
    icon: CalculatorIcon,
    href: '/hefi/calculate',
    color: 'bg-purple-500',
  },
  {
    name: 'Compare meals',
    description: 'Side-by-side HEFI ranking across multiple meal compositions. Useful for menu planning and recipe substitution analysis.',
    icon: ChartBarIcon,
    href: '/hefi/compare',
    color: 'bg-green-500',
  },
  {
    name: 'Single-food profile',
    description: 'Per-food HEFI contribution breakdown. Best used to understand why a food helps or hurts a day-level HEFI score, not as a stand-alone rating.',
    icon: UserIcon,
    href: '/hefi/food-profile',
    color: 'bg-amber-500',
  },
];

// Brassard 2022b APNM 47:582-594, Table 3 (Canadian Community Health Survey 2015).
const hefiBenchmarks = [
  { label: '1st percentile',  value: 8,    note: 'Low adherence' },
  { label: '25th percentile', value: 35,   note: 'Below median' },
  { label: '50th percentile', value: 43,   note: 'Median Canadian adult' },
  { label: '75th percentile', value: 49,   note: 'Above median' },
  { label: '99th percentile', value: 63,   note: 'Top of distribution' },
];

const hefiComponents = [
  { name: 'C1 — Vegetables & fruits',        description: 'Adequacy: full points at ≥ 0.50 ref. amts V&F / total foods.',     maxScore: 20, kind: 'adequacy' },
  { name: 'C2 — Whole-grain foods',          description: 'Adequacy: full points if whole-grain ref. amts ≥ 0.25 of total.', maxScore: 5,  kind: 'adequacy' },
  { name: 'C3 — Whole-grain ratio',          description: 'Adequacy: full points if whole grains / total grains ≥ 1.0.',     maxScore: 5,  kind: 'adequacy' },
  { name: 'C4 — Protein foods',              description: 'Adequacy: full points if protein foods / total foods ≥ 0.25.',    maxScore: 5,  kind: 'adequacy' },
  { name: 'C5 — Plant-protein foods',        description: 'Adequacy: full points if plant protein / protein foods ≥ 0.50.',  maxScore: 5,  kind: 'adequacy' },
  { name: 'C6 — Recommended beverages',      description: 'Adequacy: full points if recommended bev / total bev = 1.0.',     maxScore: 10, kind: 'adequacy' },
  { name: 'C7 — (MUFA+PUFA) / SFA',          description: 'Moderation: full points if unsaturated:SFA ratio ≥ 2.6.',         maxScore: 5,  kind: 'moderation' },
  { name: 'C8 — Saturated fat (% energy)',   description: 'Moderation: full points if SFA ≤ 10 % of energy.',                maxScore: 5,  kind: 'moderation' },
  { name: 'C9 — Free sugars (% energy)',     description: 'Moderation: full points if free sugars ≤ 20 % of energy.',        maxScore: 10, kind: 'moderation' },
  { name: 'C10 — Sodium density (mg/kcal)',  description: 'Moderation: full points if sodium density ≤ 0.9 mg/kcal.',        maxScore: 10, kind: 'moderation' },
];

export default function HEFIPage() {
  return (
    <div className="space-y-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero */}
      <section className="text-center">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
          Healthy Eating Food Index <span className="text-purple-600">(HEFI-2019)</span>
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-4 leading-relaxed">
          Score how closely a day&apos;s eating aligns with <strong>Canada&apos;s Food Guide 2019</strong>.
          Ten components — six rewarding intake of food groups, four moderating
          nutrients of concern — total 0–80 points.
        </p>
        <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-6 text-sm text-amber-900">
          <ExclamationTriangleIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            HEFI was developed against 24-h recall data (Brassard 2022b). Single-meal
            scores are interpreted as rough estimates, not adherence. No absolute &quot;healthy&quot;
            threshold — interpretation is relative to the Canadian distribution.
          </span>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/recall-24h?then=hefi"
            className="inline-flex items-center justify-center px-6 py-3 bg-purple-600 text-white text-base font-medium rounded-lg hover:bg-purple-700"
          >
            <CalendarDaysIcon className="mr-2 w-5 h-5" />
            Build a 24-h recall
          </Link>
          <Link
            href="/scorecard"
            className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50"
          >
            <SparklesIcon className="mr-2 w-5 h-5" />
            See HEFI alongside 5 other metrics
          </Link>
        </div>
      </section>

      {/* Tools */}
      <section>
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">HEFI tools</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From quick single-food checks to full 24-h recall scoring.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <Link
              key={feature.name}
              href={feature.href}
              className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 group flex flex-col"
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-11 h-11 rounded-lg ${feature.color} flex items-center justify-center group-hover:scale-110 transition-transform duration-200`}>
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
                {feature.badge && (
                  <span className="text-[10px] font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-wide">
                    {feature.badge}
                  </span>
                )}
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-2 group-hover:text-purple-700">
                {feature.name}
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed flex-1">
                {feature.description}
              </p>
              <div className="flex items-center text-purple-700 text-sm font-medium mt-3">
                <span>Open</span>
                <ArrowRightIcon className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Population benchmarks */}
      <section className="bg-purple-50 border border-purple-200 rounded-2xl p-6">
        <div className="flex items-start gap-3 mb-4">
          <ChartBarIcon className="w-6 h-6 text-purple-700 flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">How to read your HEFI score</h2>
            <p className="text-sm text-gray-600 mt-1">
              HEFI is descriptive, not normative — there is no absolute &quot;healthy&quot;
              threshold. Compare against the Canadian adult distribution (Brassard 2022b, CCHS 2015):
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {hefiBenchmarks.map((b) => (
            <div key={b.label} className="bg-white border border-purple-100 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-700">{b.value}</div>
              <div className="text-xs text-gray-600 font-medium">{b.label}</div>
              <div className="text-[10px] text-gray-500 mt-1">{b.note}</div>
            </div>
          ))}
        </div>
      </section>

      {/* HEFI components */}
      <section>
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">10 components, 80 points</h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Six <em>adequacy</em> components reward intake of food groups Canada&apos;s Food Guide
            encourages; four <em>moderation</em> components penalise nutrients of concern.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {hefiComponents.map((component) => (
            <div key={component.name} className="bg-white border border-gray-200 rounded-xl p-4 flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-base font-semibold text-gray-900">{component.name}</h3>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${
                      component.kind === 'adequacy'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}
                  >
                    {component.kind}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{component.description}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-2xl font-bold text-purple-600">{component.maxScore}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wide">max pts</div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-6">
          <div className="inline-flex items-center bg-purple-50 border border-purple-200 rounded-lg px-5 py-3">
            <CheckCircleIcon className="w-5 h-5 text-purple-600 mr-2" />
            <span className="text-sm text-purple-900">
              <strong>Total max: 80 points.</strong> 99th-percentile Canadian adult: ~63 / 80.
            </span>
          </div>
        </div>
      </section>

      {/* Food databases */}
      <section className="bg-white rounded-2xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Food composition databases</h2>
        <p className="text-sm text-gray-700 mb-4">
          HEFI scoring runs over every food in our cross-database catalog. The Canadian Nutrient
          File is authoritative for the Canadian population HEFI was developed against; WAFCT
          extends coverage to West African staples. Per-source caveats surface in researcher /
          policy mode when a WAFCT food appears in a meal (HEFI&apos;s free-sugars component
          is biased because WAFCT lacks SUGAR / SUGARS_FREE columns — flagged transparently).
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Active · authoritative</div>
            <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
            <div className="text-xs text-gray-600 mt-0.5">5,691 foods · Health Canada · HEFI was validated against CCHS 2015 (CNF-keyed)</div>
          </div>
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Active · extension</div>
            <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
            <div className="text-xs text-gray-600 mt-0.5">1,028 West African foods · per-source caveat surfaces free-sugars + mineral-method deltas</div>
          </div>
          <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
            <div className="text-sm font-medium text-gray-700 mt-1">Further composition tables</div>
            <div className="text-xs mt-0.5">Additional regional FCTs via the same source-tagged extension architecture.</div>
          </div>
        </div>
      </section>

      {/* What HEFI isn't */}
      <section className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
        <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
          <ExclamationTriangleIcon className="w-5 h-5" />
          What HEFI is <em>not</em>
        </h2>
        <ul className="space-y-1.5 text-sm text-amber-900 list-disc list-inside">
          <li><strong>Not validated against health outcomes.</strong> Measures guideline adherence, not disease risk. For mortality-anchored scoring see <Link href="/fcs" className="underline">FCS</Link>; for population health-life-minutes see <Link href="/heni" className="underline">HENI</Link>.</li>
          <li><strong>Not a single-meal verdict.</strong> Designed for full 24-h recalls. A high-HEFI meal does not guarantee a high-HEFI day.</li>
          <li><strong>Not absolute.</strong> No clinical &quot;pass / fail&quot; threshold — reported as relative position in the Canadian distribution.</li>
          <li><strong>Free-sugar proxy.</strong> The free-sugars component uses total sugars, which over-counts intrinsic sugars in fruit, milk, and yogurt.</li>
        </ul>
      </section>

      {/* Audience modes + citations */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Audience modes</h3>
          <p className="text-sm text-gray-700">
            Every HEFI calculation surfaces three explanation packs:
            <strong> Individual</strong> (plain-language band, no jargon),
            <strong> Researcher</strong> (per-component ratio audit, Brassard 2022a/b
            references, population benchmarks),
            <strong> Policy</strong> (population framing for guideline-adherence
            monitoring and CFG implementation).
          </p>
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Primary references</h3>
          <ul className="space-y-1 text-sm text-gray-700 list-disc list-inside">
            <li>Brassard D. et al. (2022a). Development of the HEFI-2019. <em>APNM</em> 47, 595–610.</li>
            <li>Brassard D. et al. (2022b). Evaluation of the HEFI-2019 with CCHS 2015 data. <em>APNM</em> 47, 582–594.</li>
            <li>Health Canada (2019). <em>Canada&apos;s Food Guide</em>.</li>
          </ul>
        </div>
      </section>

      {/* About */}
      <section className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-start mb-3">
          <InformationCircleIcon className="w-6 h-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">About HEFI-2019</h2>
            <p className="text-sm text-gray-700">
              The Healthy Eating Food Index (HEFI-2019) is a validated tool developed by
              Brassard et al. for Health Canada to assess how well dietary patterns align with
              the recommendations in Canada&apos;s Food Guide 2019. It is the natural metric
              for 24-h dietary recall data; the recall wizard above is the easiest way to
              produce a meaningful HEFI score.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
