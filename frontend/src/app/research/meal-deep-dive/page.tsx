// Permanent redirect from the legacy /research/meal-deep-dive route to
// /research/nutrient-analysis (renamed 2026-06).
//
// Preserves the query string so the recall-wizard handoff, the CNF-search
// handoff, and any externally-bookmarked links continue to round-trip.
// Note: the backend endpoint /api/research/meal-deep-dive/ is unchanged;
// only the frontend route was renamed.

import { permanentRedirect } from 'next/navigation';

type SearchParams = Record<string, string | string[] | undefined>;

export default async function LegacyMealDeepDiveRedirect({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    if (Array.isArray(value)) {
      for (const v of value) query.append(key, v);
    } else {
      query.append(key, value);
    }
  }
  const qs = query.toString();
  const target = qs ? `/research/nutrient-analysis?${qs}` : '/research/nutrient-analysis';
  permanentRedirect(target);
}
