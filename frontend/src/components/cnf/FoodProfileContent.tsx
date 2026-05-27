'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import {
  XMarkIcon,
  ScaleIcon,
  SparklesIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  LinkIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import type { Food } from '@/lib/api';
import { SourceBadge } from '@/components/shared/SourceBadge';
import type { UserType } from '@/components/shared/AudienceToggle';
import { appendToActiveFoodList } from '@/lib/activeFoodList';
import {
  LENS_NUTRIENT_PANELS,
  findNutrientByPatterns,
  getEnergyKcal,
  CNF_PER_100G_NOTE,
  type LensPanelKey,
} from '@/lib/cnfNutrientPanels';
import { EnvironmentalTeaser } from './EnvironmentalTeaser';

const SCORER_LINKS: { label: string; href: string; lens: LensPanelKey }[] = [
  { label: 'HEFI-2019', href: '/hefi/calculate', lens: 'hefi' },
  { label: 'HENI', href: '/heni/calculate', lens: 'heni' },
  { label: 'HSR', href: '/hsr/calculate', lens: 'hsr' },
  { label: 'Food Compass', href: '/fcs/calculate', lens: 'fcs' },
];

export interface FoodProfileContentProps {
  food: Food;
  userType: UserType;
  groupLabel?: string;
  variant?: 'drawer' | 'page';
  onClose?: () => void;
  onAddToCompare?: () => void;
}

