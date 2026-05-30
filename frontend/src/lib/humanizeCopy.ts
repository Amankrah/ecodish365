import type { UserType } from '@/components/shared/AudienceToggle';

function sentenceCase(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Turn stiff or technical strings into plain language for end users. */
export function humanizeForUser(text: string | undefined | null): string {
  if (!text?.trim()) return '';

  let out = text
    .trim()
    // Em / en dashes → sentence breaks or commas
    .replace(/\s*[—–]\s*/g, '. ')
    .replace(/\s*;\s*/g, '. ')
    .replace(/\s{2,}/g, ' ')
    // Shouty emphasis
    .replace(/\bIMPORTANT:\s*/gi, 'Note: ')
    .replace(/\bNOT\b/g, 'not')
    // "it is X, not Y" → softer phrasing
    .replace(/\bit is\s+([^.,]+),\s*not\s+([^.,]+)/gi, 'this is $1, rather than $2')
    .replace(/\bthis is\s+([^.,]+),\s*not\s+([^.,]+)/gi, 'this is $1, rather than $2')
    // Developer / workflow jargon
    .replace(/\bscorecard\b/gi, 'nutrition profile')
    .replace(/\bcosine similarity\b/gi, 'similarity')
    .replace(/\bembedding (corpus|alternative)\b/gi, 'food database')
    .replace(/\bCNF\/WAFCT FoodID \d+/gi, '')
    .replace(/\bfood-composition corpus\b/gi, 'food database')
    .replace(/\bpartial mapping\b/gi, 'some foods could not be grouped')
    .replace(/\brule match\b/gi, 'suggested swap')
    .replace(/\bPareto frontier\b/gi, 'well-balanced option')
    .replace(/\bfrontier\b/gi, 'well-balanced')
    // Clean punctuation
    .replace(/\.\s+\./g, '.')
    .replace(/,\s*\./g, '.')
    .replace(/\s+\./g, '.')
    .trim();

  // Ensure sentences start with a capital letter after splits
  out = out
    .split(/(?<=[.!?])\s+/)
    .map(s => sentenceCase(s.trim()))
    .filter(Boolean)
    .join(' ');

  return out;
}

/** Swap suggestion footnotes from the API. Hide jargon for individuals. */
export function humanizeSwapRationale(
  text: string | undefined | null,
  userType: UserType = 'individual',
): string | null {
  if (!text?.trim()) return null;
  if (userType !== 'individual') return text.trim();

  const t = text.trim();

  if (/CNFMatcher|cosine similarity|embedding alternative/i.test(t)) {
    return 'A similar food from our database with a close nutrition profile.';
  }
  if (/Applies the strongest swap at each step/i.test(t)) {
    return 'Swaps several ingredients in order, keeping each change as it goes.';
  }
  if (/Combines two single-ingredient swaps/i.test(t)) {
    return 'Two ingredient swaps bundled into one plan.';
  }
  if (/similar West African dish/i.test(t)) {
    return 'Suggested from a similar West African dish in our recipe library.';
  }

  const cleaned = t
    .replace(/\s*\([^)]*cosine[^)]*\)/gi, '')
    .replace(/\s*\(cosine similarity[^)]*\)/gi, '')
    .replace(/CNFMatcher\s+embedding alternative\s*[—–-]?\s*/gi, '');

  const out = humanizeForUser(cleaned);
  if (!out || /cosine|embedding|matcher|pareto|frontier/i.test(out)) return null;
  return out;
}

/** One-line summary for the improve-plan panel (client-side, no API jargon). */
export function buildImprovePlanSummary(plan: {
  baseline: { scorecard?: Record<string, { value?: number | null }> };
  priority_targets: Array<{ food_description: string; mass_pct: number }>;
  population_context?: {
    hefi?: { value: number; band_phrase: string; caveat?: string };
  } | null;
}): string {
  const parts: string[] = [];
  const hefi = plan.baseline.scorecard?.hefi?.value;
  const pop = plan.population_context?.hefi;

  if (hefi != null && pop) {
    parts.push(
      `Your day scores ${hefi.toFixed(1)} out of 80 for healthy eating (${pop.band_phrase.toLowerCase()}).`,
    );
  } else if (hefi != null) {
    parts.push(`Your healthy eating score is ${hefi.toFixed(1)} out of 80.`);
  }

  const top = plan.priority_targets[0];
  if (top) {
    parts.push(
      `The food with the most room to improve is ${top.food_description} (${top.mass_pct}% of what you ate).`,
    );
  }

  return parts.join(' ');
}

const METRIC_LABELS: Record<string, string> = {
  hefi: 'Healthy eating',
  heni: 'Health impact',
  fcs: 'Diet quality',
  hsr: 'Product rating',
  environmental: 'Environment',
  dietary_pattern: 'Eating style',
};

export function friendlyMetricLabel(key: string): string {
  return METRIC_LABELS[key] ?? key.replace(/_/g, ' ');
}
