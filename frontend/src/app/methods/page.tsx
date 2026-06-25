import type { Metadata } from 'next';
import Link from 'next/link';
import {
  BookOpenIcon,
  ArrowRightIcon,
  DocumentTextIcon,
  ArchiveBoxIcon,
  AcademicCapIcon,
  TagIcon,
  CodeBracketSquareIcon,
  LinkIcon,
  ShieldCheckIcon,
  Squares2X2Icon,
} from '@heroicons/react/24/outline';

export const metadata: Metadata = {
  title: 'Methods & data',
  description:
    'Every score traces to a published factor pack. Every factor pack is versioned and checksummed. Documentation, citations, factor packs, and the manuscript behind the ecodish365 platform.',
};

const liveTools = [
  {
    icon: DocumentTextIcon,
    name: 'Documentation',
    href: '/documentation',
    description:
      'Methods, data sources, lens-by-lens caveats, and the limits the original studies state.',
    primary: true,
  },
  {
    icon: Squares2X2Icon,
    name: 'Food catalogue overview',
    href: '/cnf',
    description:
      'The Canadian Nutrient File (5,691 foods) plus the West African Food Composition Table (1,028 foods). New regional tables plug into the same substrate.',
  },
  {
    icon: AcademicCapIcon,
    name: 'Published lenses overview',
    href: '/#lenses',
    description:
      'Healthy eating, health impact, product stars, Food Compass, environmental footprint, dietary pattern, and more as new lenses land. Each one cited and bounded by the studies that defined it.',
  },
  {
    icon: ShieldCheckIcon,
    name: 'Privacy policy',
    href: '/privacy',
    description:
      'Recall history and active food list live in your browser only. No account, no health-data collection on the server.',
  },
];

const roadmap = [
  {
    icon: ArchiveBoxIcon,
    name: 'Factor-pack registry',
    anchor: 'factor-packs',
    description:
      'Every CNF, WAFCT, Agribalyse, FPED, NOVA, and DRI version listed with checksums, change logs, and the date each became default.',
  },
  {
    icon: TagIcon,
    name: 'Citations (BibTeX / RIS)',
    anchor: 'citations',
    description:
      'One-click citation library for every lens: Brassard 2022 (HEFI), Stylianou 2021 (HENI), HSRAC v9, Mozaffarian 2021 (FCS), Poore &amp; Nemecek 2018, EAT-Lancet 2.0.',
  },
  {
    icon: BookOpenIcon,
    name: 'Manuscript',
    anchor: 'manuscript',
    description:
      'The Nature Food submission describing the platform: substrate, scoring kernels, orchestration, integration, audience-aware presentation, and the 100-day NHANES case study.',
  },
  {
    icon: LinkIcon,
    name: 'Release notes + DOI',
    anchor: 'doi',
    description:
      'Semantic versions, release notes, and a Zenodo DOI per release so the platform is citeable.',
  },
  {
    icon: CodeBracketSquareIcon,
    name: 'Public API docs',
    anchor: 'api',
    description:
      'Versioned REST endpoints with Python and R cookbooks. Recreate a manuscript figure in twelve lines.',
  },
  {
    icon: LinkIcon,
    name: 'Reproducibility URL by run ID',
    anchor: 'run-id',
    description:
      'Every analysis gets a run ID and a permalink that re-renders the exact result years later against the locked factor pack.',
  },
];

export default function MethodsHubPage() {
  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-slate-50 py-12 sm:py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-sm flex-shrink-0">
              <BookOpenIcon className="w-7 h-7 text-white" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-700 mb-2">Methods &amp; data</p>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight">
                Every score traces to a published factor pack.
              </h1>
              <p className="mt-3 text-base text-gray-700 max-w-3xl leading-relaxed">
                Every factor pack is versioned and checksummed. Every release is citeable. This is the
                back-of-the-platform: documentation, data sources, citations, factor packs, and the
                manuscript that describes the whole thing.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/documentation"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-accent-500 hover:bg-accent-600 shadow-sm"
                >
                  <DocumentTextIcon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Open documentation
                  <ArrowRightIcon className="ml-2 w-4 h-4" aria-hidden="true" />
                </Link>
                <Link
                  href="/cnf"
                  className="inline-flex items-center px-5 py-2.5 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                >
                  <Squares2X2Icon className="mr-2 w-4 h-4" aria-hidden="true" />
                  Food catalogue overview
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Live</h2>
          <p className="text-sm text-gray-600 mb-6">What the platform documents today.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-5">
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
            <p className="text-xs text-gray-500">What the methods surface ships next.</p>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            The platform is open and bounded. These items make it cite-able, reproducible, and embeddable
            in research code.
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
            <Link href="/research" className="text-primary-700 hover:underline">Researchers</Link>
            {' · '}
            <Link href="/policy" className="text-primary-700 hover:underline">Policy</Link>
            {' · '}
            <Link href="/me" className="text-primary-700 hover:underline">Individuals</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
