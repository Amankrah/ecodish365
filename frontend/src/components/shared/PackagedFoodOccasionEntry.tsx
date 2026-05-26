/**
 * PackagedFoodOccasionEntry — inline scan-and-decompose flow for one recall
 * occasion (e.g. breakfast granola bar, PM snack yogurt).
 *
 * Extracts NF panel + ingredient list from a label photo, optionally lets
 * the user edit the panel, decomposes to CNF ingredients, and reports back
 * to Recall24hWizard for aggregation with text-described meals.
 */
'use client';

import { useState } from 'react';
import {
  Camera, Loader2, AlertCircle, Check, RotateCcw, ChevronDown, ChevronUp,
  X, Image as ImageIcon,
} from 'lucide-react';
import {
  CNFApiService,
  type IngredientListExtraction,
  type NFPanelExtraction,
} from '@/lib/api';
import {
  resolvePackagedDishName,
  resolvePackagedMass,
  type PackagedOccasionState,
} from '@/lib/recallPackagedFood';

const MAX_IMAGES = 3;

type UserType = 'individual' | 'researcher' | 'policy';

type Step = 'capture' | 'reviewing' | 'decomposing' | 'ready' | 'error';

interface Props {
  occasionLabel: string;
  userType: UserType;
  value: PackagedOccasionState | null;
  onChange: (state: PackagedOccasionState | null) => void;
}

interface ScannerError {
  message: string;
}

