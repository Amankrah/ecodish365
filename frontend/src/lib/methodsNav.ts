/** Methods & data persona nav: documentation, factor packs, citations, manuscript. */
export const METHODS_NAV = {
  section: 'Methods & Data',
  overview: 'Methods hub',
  href: '/methods',
} as const;

export const METHODS_DROPDOWN = [
  { name: 'Documentation', href: '/documentation' },
  { name: 'Food catalogue overview', href: '/cnf' },
  { name: 'Published lenses overview', href: '/#lenses' },
  { name: 'Methods hub', href: '/methods' },
  { name: 'Factor-pack registry', href: '/methods#factor-packs', disabled: true },
  { name: 'Citations (BibTeX/RIS)', href: '/methods#citations', disabled: true },
  { name: 'Manuscript', href: '/methods#manuscript', disabled: true },
] as const;
