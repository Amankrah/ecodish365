import type { Metadata } from 'next';
import Link from 'next/link';
import type { ComponentType, SVGProps } from 'react';
import {
  BeakerIcon,
  ArrowRightIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  ScaleIcon,
  Squares2X2Icon,
  ArrowsRightLeftIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  ClipboardDocumentCheckIcon,
  BookmarkSquareIcon,
  PresentationChartLineIcon,
  CodeBracketSquareIcon,
  SparklesIcon,
  GlobeAltIcon,
  StarIcon,
  GlobeAmericasIcon,
} from '@heroicons/react/24/outline';
import { Salad, Dna, Compass, Target } from 'lucide-react';

type IconType = ComponentType<SVGProps<SVGSVGElement>>;

export const metadata: Metadata = {
  title: 'For researchers',
  description:
    'A unified environmental-nutrition platform. One substrate, multiple published research lenses, cross-continent, reproducible. Composition assessment plus every individual lens, independently runnable on any food, meal, or 24-hour record.',
};

const compositionTools = [
  {
    icon: BeakerIcon,
    name: 'Nutrient analysis',
    href: '/research/nutrient-analysis',
    description:
      'Composition assessment for a meal or a 24-hour record. Full nutrient panel against IOM DRIs by life-stage, FPED food groups, NOVA processing tier, IOM AMDR macronutrient bands, and per-nutrient top-contributor ranking. Export JSON or long-format CSV.',
    primary: true,
  },
  {
    icon: ArrowsRightLeftIcon,
    name: 'Compare foods',
    href: '/cnf/compare',
    description:
      'Side-by-side nutrient comparison for up to six foods. Per-100g or per-100kcal basis, delta from baseline, source badges for CNF and WAFCT, CSV and JSON export.',
  },
  {
    icon: MagnifyingGlassIcon,
    name: 'Discover by nutrient',
    href: '/cnf/discover',
    description:
      'Multi-criteria food discovery. Find every food with fibre above 5 g and sodium below 200 mg per 100 g, ranked by ratio or by energy density.',
  },
  {
    icon: Squares2X2Icon,
    name: 'Food groups',
    href: '/cnf/groups',
    description:
      'Browse the CNF (groups 1–19) and WAFCT (groups 50–63) sidebars. Filter by name, thermal state, preservation state, and preparation coverage.',
  },
  {
    icon: ChartBarIcon,
    name: 'Catalogue analytics',
    href: '/cnf/analytics',
    description:
      'Database statistics, group distribution, and coverage heatmaps across CNF and WAFCT. Useful for scoping a study before committing to a sample.',
  },
  {
    icon: ScaleIcon,
    name: 'Food search',
    href: '/cnf/search',
    description:
      'Full-text and AI-enhanced semantic search across the combined catalogue. Source-scope filter for CNF, WAFCT, or both, with regional-signal warnings on the decomposer.',
  },
];

type LensToolCard = {
  icon: IconType;
  name: string;
  href: string;
  description: string;
  citation: string;
  primary?: boolean;
};

const lensTools: LensToolCard[] = [
  {
    icon: SparklesIcon,
    name: 'All scores at once',
    href: '/scorecard',
    description:
      'Run every published lens on the same food list in one view. Reflip the audience toggle for researcher-mode methodology breakdowns, data-quality flags, and citations.',
    primary: true,
    citation: 'Multi-lens composite view',
  },
  {
    icon: Salad,
    name: 'HEFI',
    href: '/hefi/calculate',
    description: 'Healthy Eating Food Index, 0 to 80, against Canada\'s Food Guide. Ten-component breakdown in researcher mode.',
    citation: 'Brassard 2022, APNM',
  },
  {
    icon: Dna,
    name: 'HENI',
    href: '/heni/calculate',
    description: 'Health Nutritional Index: healthy-life minutes gained or lost per serving, dose-response from long-term disease research.',
    citation: 'Stylianou 2021, Nature Food',
  },
  {
    icon: StarIcon,
    name: 'HSR',
    href: '/hsr/calculate',
    description: 'Health Star Rating from 0.5 to 5 stars for packaged products, scored against the on-shelf category.',
    citation: 'HSRAC Implementation Guide v9',
  },
  {
    icon: Compass,
    name: 'Food Compass',
    href: '/fcs/calculate',
    description: 'FCS nutrient-profile score from 1 to 100, combining nutrition and NOVA processing.',
    citation: 'Mozaffarian 2021, Nature Food',
  },
  {
    icon: GlobeAltIcon,
    name: 'Environmental',
    href: '/environmental/calculate',
    description: 'Climate, land, and water footprint with uncertainty bands from ReCiPe 2016 and AGRIBALYSE 3.2.',
    citation: 'Huijbregts 2017; ADEME 2024',
  },
  {
    icon: Target,
    name: 'Dietary pattern',
    href: '/dietary-pattern',
    description: 'Classify a day against eight published eating-pattern prototypes (Mediterranean, DASH, EAT-Lancet, and more).',
    citation: 'Trichopoulou 2003; Willett 2019',
  },
  {
    icon: GlobeAmericasIcon,
    name: 'Planet budget share',
    href: '/planetary',
    description: 'EAT-Lancet 2.0 Table 2 food-system share against planetary boundaries.',
    citation: 'EAT-Lancet 2.0',
  },
];

