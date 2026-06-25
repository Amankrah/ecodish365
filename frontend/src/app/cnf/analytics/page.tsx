'use client';

import React, { useMemo, useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ChartBarIcon,
  CubeIcon,
  CircleStackIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  BeakerIcon,
  ScaleIcon,
} from '@heroicons/react/24/outline';
import { CNFApiService, DatabaseStats, IntegrityCheck } from '@/lib/api';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import { useCnfExplorer } from '@/components/cnf/CnfExplorerContext';
import {
  formatGroupDisplayName, isCnfGroup, isFdcGroup, isWafctGroup, isCiqualGroup,
} from '@/lib/cnfGroupDisplay';
import { CATALOGUE_NAV } from '@/lib/catalogueNav';

interface AnalyticsData {
  stats: DatabaseStats | null;
  integrityCheck: IntegrityCheck | null;
}

type ChartScope = 'all' | 'cnf' | 'wafct' | 'fdc' | 'ciqual';
type ChartMetric = 'foodGroups' | 'topNutrients';

const CHART_COLORS = [
  '#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280',
];

const QUICK_LINKS = [
  { name: 'Food Search', href: '/cnf/search', icon: MagnifyingGlassIcon },
  { name: 'Food Groups', href: '/cnf/groups', icon: CubeIcon },
  { name: 'Discover', href: '/cnf/discover', icon: BeakerIcon },
  { name: 'Compare', href: '/cnf/compare', icon: ScaleIcon },
];

