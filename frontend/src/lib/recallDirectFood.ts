/**
 * Helpers for user-picked CNF ingredients in 24-h recall (direct entry).
 */
import type {
  CNFRecall24hAggregatedIngredient,
  RecallMealInput,
  RecallOccasion,
  RecallPackagedPreDecomposed,
} from '@/lib/api';

export interface RecallDirectIngredient {
  food_id: number;
  food_description: string;
  food_group?: string;
  mass_g: number;
}

export function buildRecallDirectPreDecomposed(
  ingredients: RecallDirectIngredient[],
): RecallPackagedPreDecomposed {
  return {
    ingredients: ingredients.map(i => ({
      food_id: i.food_id,
      food_description: i.food_description,
      food_group: i.food_group || '',
      mass_g: i.mass_g,
      confidence: 1.0,
    })),
    decomposition_confidence: 1.0,
    decomposition_warnings: [],
  };
}

export function buildRecallMealFromDirect(
  occasion: RecallOccasion,
  dishName: string,
  ingredients: RecallDirectIngredient[],
): RecallMealInput {
  const totalMass = ingredients.reduce((s, i) => s + (i.mass_g || 0), 0);
  return {
    occasion,
    dish_name: dishName,
    total_mass_g: totalMass > 0 ? totalMass : 100,
    entry_type: 'direct',
    pre_decomposed: buildRecallDirectPreDecomposed(ingredients),
  };
}

export function directDishName(
  occasionLabel: string,
  ingredients: RecallDirectIngredient[],
): string {
  if (ingredients.length === 1) {
    return ingredients[0].food_description;
  }
  if (ingredients.length <= 3) {
    return ingredients.map(i => i.food_description).join(', ');
  }
  return `${occasionLabel} (${ingredients.length} foods)`;
}

/** Merge by food_id — sums mass when the same food appears twice. */
export function mergeRecallIngredients(
  items: RecallDirectIngredient[],
): RecallDirectIngredient[] {
  const byId = new Map<number, RecallDirectIngredient>();
  for (const item of items) {
    const existing = byId.get(item.food_id);
    if (existing) {
      byId.set(item.food_id, {
        ...existing,
        mass_g: existing.mass_g + item.mass_g,
      });
    } else {
      byId.set(item.food_id, { ...item });
    }
  }
  return Array.from(byId.values());
}

export function aggregatedToDirect(
  items: CNFRecall24hAggregatedIngredient[],
): RecallDirectIngredient[] {
  return items.map(i => ({
    food_id: i.food_id,
    food_description: i.food_description,
    food_group: i.food_group,
    mass_g: i.mass_g,
  }));
}

export function directToAggregated(
  items: RecallDirectIngredient[],
): CNFRecall24hAggregatedIngredient[] {
  return mergeRecallIngredients(items).map(i => ({
    food_id: i.food_id,
    food_description: i.food_description,
    food_group: i.food_group || '',
    mass_g: i.mass_g,
    occasions: {},
  }));
}
