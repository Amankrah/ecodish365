/**
 * ImproveProductFlow — SUBST-1 Phase 1 primary UX.
 *
 * Three input paths:
 *   1. Scan packaged food (NF + ingredients → decompose → find swaps)
 *   2. Describe homemade meal (recipe decomposer → find swaps)
 *   3. Load a saved 24-h recall day (recall history → find swaps)
 */
'use client';

import { useCallback, useState } from 'react';
import {
  Camera, ChefHat, Loader2, AlertCircle, RotateCcw, Sparkles, CalendarClock,
} from 'lucide-react';
import {
  CNFApiService,
  type DecompositionResult,
  type IngredientListExtraction,
  type NFPanelExtraction,
} from '@/lib/api';
import {
  recallDayDisplayTitle,
  recallDaySubstitutionDishName,
  recallDayToIngredientRows,
  type SavedRecallDay,
} from '@/lib/recallHistory';
import { AudienceToggle, type UserType } from './AudienceToggle';
import { PackagedFoodCompositionForm } from './PackagedFoodCompositionForm';
import { ImproveHomemadeComposition } from './ImproveHomemadeComposition';
import { RecipeDecomposerModal } from './RecipeDecomposerModal';
import { RecallDayPicker } from './RecallDayPicker';
import { useRecall24hReceiver } from './useRecall24hReceiver';

const MAX_IMAGES = 3;

type InputMode = 'scan' | 'describe' | 'recall';
type ScanStep = 'capture' | 'reviewing' | 'decomposing' | 'ready' | 'error';

interface CompositionState {
  dishName: string;
  substitutionDishName?: string;
  ingredients: Array<{ food_id: number; food_description: string; mass_g: number; food_group?: string }>;
  recallMeta?: { date?: string; kcal: number; occasions: number };
}

function recallStashTitle(
  meals: Array<{ dish_name: string; total_mass_g: number }>,
): string {
  const names = meals.map(m => m.dish_name?.trim()).filter(Boolean) as string[];
  if (names.length === 1) return names[0];
  if (names.length > 1) return `${names.length} meals · food diary day`;
  return 'Food diary day';
}

function recallStashSubstitutionDish(
  meals: Array<{ dish_name: string; total_mass_g: number }>,
): string {
  let best = '';
  let bestMass = -1;
  for (const m of meals) {
    const name = m.dish_name?.trim() ?? '';
    if (name && m.total_mass_g > bestMass) {
      bestMass = m.total_mass_g;
      best = name;
    }
  }
  return best || recallStashTitle(meals);
}

