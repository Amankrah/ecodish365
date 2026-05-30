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
] as const;
