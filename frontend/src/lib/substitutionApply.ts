import type { SubstitutionCompositionItem, SubstitutionSuggestion } from '@/lib/api';

export function suggestionKey(suggestion: SubstitutionSuggestion, index?: number): string {
  if (suggestion.id) return suggestion.id;
  const swapIds = (suggestion.swaps ?? [{ replacement: suggestion.replacement }])
    .map(sw => sw.replacement.food_id)
    .join('+');
  return `${suggestion.rule_id}:${suggestion.ingredient_index}:${swapIds}:${index ?? 0}`;
}

/** True when every swap in the suggestion is already reflected in the composition. */
export function isSuggestionApplied(
  current: SubstitutionCompositionItem[],
  suggestion: SubstitutionSuggestion,
): boolean {
  const swaps = suggestion.swaps?.length
    ? suggestion.swaps
    : [{ original: suggestion.original, replacement: suggestion.replacement }];

  return swaps.every((sw, j) => {
    const replacementId = sw.replacement.food_id;
    let idx = suggestion.ingredient_indices?.[j];
    if (idx === undefined && j === 0) {
      idx = suggestion.ingredient_index;
    }

    if (idx !== undefined && idx >= 0 && idx < current.length) {
      return current[idx].food_id === replacementId;
    }

    return current.some(row => row.food_id === replacementId)
      && !current.some(row => row.food_id === sw.original.food_id);
  });
}

/** Apply swap(s) onto the current composition (not the analyze-time baseline). */
export function applySuggestionToComposition(
  current: SubstitutionCompositionItem[],
  suggestion: SubstitutionSuggestion,
): SubstitutionCompositionItem[] {
  const next = current.map(item => ({ ...item }));
  const swaps = suggestion.swaps?.length
    ? suggestion.swaps
    : [{ original: suggestion.original, replacement: suggestion.replacement }];

  swaps.forEach((sw, j) => {
    let idx = suggestion.ingredient_indices?.[j];
    if (idx === undefined && j === 0) {
      idx = suggestion.ingredient_index;
    }

    if (idx !== undefined && idx >= 0 && idx < next.length && next[idx].food_id === sw.original.food_id) {
      next[idx] = mergeReplacement(next[idx], sw.replacement);
      return;
    }

    const byFoodId = next.findIndex(r => r.food_id === sw.original.food_id);
    if (byFoodId >= 0) {
      next[byFoodId] = mergeReplacement(next[byFoodId], sw.replacement);
    }
  });

  return next;
}

function mergeReplacement(
  row: SubstitutionCompositionItem,
  replacement: SubstitutionSuggestion['replacement'],
): SubstitutionCompositionItem {
  return {
    ...row,
    food_id: replacement.food_id,
    food_description: replacement.food_description,
    mass_g: replacement.mass_g ?? row.mass_g,
  };
}
