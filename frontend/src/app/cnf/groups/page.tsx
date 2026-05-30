'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  CubeIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  ListBulletIcon,
  Squares2X2Icon,
  InformationCircleIcon,
  ScaleIcon,
  ArrowDownTrayIcon,
  ChartBarIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';
import {
  CNFApiService,
  FoodGroup,
  Food,
  type GroupFoodRow,
  type GroupFoodsResult,
  type GroupSummary,
} from '@/lib/api';
import toast from 'react-hot-toast';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import { FoodDetailDrawer } from '@/components/cnf/FoodProfileContent';
import { SourceBadge } from '@/components/shared/SourceBadge';
import { GroupSidebar, getFoodGroupIcon } from '@/components/cnf/foodGroups/GroupSidebar';
import { GroupSummaryCard } from '@/components/cnf/foodGroups/GroupSummaryCard';
import { MiniDiscoverPanel } from '@/components/cnf/foodGroups/MiniDiscoverPanel';
import { topGroupsByCount, prepStateLabel } from '@/lib/cnfGroupDisplay';
import { toCsv, downloadCsv } from '@/lib/csv';
import type { SourceChoice } from '@/components/shared/SourceFilter';

const PAGE_SIZE = 50;

export default function CNFGroupsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center text-gray-600">
        Loading food groups…
      </div>
    }>
      <CNFGroupsPageContent />
    </Suspense>
  );
}

function CNFGroupsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { userType, resolveGroupName, groupCountById, foodGroups: contextGroups } = useCnfExplorer();

  const [foodGroups, setFoodGroups] = useState<FoodGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<FoodGroup | null>(null);
  const [foodsResult, setFoodsResult] = useState<GroupFoodsResult | null>(null);
  const [summary, setSummary] = useState<GroupSummary | null>(null);
  const [selectedFoods, setSelectedFoods] = useState<number[]>([]);
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [loading, setLoading] = useState(true);
  const [foodsLoading, setFoodsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [showFrench, setShowFrench] = useState(false);

  // Filters
  const [sourceFilter, setSourceFilter] = useState<SourceChoice>('both');
  const [foodTypeFilter, setFoodTypeFilter] = useState<'all' | 'single' | 'mixed'>('all');
  const [thermalFilter, setThermalFilter] = useState('');
  const [preservationFilter, setPreservationFilter] = useState('');
  const [sort, setSort] = useState<'name' | 'kcal' | 'food_id'>('name');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (contextGroups.length > 0) {
      setFoodGroups(contextGroups);
      setLoading(false);
      return;
    }
    CNFApiService.getFoodGroups()
      .then(setFoodGroups)
      .catch(() => toast.error('Failed to load food groups'))
      .finally(() => setLoading(false));
  }, [contextGroups]);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(searchQuery.trim()), 350);
    return () => clearTimeout(t);
  }, [searchQuery]);

  const loadFoodsForGroup = useCallback(async (
    group: FoodGroup,
    opts?: { offset?: number; append?: boolean },
  ) => {
    const pageOffset = opts?.offset ?? 0;
    try {
      setFoodsLoading(true);
      if (!opts?.append) {
        setSelectedGroup(group);
        setOffset(0);
      }

      const result = await CNFApiService.getFoodsByGroup(group.FoodGroupID, {
        limit: PAGE_SIZE,
        offset: pageOffset,
        q: debouncedQ || undefined,
        sort,
        sort_dir: sortDir,
        food_type: foodTypeFilter === 'all' ? undefined : foodTypeFilter,
        thermal: thermalFilter || undefined,
        preservation: preservationFilter || undefined,
        source: sourceFilter,
        summary: pageOffset === 0,
      });

      if (opts?.append) {
        setFoodsResult(prev => prev ? {
          ...result,
          foods: [...prev.foods, ...result.foods],
        } : result);
      } else {
        setFoodsResult(result);
      }
      if (result.summary) setSummary(result.summary);
      setOffset(pageOffset + result.count);

      router.replace(`/cnf/groups?group=${group.FoodGroupID}`, { scroll: false });
    } catch {
      toast.error('Failed to load foods for group');
    } finally {
      setFoodsLoading(false);
    }
  }, [
    debouncedQ, sort, sortDir, foodTypeFilter, thermalFilter,
    preservationFilter, sourceFilter, router,
  ]);

  // Initial group from URL
  useEffect(() => {
    const groupParam = searchParams.get('group');
    if (!groupParam || foodGroups.length === 0) return;
    const groupId = parseInt(groupParam, 10);
    if (Number.isNaN(groupId)) return;
    const group = foodGroups.find(g => g.FoodGroupID === groupId);
    if (group && selectedGroup?.FoodGroupID !== groupId) {
      setSelectedGroup(group);
    }
  }, [searchParams, foodGroups, selectedGroup?.FoodGroupID]);

  // Reload when group selected or filters change
  useEffect(() => {
    if (!selectedGroup) return;
    loadFoodsForGroup(selectedGroup, { offset: 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedGroup?.FoodGroupID, debouncedQ, sort, sortDir, foodTypeFilter, thermalFilter, preservationFilter, sourceFilter]);

  const handleSelectGroup = (group: FoodGroup) => {
    setSearchQuery('');
    setDebouncedQ('');
    setFoodTypeFilter('all');
    setThermalFilter('');
    setPreservationFilter('');
    setSourceFilter('both');
    setSelectedGroup(group);
  };

  const toggleFoodSelection = (foodId: number) => {
    setSelectedFoods(prev =>
      prev.includes(foodId) ? prev.filter(id => id !== foodId) : [...prev, foodId],
    );
  };

  const loadFoodDetails = async (foodId: number) => {
    try {
      const food = await CNFApiService.getFoodDetails(foodId);
      setSelectedFood(food);
    } catch {
      toast.error('Failed to load food details');
    }
  };

  const exportCsv = () => {
    if (!foodsResult?.foods.length || !selectedGroup) return;
    const headers = [
      'FoodID', 'FoodCode', 'FoodDescription', 'FoodDescriptionF', 'source',
      'energy_kcal', 'protein_g', 'fibre_g', 'food_type', 'thermal_state', 'preservation_state',
    ];
    const rows = foodsResult.foods.map(f => [
      f.FoodID, f.FoodCode, f.FoodDescription, f.FoodDescriptionF ?? '',
      f.source, f.energy_kcal ?? '', f.protein_g ?? '', f.fibre_g ?? '',
      f.food_type ?? '', f.thermal_state ?? '', f.preservation_state ?? '',
    ]);
    const slug = selectedGroup.FoodGroupName.replace(/[^\w]+/g, '_').slice(0, 40);
    downloadCsv(`cnf_group_${slug}_${new Date().toISOString().slice(0, 10)}.csv`, toCsv(headers, rows));
    toast.success('CSV exported');
  };

  const foods = foodsResult?.foods ?? [];
  const quickPicks = topGroupsByCount(foodGroups, groupCountById, 6);

  const thermalOptions = summary
    ? Object.keys(summary.thermal_state).filter(k => k !== 'unknown').sort()
    : [];
  const preservationOptions = summary
    ? Object.keys(summary.preservation_state).filter(k => k !== 'unknown').sort()
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center">
        <div className="inline-flex items-center text-gray-600">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
          <span className="ml-2">Loading food groups…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Browse by food groups</h1>
              <p className="text-gray-600 max-w-2xl">
                Explore the CNF + WAFCT catalogue by category. Filter by source, food type, and
                preparation state; screen within a group; or send selections to compare or all scores.
              </p>
            </div>
            {selectedFoods.length > 0 && (
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-sm text-gray-600">{selectedFoods.length} selected</span>
                <Link
                  href={`/cnf/compare?foods=${selectedFoods.join(',')}`}
                  className="btn-primary inline-flex items-center text-sm"
                >
                  <ScaleIcon className="w-4 h-4 mr-2" />
                  Compare
                </Link>
                <button type="button" onClick={() => setSelectedFoods([])} className="text-sm text-gray-500 hover:text-gray-700">
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 xl:col-span-3">
            <GroupSidebar
              groups={foodGroups}
              countById={groupCountById}
              selectedId={selectedGroup?.FoodGroupID ?? null}
              onSelect={handleSelectGroup}
            />
          </div>

          <div className="lg:col-span-8 xl:col-span-9">
            {!selectedGroup ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 lg:p-10">
                <div className="text-center mb-8">
                  <CubeIcon className="w-14 h-14 text-gray-300 mx-auto mb-3" />
                  <h3 className="text-lg font-medium text-gray-900 mb-1">Select a food group</h3>
                  <p className="text-gray-600 text-sm">
                    {foodGroups.length} groups · CNF + WAFCT combined
                  </p>
                </div>

                <div className="mb-8">
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3 text-center">
                    Largest groups
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {quickPicks.map(({ group, count }) => (
                      <button
                        key={group.FoodGroupID}
                        type="button"
                        onClick={() => handleSelectGroup(group)}
                        className="text-left p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50/50 transition-colors"
                      >
                        <span className="text-lg">{getFoodGroupIcon(group.FoodGroupName)}</span>
                        <div className="text-sm font-medium text-gray-900 mt-1 line-clamp-2 leading-snug">
                          {group.FoodGroupName}
                        </div>
                        <div className="text-xs text-gray-500">{count.toLocaleString()} foods</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex flex-wrap justify-center gap-3 text-sm">
                  <Link href="/cnf/discover" className="inline-flex items-center gap-1.5 text-primary-700 hover:text-primary-900">
                    <BeakerIcon className="w-4 h-4" /> Discover by nutrient
                  </Link>
                  <Link href="/cnf/analytics" className="inline-flex items-center gap-1.5 text-primary-700 hover:text-primary-900">
                    <ChartBarIcon className="w-4 h-4" /> Database analytics
                  </Link>
                  <Link href="/cnf/search" className="inline-flex items-center gap-1.5 text-primary-700 hover:text-primary-900">
                    <MagnifyingGlassIcon className="w-4 h-4" /> Advanced search
                  </Link>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="px-5 py-4 border-b border-gray-200">
                  <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <span className="text-xl">{getFoodGroupIcon(selectedGroup.FoodGroupName)}</span>
                        {selectedGroup.FoodGroupName}
                      </h2>
                      {foodsResult && (
                        <p className="text-sm text-gray-600 mt-0.5">
                          {foodsResult.total_count.toLocaleString()} match
                          {foodsResult.total_in_group !== foodsResult.total_count && (
                            <> of {foodsResult.total_in_group.toLocaleString()} in group</>
                          )}
                          {foodsResult.has_more && foods.length < foodsResult.total_count && (
                            <> · showing {foods.length}</>
                          )}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={exportCsv}
                        disabled={!foods.length}
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                      >
                        <ArrowDownTrayIcon className="w-3.5 h-3.5" /> CSV
                      </button>
                      <button type="button" onClick={() => setViewMode('grid')} title="Grid view"
                        className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}>
                        <Squares2X2Icon className="w-4 h-4" />
                      </button>
                      <button type="button" onClick={() => setViewMode('list')} title="List view"
                        className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}>
                        <ListBulletIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {summary && foodsResult && (
                    <GroupSummaryCard
                      summary={summary}
                      totalInCatalog={foodsResult.total_in_group}
                      filteredCount={summary.total_in_group}
                    />
                  )}

                  <MiniDiscoverPanel
                    foodGroupId={selectedGroup.FoodGroupID}
                    groupName={selectedGroup.FoodGroupName}
                    userType={userType}
                  />

                  {/* Filters */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    <select
                      value={sourceFilter}
                      onChange={e => setSourceFilter(e.target.value as SourceChoice)}
                      aria-label="Source filter"
                      className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                    >
                      <option value="both">CNF + WAFCT</option>
                      <option value="cnf">CNF only</option>
                      <option value="wafct">WAFCT only</option>
                    </select>
                    <select
                      value={foodTypeFilter}
                      onChange={e => setFoodTypeFilter(e.target.value as typeof foodTypeFilter)}
                      aria-label="Food type filter"
                      className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                    >
                      <option value="all">All types</option>
                      <option value="single">Single ingredient</option>
                      <option value="mixed">Mixed dish</option>
                    </select>
                    <select
                      value={thermalFilter}
                      onChange={e => setThermalFilter(e.target.value)}
                      aria-label="Thermal state filter"
                      className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                    >
                      <option value="">Any thermal</option>
                      {thermalOptions.map(t => (
                        <option key={t} value={t}>{prepStateLabel(t)}</option>
                      ))}
                      <option value="unknown">Unknown</option>
                    </select>
                    <select
                      value={preservationFilter}
                      onChange={e => setPreservationFilter(e.target.value)}
                      aria-label="Preservation filter"
                      className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                    >
                      <option value="">Any preservation</option>
                      {preservationOptions.map(p => (
                        <option key={p} value={p}>{prepStateLabel(p)}</option>
                      ))}
                      <option value="unknown">Unknown</option>
                    </select>
                    <select
                      value={sort}
                      onChange={e => setSort(e.target.value as typeof sort)}
                      aria-label="Sort by"
                      className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                    >
                      <option value="name">Sort: name</option>
                      <option value="kcal">Sort: energy</option>
                      <option value="food_id">Sort: FoodID</option>
                    </select>
                    <select
                      value={sortDir}
                      onChange={e => setSortDir(e.target.value as typeof sortDir)}
                      aria-label="Sort direction"
                      className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white"
                    >
                      <option value="asc">Ascending</option>
                      <option value="desc">Descending</option>
                    </select>
                    <label className="inline-flex items-center gap-1.5 text-xs text-gray-600 ml-auto">
                      <input
                        type="checkbox"
                        checked={showFrench}
                        onChange={e => setShowFrench(e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      Show French names
                    </label>
                  </div>

                  <div className="relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="search"
                      placeholder="Search within this group (server-side)…"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="block w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                </div>

                {foodsLoading && foods.length === 0 ? (
                  <div className="p-10 text-center text-gray-600">
                    <div className="inline-flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600" />
                      <span className="ml-2">Loading foods…</span>
                    </div>
                  </div>
                ) : foods.length === 0 ? (
                  <div className="text-center py-12 px-6">
                    <InformationCircleIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <h3 className="text-lg font-medium text-gray-900 mb-1">No foods found</h3>
                    <p className="text-gray-600 text-sm">
                      {searchQuery ? `No matches for "${searchQuery}" with current filters.` : 'This group is empty or all rows were filtered out.'}
                    </p>
                  </div>
                ) : (
                  <div className="p-5">
                    <FoodList
                      foods={foods}
                      viewMode={viewMode}
                      showFrench={showFrench}
                      userType={userType}
                      selectedFoods={selectedFoods}
                      onToggleSelect={toggleFoodSelection}
                      onViewDetails={loadFoodDetails}
                    />

                    {foodsResult?.has_more && (
                      <div className="mt-4 text-center">
                        <button
                          type="button"
                          disabled={foodsLoading}
                          onClick={() => loadFoodsForGroup(selectedGroup, { offset, append: true })}
                          className="text-sm px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                        >
                          {foodsLoading ? 'Loading…' : `Load more (${foods.length} of ${foodsResult.total_count})`}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {selectedFood && (
          <FoodDetailDrawer
            food={selectedFood}
            userType={userType}
            groupLabel={selectedGroup ? selectedGroup.FoodGroupName : resolveGroupName(selectedFood.FoodGroupID, selectedFood.FoodGroupName)}
            onClose={() => setSelectedFood(null)}
            onAddToCompare={() => {
              if (!selectedFoods.includes(selectedFood.FoodID)) {
                setSelectedFoods(prev => [...prev, selectedFood.FoodID]);
              }
              toast.success('Added to compare selection');
            }}
          />
        )}
      </div>
    </div>
  );
}

function PrepChip({ label }: { label: string }) {
  return (
    <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 border border-slate-200">
      {label}
    </span>
  );
}

function FoodList({
  foods,
  viewMode,
  showFrench,
  userType,
  selectedFoods,
  onToggleSelect,
  onViewDetails,
}: {
  foods: GroupFoodRow[];
  viewMode: 'grid' | 'list';
  showFrench: boolean;
  userType: ReturnType<typeof useCnfExplorer>['userType'];
  selectedFoods: number[];
  onToggleSelect: (id: number) => void;
  onViewDetails: (id: number) => void;
}) {
  if (viewMode === 'list') {
    return (
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500">
            <tr>
              <th className="w-8 px-3 py-2" />
              <th className="text-left px-3 py-2 font-medium">Food</th>
              <th className="text-right px-3 py-2 font-medium whitespace-nowrap">kcal</th>
              <th className="text-right px-3 py-2 font-medium whitespace-nowrap">Protein</th>
              <th className="text-right px-3 py-2 font-medium whitespace-nowrap">Fibre</th>
              <th className="text-left px-3 py-2 font-medium hidden lg:table-cell">Tags</th>
              <th className="w-10" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {foods.map(food => (
              <tr key={food.FoodID} className={selectedFoods.includes(food.FoodID) ? 'bg-primary-50/50' : 'hover:bg-gray-50'}>
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selectedFoods.includes(food.FoodID)}
                    onChange={() => onToggleSelect(food.FoodID)}
                    aria-label={`Select ${food.FoodDescription}`}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                </td>
                <td className="px-3 py-2 min-w-[12rem]">
                  <Link href={`/cnf/foods/${food.FoodID}`} className="font-medium text-gray-900 hover:text-primary-700">
                    {food.FoodDescription}
                  </Link>
                  {showFrench && food.FoodDescriptionF && (
                    <div className="text-xs text-gray-500 mt-0.5">{food.FoodDescriptionF}</div>
                  )}
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <SourceBadge source={food.source} userType={userType} />
                    <span className="text-[10px] text-gray-400">{food.FoodCode}</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-gray-700">
                  {food.energy_kcal != null ? food.energy_kcal.toFixed(0) : '—'}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-gray-700">
                  {food.protein_g != null ? food.protein_g.toFixed(1) : '—'}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-gray-700">
                  {food.fibre_g != null ? food.fibre_g.toFixed(1) : '—'}
                </td>
                <td className="px-3 py-2 hidden lg:table-cell">
                  <div className="flex flex-wrap gap-1">
                    {food.food_type && <PrepChip label={food.food_type} />}
                    {food.thermal_state && food.thermal_state !== 'unknown' && (
                      <PrepChip label={prepStateLabel(food.thermal_state)} />
                    )}
                    {food.preservation_state && food.preservation_state !== 'unknown' && (
                      <PrepChip label={prepStateLabel(food.preservation_state)} />
                    )}
                  </div>
                </td>
                <td className="px-2 py-2">
                  <button type="button" onClick={() => onViewDetails(food.FoodID)} className="p-1.5 text-gray-400 hover:text-primary-600" title="Quick view">
                    <EyeIcon className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
      {foods.map(food => (
        <div
          key={food.FoodID}
          className={`border rounded-lg p-3 ${
            selectedFoods.includes(food.FoodID) ? 'border-primary-200 bg-primary-50/50' : 'border-gray-200 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              checked={selectedFoods.includes(food.FoodID)}
              onChange={() => onToggleSelect(food.FoodID)}
              className="mt-1 h-4 w-4 rounded border-gray-300"
              aria-label={`Select ${food.FoodDescription}`}
            />
            <div className="flex-1 min-w-0">
              <Link href={`/cnf/foods/${food.FoodID}`} className="text-sm font-medium text-gray-900 hover:text-primary-700 line-clamp-2">
                {food.FoodDescription}
              </Link>
              {showFrench && food.FoodDescriptionF && (
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{food.FoodDescriptionF}</p>
              )}
              <div className="flex flex-wrap gap-1.5 mt-1.5 text-xs text-gray-500">
                <SourceBadge source={food.source} userType={userType} />
                {food.energy_kcal != null && <span>{food.energy_kcal.toFixed(0)} kcal</span>}
              </div>
              <div className="flex flex-wrap gap-1 mt-1.5">
                {food.food_type && <PrepChip label={food.food_type} />}
                {food.thermal_state && food.thermal_state !== 'unknown' && (
                  <PrepChip label={prepStateLabel(food.thermal_state)} />
                )}
              </div>
            </div>
            <button type="button" onClick={() => onViewDetails(food.FoodID)} className="p-1 text-gray-400 hover:text-primary-600 shrink-0" title="Quick view">
              <EyeIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
