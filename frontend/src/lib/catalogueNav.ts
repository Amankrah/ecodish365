/** Shared labels for the CNF + WAFCT + FDC food-composition catalogue section (`/cnf/*`). */
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
  // NUTRIENT-ANALYSIS (2026-06-25, renamed from /research/meal-deep-dive):
  // researcher-facing composition substrate. Full nutrient panel against
  // IOM DRIs by life stage, FPED food-group decomposition, NOVA
  // processing, per-nutrient food-source attribution. Piped from the
  // 24h-recall, the recipe decomposer, and AI-enhanced search via the
  // shared activeFoodList handoff. Sibling tools (multi-lens scoring,
  // per-lens calculators) live elsewhere; this one is composition only.
  { name: 'Nutrient analysis', href: '/research/nutrient-analysis' },
] as const;