export function FoodProfileContent({
  food,
  userType,
  groupLabel,
  variant = 'drawer',
  onClose,
  onAddToCompare,
}: FoodProfileContentProps) {
  const [massG, setMassG] = useState(100);
  const [showAllNutrients, setShowAllNutrients] = useState(false);
  const [expandedLens, setExpandedLens] = useState<LensPanelKey | null>('hefi');

  const energyKcal = useMemo(() => getEnergyKcal(food.NutrientValues), [food.NutrientValues]);
  const scaledEnergy = energyKcal != null ? (energyKcal * massG) / 100 : null;
  const shareUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/cnf/foods/${food.FoodID}`
    : `/cnf/foods/${food.FoodID}`;

  const handleAddToScorecard = () => {
    if (!Number.isFinite(massG) || massG <= 0) {
      toast.error('Enter a portion size in grams');
      return;
    }
    appendToActiveFoodList(
      {
        food_id: food.FoodID,
        food_description: food.FoodDescription,
        food_group: groupLabel ?? food.FoodGroupName,
        mass_g: massG,
      },
      userType,
    );
    toast.success(`Added ${food.FoodDescription} (${massG} g) to Scorecard`);
  };

  const copyShareLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast.success('Link copied to clipboard');
    } catch {
      toast.error('Could not copy link');
    }
  };

  const header = (
    <div className={`sticky top-0 bg-white px-5 py-4 border-b border-gray-200 flex items-start justify-between gap-3 z-10 ${variant === 'page' ? 'rounded-t-xl' : ''}`}>
      <div className="min-w-0">
        {variant === 'page' && (
          <Link href="/cnf/search" className="inline-flex items-center text-xs text-gray-500 hover:text-gray-800 mb-2">
            <ArrowLeftIcon className="w-3.5 h-3.5 mr-1" />
            Back to search
          </Link>
        )}
        <h1 className="text-lg font-semibold text-gray-900 leading-snug">
          {food.FoodDescription}
        </h1>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <SourceBadge foodId={food.FoodID} userType={userType} />
          <span className="text-xs text-gray-500">Code {food.FoodCode}</span>
          <button
            type="button"
            onClick={copyShareLink}
            className="inline-flex items-center text-xs text-blue-700 hover:text-blue-900"
            title="Copy shareable link"
          >
            <LinkIcon className="w-3.5 h-3.5 mr-0.5" />
            Share
          </button>
        </div>
      </div>
      {variant === 'drawer' && onClose && (
        <button
          type="button"
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 shrink-0"
          title="Close"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      )}
    </div>
  );

  const body = (
    <div className="px-5 py-4 space-y-5">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Food group</div>
          <div className="text-gray-900">
            {groupLabel ?? food.FoodGroupName ?? `Group ${food.FoodGroupID}`}
          </div>
          {food.FoodGroupID > 0 && (
            <Link href={`/cnf/groups?group=${food.FoodGroupID}`} className="text-xs text-blue-700 hover:underline">
              Browse group
            </Link>
          )}
        </div>
        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Country</div>
          <div className="text-gray-900">{food.CountryCode || '—'}</div>
        </div>
        {energyKcal != null && (
          <div>
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Energy</div>
            <div className="text-gray-900">{energyKcal.toFixed(0)} kcal / 100 g</div>
          </div>
        )}
        {food.ScientificName && userType !== 'individual' && (
          <div className="col-span-2 sm:col-span-3">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Scientific name</div>
            <div className="text-gray-700 italic">{food.ScientificName}</div>
          </div>
        )}
        {food.FoodSourceDescription && userType === 'researcher' && (
          <div className="col-span-2 sm:col-span-3">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Source</div>
            <div className="text-gray-700">{food.FoodSourceDescription}</div>
          </div>
        )}
      </div>

      {userType === 'individual' && (
        <p className="text-sm text-gray-600 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
          This profile shows what is in the food catalogue. To see HEFI, HENI, HSR, FCS, environmental,
          or dietary-pattern scores, add it to the Scorecard at your chosen portion size.
        </p>
      )}

      <div>
        <h2 className="text-sm font-semibold text-gray-900 mb-2">
          {userType === 'researcher' ? 'Nutrients each scoring lens reads' : 'Key nutrients for scoring'}
        </h2>
        <p className="text-xs text-gray-500 mb-3">{CNF_PER_100G_NOTE}</p>
        <div className="space-y-2">
          {SCORER_LINKS.map(({ label, href, lens }) => {
            const panel = LENS_NUTRIENT_PANELS[lens];
            const hits = findNutrientByPatterns(food.NutrientValues, panel.patterns);
            const open = expandedLens === lens;
            return (
              <div key={lens} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedLens(prev => (prev === lens ? null : lens))}
                  className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 text-left"
                >
                  <span className="text-sm font-medium text-gray-900">{panel.label}</span>
                  {open ? <ChevronUpIcon className="w-4 h-4 text-gray-500" /> : <ChevronDownIcon className="w-4 h-4 text-gray-500" />}
                </button>
                {open && (
                  <div className="px-3 py-2 border-t border-gray-100">
                    {userType !== 'individual' && <p className="text-xs text-gray-500 mb-2">{panel.hint}</p>}
                    {hits.length === 0 ? (
                      <p className="text-xs text-amber-700">No matching nutrients in catalogue for this food.</p>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                        {hits.map(n => (
                          <div key={n.NutrientName} className="flex justify-between text-xs py-1.5 px-2 bg-white rounded border border-gray-100">
                            <span className="text-gray-700 truncate pr-2">{n.NutrientName}</span>
                            <span className="font-medium text-gray-900 shrink-0">{n.NutrientValue} {n.NutrientUnit}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <Link href={href} className="inline-block mt-2 text-xs font-medium text-blue-700 hover:text-blue-900">
                      Open {label} calculator →
                    </Link>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <EnvironmentalTeaser foodId={food.FoodID} massG={massG} userType={userType} />

      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label htmlFor="portion-mass" className="block text-xs font-medium text-gray-700 mb-1">Portion (g)</label>
            <input
              id="portion-mass"
              type="number"
              min={1}
              step={1}
              value={massG}
              onChange={(e) => setMassG(Number(e.target.value))}
              className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          {scaledEnergy != null && (
            <div className="text-sm text-gray-600 pb-2">≈ {scaledEnergy.toFixed(0)} kcal for this portion</div>
          )}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" onClick={handleAddToScorecard} className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-white bg-emerald-600 hover:bg-emerald-700">
            <SparklesIcon className="w-4 h-4 mr-1.5" />
            Add to Scorecard
          </button>
          <Link href="/scorecard" className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-emerald-800 bg-white border border-emerald-300 hover:bg-emerald-50">
            Open Scorecard
          </Link>
          {onAddToCompare && (
            <button type="button" onClick={onAddToCompare} className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50">
              <ScaleIcon className="w-4 h-4 mr-1.5" />
              Add to compare
            </button>
          )}
          <Link href={`/cnf/compare?foods=${food.FoodID}`} className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg text-gray-700 bg-white border border-gray-300 hover:bg-gray-50">
            Compare this food
          </Link>
        </div>
      </div>

      <div>
        <button type="button" onClick={() => setShowAllNutrients(v => !v)} className="flex items-center text-sm font-medium text-gray-800 hover:text-gray-900">
          {showAllNutrients ? <ChevronUpIcon className="w-4 h-4 mr-1" /> : <ChevronDownIcon className="w-4 h-4 mr-1" />}
          {showAllNutrients ? 'Hide' : 'Show'} all {food.NutrientValues.length} nutrients
        </button>
        {showAllNutrients && (
          <div className="mt-2 max-h-64 overflow-y-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
            {food.NutrientValues.map((nutrient, index) => (
              <div key={`${nutrient.NutrientName}-${index}`} className="flex justify-between items-start gap-2 px-3 py-2 text-sm">
                <div className="min-w-0">
                  <div className="text-gray-800">{nutrient.NutrientName}</div>
                  {userType === 'researcher' && nutrient.NutrientSourceDescription && (
                    <div className="text-[10px] text-gray-500 truncate">{nutrient.NutrientSourceDescription}</div>
                  )}
                </div>
                <span className="font-medium text-gray-900 shrink-0">{nutrient.NutrientValue} {nutrient.NutrientUnit}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {food.ConversionFactors.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-900 mb-2">Household measures</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {food.ConversionFactors.map((c, index) => (
              <div key={index} className="flex justify-between text-sm py-2 px-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">{c.MeasureDescription}</span>
                <span className="font-medium text-gray-900">{c.ConversionFactorValue} g</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (variant === 'page') {
    return (
      <article className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {header}
        {body}
      </article>
    );
  }

  return (
    <>
      {header}
      {body}
    </>
  );
}

interface FoodDetailDrawerProps {
  food: Food;
  userType: UserType;
  groupLabel?: string;
  onClose: () => void;
  onAddToCompare?: () => void;
}

export function FoodDetailDrawer(props: FoodDetailDrawerProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center p-0 sm:p-4 z-50">
      <div
        className="bg-white rounded-t-2xl sm:rounded-xl shadow-xl w-full sm:max-w-3xl max-h-[92vh] overflow-y-auto"
        role="dialog"
        aria-labelledby="food-detail-title"
      >
        <FoodProfileContent {...props} variant="drawer" />
      </div>
    </div>
  );
}