export function ImproveProductFlow(): JSX.Element {
  const [userType, setUserType] = useState<UserType>('individual');
  const [mode, setMode] = useState<InputMode>('scan');

  // Packaged scan state
  const [scanStep, setScanStep] = useState<ScanStep>('capture');
  const [pickedFiles, setPickedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [panel, setPanel] = useState<NFPanelExtraction | null>(null);
  const [ingredientList, setIngredientList] = useState<IngredientListExtraction | null>(null);
  const [decomposition, setDecomposition] = useState<DecompositionResult | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [decomposing, setDecomposing] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);

  // Homemade / recall composition state
  const [composition, setComposition] = useState<CompositionState | null>(null);
  const [decomposerOpen, setDecomposerOpen] = useState(false);

  const loadRecallDay = useCallback((day: SavedRecallDay): void => {
    setUserType(day.user_type);
    setComposition({
      dishName: recallDayDisplayTitle(day),
      substitutionDishName: recallDaySubstitutionDishName(day),
      ingredients: recallDayToIngredientRows(day),
      recallMeta: {
        date: day.date,
        kcal: day.estimated_daily_kcal,
        occasions: day.occasions_count,
      },
    });
  }, []);

  useRecall24hReceiver({
    target: 'improve_product',
    onIngredients: (ingredients, meta) => {
      setUserType(meta.user_type);
      setMode('recall');
      setComposition({
        dishName: recallStashTitle(meta.meals_meta),
        substitutionDishName: recallStashSubstitutionDish(meta.meals_meta),
        ingredients: ingredients.map(i => ({
          food_id: i.food_id,
          food_description: i.food_description,
          mass_g: i.mass_g,
          food_group: i.food_group || undefined,
        })),
        recallMeta: {
          kcal: meta.estimated_daily_kcal,
          occasions: meta.meals_meta.length,
        },
      });
    },
  });

  function resetScan(): void {
    for (const url of previewUrls) URL.revokeObjectURL(url);
    setPickedFiles([]);
    setPreviewUrls([]);
    setPanel(null);
    setIngredientList(null);
    setDecomposition(null);
    setScanError(null);
    setScanStep('capture');
  }

  function resetAll(): void {
    resetScan();
    setComposition(null);
  }

  function clearComposition(): void {
    setComposition(null);
  }

  function switchMode(next: InputMode): void {
    setMode(next);
    if (next === 'scan') {
      setComposition(null);
    } else {
      resetScan();
      if (next === 'describe') setComposition(null);
    }
  }

  function appendFiles(incoming: FileList | File[] | null): void {
    if (!incoming) return;
    const arr = Array.from(incoming);
    const room = MAX_IMAGES - pickedFiles.length;
    if (room <= 0) return;
    const accepted = arr.slice(0, room);
    setPickedFiles(prev => [...prev, ...accepted]);
    setPreviewUrls(prev => [...prev, ...accepted.map(f => URL.createObjectURL(f))]);
    setScanError(null);
  }

  async function handleExtract(): Promise<void> {
    if (pickedFiles.length === 0) return;
    setExtracting(true);
    setScanError(null);
    setDecomposition(null);
    try {
      const rsp = await CNFApiService.extractPackagedFoodCombined(pickedFiles);
      if (!rsp.extraction.extraction_succeeded) {
        setScanError(rsp.extraction.failure_reason || 'Could not read the label.');
        setScanStep('error');
        return;
      }
      if (!rsp.extraction.ingredient_list?.ingredients_parsed?.length) {
        setScanError('Ingredient list not found. Include a photo of the ingredients panel.');
        setScanStep('error');
        return;
      }
      setPanel(rsp.extraction.nf_panel);
      setIngredientList(rsp.extraction.ingredient_list);
      setScanStep('reviewing');
    } catch {
      setScanError('Failed to extract label. Try clearer photos.');
      setScanStep('error');
    } finally {
      setExtracting(false);
    }
  }

  async function handleDecompose(): Promise<void> {
    if (!panel || !ingredientList) return;
    setDecomposing(true);
    setScanError(null);
    setScanStep('decomposing');
    try {
      const rsp = await CNFApiService.decomposePackagedFood(panel, ingredientList);
      if (!rsp.decomposition.decomposition_succeeded) {
        setScanError(rsp.decomposition.failure_reason || 'Decomposition failed.');
        setScanStep('error');
        return;
      }
      setDecomposition(rsp.decomposition);
      setScanStep('ready');
    } catch {
      setScanError('Could not decompose ingredients.');
      setScanStep('error');
    } finally {
      setDecomposing(false);
    }
  }

  const tabClass = (active: boolean) =>
    `flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-sm font-medium rounded-md ${
      active ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
    }`;

  return (
    <div className="space-y-6">
      <div className="flex justify-center">
        <AudienceToggle userType={userType} onChange={setUserType} accent="purple" />
      </div>

      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg" role="tablist" aria-label="Input method">
        <button
          type="button"
          role="tab"
          id="improve-tab-scan"
          {...(mode === 'scan' ? { 'aria-selected': 'true' as const } : { 'aria-selected': 'false' as const })}
          aria-controls="improve-panel-scan"
          onClick={() => switchMode('scan')}
          className={tabClass(mode === 'scan')}
        >
          <Camera className="h-4 w-4" aria-hidden="true" />
          Scan product
        </button>
        <button
          type="button"
          role="tab"
          id="improve-tab-describe"
          {...(mode === 'describe' ? { 'aria-selected': 'true' as const } : { 'aria-selected': 'false' as const })}
          aria-controls="improve-panel-describe"
          onClick={() => switchMode('describe')}
          className={tabClass(mode === 'describe')}
        >
          <ChefHat className="h-4 w-4" aria-hidden="true" />
          Describe meal
        </button>
        <button
          type="button"
          role="tab"
          id="improve-tab-recall"
          {...(mode === 'recall' ? { 'aria-selected': 'true' as const } : { 'aria-selected': 'false' as const })}
          aria-controls="improve-panel-recall"
          onClick={() => switchMode('recall')}
          className={tabClass(mode === 'recall')}
        >
          <CalendarClock className="h-4 w-4" aria-hidden="true" />
          Food diary
        </button>
      </div>

      {mode === 'scan' && (
        <div id="improve-panel-scan" role="tabpanel" aria-labelledby="improve-tab-scan">
          {scanStep === 'ready' && decomposition && panel ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  <Sparkles className="inline h-4 w-4 text-violet-600 mr-1" aria-hidden="true" />
                  Review the ingredients below, then click Find swaps when you are ready.
                </p>
                <button type="button" onClick={resetAll} className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1">
                  <RotateCcw className="h-4 w-4" aria-hidden="true" /> Start over
                </button>
              </div>
              <PackagedFoodCompositionForm
                decomposition={decomposition}
                panel={panel}
                userType={userType}
                showSubstitutions
              />
            </div>
          ) : (
            <div className="bg-white border rounded-lg p-6 space-y-4">
              <p className="text-sm text-gray-600">
                Upload one to three photos showing the nutrition panel and ingredient list. We read
                the label and estimate how much of each ingredient is in the product.
              </p>

              <div className="flex flex-wrap gap-2">
                {previewUrls.map(url => (
                  <img key={url} src={url} alt="" className="h-20 w-20 object-cover rounded border" />
                ))}
              </div>

              <input
                type="file"
                accept="image/*"
                multiple
                onChange={e => appendFiles(e.target.files)}
                className="text-sm"
                aria-label="Upload label photos"
              />

              {scanError && (
                <div className="flex items-start gap-2 text-sm text-red-800 bg-red-50 border border-red-200 rounded-md p-3">
                  <AlertCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                  {scanError}
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                {scanStep !== 'reviewing' && (
                  <button
                    type="button"
                    onClick={() => void handleExtract()}
                    disabled={pickedFiles.length === 0 || extracting}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-md text-sm font-medium hover:bg-violet-700 disabled:opacity-50"
                  >
                    {extracting && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
                    Extract label
                  </button>
                )}
                {scanStep === 'reviewing' && (
                  <button
                    type="button"
                    onClick={() => void handleDecompose()}
                    disabled={decomposing}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-md text-sm font-medium hover:bg-violet-700 disabled:opacity-50"
                  >
                    {decomposing && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
                    Decompose ingredients
                  </button>
                )}
                {(scanStep === 'error' || scanStep === 'reviewing') && (
                  <button type="button" onClick={resetScan} className="px-4 py-2 border rounded-md text-sm">
                    Reset
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {mode === 'describe' && (
        <div id="improve-panel-describe" role="tabpanel" aria-labelledby="improve-tab-describe">
          {composition ? (
            <div className="space-y-4">
              <div className="flex justify-end">
                <button type="button" onClick={clearComposition} className="text-sm text-gray-500 hover:text-gray-800">
                  Describe another meal
                </button>
              </div>
              <ImproveHomemadeComposition
                dishName={composition.dishName}
                substitutionDishName={composition.substitutionDishName}
                initialRows={composition.ingredients}
                userType={userType}
              />
            </div>
          ) : (
            <div className="bg-white border rounded-lg p-6 text-center space-y-4">
              <ChefHat className="h-10 w-10 text-violet-600 mx-auto" aria-hidden="true" />
              <p className="text-sm text-gray-600 max-w-md mx-auto">
                Name your dish and how much you ate. We estimate the ingredients, then you can try
                healthier swaps and see how the scores change.
              </p>
              <button
                type="button"
                onClick={() => setDecomposerOpen(true)}
                className="px-4 py-2 bg-violet-600 text-white rounded-md text-sm font-medium hover:bg-violet-700"
              >
                Describe your meal
              </button>
            </div>
          )}
        </div>
      )}

      {mode === 'recall' && (
        <div id="improve-panel-recall" role="tabpanel" aria-labelledby="improve-tab-recall">
          {composition ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                {composition.recallMeta && (
                  <p className="text-xs text-gray-500">
                    Loaded food diary day
                    {composition.recallMeta.date ? ` · ${composition.recallMeta.date}` : ''}
                    {' · '}
                    {composition.recallMeta.kcal.toFixed(0)} kcal
                    {' · '}
                    {composition.recallMeta.occasions} occasion{composition.recallMeta.occasions !== 1 ? 's' : ''}
                  </p>
                )}
                <button type="button" onClick={clearComposition} className="text-sm text-gray-500 hover:text-gray-800 ml-auto">
                  Choose another day
                </button>
              </div>
              <ImproveHomemadeComposition
                dishName={composition.dishName}
                substitutionDishName={composition.substitutionDishName}
                initialRows={composition.ingredients}
                userType={userType}
              />
            </div>
          ) : (
            <RecallDayPicker onSelect={loadRecallDay} />
          )}
        </div>
      )}

      <RecipeDecomposerModal
        open={decomposerOpen}
        onClose={() => setDecomposerOpen(false)}
        userType={userType}
        accent="purple"
        onApply={(ingredients, name) => {
          setComposition({
            dishName: name?.trim() || 'Homemade meal',
            ingredients,
          });
          setDecomposerOpen(false);
        }}
      />
    </div>
  );
}