export function PackagedFoodOccasionEntry({
  occasionLabel, value, onChange,
}: Props): JSX.Element {
  const [step, setStep] = useState<Step>(value ? 'ready' : 'capture');
  const [pickedFiles, setPickedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>(
    value?.imagePreviewUrl ? [value.imagePreviewUrl] : [],
  );
  const [editedPanel, setEditedPanel] = useState<NFPanelExtraction | null>(
    value?.panel ?? null,
  );
  const [ingredientList, setIngredientList] = useState<IngredientListExtraction | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [decomposing, setDecomposing] = useState(false);
  const [error, setError] = useState<ScannerError | null>(null);
  const [showPanelEditor, setShowPanelEditor] = useState(false);
  const [netWeightMissing, setNetWeightMissing] = useState(false);

  function appendPickedFiles(incoming: FileList | File[] | null): void {
    if (!incoming) return;
    const arr = Array.from(incoming);
    const room = MAX_IMAGES - pickedFiles.length;
    if (room <= 0) return;
    const accepted = arr.slice(0, room);
    if (accepted.length === 0) return;
    const newUrls = accepted.map(f => URL.createObjectURL(f));
    setPickedFiles(prev => [...prev, ...accepted]);
    setPreviewUrls(prev => [...prev, ...newUrls]);
    setError(null);
    if (arr.length > room) {
      setError({ message: `Only the first ${MAX_IMAGES} images are kept per scan.` });
    }
  }

  function removePickedAt(idx: number): void {
    URL.revokeObjectURL(previewUrls[idx]);
    setPickedFiles(prev => prev.filter((_, i) => i !== idx));
    setPreviewUrls(prev => prev.filter((_, i) => i !== idx));
    setError(null);
  }

  async function handleExtract(): Promise<void> {
    if (pickedFiles.length === 0) return;
    setError(null);
    onChange(null);
    setExtracting(true);
    setStep('capture');
    try {
      const rsp = await CNFApiService.extractPackagedFoodCombined(pickedFiles);
      if (!rsp.extraction.extraction_succeeded) {
        setError({
          message: rsp.extraction.failure_reason
            || 'No nutrition panel or ingredient list detected. Try clearer photos of the back-of-pack label.',
        });
        setStep('error');
        return;
      }
      if (!rsp.extraction.ingredient_list?.ingredients_parsed?.length) {
        setError({
          message: 'Ingredient list not found on these photos. For recall scoring we need the ingredient list — try a photo that includes it, or describe the meal as text instead.',
        });
        setStep('error');
        return;
      }
      setEditedPanel(rsp.extraction.nf_panel);
      setIngredientList(rsp.extraction.ingredient_list);
      setStep('reviewing');
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { message?: string } } };
      setError({
        message: ax.response?.data?.message
          || (ax.response?.status === 429 ? 'Rate limit reached. Try again later.'
          :   ax.response?.status === 503 ? 'AI service temporarily unavailable.'
          :   'Failed to extract the label.'),
      });
      setStep('error');
    } finally {
      setExtracting(false);
    }
  }

  async function handleDecompose(panel: NFPanelExtraction): Promise<void> {
    if (!ingredientList) return;
    setError(null);
    setNetWeightMissing(false);
    setDecomposing(true);
    setStep('decomposing');
    try {
      const rsp = await CNFApiService.decomposePackagedFood(panel, ingredientList);
      if (!rsp.decomposition.decomposition_succeeded) {
        const reason = rsp.decomposition.failure_reason || '';
        // Recoverable: panel didn't show net weight AND we couldn't fall back
        // to servings × serving_size. Stay on the review step, expand the
        // editor, highlight the field, and let the user supply it and retry.
        if (reason.startsWith('no_net_weight')) {
          setEditedPanel(panel);
          setNetWeightMissing(true);
          setShowPanelEditor(true);
          setError({
            message: 'Net weight not on this panel. Enter it below (check the front or side of pack) and retry.',
          });
          setStep('reviewing');
          return;
        }
        setError({
          message: reason
            || 'Decomposition failed. Edit net weight on the panel or switch to text entry.',
        });
        setStep('error');
        return;
      }
      const dishName = resolvePackagedDishName(panel);
      const totalMass = resolvePackagedMass(panel, rsp.decomposition);
      const state: PackagedOccasionState = {
        dishName,
        totalMass,
        panel,
        decomposition: rsp.decomposition,
        imagePreviewUrl: previewUrls[0] ?? undefined,
      };
      onChange(state);
      setStep('ready');
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { message?: string } } };
      setError({
        message: ax.response?.data?.message || 'Could not decompose the ingredient list.',
      });
      setStep('error');
    } finally {
      setDecomposing(false);
    }
  }

  function reset(): void {
    for (const url of previewUrls) URL.revokeObjectURL(url);
    setPickedFiles([]);
    setPreviewUrls([]);
    setEditedPanel(null);
    setIngredientList(null);
    setError(null);
    setShowPanelEditor(false);
    setNetWeightMissing(false);
    onChange(null);
    setStep('capture');
  }

  function updatePanelField(
    patch: Partial<Pick<NFPanelExtraction, 'product_name_visible' | 'brand_visible' | 'net_weight'>>,
  ): void {
    if (!editedPanel) return;
    setEditedPanel({
      ...editedPanel,
      ...patch,
      product_name_visible: patch.product_name_visible ?? editedPanel.product_name_visible,
      brand_visible: patch.brand_visible ?? editedPanel.brand_visible,
      net_weight: patch.net_weight ?? editedPanel.net_weight,
    });
  }

  if (step === 'ready' && value) {
    return (
      <div className="rounded-md border border-emerald-300 bg-emerald-50 p-3 space-y-2">
        <div className="flex items-start gap-2">
          <Check className="h-4 w-4 text-emerald-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-emerald-900 truncate">{value.dishName}</p>
            <p className="text-xs text-emerald-800 mt-0.5">
              {value.decomposition.ingredients.length} CNF ingredients · {value.totalMass.toFixed(0)} g
              · confidence {(value.decomposition.decomposition_confidence * 100).toFixed(0)}%
            </p>
            <p className="text-[11px] text-emerald-700 mt-1">
              Composition inferred from label — will fold into your {occasionLabel.toLowerCase()} occasion.
            </p>
          </div>
          <button
            type="button"
            onClick={reset}
            className="text-xs text-emerald-800 hover:text-emerald-950 underline flex-shrink-0"
          >
            Retake
          </button>
        </div>
        {previewUrls.length > 0 && (
          <div className="flex gap-1.5">
            {previewUrls.map((url, i) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={i}
                src={url}
                alt={`Scanned packaged food label face ${i + 1}`}
                className="max-h-24 rounded border border-emerald-200"
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const canAddMore = pickedFiles.length < MAX_IMAGES;
  const canExtract = pickedFiles.length > 0 && !extracting;

  return (
    <div className="space-y-3 rounded-md border border-dashed border-blue-300 bg-blue-50/50 p-3">
      <div className="text-xs text-gray-700">
        <p>
          Photograph the <strong>Nutrition Facts</strong> and <strong>ingredient list</strong> on the package.
          We&apos;ll infer CNF ingredients for this {occasionLabel.toLowerCase()} occasion.
        </p>
        <p className="mt-1 text-gray-600">
          You can upload up to <strong>{MAX_IMAGES} photos</strong> of the same product — useful when the NF panel,
          ingredient list, and net weight are on different faces.
        </p>
      </div>

      {(step === 'capture' || step === 'error') && (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <label
              className={`cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md ${
                canAddMore && !extracting
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Camera className="h-4 w-4" aria-hidden="true" />
              {pickedFiles.length === 0 ? 'Take photo' : 'Add another photo'}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={e => {
                  appendPickedFiles(e.target.files);
                  e.target.value = '';
                }}
                disabled={!canAddMore || extracting}
              />
            </label>
            <label
              className={`cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border ${
                canAddMore && !extracting
                  ? 'bg-white border-blue-300 text-blue-800 hover:bg-blue-50'
                  : 'bg-gray-100 border-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <ImageIcon className="h-4 w-4" aria-hidden="true" />
              {pickedFiles.length === 0 ? 'Or pick from gallery' : 'Add from gallery'}
              <input
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={e => {
                  appendPickedFiles(e.target.files);
                  e.target.value = '';
                }}
                disabled={!canAddMore || extracting}
              />
            </label>
            <button
              type="button"
              onClick={() => void handleExtract()}
              disabled={!canExtract}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed text-white text-xs font-medium rounded-md"
            >
              {extracting
                ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                : <Check className="h-3.5 w-3.5" aria-hidden="true" />}
              {extracting
                ? 'Extracting…'
                : pickedFiles.length === 0
                  ? 'Extract label'
                  : `Extract from ${pickedFiles.length} photo${pickedFiles.length > 1 ? 's' : ''}`}
            </button>
          </div>
          <p className="text-[11px] text-gray-500">
            {pickedFiles.length}/{MAX_IMAGES} photos selected.
            {!canAddMore && ' Maximum reached.'}
          </p>
        </div>
      )}

      {previewUrls.length > 0 && step !== 'ready' && (
        <div className="flex flex-wrap gap-2">
          {previewUrls.map((url, i) => (
            <div key={i} className="relative">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={url}
                alt={`Selected label face ${i + 1}`}
                className="max-h-32 rounded border border-gray-200"
              />
              {(step === 'capture' || step === 'error') && !extracting && (
                <button
                  type="button"
                  onClick={() => removePickedAt(i)}
                  aria-label={`Remove photo ${i + 1}`}
                  title={`Remove photo ${i + 1}`}
                  className="absolute -top-1.5 -right-1.5 inline-flex items-center justify-center h-5 w-5 rounded-full bg-white border border-gray-300 text-gray-700 hover:bg-red-50 hover:text-red-700 hover:border-red-300 shadow-sm"
                >
                  <X className="h-3 w-3" aria-hidden="true" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {step === 'reviewing' && editedPanel && (
        <div className="space-y-2">
          <div className="text-xs text-gray-700 bg-white border rounded p-2">
            <strong>{resolvePackagedDishName(editedPanel)}</strong>
            {editedPanel.net_weight?.value != null && (
              <> · net {editedPanel.net_weight.value} {editedPanel.net_weight.unit || 'g'}</>
            )}
            {ingredientList && (
              <> · {ingredientList.ingredients_parsed.length} ingredients detected</>
            )}
          </div>
          {netWeightMissing && (
            <div role="alert" className="flex items-start gap-2 text-xs text-red-900 bg-red-50 border border-red-300 rounded p-2">
              <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <span>
                <strong>Net weight required.</strong> The AI couldn&apos;t find a net weight on this panel,
                and there&apos;s no servings-per-container fallback. Enter it below (check the front or side
                of pack — e.g. <em>Net wt 400 g</em>) and click <strong>Confirm &amp; decompose</strong> again.
              </span>
            </div>
          )}
          <button
            type="button"
            onClick={() => setShowPanelEditor(v => !v)}
            className="inline-flex items-center gap-1 text-xs text-blue-700 hover:text-blue-900"
          >
            {showPanelEditor ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            {showPanelEditor
              ? 'Hide panel editor'
              : netWeightMissing
                ? 'Open panel editor to add net weight'
                : 'Edit nutrition panel (optional)'}
          </button>
          {showPanelEditor && editedPanel && (
            <div className="bg-white rounded border p-3 space-y-2 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Product name</label>
                <input
                  type="text"
                  value={editedPanel.product_name_visible.value ?? ''}
                  onChange={e => updatePanelField({
                    product_name_visible: {
                      ...editedPanel.product_name_visible,
                      value: e.target.value,
                    },
                  })}
                  aria-label="Product name"
                  title="Product name"
                  className="w-full px-2 py-1.5 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block font-medium text-gray-700 mb-1">Brand (optional)</label>
                <input
                  type="text"
                  value={editedPanel.brand_visible.value ?? ''}
                  onChange={e => updatePanelField({
                    brand_visible: {
                      ...editedPanel.brand_visible,
                      value: e.target.value,
                    },
                  })}
                  aria-label="Brand name"
                  title="Brand name"
                  className="w-full px-2 py-1.5 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className={`block font-medium mb-1 ${netWeightMissing ? 'text-red-700' : 'text-gray-700'}`}>
                  Net weight (g){netWeightMissing && ' — required'}
                </label>
                <input
                  type="number"
                  min={1}
                  max={5000}
                  step={1}
                  value={editedPanel.net_weight?.value ?? ''}
                  onChange={e => {
                    if (netWeightMissing) setNetWeightMissing(false);
                    updatePanelField({
                      net_weight: {
                        ...(editedPanel.net_weight ?? {
                          unit: 'g', confidence: 0.5, raw_text: null,
                          from_dv_percent: false, from_kcal_conversion: false,
                        }),
                        value: parseFloat(e.target.value) || null,
                        unit: 'g',
                      },
                    });
                  }}
                  aria-label="Net weight in grams"
                  {...(netWeightMissing ? { 'aria-invalid': 'true' as const } : {})}
                  title="Net weight in grams"
                  className={`w-full px-2 py-1.5 border rounded-md ${
                    netWeightMissing
                      ? 'border-red-400 bg-red-50 focus:border-red-500 focus:ring-red-200'
                      : 'border-gray-300'
                  }`}
                  placeholder="e.g. 400"
                  autoFocus={netWeightMissing}
                />
                <p className={`text-[11px] mt-1 ${netWeightMissing ? 'text-red-700' : 'text-gray-500'}`}>
                  Required for mass-conservation when decomposing. Check the front or side of pack if missing.
                </p>
              </div>
            </div>
          )}
          <button
            type="button"
            onClick={() => editedPanel && void handleDecompose(editedPanel)}
            disabled={decomposing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-md disabled:opacity-50"
          >
            {decomposing
              ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              : <Check className="h-3.5 w-3.5" aria-hidden="true" />}
            {decomposing ? 'Decomposing…' : 'Confirm & decompose for recall'}
          </button>
        </div>
      )}

      {step === 'decomposing' && (
        <div className="flex items-center gap-2 text-xs text-gray-700">
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          Mapping ingredients to CNF foods…
        </div>
      )}

      {error && !netWeightMissing && (
        <div role="alert" className="flex items-start gap-2 text-xs text-red-800 bg-red-50 border-l-4 border-red-400 px-2 py-1.5 rounded">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span>{error.message}</span>
        </div>
      )}

      {(step === 'error' || step === 'reviewing') && (
        <button
          type="button"
          onClick={reset}
          className="inline-flex items-center gap-1 text-xs text-gray-600 hover:text-gray-900"
        >
          <RotateCcw className="h-3 w-3" aria-hidden="true" />
          Start over
        </button>
      )}
    </div>
  );
}
