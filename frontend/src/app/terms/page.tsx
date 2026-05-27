import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Terms of use for EcoDish365 research scoring tools.',
};

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12 sm:py-16">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Terms of Service</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: May 2026</p>

      <div className="prose prose-gray max-w-none space-y-6 text-gray-700">
        <section>
          <h2 className="text-xl font-semibold text-gray-900">Research and education tool</h2>
          <p>
            EcoDish365 provides nutrition and environmental scoring based on published research
            methods. It is not medical advice, dietary counselling, or a clinical decision support
            system. Always consult a qualified health professional for personal health decisions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">No warranty</h2>
          <p>
            Scores depend on food-composition data, model assumptions, and the limits documented
            in each underlying method. Results are provided &quot;as is&quot; for research and
            educational use. We do not guarantee completeness or fitness for any particular purpose.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">Acceptable use</h2>
          <p>
            You may use the platform for lawful personal, research, and policy-analysis purposes.
            Automated scraping, attempts to overload the API, or misuse of AI-assisted features may
            result in access restrictions.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900">Citations</h2>
          <p>
            If you publish work using EcoDish365 outputs, cite the underlying methods (HEFI, HENI,
            HSR, FCS, ReCiPe, AGRIBALYSE, and related papers) as listed on the home page and in
            Researcher mode explanations.
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
