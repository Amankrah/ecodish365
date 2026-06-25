/** Individuals persona nav: consumer-friendly scoring, diary, and meals. */
export const ME_NAV = {
  section: 'Individuals',
  overview: 'Individuals hub',
  href: '/me',
} as const;

export const ME_DROPDOWN = [
  { name: 'All scores', href: '/scorecard' },
  { name: 'Food diary', href: '/recall-24h' },
  { name: 'Saved days', href: '/recall-history' },
  { name: 'Scan a product', href: '/scan-product' },
  { name: 'Improve one meal', href: '/improve-product' },
  { name: 'Dietary pattern', href: '/dietary-pattern' },
  { name: 'My meals', href: '/meals/my-meals', authOnly: true },
  { name: 'Saved meals', href: '/meals/saved-meals', authOnly: true },
  { name: 'Individuals hub', href: '/me' },
] as const;
