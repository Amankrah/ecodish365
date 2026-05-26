/**
 * PackagedFoodScanner — HSR-only packaged-food flow:
 *   Step 1: image input (mobile camera or file upload)
 *   Step 2: review-and-edit prefilled NF panel form (PackagedFoodPanelForm)
 *   Step 3: HSR result with audience-aware explanation + provenance
 *
 * HEFI / HENI / FCS scoring of packaged foods lives in the 24-h recall
 * wizard (/recall-24h) where a scanned product can be logged per occasion.
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Camera, Loader2, AlertCircle, Award, RotateCcw, AlertTriangle, Info,
  TrendingUp, ThumbsUp, CalendarClock,
  Image as ImageIcon, X, Check,
} from 'lucide-react';

const MAX_IMAGES = 3;
import {
  CNFApiService,
  type NFPanelExtraction,
  type HSRCategoryCode,
  type HsrFromPanelResponse,
} from '@/lib/api';
import { PackagedFoodPanelForm } from './PackagedFoodPanelForm';

type UserType = 'individual' | 'researcher' | 'policy';

interface Props {
  userType: UserType;
}

type FlowStep = 'capture' | 'reviewing' | 'scored' | 'error';

interface ScannerError {
  code: string;
  message: string;
}

export function PackagedFoodScanner({ userType }: Props): JSX.Element {
  const [step, setStep] = useState<FlowStep>('capture');
  const [pickedFiles, setPickedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [extracting, setExtracting] = useState(false);
  const [editedPanel, setEditedPanel] = useState<NFPanelExtraction | null>(null);
  const [cacheHit, setCacheHit] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [scoreResult, setScoreResult] = useState<HsrFromPanelResponse | null>(null);
  const [error, setError] = useState<ScannerError | null>(null);

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
      setError({
        code: 'too_many_images',
        message: `Only the first ${MAX_IMAGES} images are kept per scan.`,
      });
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
    setExtracting(true);
    setStep('capture');
    try {
      const rsp = await CNFApiService.extractPackagedFood(pickedFiles, { target: 'hsr' });
      if (!rsp.extraction.extraction_succeeded) {
        setError({
          code: 'extraction_failed',
          message: rsp.extraction.failure_reason
            || 'No nutrition panel detected. Try clearer photos of the Nutrition Facts panel.',
        });
        setStep('error');
        return;
      }
      setEditedPanel(rsp.extraction);
      setCacheHit(rsp.cache_hit);
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

  async function handleScore(
    edited: NFPanelExtraction,
    category: HSRCategoryCode,
    consumedPortionGrams: number,
    fvnlPercent: number,
  ): Promise<void> {
    setError(null);
    setEditedPanel(edited);
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
    for (const url of previewUrls) URL.revokeObjectURL(url);
    setPickedFiles([]);
    setPreviewUrls([]);
    setEditedPanel(null);
    setScoreResult(null);
    setCacheHit(false);
    setError(null);
    setStep('capture');
  }

  function reextract(): void {
    if (pickedFiles.length > 0) {
      void handleExtract();
    }
  }

  return (
    <div className="space-y-6">
      {step === 'capture' && (() => {
        const canAddMore = pickedFiles.length < MAX_IMAGES;
        const canExtract = pickedFiles.length > 0 && !extracting;
        return (
        <div className="bg-white rounded-lg border p-6 shadow-sm space-y-4">
          <div className="flex items-start gap-3">
            <Camera className="h-6 w-6 text-blue-700 flex-shrink-0 mt-1" aria-hidden="true" />
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900">Photograph the Nutrition Facts panel</h2>
              <p className="text-sm text-gray-600 mt-1">
                On mobile, tap to use the rear camera. On desktop, you can also pick a file.
                Aim for the panel filling most of the frame, with even lighting and no glare.
              </p>
              <p className="text-sm text-gray-600 mt-1">
                You can add up to <strong>{MAX_IMAGES} photos</strong> of the same product
                — useful when the NF panel, ingredient list, or net weight are on different faces.
              </p>
            </div>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 bg-gray-50 space-y-3">
            <div className="flex flex-wrap items-center justify-center gap-2">
              <label
                className={`cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-md ${
                  canAddMore && !extracting
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <Camera className="h-5 w-5" aria-hidden="true" />
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
                className={`cursor-pointer inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-md border ${
                  canAddMore && !extracting
                    ? 'bg-white border-blue-300 text-blue-800 hover:bg-blue-50'
                    : 'bg-gray-100 border-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                <ImageIcon className="h-5 w-5" aria-hidden="true" />
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
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md"
              >
                {extracting
                  ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                  : <Check className="h-5 w-5" aria-hidden="true" />}
                {extracting
                  ? 'Extracting…'
                  : pickedFiles.length === 0
                    ? 'Extract panel'
                    : `Extract from ${pickedFiles.length} photo${pickedFiles.length > 1 ? 's' : ''}`}
              </button>
            </div>
            <p className="text-xs text-gray-500 text-center">
              Accepts JPEG, PNG, WebP, HEIC (iOS), AVIF. Max 10 MB per photo.
              {' · '}{pickedFiles.length}/{MAX_IMAGES} selected.
              {!canAddMore && ' Maximum reached.'}
            </p>
          </div>

          {previewUrls.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-gray-600">Selected photos:</p>
              <div className="flex flex-wrap justify-center gap-3">
                {previewUrls.map((url, i) => (
                  <div key={i} className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={url}
                      alt={`Selected packaged food face ${i + 1}`}
                      className="max-h-48 rounded-md border border-gray-200"
                    />
                    {!extracting && (
                      <button
                        type="button"
                        onClick={() => removePickedAt(i)}
                        aria-label={`Remove photo ${i + 1}`}
                        title={`Remove photo ${i + 1}`}
                        className="absolute -top-2 -right-2 inline-flex items-center justify-center h-6 w-6 rounded-full bg-white border border-gray-300 text-gray-700 hover:bg-red-50 hover:text-red-700 hover:border-red-300 shadow-sm"
                      >
                        <X className="h-3.5 w-3.5" aria-hidden="true" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {extracting && (
            <div className="flex items-center gap-2 text-sm text-gray-700 bg-blue-50 border border-blue-200 rounded-md p-3">
              <Loader2 className="h-4 w-4 animate-spin text-blue-700" aria-hidden="true" />
              Extracting the nutrition panel… this usually takes 2–3 seconds per photo.
            </div>
          )}

          <p className="text-[11px] text-gray-500 border-t pt-2">
            <strong>Privacy:</strong> your image{pickedFiles.length === 1 ? '' : 's'} {pickedFiles.length === 1 ? 'is' : 'are'} sent to a multimodal AI model for one-time
            text extraction and {pickedFiles.length === 1 ? 'is' : 'are'} not stored after that. Only the extracted nutrition values
            (which you will review on the next screen) are saved if you choose to score this product.
          </p>
        </div>
        );
      })()}

      {step === 'reviewing' && editedPanel && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg border p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900">Review nutrition values</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Confirm or correct the values below, then score with HSR. Yellow / red dots
                  flag fields the AI was less confident about.
                </p>
              </div>
              {cacheHit && (
                <span className="text-xs px-2 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
                  cached
                </span>
              )}
            </div>

            {previewUrls.length > 0 && (
              <details className="mt-3 text-sm">
                <summary className="cursor-pointer text-blue-700">
                  Show {previewUrls.length === 1 ? 'source image' : `${previewUrls.length} source images`} side-by-side
                </summary>
                <div className="mt-2 flex flex-wrap gap-2">
                  {previewUrls.map((url, i) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={i}
                      src={url}
                      alt={`Source image ${i + 1}`}
                      className="max-h-48 rounded border border-gray-200"
                    />
                  ))}
                </div>
              </details>
            )}
          </div>

          <div className="bg-white rounded-lg border p-6 shadow-sm space-y-3">
            <PackagedFoodPanelForm
              initial={editedPanel}
              busy={scoring}
              onSubmit={handleScore}
              onReextract={reextract}
              onCancel={reset}
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
            <CalendarClock className="h-5 w-5 text-blue-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div className="text-sm text-blue-900">
              <p className="font-semibold">Want HEFI, HENI, or FCS instead?</p>
              <p className="mt-1">
                Use the{' '}
                <Link href="/recall-24h" className="underline font-medium">
                  24-hour dietary recall
                </Link>
                {' '}and choose <strong>Scan packaged food</strong> for the occasion
                (breakfast, snack, etc.). That path decomposes the ingredient list into
                CNF foods and folds the product into your full day before scoring.
              </p>
            </div>
          </div>
        </div>
      )}

      {step === 'scored' && scoreResult && (
        <PackagedFoodResult result={scoreResult} userType={userType} onAnother={reset} />
      )}

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

  const humaniseKey = (k: string): string =>
    k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  const PARAGRAPH_KEYS = [
    'headline', 'message', 'units', 'interpretation', 'mandatory_caveat',
    'simple_guidance', 'cross_category_tool', 'reporting', 'thresholds',
    'use_cases', 'category_specificity', 'version', 'fvnl_imputation',
    'algorithm_verification', 'primary', 'algorithm_description',
    'canadian_validation', 'evaluation',
  ];

  return (
    <div className="bg-white rounded-lg border p-6 shadow-sm space-y-5">
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

      {Object.entries(explanations).length > 0 && (
        <div className="border-t pt-4 space-y-3">
          {Object.entries(explanations).map(([sectionKey, section]) => {
            if (!section || typeof section !== 'object') return null;
            const sec = section as Record<string, string>;
            const title = sec.title || humaniseKey(sectionKey);
            const paragraphs = PARAGRAPH_KEYS
              .filter(k => typeof sec[k] === 'string' && sec[k].trim().length > 0)
              .map(k => ({ key: k, text: sec[k] }));
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
