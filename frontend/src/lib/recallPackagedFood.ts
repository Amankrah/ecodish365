/**
 * Helpers for folding packaged-food decomposition into 24-h recall meals.
 */
import type {
  DecompositionResult,
  NFPanelExtraction,
  RecallMealInput,
  RecallOccasion,
  RecallPackagedPreDecomposed,
} from '@/lib/api';

export interface PackagedOccasionState {
  dishName: string;
  totalMass: number;
  panel: NFPanelExtraction;
  decomposition: DecompositionResult;
  imagePreviewUrl?: string;
}

export function buildRecallPackagedPreDecomposed(
  panel: NFPanelExtraction,
  decomposition: DecompositionResult,
): RecallPackagedPreDecomposed {
  return {
    ingredients: decomposition.ingredients.map(i => ({
      food_id: i.food_id,
      food_description: i.food_description,
      food_group: i.food_group || '',
      mass_g: i.mass_g,
      confidence: i.confidence,
    })),
    decomposition_confidence: decomposition.decomposition_confidence,
    decomposition_warnings: decomposition.decomposition_warnings,
    product_name: panel.product_name_visible.value,
    brand: panel.brand_visible.value,
    image_sha256: panel.extraction_metadata.image_sha256,
  };
}

export function buildRecallMealFromPackaged(
  occasion: RecallOccasion,
  state: PackagedOccasionState,
): RecallMealInput {
  return {
    occasion,
    dish_name: state.dishName,
    total_mass_g: state.totalMass,
    entry_type: 'packaged',
    pre_decomposed: buildRecallPackagedPreDecomposed(state.panel, state.decomposition),
  };
}

export function resolvePackagedDishName(panel: NFPanelExtraction): string {
  const brand = panel.brand_visible.value?.trim();
  const product = panel.product_name_visible.value?.trim();
  if (brand && product) return `${brand} ${product}`;
  return product || brand || 'Packaged food';
}

export function resolvePackagedMass(
  panel: NFPanelExtraction,
  decomposition: DecompositionResult,
): number {
  const net = panel.net_weight?.value;
  if (typeof net === 'number' && net > 0) return net;
  const assumed = decomposition.net_weight_g_assumed;
  if (assumed > 0) return assumed;
  const sum = decomposition.ingredients.reduce((s, i) => s + (i.mass_g || 0), 0);
  return sum > 0 ? sum : 100;
}
