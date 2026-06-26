/** Researcher persona nav: top-level Research category surfaced in the main nav
 * (PLATFORM-CODE-1.l). The dropdown lists research-specific surfaces only —
 * catalogue exploration tools live under Food Catalogue, lens calculators under
 * Nutrition Indicators, so we don't duplicate them here. */
export const RESEARCH_NAV = {
  section: 'Research',
  overview: 'Research hub',
  href: '/research',
} as const;

export const RESEARCH_DROPDOWN = [
  { name: 'Research hub',                href: '/research' },
  { name: 'Nutrient analysis',           href: '/research/nutrient-analysis' },
  { name: 'Cohort upload',               href: '/research/cohort' },
  { name: 'Compare cohorts',             href: '/research/cohort/compare' },
  // PLATFORM-CODE-1.m (2026-06-26): standalone browse of the Health Canada
  // CCHS Nutrition 2015 Food Consumption Table by (subgroup × stratum).
  { name: 'Canadian population reference', href: '/research/canadian-population-reference' },
  { name: 'Methods & citation export',   href: '/research#methods-export', disabled: true },
] as const;
