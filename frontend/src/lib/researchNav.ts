/** Researcher persona nav: deep-dive analyzer + catalogue exploration + roadmap. */
export const RESEARCH_NAV = {
  section: 'Researchers',
  overview: 'Research hub',
  href: '/research',
} as const;

export const RESEARCH_DROPDOWN = [
  { name: 'Nutrient analysis', href: '/research/nutrient-analysis' },
  { name: 'All scores at once', href: '/scorecard' },
  { name: 'Compare foods', href: '/cnf/compare' },
  { name: 'Discover by nutrient', href: '/cnf/discover' },
  { name: 'Food groups', href: '/cnf/groups' },
  { name: 'Catalogue analytics', href: '/cnf/analytics' },
  { name: 'Food search', href: '/cnf/search' },
  { name: 'Research hub', href: '/research' },
  { name: 'Cohort upload', href: '/research#cohort', disabled: true },
  { name: 'Methods & citation export', href: '/research#methods-export', disabled: true },
] as const;
