import type { Metadata } from 'next';
import Link from 'next/link';
import {
  UserGroupIcon,
  ArrowRightIcon,
  GlobeAltIcon,
  SparklesIcon,
  CurrencyDollarIcon,
  MapIcon,
  AdjustmentsHorizontalIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';

export const metadata: Metadata = {
  title: 'For policy makers',
  description:
    'Population-level framing for procurement, taxation, labelling, and food-environment surveillance. Versioned numbers, plain explanations. The policy surface of the ecodish365 platform.',
};

const liveTools = [
  {
    icon: GlobeAltIcon,
    name: 'Planet budget share',
    href: '/planetary',
    description:
      'EAT-Lancet 2.0 Table 2 food-system share against planetary boundaries. Frame a national or regional diet against the share the food system is allowed to consume.',
    primary: true,
  },
  {
    icon: SparklesIcon,
    name: 'Population scorecard',
    href: '/scorecard',
    description:
      'Every published lens on one screen. Switch to the Policy audience toggle for population-anchored explanations and the monetised social-cost framing where evidence supports it.',
    note: 'Flip the audience toggle to Policy after loading a food list.',
  },
];

const roadmap = [
  {
    icon: AdjustmentsHorizontalIcon,
    name: 'Cohort scenario simulator',
    anchor: 'scenarios',
    description:
      'Take a representative day or a national-survey medoid, apply N substitutions (replace 30% of red meat with legumes, for example), compute the multi-lens delta, surface the Pareto frontier.',
  },
  {
    icon: CurrencyDollarIcon,
    name: 'Social-cost overlay',
    anchor: 'social-cost',
    description:
      'Monetised health-cost and environmental-cost framing for the population, anchored to the lenses where the evidence supports a money figure.',
  },
  {
    icon: MapIcon,
    name: 'National food-system snapshot',
    anchor: 'national',
    description:
      'One-page snapshots of a country or region against every published lens, sourced from national surveys and the multi-database catalogue.',
  },
  {
    icon: AdjustmentsHorizontalIcon,
    name: 'Procurement substitution explorer',
    anchor: 'procurement',
    description:
      'Apply a procurement rule (school meals, hospital catering) and see the population-level change across every lens, with uncertainty bands.',
  },
];

export default function PolicyHubPage() {
  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-slate-50 py-12 sm:py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-sm flex-shrink-0">
              <UserGroupIcon className="w-7 h-7 text-white" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-700 mb-2">For policy makers</p>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight">
                Population-level framing for the food system.
              </h1>
              <p className="mt-3 text-base text-gray-700 max-w-3xl leading-relaxed">
                Versioned numbers. Plain explanations. Population-anchored framing for procurement,
                taxation, labelling, and food-environment surveillance, with a monetised social-cost
                overlay where the evidence supports it.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/planetary"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600 shadow-sm"
                >
                  <GlobeAltIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Open planet budget share
                  <ArrowRightIcon className="ml-2 w-4 h-4" aria-hidden="true" />
                </Link>
                <Link
                  href="/scorecard"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                >
                  <SparklesIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Open population scorecard
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Live tools</h2>
          <p className="text-sm text-gray-600 mb-6">
            Policy framing is shipped on the existing scoring surfaces via the audience toggle. The scenario
            simulator and the social-cost overlay are in flight; see the roadmap below.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {liveTools.map((t) => (
              <Link
                key={t.name}
                href={t.href}
                className={`rounded-2xl p-5 border hover:shadow-lg hover:-translate-y-0.5 transition group ${
                  t.primary ? 'bg-gradient-to-br from-primary-50 to-blue-50 border-primary-300' : 'bg-white border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${t.primary ? 'bg-gradient-to-br from-primary-500 to-primary-600' : 'bg-gray-100'}`}>
                    <t.icon className={`w-5 h-5 ${t.primary ? 'text-white' : 'text-gray-700'}`} aria-hidden="true" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">{t.name}</h3>
                </div>
                <p className="text-sm text-gray-700 leading-snug line-clamp-3">{t.description}</p>
                {t.note && (
                  <p className="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1">{t.note}</p>
                )}
                <div className="mt-3 flex items-center text-sm font-medium text-primary-700 group-hover:text-primary-900">
                  Open <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section id="roadmap" className="py-12 bg-gray-50 border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-baseline justify-between mb-2">
            <h2 className="text-2xl font-bold text-gray-900">Roadmap</h2>
            <p className="text-xs text-gray-500">What is in flight for the policy surface.</p>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            Today the policy surface is positioning plus the audience toggle on the existing scorers. The
            machinery for scenario simulation and social-cost overlay exists in the substitution engine
            (SUBST-1) and the LCA factor packs; what is missing is the policy-shaped frontend.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {roadmap.map((r) => (
              <div key={r.name} id={r.anchor} className="rounded-2xl border border-dashed border-gray-300 bg-white p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center">
                    <r.icon className="w-4 h-4 text-gray-500" aria-hidden="true" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-700">{r.name}</h3>
                  <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">Soon</span>
                </div>
                <p className="text-sm text-gray-600 leading-snug">{r.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-8 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm text-gray-500">
            Also see:
            {' '}
            <Link href="/research" className="text-primary-700 hover:underline inline-flex items-center"><BeakerIcon className="w-3.5 h-3.5 mr-1" aria-hidden="true" />Researchers</Link>
            {' · '}
            <Link href="/me" className="text-primary-700 hover:underline">Individuals</Link>
            {' · '}
            <Link href="/methods" className="text-primary-700 hover:underline">Methods &amp; data</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
