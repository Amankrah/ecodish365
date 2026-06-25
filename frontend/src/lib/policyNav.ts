/** Policy persona nav: population-level framing for the published lenses + roadmap. */
export const POLICY_NAV = {
  section: 'Policy',
  overview: 'Policy hub',
  href: '/policy',
} as const;

export const POLICY_DROPDOWN = [
  { name: 'Planet budget share', href: '/planetary' },
  { name: 'Population scorecard', href: '/scorecard' },
  { name: 'Policy hub', href: '/policy' },
  { name: 'Scenario simulator', href: '/policy#scenarios', disabled: true },
  { name: 'Social-cost overlay', href: '/policy#social-cost', disabled: true },
  { name: 'National food-system snapshot', href: '/policy#national', disabled: true },
] as const;
