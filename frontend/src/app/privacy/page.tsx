import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'How EcoDish365 handles your data: browser-local storage only, no health-data collection on our servers.',
};

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 sm:py-16">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Privacy Policy</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: May 2026</p>

      <div className="prose prose-gray max-w-none space-y-6 text-gray-700">
        <section>
          <h2 className="text-xl font-semibold text-gray-900">Summary</h2>
          <p>
            EcoDish365 is designed so that your food lists, recall history, and scoring inputs
            stay in your browser. We do not require an account to use the scoring tools, and we
            do not store personal health or dietary data on our servers.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">What stays on your device</h2>
          <ul className="list-disc list-inside space-y-1">
            <li>Your active food list and recall history (browser session storage)</li>
            <li>Cached scorecard results for faster re-display</li>
            <li>Optional sign-in credentials if you choose to create an account for saved meals</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">What we send to our servers</h2>
          <p>
            When you score foods, search the catalogue, or scan a packaged label, the minimum data
            needed for that calculation is sent to our API (food IDs, amounts, and images you
            choose to upload for label reading). We use these requests to return scores; we do not
            build a personal dietary profile from them unless you explicitly use account features.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">Third-party services</h2>
          <p>
            Label scanning and some search features use AI services to read images or match food
            names. Images you submit for scanning are processed for extraction only and are not
            used to train models on your behalf.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">Contact</h2>
          <p>
            Questions about this policy: see the project repository or contact the EcoDish365 team
            through the channels listed there.
          </p>
        </section>
      </div>

      <p className="mt-10">
        <Link href="/" className="text-blue-700 hover:text-blue-900 text-sm font-medium">
          ← Back to home
        </Link>
      </p>
    </div>
  );
}
