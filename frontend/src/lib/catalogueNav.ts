/** Shared labels for the CNF + WAFCT + FDC + CIQUAL food-composition catalogue section (`/cnf/*`). */
export const CATALOGUE_NAV = {
  section: 'Food Catalogue',
  overview: 'Catalogue overview',
  href: '/cnf',
} as const;

export const CATALOGUE_DROPDOWN = [
  { name: 'Food Search', href: '/cnf/search' },
  { name: 'Discover by Nutrient', href: '/cnf/discover' },
  { name: 'Compare Foods', href: '/cnf/compare' },
  { name: 'Food Groups', href: '/cnf/groups' },
  { name: CATALOGUE_NAV.overview, href: '/cnf/analytics' },
] as const;
// Nutrient analysis (/research/nutrient-analysis) and Cohort upload
// (/research/cohort) used to live here while Research was tucked under Food
// Catalogue. Promoted to a top-level Research category 2026-06-26 — see
// [`researchNav.ts`](frontend/src/lib/researchNav.ts) RESEARCH_DROPDOWN.
