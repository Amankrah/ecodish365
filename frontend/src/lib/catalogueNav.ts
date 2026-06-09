/** Shared labels for the CNF + WAFCT food-composition catalogue section (`/cnf/*`). */
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
  // RESEARCH-DEEP-DIVE (2026-06-09): researcher-facing substrate exposure
  // — full nutrient panel against IOM DRIs by life stage, FPED food-group
  // decomposition, NOVA processing, per-nutrient food-source attribution.
  // Piped from the 24h-recall, the recipe decomposer, and AI-enhanced
  // search via the shared activeFoodList handoff.
  { name: 'Research deep-dive', href: '/research/meal-deep-dive' },
] as const;
