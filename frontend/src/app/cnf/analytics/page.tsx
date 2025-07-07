'use client';

import React, { useState, useEffect } from 'react';
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
  EyeIcon
} from '@heroicons/react/24/outline';
import { CNFApiService, DatabaseStats, IntegrityCheck } from '@/lib/api';
import toast from 'react-hot-toast';

interface AnalyticsData {
  stats: DatabaseStats | null;
  integrityCheck: IntegrityCheck | null;
}

const CHART_COLORS = [
  '#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6b7280'
];

export default function CNFAnalyticsPage() {
  const [data, setData] = useState<AnalyticsData>({ stats: null, integrityCheck: null });
  const [loading, setLoading] = useState(true);
  const [selectedChart, setSelectedChart] = useState<'foodGroups' | 'topNutrients'>('foodGroups');
  const [integrityLoading, setIntegrityLoading] = useState(false);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [stats, integrityCheck] = await Promise.all([
        CNFApiService.getDatabaseStatistics(),
        CNFApiService.checkDataIntegrity().catch(() => null) // Don't fail if integrity check fails
      ]);
      
      setData({ stats, integrityCheck });
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      toast.error('Failed to load analytics data');
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
    } catch (error) {
      console.error('Integrity check failed:', error);
      toast.error('Integrity check failed');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const exportAnalytics = async () => {
    try {
      const exportData = {
        timestamp: new Date().toISOString(),
        statistics: data.stats,
        integrity_check: data.integrityCheck
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cnf-analytics-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('Analytics data exported successfully');
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Export failed');
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const getChartData = () => {
    if (!data.stats) return [];

    const sourceData = selectedChart === 'foodGroups' 
      ? data.stats.foods_by_group 
      : data.stats.top_nutrients;

    return Object.entries(sourceData)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
  };

  const getMaxValue = () => {
    const chartData = getChartData();
    return Math.max(...chartData.map(item => item.value));
  };

  const getIntegrityStatus = () => {
    if (!data.integrityCheck) return null;
    
    const { overall_status } = data.integrityCheck;
    const statusConfig = {
      'passed': { color: 'text-green-600', bg: 'bg-green-100', icon: CheckCircleIcon },
      'warning': { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: ExclamationTriangleIcon },
      'failed': { color: 'text-red-600', bg: 'bg-red-100', icon: ExclamationTriangleIcon },
    };

    return statusConfig[overall_status] || statusConfig.failed;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-gray-600">Loading analytics data...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Database Analytics
              </h1>
              <p className="text-gray-600">
                Comprehensive insights and statistics about the Canadian Nutrient File database
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={runIntegrityCheck}
                disabled={integrityLoading}
                className="btn-outline inline-flex items-center"
              >
                {integrityLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                    Running Check
                  </>
                ) : (
                  <>
                    <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
                    Run Integrity Check
                  </>
                )}
              </button>
              <button
                onClick={exportAnalytics}
                className="btn-primary inline-flex items-center"
              >
                <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                Export Analytics
              </button>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        {data.stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="stat-card">
              <div className="flex items-center">
                              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <CircleStackIcon className="w-6 h-6 text-primary-600" />
              </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(data.stats.food_count)}
                  </div>
                  <div className="text-sm text-gray-600">Total Foods</div>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <ChartBarIcon className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(data.stats.nutrient_records)}
                  </div>
                  <div className="text-sm text-gray-600">Nutrient Records</div>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <CubeIcon className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(data.stats.food_groups)}
                  </div>
                  <div className="text-sm text-gray-600">Food Groups</div>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="flex items-center">
                              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <ArrowTrendingUpIcon className="w-6 h-6 text-purple-600" />
              </div>
                <div className="ml-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatNumber(data.stats.nutrient_types)}
                  </div>
                  <div className="text-sm text-gray-600">Nutrient Types</div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Chart Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">
                  Distribution Analysis
                </h2>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedChart('foodGroups')}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      selectedChart === 'foodGroups'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Food Groups
                  </button>
                  <button
                    onClick={() => setSelectedChart('topNutrients')}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      selectedChart === 'topNutrients'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Top Nutrients
                  </button>
                </div>
              </div>

              {data.stats && (
                <div className="space-y-4">
                  {getChartData().map((item, index) => (
                    <div key={item.name} className="flex items-center space-x-4">
                      <div className="w-32 text-sm text-gray-700 truncate font-medium">
                        {item.name}
                      </div>
                      <div className="flex-1 relative">
                        <div className="w-full bg-gray-200 rounded-full h-4">
                          <div
                            className="h-4 rounded-full transition-all duration-500"
                            style={{
                              width: `${(item.value / getMaxValue()) * 100}%`,
                              backgroundColor: CHART_COLORS[index % CHART_COLORS.length]
                            }}
                          />
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-xs font-medium text-gray-700">
                            {formatNumber(item.value)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Data Quality Section */}
          <div className="space-y-6">
            {/* Integrity Check */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Data Integrity
                </h3>
                <button
                  type="button"
                  onClick={runIntegrityCheck}
                  disabled={integrityLoading}
                  className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                  title="Run integrity check"
                >
                  <EyeIcon className="w-4 h-4" />
                </button>
              </div>

              {data.integrityCheck && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    {(() => {
                      const status = getIntegrityStatus();
                      if (!status) return null;
                      const Icon = status.icon;
                      return (
                        <>
                          <div className={`w-8 h-8 rounded-full ${status.bg} flex items-center justify-center`}>
                            <Icon className={`w-4 h-4 ${status.color}`} />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900 capitalize">
                              {data.integrityCheck.overall_status}
                            </div>
                            <div className="text-sm text-gray-600">
                              Overall Status
                            </div>
                          </div>
                        </>
                      );
                    })()}
                  </div>

                  <div className="space-y-2">
                    {Object.entries(data.integrityCheck.checks).map(([checkName, checkData]) => (
                      <div key={checkName} className="flex items-center justify-between text-sm">
                        <span className="text-gray-700 capitalize">
                          {checkName.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-900 font-medium">
                            {formatNumber(checkData.count)}
                          </span>
                          <div className={`w-2 h-2 rounded-full ${
                            checkData.status === 'passed' ? 'bg-green-500' :
                            checkData.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                          }`} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!data.integrityCheck && (
                <div className="text-center py-6">
                  <InformationCircleIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">
                    Run integrity check to see data quality metrics
                  </p>
                </div>
              )}
            </div>

            {/* Database Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Database Information
              </h3>
              {data.stats && (
                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Last Updated</span>
                    <span className="text-gray-900 font-medium">
                      {new Date(data.stats.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Food Sources</span>
                    <span className="text-gray-900 font-medium">
                      {formatNumber(data.stats.food_sources)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Nutrient Sources</span>
                    <span className="text-gray-900 font-medium">
                      {formatNumber(data.stats.nutrient_sources)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Measures</span>
                    <span className="text-gray-900 font-medium">
                      {formatNumber(data.stats.measures)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Conversion Records</span>
                    <span className="text-gray-900 font-medium">
                      {formatNumber(data.stats.conversion_records)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Insights Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Key Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <CircleStackIcon className="w-5 h-5 text-blue-600 mr-2" />
                <h3 className="font-medium text-blue-900">Database Coverage</h3>
              </div>
              <p className="text-sm text-blue-800">
                {data.stats && (
                  <>
                    The database contains {formatNumber(data.stats.food_count)} foods across {data.stats.food_groups} food groups, 
                    providing comprehensive nutritional data for Canadian foods.
                  </>
                )}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <ChartBarIcon className="w-5 h-5 text-green-600 mr-2" />
                <h3 className="font-medium text-green-900">Nutrient Richness</h3>
              </div>
              <p className="text-sm text-green-800">
                {data.stats && (
                  <>
                    With {formatNumber(data.stats.nutrient_records)} nutrient records across {data.stats.nutrient_types} nutrient types, 
                    the database offers detailed nutritional analysis capabilities.
                  </>
                )}
              </p>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <ClockIcon className="w-5 h-5 text-purple-600 mr-2" />
                <h3 className="font-medium text-purple-900">Data Freshness</h3>
              </div>
              <p className="text-sm text-purple-800">
                {data.stats && (
                  <>
                    Last updated on {new Date(data.stats.timestamp).toLocaleDateString()}, 
                    ensuring users have access to current nutritional information.
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 