export default function CatalogueOverviewPage() {
  const router = useRouter();
  const { groupIdByName } = useCnfExplorer();
  const [data, setData] = useState<AnalyticsData>({ stats: null, integrityCheck: null });
  const [loading, setLoading] = useState(true);
  const [chartMetric, setChartMetric] = useState<ChartMetric>('foodGroups');
  const [chartScope, setChartScope] = useState<ChartScope>('all');
  const [integrityLoading, setIntegrityLoading] = useState(false);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [stats, integrityCheck] = await Promise.all([
        CNFApiService.getDatabaseStatistics(),
        CNFApiService.checkDataIntegrity().catch(() => null),
      ]);
      setData({ stats, integrityCheck });
    } catch {
      toast.error('Failed to load catalogue statistics');
    } finally {
      setLoading(false);
    }
  };

  const runIntegrityCheck = async () => {
    try {
      setIntegrityLoading(true);
      const integrityCheck = await CNFApiService.checkDataIntegrity();
      setData(prev => ({ ...prev, integrityCheck }));
      toast.success('Data integrity check completed');
    } catch {
      toast.error('Integrity check failed');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const exportAnalytics = () => {
    try {
      const exportData = {
        timestamp: new Date().toISOString(),
        catalogue: 'CNF + WAFCT + FDC + CIQUAL',
        statistics: data.stats,
        integrity_check: data.integrityCheck,
      };
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `catalogue-overview-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Overview exported');
    } catch {
      toast.error('Export failed');
    }
  };

  const formatNumber = (num: number) => new Intl.NumberFormat().format(num);

  const chartData = useMemo(() => {
    if (!data.stats) return [];
    const sourceData = chartMetric === 'foodGroups'
      ? data.stats.foods_by_group
      : data.stats.top_nutrients;

    return Object.entries(sourceData)
      .filter(([name]) => {
        if (chartMetric !== 'foodGroups' || chartScope === 'all') return true;
        const id = groupIdByName.get(name);
        if (id == null) return chartScope === 'cnf';
        if (chartScope === 'wafct')  return isWafctGroup(id);
        if (chartScope === 'fdc')    return isFdcGroup(id);
        if (chartScope === 'ciqual') return isCiqualGroup(id);
        return isCnfGroup(id);  // 'cnf' scope
      })
      .map(([name, value]) => {
        const id = groupIdByName.get(name);
        const label = id != null ? formatGroupDisplayName(name, id) : name;
        return { name, label, value, groupId: id };
      })
      .sort((a, b) => b.value - a.value)
      .slice(0, chartScope === 'fdc' ? 20 : chartScope === 'ciqual' ? 12 : chartScope === 'wafct' ? 14 : 10);
  }, [data.stats, chartMetric, chartScope, groupIdByName]);

  const maxChartValue = chartData.length ? Math.max(...chartData.map(d => d.value)) : 1;

  const getIntegrityStatus = () => {
    if (!data.integrityCheck) return null;
    const { overall_status } = data.integrityCheck;
    const statusConfig = {
      passed: { color: 'text-green-600', bg: 'bg-green-100', icon: CheckCircleIcon },
      warning: { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: ExclamationTriangleIcon },
      failed: { color: 'text-red-600', bg: 'bg-red-100', icon: ExclamationTriangleIcon },
    };
    return statusConfig[overall_status] || statusConfig.failed;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center text-gray-600">
        <div className="inline-flex items-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
          <span className="ml-2">Loading catalogue overview…</span>
        </div>
      </div>
    );
  }

  const stats = data.stats;
  const cnfCount   = stats?.cnf_food_count ?? (stats ? stats.food_count : 0);
  const wafctCount = stats?.wafct_food_count ?? 0;
  const fdcCount   = stats?.fdc_food_count ?? 0;
  const fdcFoundationCount = stats?.fdc_foundation_food_count ?? 0;
  const fdcSrLegacyCount   = stats?.fdc_sr_legacy_food_count ?? 0;
  const fdcFnddsCount      = stats?.fdc_survey_fndds_food_count ?? 0;
  const ciqualCount        = stats?.ciqual_food_count ?? 0;

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
            <div>
              <p className="text-sm text-gray-500 mb-1">{CATALOGUE_NAV.section}</p>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{CATALOGUE_NAV.overview}</h1>
              <p className="text-gray-600 max-w-2xl">
                Combined statistics for Health Canada CNF and FAO/INFOODS WAFCT 2019.
                Click a food group to browse its foods.
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <span className="px-2 py-1 rounded border bg-gray-100 text-gray-700 font-semibold">CNF — Health Canada</span>
                <span className="px-2 py-1 rounded border bg-amber-100 text-amber-800 font-semibold">WAFCT — FAO/INFOODS</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 shrink-0">
              <button type="button" onClick={runIntegrityCheck} disabled={integrityLoading} className="btn-outline inline-flex items-center text-sm">
                {integrityLoading ? 'Running…' : 'Run integrity check'}
              </button>
              <button type="button" onClick={exportAnalytics} className="btn-primary inline-flex items-center text-sm">
                <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                Export JSON
              </button>
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {QUICK_LINKS.map(link => (
            <Link
              key={link.href}
              href={link.href}
              className="flex items-center gap-2 px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-800 hover:border-primary-300 hover:bg-primary-50/40 transition-colors"
            >
              <link.icon className="w-4 h-4 text-primary-600 shrink-0" />
              {link.name}
            </Link>
          ))}
        </div>

        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-7 gap-4 mb-6">
            <div className="stat-card col-span-2 lg:col-span-1">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(stats.food_count)}</div>
              <div className="text-sm text-gray-600">Foods total</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(cnfCount)}</div>
              <div className="text-sm text-gray-600">CNF foods</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-bold text-amber-800">{formatNumber(wafctCount)}</div>
              <div className="text-sm text-gray-600">WAFCT foods</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-bold text-sky-800">{formatNumber(fdcCount)}</div>
              <div className="text-sm text-gray-600">FDC foods</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-bold text-purple-800">{formatNumber(ciqualCount)}</div>
              <div className="text-sm text-gray-600">CIQUAL foods</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(stats.food_groups)}</div>
              <div className="text-sm text-gray-600">Food groups</div>
            </div>
            <div className="stat-card">
              <div className="text-2xl font-bold text-gray-900">{formatNumber(stats.nutrient_types)}</div>
              <div className="text-sm text-gray-600">Nutrient types</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
              <h2 className="text-lg font-semibold text-gray-900">Distribution</h2>
              <div className="flex flex-wrap gap-2">
                {chartMetric === 'foodGroups' && (
                  <>
                    {(['all', 'cnf', 'wafct', 'fdc', 'ciqual'] as ChartScope[]).map(scope => (
                      <button
                        key={scope}
                        type="button"
                        onClick={() => setChartScope(scope)}
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          chartScope === scope ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {scope === 'all' ? 'All' : scope.toUpperCase()}
                      </button>
                    ))}
                  </>
                )}
                <button
                  type="button"
                  onClick={() => setChartMetric('foodGroups')}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    chartMetric === 'foodGroups' ? 'bg-slate-800 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  Food groups
                </button>
                <button
                  type="button"
                  onClick={() => setChartMetric('topNutrients')}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    chartMetric === 'topNutrients' ? 'bg-slate-800 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  Nutrient coverage
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {chartData.map((item, index) => (
                <div key={item.name} className="flex items-center gap-3">
                  <div className="w-36 sm:w-44 text-sm text-gray-700 truncate font-medium shrink-0">
                    {chartMetric === 'foodGroups' && item.groupId != null ? (
                      <button
                        type="button"
                        onClick={() => router.push(`/cnf/groups?group=${item.groupId}`)}
                        className="text-left hover:text-primary-700 hover:underline truncate w-full"
                        title={item.name}
                      >
                        {item.label}
                      </button>
                    ) : (
                      <span title={item.name}>{item.label}</span>
                    )}
                  </div>
                  <div className="flex-1 relative min-w-0">
                    <div className="w-full bg-gray-200 rounded-full h-3.5">
                      <div
                        className="h-3.5 rounded-full transition-all duration-500"
                        style={{
                          width: `${(item.value / maxChartValue) * 100}%`,
                          backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
                        }}
                      />
                    </div>
                  </div>
                  <span className="text-xs font-medium text-gray-700 w-12 text-right tabular-nums shrink-0">
                    {formatNumber(item.value)}
                  </span>
                </div>
              ))}
              {chartData.length === 0 && (
                <p className="text-sm text-gray-500 py-4 text-center">No data for this view.</p>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-gray-900">Data integrity</h3>
                <button type="button" onClick={runIntegrityCheck} disabled={integrityLoading} className="p-1.5 text-gray-400 hover:text-primary-600" title="Run integrity check">
                  <EyeIcon className="w-4 h-4" />
                </button>
              </div>
              {data.integrityCheck ? (
                <div className="space-y-3">
                  {(() => {
                    const status = getIntegrityStatus();
                    if (!status) return null;
                    const Icon = status.icon;
                    return (
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-full ${status.bg} flex items-center justify-center`}>
                          <Icon className={`w-4 h-4 ${status.color}`} />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 capitalize">{data.integrityCheck.overall_status}</div>
                          <div className="text-xs text-gray-500">Pipeline checks</div>
                        </div>
                      </div>
                    );
                  })()}
                  <div className="space-y-1.5">
                    {Object.entries(data.integrityCheck.checks).map(([checkName, checkData]) => (
                      <div key={checkName} className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 capitalize">{checkName.replace(/_/g, ' ')}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-medium tabular-nums">{formatNumber(checkData.count)}</span>
                          <div className={`w-2 h-2 rounded-full ${
                            checkData.status === 'passed' ? 'bg-green-500' :
                            checkData.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                          }`} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500">Run the integrity check to validate catalogue joins.</p>
              )}
            </div>

            {stats && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <h3 className="text-base font-semibold text-gray-900 mb-3">Catalogue details</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between gap-4">
                    <dt className="text-gray-600">Nutrient records</dt>
                    <dd className="font-medium tabular-nums">{formatNumber(stats.nutrient_records)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-gray-600">Measures</dt>
                    <dd className="font-medium tabular-nums">{formatNumber(stats.measures)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-gray-600">Last refreshed</dt>
                    <dd className="font-medium">{new Date(stats.timestamp).toLocaleDateString()}</dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <CircleStackIcon className="w-5 h-5 text-blue-600" />
                <h3 className="font-medium text-blue-900">Multi-database coverage</h3>
              </div>
              <p className="text-sm text-blue-800">
                {formatNumber(cnfCount)} Canadian (CNF), {formatNumber(wafctCount)} West African (WAFCT),
                {' '}{formatNumber(fdcCount)} US foods (FDC — {formatNumber(fdcFoundationCount)} Foundation,
                {' '}{formatNumber(fdcSrLegacyCount)} SR Legacy, {formatNumber(fdcFnddsCount)} Survey FNDDS),
                and {formatNumber(ciqualCount)} French foods (CIQUAL 2025), in {stats.food_groups} groups.
                Use the source filter on search and compare to scope any single database or search all four
                at once.
              </p>
            </div>
            <div className="bg-green-50 border border-green-100 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <ChartBarIcon className="w-5 h-5 text-green-600" />
                <h3 className="font-medium text-green-900">Nutrient depth</h3>
              </div>
              <p className="text-sm text-green-800">
                {formatNumber(stats.nutrient_records)} measured values across {stats.nutrient_types} nutrient types.
                WAFCT rows use an INFOODS→CNF nutrient bridge where names differ.
              </p>
            </div>
            <div className="bg-purple-50 border border-purple-100 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowTrendingUpIcon className="w-5 h-5 text-purple-600" />
                <h3 className="font-medium text-purple-900">Research tooling</h3>
              </div>
              <p className="text-sm text-purple-800">
                Browse by group for prep-state tags, screen within a group by nutrient, or export comparison tables.
                Scoring surfaces WAFCT caveats when West African foods are included.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
