'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon,
  BeakerIcon,
  ChartBarIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { FCSApiService, CNFApiService, type FCSFoodProfile, type SearchResult } from '@/lib/api';

interface SearchState {
  query: string;
  results: SearchResult['results'];
  isLoading: boolean;
  showResults: boolean;
}

export default function FCSFoodProfile() {
  const [search, setSearch] = useState<SearchState>({
    query: '',
    results: [],
    isLoading: false,
    showResults: false
  });
  const [selectedFood, setSelectedFood] = useState<{ id: number; name: string } | null>(null);
  const [profile, setProfile] = useState<FCSFoodProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Helper to get the actual profile data from the response
  const getProfileData = (profileResponse: FCSFoodProfile | { success: boolean; data: FCSFoodProfile; message: string } | null): FCSFoodProfile | null => {
    if (!profileResponse) return null;
    // Check if we have the response wrapper structure
    if ('data' in profileResponse && 'success' in profileResponse) {
      return profileResponse.data;
    }
    // Otherwise assume it's already the profile data
    return profileResponse as FCSFoodProfile;
  };

  // Debounced search
  useEffect(() => {
    if (search.query.length < 2) {
      setSearch(prev => ({ ...prev, results: [], showResults: false }));
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSearch(prev => ({ ...prev, isLoading: true }));
      try {
        // Try enhanced search first, fallback to regular search
        let searchResult;
        try {
          searchResult = await CNFApiService.searchFoodsEnhanced({
            query: search.query,
            limit: 10
          });
        } catch {
          searchResult = await CNFApiService.searchFoods(search.query, 10);
        }
        setSearch(prev => ({ 
          ...prev, 
          results: searchResult.results, 
          isLoading: false, 
          showResults: true 
        }));
      } catch (error) {
        console.error('Search error:', error);
        setSearch(prev => ({ ...prev, isLoading: false, showResults: false }));
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [search.query]);

  const selectFood = async (food: SearchResult['results'][0]) => {
    setSelectedFood({ id: food.FoodID, name: food.FoodDescription });
    setSearch(prev => ({ ...prev, query: food.FoodDescription, showResults: false }));
    
    setIsLoading(true);
    try {
      const profileResult = await FCSApiService.getFoodFCSProfile(food.FoodID);
      setProfile(profileResult.data);
    } catch (error) {
      console.error('Profile loading error:', error);
      alert('Failed to load food profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getFCSColor = (fcs: number) => {
    if (fcs >= 70) return 'text-green-600';
    if (fcs >= 31) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getFCSLevel = (fcs: number) => {
    if (fcs >= 70) return 'Encourage';
    if (fcs >= 31) return 'Moderation';
    return 'Minimize';
  };

  const getAttributeTypeColor = (type: string) => {
    switch (type) {
      case 'BENEFICIAL': return 'text-green-600';
      case 'HARMFUL': return 'text-red-600';
      case 'RATIO': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const getAttributeTypeIcon = (type: string) => {
    switch (type) {
      case 'BENEFICIAL': return '✓';
      case 'HARMFUL': return '⚠';
      case 'RATIO': return '⚖';
      default: return '•';
    }
  };

  const formatDomainName = (domain: string) => {
    return domain.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatAttributeName = (attribute: string) => {
    return attribute.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const profileData = getProfileData(profile);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Food Profile</h1>
          <p className="text-lg text-gray-600">
            Get detailed FCS analysis with domain-by-domain breakdown of all evaluated attributes.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Search Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Food</h2>
              
              <div className="relative">
                <div className="relative">
                  <input
                    type="text"
                    value={search.query}
                    onChange={(e) => setSearch(prev => ({ ...prev, query: e.target.value }))}
                    placeholder="Search for a food..."
                    className="w-full border border-gray-300 rounded-md pl-10 pr-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <MagnifyingGlassIcon className="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
                </div>
                
                {/* Search Results */}
                {search.showResults && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-64 overflow-y-auto">
                    {search.isLoading ? (
                      <div className="p-3 text-center text-sm text-gray-500">
                        Searching...
                      </div>
                    ) : search.results.length > 0 ? (
                      search.results.map((item) => (
                        <button
                          key={item.FoodID}
                          onClick={() => selectFood(item)}
                          className="w-full text-left px-3 py-3 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                        >
                          <div className="font-medium text-gray-900 truncate">
                            {item.FoodDescription}
                          </div>
                          <div className="text-xs text-gray-500">
                            Code: {item.FoodCode}
                          </div>
                        </button>
                      ))
                    ) : (
                      <div className="p-3 text-center text-sm text-gray-500">
                        No foods found
                      </div>
                    )}
                  </div>
                )}
              </div>

              {selectedFood && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="text-sm font-medium text-blue-900">Selected Food:</div>
                  <div className="text-sm text-blue-800 mt-1">{selectedFood.name}</div>
                  <div className="text-xs text-blue-600 mt-1">ID: {selectedFood.id}</div>
                </div>
              )}
            </div>
          </div>

          {/* Profile Panel */}
          <div className="lg:col-span-2">
            {isLoading ? (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <ArrowPathIcon className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Profile</h3>
                <p className="text-gray-600">
                  Analyzing food composition and calculating comprehensive FCS profile...
                </p>
              </div>
            ) : profile && profileData ? (
              <div className="space-y-6">
                {/* Main Profile Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    {profileData.food_name}
                  </h2>

                  {/* FCS Score Display */}
                  <div className="text-center mb-6">
                    <div className="mb-4">
                      <span className={`text-6xl font-bold ${getFCSColor(profileData.fcs_summary?.fcs || 0)}`}>
                        {profileData.fcs_summary?.fcs || 'N/A'}
                      </span>
                      <span className="text-2xl text-gray-500 ml-2">/100</span>
                    </div>
                    <div className={`text-xl font-semibold mb-2 ${getFCSColor(profileData.fcs_summary?.fcs || 0)}`}>
                      {profileData.fcs_summary?.fcs ? getFCSLevel(profileData.fcs_summary.fcs) : 'Unknown'}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-2xl font-bold text-gray-900">{profileData.fcs_summary?.original_score?.toFixed(2) || 'N/A'}</div>
                      <div className="text-sm text-gray-600">Original Score</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-2xl font-bold text-blue-600">{profileData.attributes_count || 0}</div>
                      <div className="text-sm text-gray-600">Attributes Analyzed</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="text-sm font-medium text-gray-900">{profileData.fcs_summary?.nova_category?.replace(/_/g, ' ') || 'Unknown'}</div>
                      <div className="text-sm text-gray-600">NOVA Category</div>
                    </div>
                  </div>
                </div>

                {/* Domain Breakdown */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Domain Breakdown ({Object.keys(profileData.domain_breakdown || {}).length} domains)
                  </h3>

                  <div className="space-y-6">
                    {Object.entries(profileData.domain_breakdown || {}).map(([domain, attributes]) => (
                      <div key={domain} className="border border-gray-200 rounded-lg p-4">
                        <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                          <BeakerIcon className="w-4 h-4 mr-2 text-blue-600" />
                          {formatDomainName(domain)}
                          <span className="ml-2 text-sm text-gray-500">
                            ({Object.keys(attributes || {}).length} attributes)
                          </span>
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {Object.entries(attributes || {}).map(([attribute, data]) => (
                            <div key={attribute} className="bg-gray-50 rounded p-3">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-gray-900 flex items-center">
                                  <span className={`mr-2 ${getAttributeTypeColor(data.type)}`}>
                                    {getAttributeTypeIcon(data.type)}
                                  </span>
                                  {formatAttributeName(attribute)}
                                </span>
                                <span className={`text-sm font-bold ${
                                  data.score > 0 ? 'text-green-600' : 
                                  data.score < 0 ? 'text-red-600' : 
                                  'text-gray-600'
                                }`}>
                                  {data.score > 0 ? '+' : ''}{data.score.toFixed(1)}
                                </span>
                              </div>
                              <div className="text-xs text-gray-600 flex justify-between">
                                <span>Value: {data.value.toFixed(3)}</span>
                                <span className={`${getAttributeTypeColor(data.type)}`}>
                                  {data.type}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Analysis Summary */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Summary</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-md font-medium text-green-600 mb-3 flex items-center">
                        <CheckCircleIcon className="w-4 h-4 mr-2" />
                        Nutritional Strengths
                      </h4>
                      <div className="space-y-2">
                        {Object.entries(profileData.domain_breakdown || {}).map(([domain, attributes]) => {
                          const positiveAttributes = Object.entries(attributes || {}).filter(([, data]) => data.score > 0);
                          if (positiveAttributes.length === 0) return null;
                          
                          return (
                            <div key={domain} className="text-sm">
                              <span className="font-medium text-gray-700">{formatDomainName(domain)}:</span>
                              <span className="text-gray-600 ml-1">
                                {positiveAttributes.length} beneficial attribute{positiveAttributes.length > 1 ? 's' : ''}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-md font-medium text-red-600 mb-3 flex items-center">
                        <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
                        Areas of Concern
                      </h4>
                      <div className="space-y-2">
                        {Object.entries(profileData.domain_breakdown || {}).map(([domain, attributes]) => {
                          const negativeAttributes = Object.entries(attributes || {}).filter(([, data]) => data.score < 0);
                          if (negativeAttributes.length === 0) return null;
                          
                          return (
                            <div key={domain} className="text-sm">
                              <span className="font-medium text-gray-700">{formatDomainName(domain)}:</span>
                              <span className="text-gray-600 ml-1">
                                {negativeAttributes.length} concern{negativeAttributes.length > 1 ? 's' : ''}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center mb-2">
                      <InformationCircleIcon className="w-5 h-5 text-blue-600 mr-2" />
                      <span className="text-sm font-medium text-blue-900">Understanding the Analysis</span>
                    </div>
                    <div className="text-sm text-blue-800 space-y-1">
                      <p>• <strong>Positive scores</strong> indicate beneficial attributes that improve nutritional quality</p>
                      <p>• <strong>Negative scores</strong> indicate harmful attributes that may pose health concerns</p>
                      <p>• <strong>Domain weighting</strong> follows FCS 2.0 methodology with full/half weights based on evidence</p>
                      <p>• <strong>Per 100 kcal</strong> normalization allows fair comparison across different food types</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <ChartBarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Profile Loaded</h3>
                <p className="text-gray-600">
                  Search for a food above to see its detailed nutritional profile and FCS analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}