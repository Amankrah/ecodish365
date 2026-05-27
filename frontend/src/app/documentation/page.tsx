import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Documentation',
  description: 'How to use EcoDish365: Scorecard, 24-h recall, packaged-food scanning, and the six scoring lenses.',
};

const guides = [
  { title: 'Scorecard (all six lenses)', href: '/scorecard', blurb: 'Score one food list under HEFI, HENI, HSR, FCS, environmental, and dietary pattern at once.' },
  { title: '24-h dietary recall', href: '/recall-24h', blurb: 'Build a full day occasion by occasion, then route to any scorer.' },
  { title: 'Packaged-food scanner', href: '/scan-product', blurb: 'Photograph a label, confirm extracted values, score the product.' },
  { title: 'Recall history', href: '/recall-history', blurb: 'Save days and average across multiple recalls.' },
  { title: 'CNF + WAFCT explorer', href: '/cnf', blurb: 'Search 6,719 foods in the integrated catalogue.' },
  { title: 'My meals', href: '/meals', blurb: 'Save reusable meal templates.' },
];

const lenses = [
  { title: 'HEFI-2019', href: '/hefi' },
  { title: 'HENI', href: '/heni' },
  { title: 'HSR', href: '/hsr' },
  { title: 'Food Compass', href: '/fcs' },
  { title: 'Environmental', href: '/environmental' },
  { title: 'Dietary pattern', href: '/dietary-pattern' },
];

export default function DocumentationPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 sm:py-16">
      <h1 className="text-3xl font-bold text-gray-900 mb-3">Documentation</h1>
      <p className="text-gray-600 mb-10">
        Quick paths into the platform. For full methodology, switch to Researcher mode on any
        scoring page or read the primary references on the{' '}
        <Link href="/" className="text-blue-700 hover:underline">home page</Link>.
      </p>

      <h2 className="text-xl font-semibold text-gray-900 mb-4">Getting started</h2>
      <ul className="space-y-4 mb-10">
        {guides.map((g) => (
          <li key={g.href} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
            <Link href={g.href} className="font-medium text-blue-700 hover:text-blue-900">
              {g.title} →
            </Link>
            <p className="text-sm text-gray-600 mt-1">{g.blurb}</p>
          </li>
        ))}
      </ul>

      <h2 className="text-xl font-semibold text-gray-900 mb-4">Individual scoring lenses</h2>
      <ul className="grid sm:grid-cols-2 gap-2 mb-10">
        {lenses.map((l) => (
          <li key={l.href}>
            <Link href={l.href} className="text-blue-700 hover:underline text-sm">
              {l.title}
            </Link>
          </li>
        ))}
      </ul>

      <h2 className="text-xl font-semibold text-gray-900 mb-2">Developer resources</h2>
      <p className="text-sm text-gray-600">
        Source code and technical manuscripts live in the project repository. API endpoints mirror
        the same scoring logic used in the web app.
      </p>

      <p className="mt-10">
        <Link href="/" className="text-blue-700 hover:text-blue-900 text-sm font-medium">
          ← Back to home
        </Link>
      </p>
    </div>
  );
}
