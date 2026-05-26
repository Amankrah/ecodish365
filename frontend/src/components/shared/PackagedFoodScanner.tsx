/**
 * PackagedFoodScanner — orchestrates the 3-step packaged-food flow:
 *   Step 1: image input (mobile camera or file upload)
 *   Step 2: review-and-edit prefilled NF panel form (PackagedFoodPanelForm)
 *   Step 3: HSR result with audience-aware explanation + provenance
 *
 * Step 1 uses <input type="file" accept="image/*" capture="environment"> —
 * on mobile this opens the rear camera directly; on desktop it shows the
 * file picker. We deliberately do NOT use getUserMedia for v1 because the
 * capture-input flow is simpler, works in iOS Safari without permissions
 * gymnastics, and lets users review the photo natively before submitting.
 */
'use client';

import { useState } from 'react';
import { Camera, Loader2, AlertCircle, Award, RotateCcw, AlertTriangle, Info, TrendingUp, ThumbsUp, FileText, ListChecks } from 'lucide-react';
import {
  CNFApiService,
  type NFPanelExtraction,
  type PackagedFoodExtraction,
  type HSRCategoryCode,
  type HsrFromPanelResponse,
  type DecompositionResult,
} from '@/lib/api';
import { PackagedFoodPanelForm } from './PackagedFoodPanelForm';
import { PackagedFoodCompositionForm } from './PackagedFoodCompositionForm';

type UserType = 'individual' | 'researcher' | 'policy';

interface Props {
  userType: UserType;
}

type FlowStep =
  | 'capture'      // user picking an image
  | 'reviewing'    // editing the extracted NF panel (Phase 1 + 2)
  | 'decomposing'  // /api/packaged-food/decompose-ingredients/ in flight
  | 'composing'    // editing the inferred CNF composition (Phase 2)
  | 'scored'       // HSR result (Phase 1 path)
  | 'error';

interface ScannerError {
  code: string;
  message: string;
}