const roadmap = [
  {
    icon: CloudArrowUpIcon,
    name: 'Cohort upload',
    anchor: 'cohort',
    description:
      'CSV ingest of multiple 24-hour recalls (respondent, occasion, food_id, mass_g). Parallel scoring across the cohort under any single lens or all lenses at once.',
  },
  {
    icon: DocumentTextIcon,
    name: 'Methods + citation export',
    anchor: 'methods-export',
    description:
      'One-click methods.md plus BibTeX or RIS for every analysis. Drop the methods block straight into a manuscript.',
  },
  {
    icon: ClipboardDocumentCheckIcon,
    name: 'Reproducibility manifest',
    anchor: 'manifest',
    description:
      'Run ID, factor-pack SHA-256, git commit, API version, and a permalink that re-renders the exact result years later.',
  },
  {
    icon: BookmarkSquareIcon,
    name: 'Saved analyses',
    anchor: 'saved',
    description:
      'Name a meal or a cohort run, link it to a respondent ID, retrieve it later, export the manifest.',
  },
  {
    icon: ArrowsRightLeftIcon,
    name: 'Side-by-side comparison',
    anchor: 'compare',
    description:
      'Baseline versus intervention across every lens. Delta tables, Pareto frontier when trade-offs exist.',
  },
  {
    icon: PresentationChartLineIcon,
    name: 'Uncertainty bands in UI',
    anchor: 'uncertainty',
    description:
      'Surface the Monte Carlo intervals the backend already computes. Render 95% CI in the results, parallel columns in the CSV.',
  },
  {
    icon: CodeBracketSquareIcon,
    name: 'Public API + cookbook',
    anchor: 'api',
    description:
      'Versioned REST endpoints with Python and R recipes. Recreate a manuscript figure in twelve lines.',
  },
];

export default function ResearchHubPage() {
  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-slate-50 py-12 sm:py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-sm flex-shrink-0">
              <BeakerIcon className="w-7 h-7 text-white" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-700 mb-2">For researchers</p>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight">
                One substrate. Every published lens. Cross-continent. Reproducible.
              </h1>
              <p className="mt-3 text-base text-gray-700 max-w-3xl leading-relaxed">
                The research surface of ecodish365. Run a nutrient composition deep-dive on any meal
                or 24-hour record, score it across every published lens at once, or run any single
                lens on its own. Every result is auditable, citable, and traceable to a versioned
                factor pack.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/research/nutrient-analysis"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600 shadow-sm"
                >
                  <BeakerIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Open nutrient analysis
                  <ArrowRightIcon className="ml-2 w-4 h-4" aria-hidden="true" />
                </Link>
                <Link
                  href="/scorecard"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                >
                  <SparklesIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  All scores at once
                </Link>
                <Link
                  href="/methods"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                >
                  <DocumentTextIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Read the methods
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Composition & catalogue */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Composition &amp; catalogue</h2>
          <p className="text-sm text-gray-600 mb-6">
            The substrate every lens sits on. Nutrient composition, food-group attribution, processing tier,
            and catalogue exploration across CNF and WAFCT.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {compositionTools.map((t) => (
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
                <div className="mt-3 flex items-center text-sm font-medium text-primary-700 group-hover:text-primary-900">
                  Open <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Per-lens calculators */}
      <section className="py-12 bg-gray-50 border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-baseline justify-between mb-2">
            <h2 className="text-2xl font-bold text-gray-900">Published lenses</h2>
            <p className="text-xs text-gray-500">Each lens runs independently on the same substrate.</p>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            Run the full multi-lens scorecard, or run any single lens on its own. New lenses plug into the
            same substrate as they are published; the list is open, not fixed.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {lensTools.map((t) => (
              <Link
                key={t.name}
                href={t.href}
                className={`rounded-2xl p-4 border hover:shadow-lg hover:-translate-y-0.5 transition group ${
                  t.primary ? 'bg-primary-50 border-primary-300 lg:col-span-4' : 'bg-white border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      t.primary ? 'bg-gradient-to-br from-primary-500 to-primary-600' : 'bg-gray-100'
                    }`}
                    aria-hidden="true"
                  >
                    <t.icon className={`w-5 h-5 ${t.primary ? 'text-white' : 'text-gray-700'}`} aria-hidden="true" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">{t.name}</h3>
                </div>
                <p className="text-sm text-gray-700 leading-snug line-clamp-3">{t.description}</p>
                <p className="mt-2 text-[11px] text-gray-500">{t.citation}</p>
                <div className="mt-3 flex items-center text-sm font-medium text-primary-700 group-hover:text-primary-900">
                  Open <ArrowRightIcon className="ml-1 w-4 h-4" aria-hidden="true" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section id="roadmap" className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-baseline justify-between mb-2">
            <h2 className="text-2xl font-bold text-gray-900">Roadmap</h2>
            <p className="text-xs text-gray-500">What is in flight for the next research-platform cycle.</p>
          </div>
          <p className="text-sm text-gray-600 mb-6">These are the gaps between a decision-support tool and a publication-ready research platform. None of them require new science; all of them require frontend surfaces on top of capabilities the backend already provides.</p>
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

      <section className="py-8 bg-gray-50 border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm text-gray-500">
            Also see:
            {' '}
            <Link href="/policy" className="text-primary-700 hover:underline">Policy</Link>
            {' · '}
            <Link href="/me" className="text-primary-700 hover:underline">Individuals</Link>
            {' · '}
            <Link href="/methods" className="text-primary-700 hover:underline inline-flex items-center"><GlobeAltIcon className="w-3.5 h-3.5 mr-1" aria-hidden="true" />Methods &amp; data</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