export function PackagedFoodScanner({ userType }: Props): JSX.Element {
  const [step, setStep] = useState<FlowStep>('capture');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);
  // Phase 2: extraction is now the unified wrapper. nf_panel and
  // ingredient_list may each be null.
  const [combined, setCombined] = useState<PackagedFoodExtraction | null>(null);
  // Editable copy of the NF panel (Phase 2: this is initialised from
  // combined.nf_panel and survives edits the user makes in the form).
  const [editedPanel, setEditedPanel] = useState<NFPanelExtraction | null>(null);
  const [scoring, setScoring] = useState(false);
  const [scoreResult, setScoreResult] = useState<HsrFromPanelResponse | null>(null);
  // Phase 2: decomposition state for the "full scoring" path.
  const [decomposing, setDecomposing] = useState(false);
  const [decomposition, setDecomposition] = useState<DecompositionResult | null>(null);
  const [error, setError] = useState<ScannerError | null>(null);

  async function handleImagePicked(file: File): Promise<void> {
    setError(null);
    setImageFile(file);
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setImagePreviewUrl(URL.createObjectURL(file));
    setExtracting(true);
    setStep('capture');
    try {
      // Phase 2: adaptive extraction. May return NF, ingredients, or both.
      const rsp = await CNFApiService.extractPackagedFoodCombined(file);
      if (!rsp.extraction.extraction_succeeded) {
        setError({
          code: 'extraction_failed',
          message: rsp.extraction.failure_reason
            || 'No nutrition panel or ingredient list detected in this image. Try a clearer photo of the back-of-pack label.',
        });
        setStep('error');
        return;
      }
      setCombined(rsp.extraction);
      setEditedPanel(rsp.extraction.nf_panel);
      setStep('reviewing');
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { error?: string; message?: string } } };
      const code = ax.response?.data?.error || `http_${ax.response?.status ?? 'unknown'}`;
      const msg = ax.response?.data?.message
        || (ax.response?.status === 429 ? 'Rate limit reached. Try again later.'
        :   ax.response?.status === 503 ? 'AI service temporarily unavailable.'
        :   'Failed to extract the nutrition panel.');
      setError({ code, message: msg });
      setStep('error');
    } finally {
      setExtracting(false);
    }
  }

  // Phase 2 path — decompose ingredients with the (possibly edited) panel.
  async function handleDecompose(): Promise<void> {
    if (!editedPanel || !combined?.ingredient_list) return;
    setError(null);
    setDecomposing(true);
    setStep('decomposing');
    try {
      const rsp = await CNFApiService.decomposePackagedFood(
        editedPanel, combined.ingredient_list,
      );
      if (!rsp.decomposition.decomposition_succeeded) {
        setError({
          code: 'decomposition_failed',
          message: rsp.decomposition.failure_reason
            || 'Ingredient decomposition failed. Try editing the ingredient list (or NF panel) first.',
        });
        setStep('error');
        return;
      }
      setDecomposition(rsp.decomposition);
      setStep('composing');
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { error?: string; message?: string } } };
      setError({
        code: ax.response?.data?.error || 'decomposition_failed',
        message: ax.response?.data?.message
          || 'Could not decompose the ingredient list.',
      });
      setStep('error');
    } finally {
      setDecomposing(false);
    }
  }

  async function handleScore(
    edited: NFPanelExtraction,
    category: HSRCategoryCode,
    consumedPortionGrams: number,
    fvnlPercent: number,
  ): Promise<void> {
    setError(null);
    setEditedPanel(edited);   // persist edits in case user backtracks to decompose
    setScoring(true);
    try {
      const rsp = await CNFApiService.calculateHsrFromPanel(edited, category, {
        userType, consumedPortionGrams, fvnlPercent,
      });
      setScoreResult(rsp);
      setStep('scored');
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { error?: string; message?: string } } };
      setError({
        code: ax.response?.data?.error || 'score_failed',
        message: ax.response?.data?.message || 'Failed to score the panel.',
      });
      setStep('error');
    } finally {
      setScoring(false);
    }
  }

  function reset(): void {
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    setImageFile(null);
    setImagePreviewUrl(null);
    setCombined(null);
    setEditedPanel(null);
    setScoreResult(null);
    setDecomposition(null);
    setError(null);
    setStep('capture');
  }

  function reextract(): void {
    if (imageFile) {
      void handleImagePicked(imageFile);
    }
  }

  // ---------- render ----------

  return (
    <div className="space-y-6">
      {/* Step 1 — capture / upload. Always visible until we have an extraction. */}
      {step === 'capture' && (
        <div className="bg-white rounded-lg border p-6 shadow-sm space-y-4">
          <div className="flex items-start gap-3">
            <Camera className="h-6 w-6 text-blue-700 flex-shrink-0 mt-1" aria-hidden="true" />
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900">Photograph the Nutrition Facts panel</h2>
              <p className="text-sm text-gray-600 mt-1">
                On mobile, tap to use the rear camera. On desktop, you can also pick a file.
                Aim for the panel filling most of the frame, with even lighting and no glare.
              </p>
            </div>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50">
            <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md">
              <Camera className="h-5 w-5" aria-hidden="true" />
              {imageFile ? 'Pick a different image' : 'Take photo or pick file'}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={e => {
                  const f = e.target.files?.[0];
                  if (f) void handleImagePicked(f);
                }}
                disabled={extracting}
              />
            </label>
            <p className="text-xs text-gray-500 mt-2">
              Accepts JPEG, PNG, WebP, HEIC (iOS), AVIF. Max 10 MB.
            </p>
          </div>

          {imagePreviewUrl && (
            <div className="space-y-2">
              <p className="text-xs text-gray-600">Image preview:</p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imagePreviewUrl}
                alt="Selected packaged food"
                className="max-h-64 mx-auto rounded-md border border-gray-200"
              />
            </div>
          )}

          {extracting && (
            <div className="flex items-center gap-2 text-sm text-gray-700 bg-blue-50 border border-blue-200 rounded-md p-3">
              <Loader2 className="h-4 w-4 animate-spin text-blue-700" aria-hidden="true" />
              Extracting the nutrition panel… this usually takes 2–3 seconds.
            </div>
          )}

          <p className="text-[11px] text-gray-500 border-t pt-2">
            <strong>Privacy:</strong> your image is sent to a multimodal AI model for one-time
            text extraction and is not stored after that. Only the extracted nutrition values
            (which you will review on the next screen) are saved if you choose to score this product.
          </p>
        </div>
      )}

      {/* Step 2 — review-and-edit. Renders the NF panel form when present
          and an ingredient-list status block (Phase 2). */}
      {step === 'reviewing' && combined && (
        <div className="space-y-4">
          {/* Coverage summary: what did we find? */}
          <div className="bg-white rounded-lg border p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900">What we extracted</h2>
                <p className="text-sm text-gray-600 mt-1">
                  This image contains:
                </p>
                <ul className="mt-2 space-y-1 text-sm">
                  <li className="flex items-center gap-2">
                    <FileText className={`h-4 w-4 ${combined.has_nf_panel ? 'text-emerald-600' : 'text-gray-300'}`} aria-hidden="true" />
                    <span className={combined.has_nf_panel ? 'text-gray-900' : 'text-gray-400'}>
                      Nutrition Facts panel{' '}
                      {combined.has_nf_panel ? '✓ found' : '— not in this image'}
                    </span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ListChecks className={`h-4 w-4 ${combined.has_ingredient_list ? 'text-emerald-600' : 'text-gray-300'}`} aria-hidden="true" />
                    <span className={combined.has_ingredient_list ? 'text-gray-900' : 'text-gray-400'}>
                      Ingredient list{' '}
                      {combined.has_ingredient_list ? '✓ found' : '— not in this image'}
                    </span>
                  </li>
                </ul>
                {(!combined.has_nf_panel || !combined.has_ingredient_list) && (
                  <p className="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2">
                    Missing piece? Take another photo focusing on the other side of the
                    package, then come back here.{' '}
                    <button type="button" onClick={reset} className="underline">
                      Try another photo
                    </button>.
                  </p>
                )}
              </div>
              {combined.extraction_metadata.cache_hit && (
                <span className="text-xs px-2 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
                  cached
                </span>
              )}
            </div>

            {imagePreviewUrl && (
              <details className="mt-3 text-sm">
                <summary className="cursor-pointer text-blue-700">Show image side-by-side</summary>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imagePreviewUrl}
                  alt="Source image"
                  className="mt-2 max-h-48 rounded border border-gray-200"
                />
              </details>
            )}
          </div>

          {/* NF panel form — the HSR scoring path (Phase 1) */}
          {editedPanel && (
            <div className="bg-white rounded-lg border p-6 shadow-sm space-y-3">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Review nutrition values</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Confirm or correct the values below before scoring. Yellow / red dots
                  flag fields the AI was less confident about. Hover any field name to
                  see the raw text it read.
                </p>
              </div>
              <PackagedFoodPanelForm
                initial={editedPanel}
                busy={scoring}
                onSubmit={handleScore}
                onReextract={reextract}
                onCancel={reset}
              />
            </div>
          )}

          {/* Phase 2 — ingredient list summary + decompose CTA */}
          {combined.has_ingredient_list && combined.ingredient_list && (
            <div className="bg-white rounded-lg border p-6 shadow-sm space-y-3">
              <div className="flex items-start gap-3">
                <ListChecks className="h-5 w-5 text-blue-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Ingredient list also found
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Decompose into CNF foods to score with HEFI, HENI, FCS, dietary-pattern,
                    or environmental scorers. Composition will be INFERRED from the ingredient
                    order + Nutrition Facts macros — labels rarely disclose percentages.
                  </p>
                </div>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded p-2 text-xs text-gray-700 max-h-32 overflow-y-auto">
                <p className="font-medium text-gray-600 mb-1">Raw ingredient text the AI read:</p>
                <p className="font-mono">{combined.ingredient_list.ingredients_text}</p>
              </div>
              {combined.ingredient_list.ingredients_parsed.length > 0 && (
                <p className="text-xs text-gray-500">
                  Parsed {combined.ingredient_list.ingredients_parsed.length} ingredient
                  {combined.ingredient_list.ingredients_parsed.length === 1 ? '' : 's'}
                  {combined.ingredient_list.explicit_percentages_found
                    && ' (label discloses explicit %)'}.
                </p>
              )}
              <button
                type="button"
                onClick={handleDecompose}
                disabled={decomposing || !editedPanel}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium rounded-md"
              >
                {decomposing ? (
                  <><Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />Decomposing…</>
                ) : (
                  <>📊 Decompose for full scoring (HEFI / HENI / FCS / pattern / env)</>
                )}
              </button>
              {!editedPanel && (
                <p className="text-xs text-red-700">
                  Decomposition requires the Nutrition Facts panel as a macro-conservation
                  anchor. Take a photo that includes both.
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 3a — decomposing (loading) */}
      {step === 'decomposing' && (
        <div className="bg-white rounded-lg border p-6 shadow-sm flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-indigo-700" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-gray-900">
              Decomposing ingredient list into CNF composition…
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              Looking up CNF candidates for each ingredient, then asking the LLM to
              infer per-ingredient masses constrained by your NF panel macros. ~5 seconds.
            </p>
          </div>
        </div>
      )}

      {/* Step 3b — composing (editable composition table + route to scorers) */}
      {step === 'composing' && decomposition && editedPanel && (
        <div className="bg-white rounded-lg border p-6 shadow-sm space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900">
                Inferred composition — review before scoring
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Each label ingredient was mapped to a CNF food + an inferred mass.
                Edit any obviously-wrong mass below, then route to your chosen scorer.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setStep('reviewing')}
              className="px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              ← Back to NF panel
            </button>
          </div>
          <PackagedFoodCompositionForm
            decomposition={decomposition}
            panel={editedPanel}
            userType={userType}
          />
        </div>
      )}

      {/* Step 4 — HSR result (Phase 1 path). */}
      {step === 'scored' && scoreResult && (
        <PackagedFoodResult result={scoreResult} userType={userType} onAnother={reset} />
      )}

      {/* Error state — graceful retry. */}
      {step === 'error' && error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1 text-sm">
            <p className="font-semibold text-red-900">
              {error.code === 'extraction_failed' ? 'No nutrition panel found'
               : error.code === 'rate_limit' ? 'Rate limit reached'
               : error.code === 'circuit_breaker' ? 'Service temporarily unavailable'
               : 'Extraction failed'}
            </p>
            <p className="text-red-800 mt-1">{error.message}</p>
            <button
              type="button"
              onClick={reset}
              className="mt-2 inline-flex items-center gap-1 px-3 py-1 bg-white border border-red-300 text-red-800 text-xs font-medium rounded-md hover:bg-red-50"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              Try a different photo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


// ---------- Result rendering ----------

interface ResultProps {
  result: HsrFromPanelResponse;
  userType: UserType;
  onAnother: () => void;
}

function PackagedFoodResult({ result, userType, onAnother }: ResultProps): JSX.Element {
  const stars = result.hsr_result.star_rating;
  const explanations = result.explanations as Record<string, Record<string, string>>;
  const provenance = result.provenance;
  const notes = result.result_notes;

  // Humanise an explanation-section key for use as a fallback heading
  // when the section dict doesn't carry an explicit "title" string.
  const humaniseKey = (k: string): string =>
    k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // The set of keys we treat as "content paragraphs" inside an explanation
  // section. `title` is rendered separately as the heading.
  const PARAGRAPH_KEYS = [
    'headline', 'message', 'units', 'interpretation', 'mandatory_caveat',
    'simple_guidance', 'cross_category_tool', 'reporting', 'thresholds',
    'use_cases', 'category_specificity', 'version', 'fvnl_imputation',
    'algorithm_verification', 'primary', 'algorithm_description',
    'canadian_validation', 'evaluation',
  ];

  return (
    <div className="bg-white rounded-lg border p-6 shadow-sm space-y-5">
      {/* Headline + stars */}
      <div className="flex items-start gap-3">
        <Award className="h-7 w-7 text-blue-700 flex-shrink-0 mt-1" aria-hidden="true" />
        <div className="flex-1">
          <h2 className="text-xl font-bold text-gray-900">
            Health Star Rating: {stars.toFixed(1)} / 5
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            HSRAC v9, Category {result.hsr_result.category}
            {result.hsr_result.level && ` · ${result.hsr_result.level.replace(/_/g, ' ')}`}
          </p>
        </div>
        <button
          type="button"
          onClick={onAnother}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Scan another
        </button>
      </div>

      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(i => {
          const filled = stars >= i;
          const half = !filled && stars >= i - 0.5;
          return (
            <span
              key={i}
              className={`text-3xl ${filled || half ? 'text-amber-500' : 'text-gray-300'}`}
              aria-hidden="true"
            >
              {filled ? '★' : half ? '⯨' : '☆'}
            </span>
          );
        })}
        <span className="ml-2 text-sm text-gray-600">{stars.toFixed(1)} / 5.0</span>
      </div>

      {/* Score drivers — why this rating */}
      {notes?.drivers?.length > 0 && (
        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-1.5">
            <TrendingUp className="h-4 w-4 text-blue-700" aria-hidden="true" />
            What drove this rating
          </h3>
          <ul className="space-y-1.5 text-sm">
            {notes.drivers.map((d, i) => (
              <li key={i} className="flex items-start gap-2">
                <span
                  className={
                    d.kind === 'modifying_good'
                      ? 'text-emerald-600'
                      : d.severity === 'high'
                      ? 'text-red-600'
                      : 'text-amber-600'
                  }
                >
                  {d.kind === 'modifying_good' ? <ThumbsUp className="h-4 w-4" aria-hidden="true" /> : '●'}
                </span>
                <span className="text-gray-800">{d.threshold_phrase}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Interpretive caveats specific to this product */}
      {notes?.notes?.length > 0 && (
        <div className="border-t pt-4 space-y-3">
          {notes.notes.map((n, i) => {
            const Icon = n.severity === 'warn' ? AlertTriangle : Info;
            const palette = n.severity === 'warn'
              ? 'bg-amber-50 border-amber-300 text-amber-900'
              : 'bg-blue-50 border-blue-200 text-blue-900';
            return (
              <div key={i} className={`flex items-start gap-2 p-3 border rounded-md ${palette}`}>
                <Icon className="h-4 w-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1 text-sm">
                  <p className="font-semibold">{n.title}</p>
                  <p className="mt-1">{n.message}</p>
                  {n.suggestion && (
                    <p className="mt-1 italic text-xs">{n.suggestion}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Audience-aware explanation pack (now renders all sub-fields). */}
      {Object.entries(explanations).length > 0 && (
        <div className="border-t pt-4 space-y-3">
          {Object.entries(explanations).map(([sectionKey, section]) => {
            if (!section || typeof section !== 'object') return null;
            const sec = section as Record<string, string>;
            const title = sec.title || humaniseKey(sectionKey);
            const paragraphs = PARAGRAPH_KEYS
              .filter(k => typeof sec[k] === 'string' && sec[k].trim().length > 0)
              .map(k => ({ key: k, text: sec[k] }));
            // Also include any other string fields we didn't enumerate
            // explicitly (forward-compat with future explanation pack keys).
            const knownKeys = new Set(['title', ...PARAGRAPH_KEYS]);
            for (const [k, v] of Object.entries(sec)) {
              if (!knownKeys.has(k) && typeof v === 'string' && v.trim().length > 0) {
                paragraphs.push({ key: k, text: v });
              }
            }
            if (paragraphs.length === 0 && !sec.title) return null;

            const isCaveat = sectionKey.toLowerCase().includes('caveat')
                          || paragraphs.some(p => p.key === 'mandatory_caveat');
            const palette = isCaveat
              ? 'bg-amber-50 border-amber-200'
              : 'bg-gray-50 border-gray-200';

            return (
              <div key={sectionKey} className={`border rounded-md p-3 ${palette}`}>
                <p className="font-semibold text-gray-900 text-sm">{title}</p>
                {paragraphs.map(p => {
                  const isMandatory = p.key === 'mandatory_caveat';
                  return (
                    <p
                      key={p.key}
                      className={`mt-1.5 text-sm leading-relaxed ${
                        isMandatory ? 'text-amber-900 font-medium' : 'text-gray-700'
                      }`}
                    >
                      {isMandatory && '⚠ '}
                      {p.text}
                    </p>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}

      {/* Provenance — visible by default. Researcher mode auto-expands. */}
      <details className="text-xs border-t pt-4" open={userType === 'researcher'}>
        <summary className="cursor-pointer text-gray-600 font-medium">
          ⌖ Source: extracted from image by {provenance.model} at {provenance.extracted_at}
          {provenance.extraction_warnings.length > 0 && ' (with warnings)'}
        </summary>
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md space-y-1 text-gray-700">
          <p><strong>Model:</strong> {provenance.provider}/{provenance.model}</p>
          <p><strong>Prompt version:</strong> {provenance.prompt_version}, schema {provenance.schema_version}</p>
          <p><strong>Image SHA-256:</strong> <code className="text-[10px]">{provenance.image_sha256}</code></p>
          <p><strong>Confirmed at:</strong> {provenance.confirmed_at}</p>
          <p>
            <strong>Serving size used:</strong> {provenance.serving_size_grams.toFixed(0)} g
            {provenance.ml_to_g_assumption && ' (ml→g via density=1.0 assumption)'}
          </p>
          <p><strong>Consumed portion:</strong> {provenance.consumed_portion_grams.toFixed(0)} g</p>
          <p>
            <strong>FVNL supplied:</strong>{' '}
            {provenance.fvnl_percent_supplied_by_user ? 'yes (user-entered)' : 'no (defaulted to 0%)'}
          </p>
          {provenance.extraction_warnings.length > 0 && (
            <div>
              <p className="font-semibold mt-1">Warnings:</p>
              <ul className="list-disc list-inside text-amber-800">
                {provenance.extraction_warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
          {provenance.sanity_guard_rejections.length > 0 && (
            <div>
              <p className="font-semibold mt-1 text-red-700">Sanity-guard rejections:</p>
              <ul className="list-disc list-inside text-red-800">
                {provenance.sanity_guard_rejections.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

