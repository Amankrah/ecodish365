/**
 * Disease Impact Chart Component
 * Visualizes HENI health impacts by disease category using charts and infographics
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { type HENIResult, type HENIFoodProfile } from '../../lib/api';
import {
  Heart,
  Activity,
  Brain,
  Bone,
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Info,
  BarChart3,
  PieChart
} from 'lucide-react';

type HENIAnalysis = HENIResult['data'] | HENIFoodProfile['data']['heni_analysis'];
type DiseaseImpactChartProps = {
  results: HENIResult | HENIAnalysis | HENIFoodProfile['data'];
};

export const DiseaseImpactChart: React.FC<DiseaseImpactChartProps> = ({ results }) => {
  const [chartType, setChartType] = useState<'category' | 'timeline' | 'comparison'>('category');

  // Type guards to normalize input to a HENI analysis block without using 'any'
  const hasDataWithHeniScores = (obj: unknown): obj is { data: HENIAnalysis } => {
    if (!obj || typeof obj !== 'object') return false;
    const root = obj as Record<string, unknown>;
    const data = root['data'] as unknown;
    return !!(data && typeof data === 'object' && 'heni_scores' in (data as Record<string, unknown>));
  };

  const hasHeniAnalysis = (obj: unknown): obj is { heni_analysis: HENIAnalysis } => {
    if (!obj || typeof obj !== 'object') return false;
    const root = obj as Record<string, unknown>;
    const ha = root['heni_analysis'] as unknown;
    return !!(ha && typeof ha === 'object' && 'heni_scores' in (ha as Record<string, unknown>));
  };

  const hasHeniScores = (obj: unknown): obj is HENIAnalysis => {
    return !!(obj && typeof obj === 'object' && 'heni_scores' in (obj as Record<string, unknown>));
  };

  const analysis: HENIAnalysis | null = hasDataWithHeniScores(results)
    ? results.data
    : hasHeniAnalysis(results)
      ? results.heni_analysis
      : hasHeniScores(results)
        ? (results as HENIAnalysis)
        : null;


  if (!analysis?.component_breakdown && !analysis?.disease_burden_analysis) return null;

  // FIX (audit bug #1 + #4): switch from fabricating disease burden out of
  // grams × hardcoded percentages to reading the backend's real per-disease
  // μDALY breakdown (`disease_burden_analysis.disease_breakdown` — see
  // heni_calculator_methods.py:315-324 and rust_core::heni::disease_breakdown).
  // The previous implementation invented disease-category constants (CVD 45 %,
  // Cancer 25 %, ...) that had no provenance and contradicted the per-factor
  // numbers shown elsewhere on the same page.
  const diseaseBreakdown: Record<string, number> =
    (analysis.disease_burden_analysis?.disease_breakdown as Record<string, number>) || {};
  // Merged μDALY contributions (food groups + nutrients) for the
  // risk-vs-benefit comparison panels (no longer the grams-mislabelled-as-μDALY).
  const foodGroupContrib: Record<string, number> =
    analysis.component_breakdown?.food_group_contributions || {};
  const nutrientContrib: Record<string, number> =
    analysis.component_breakdown?.nutrient_contributions || {};
  const factorContrib: Record<string, number> = { ...foodGroupContrib, ...nutrientContrib };
  for (const k of Object.keys(factorContrib)) {
    if (k.startsWith('__') || factorContrib[k] === 0) delete factorContrib[k];
  }
  const healthImpact = analysis.health_impact || {};

  // The Rust kernel (rust_core::heni::disease_breakdown) emits one row per
  // GBD-2016 outcome — sodium alone fans out into 15 cardiovascular/renal
  // outcomes (factors.rs:201-220). Aggregate those raw outcomes into
  // researcher-meaningful categories so the panel shows a handful of buckets
  // instead of 25 quasi-duplicate rows. The bucket → outcome map below is the
  // INVERSE of RISK_FACTOR_DISEASE_WEIGHTS, hand-curated.
  type DiseaseMeta = {
    name: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    conditions: string[];
  };
  const bucketOf: Record<string, string> = {
    // Cardiovascular family
    ischaemic_heart_disease: 'cardiovascular',
    hypertensive_heart_disease: 'cardiovascular',
    ischaemic_stroke: 'cardiovascular',
    haemorrhagic_stroke: 'cardiovascular',
    subarachnoid_stroke: 'cardiovascular',
    intracerebral_haemorrhage: 'cardiovascular',
    atrial_fibrillation_flutter: 'cardiovascular',
    aortic_aneurysm: 'cardiovascular',
    peripheral_artery_disease: 'cardiovascular',
    rheumatic_heart_disease: 'cardiovascular',
    endocarditis: 'cardiovascular',
    non_rheumatic_valvular_disease: 'cardiovascular',
    cardiomyopathy_myocarditis: 'cardiovascular',
    other_cardiovascular: 'cardiovascular',
    // Cancers
    colorectal_cancer: 'cancer',
    lung_cancer: 'cancer',
    oesophageal_cancer: 'cancer',
    mouth_cancer: 'cancer',
    nasopharynx_cancer: 'cancer',
    other_pharynx_cancer: 'cancer',
    larynx_cancer: 'cancer',
    stomach_cancer: 'cancer',
    breast_cancer: 'cancer',
    prostate_cancer: 'cancer',
    // Metabolic
    type_2_diabetes: 'metabolic',
    // Renal
    chronic_kidney_disease: 'renal',
  };
  const bucketMeta: Record<string, DiseaseMeta> = {
    cardiovascular: {
      name: 'Cardiovascular Diseases',
      icon: Heart,
      color: 'red',
      conditions: ['Ischaemic heart disease, stroke family, hypertensive HD, atrial fibrillation, etc.'],
    },
    cancer: {
      name: 'Cancers',
      icon: Shield,
      color: 'purple',
      conditions: ['Colorectal, lung, upper aerodigestive (oesophagus, mouth, larynx, pharynx)'],
    },
    metabolic: {
      name: 'Metabolic Disorders',
      icon: Activity,
      color: 'orange',
      conditions: ['Type 2 diabetes mellitus'],
    },
    renal: {
      name: 'Renal',
      icon: Bone,
      color: 'amber',
      conditions: ['Chronic kidney disease (sodium-mediated)'],
    },
    other: {
      name: 'Other',
      icon: Brain,
      color: 'blue',
      conditions: [],
    },
  };

  // Aggregate raw GBD outcomes → display buckets. Each bucket holds the sum
  // of its constituent μDALYs and the list of contributing outcome names for
  // a researcher-readable expanded view.
  type DiseaseImpactRow = DiseaseMeta & {
    key: string;
    impactUdaly: number;
    sharePct: number;
    outcomes: Array<{ name: string; impactUdaly: number }>;
  };
  const buckets: Record<string, DiseaseImpactRow> = {};
  for (const [outcome, val] of Object.entries(diseaseBreakdown)) {
    if (val === 0) continue;
    const bucketKey = bucketOf[outcome] || 'other';
    const meta = bucketMeta[bucketKey];
    if (!buckets[bucketKey]) {
      buckets[bucketKey] = {
        ...meta,
        key: bucketKey,
        impactUdaly: 0,
        sharePct: 0,
        outcomes: [],
      };
    }
    buckets[bucketKey].impactUdaly += val;
    buckets[bucketKey].outcomes.push({
      name: outcome.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      impactUdaly: val,
    });
  }
  const totalAbsBurden = Object.values(buckets).reduce(
    (s, row) => s + Math.abs(row.impactUdaly), 0
  );
  for (const row of Object.values(buckets)) {
    row.sharePct = totalAbsBurden > 0 ? Math.round((Math.abs(row.impactUdaly) / totalAbsBurden) * 100) : 0;
    row.outcomes.sort((a, b) => Math.abs(b.impactUdaly) - Math.abs(a.impactUdaly));
  }
  const sortedCategories: Array<[string, DiseaseImpactRow]> = (Object.entries(buckets) as Array<[string, DiseaseImpactRow]>)
    .sort(([, a], [, b]) => Math.abs(b.impactUdaly) - Math.abs(a.impactUdaly));

  const totalImpact = Object.values(buckets).reduce((s, row) => s + row.impactUdaly, 0);

  // Sign convention reminder: positive μDALY = harm (negative minutes), negative
  // μDALY = benefit (positive minutes).
  //
  // Per-disease band thresholds — TIGHTER than the whole-meal calibration. A
  // meal's total HENI typically distributes across several GBD outcomes, so
  // individual buckets sit at smaller absolute values than the meal total.
  // Using the meal-level table (<5 = Neutral) hid dominant harms — e.g. Beef
  // stew canned 4964 puts +4.4 μDALY entirely into Cardiovascular Diseases
  // (84 % of |total burden|) yet was labelled "Neutral".
  const getDiseaseImpactStatus = (impactUdaly: number) => {
    if (impactUdaly < -3)   return { level: 'Strongly Protective', color: 'green', icon: TrendingUp };
    if (impactUdaly < -0.5) return { level: 'Protective',          color: 'green', icon: TrendingUp };
    if (impactUdaly < 0.5)  return { level: 'Neutral',             color: 'gray',  icon: Shield };
    if (impactUdaly < 3)    return { level: 'Elevated Risk',       color: 'amber', icon: TrendingDown };
    return { level: 'High Risk', color: 'red', icon: AlertTriangle };
  };

  // Whole-meal-equivalent bands for the Overall Disease Risk Profile so its
  // label matches the Health Impact Meter (HENIResultsCard.getHealthCategory)
  // for the same meal. Converts the μDALY sum to minutes via MINUTES_PER_UDALY
  // = -0.5256 and reuses the meal-level minute thresholds. Without this, the
  // same +4.3 μDALY ≡ -2.30 min reads "Neutral" in one panel and "High Risk"
  // in another.
  const getOverallImpactStatus = (impactUdaly: number) => {
    const minutes = impactUdaly * -0.5256;
    if (minutes > 20)  return { level: 'Excellent',  color: 'green', icon: TrendingUp };
    if (minutes > 5)   return { level: 'Good',       color: 'green', icon: TrendingUp };
    if (minutes > 0)   return { level: 'Mild Benefit', color: 'blue', icon: TrendingUp };
    if (minutes > -5)  return { level: 'Neutral',    color: 'gray',  icon: Shield };
    if (minutes > -20) return { level: 'Concerning', color: 'amber', icon: TrendingDown };
    return { level: 'Poor', color: 'red', icon: AlertTriangle };
  };

  return (
    <div className="space-y-6">
      {/* Chart Type Toggle */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={chartType === 'category' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setChartType('category')}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          By Disease
        </Button>
        <Button
          variant={chartType === 'timeline' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setChartType('timeline')}
        >
          <TrendingUp className="h-4 w-4 mr-2" />
          Timeline
        </Button>
        <Button
          variant={chartType === 'comparison' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setChartType('comparison')}
        >
          <PieChart className="h-4 w-4 mr-2" />
          Risk vs Benefit
        </Button>
      </div>

      {chartType === 'category' && (
        <div className="space-y-4">
          {/* Overall Health Impact */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full bg-${getOverallImpactStatus(totalImpact).color}-100`}>
                    {React.createElement(getOverallImpactStatus(totalImpact).icon, {
                      className: `h-5 w-5 text-${getOverallImpactStatus(totalImpact).color}-600`
                    })}
                  </div>
                  <div>
                    <h3 className="font-semibold">Overall Disease Risk Profile</h3>
                    <p className="text-sm text-gray-600">{getOverallImpactStatus(totalImpact).level}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold text-${getOverallImpactStatus(totalImpact).color}-600`}>
                    {totalImpact > 0 ? '+' : ''}{totalImpact.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">μDALY Total</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Disease Categories — drawn directly from
              analysis.disease_burden_analysis.disease_breakdown (real per-disease
              μDALY values, kernel-computed). The "share of total burden" is
              derived from |this disease| ÷ Σ|burdens|, NOT from a hardcoded table. */}
          {sortedCategories.map(([key, category]) => {
            const IconComponent = category.icon as React.ComponentType<{ className?: string }>;
            const status = getDiseaseImpactStatus(category.impactUdaly);

            return (
              <Card key={key}>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <IconComponent className={`h-5 w-5 text-${category.color}-500`} />
                      <span className="text-base">{category.name}</span>
                      <Badge
                        variant="secondary"
                        className={`bg-${status.color}-100 text-${status.color}-800`}
                      >
                        {status.level}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold text-${status.color}-600`}>
                        {category.impactUdaly > 0 ? '+' : ''}{category.impactUdaly.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">μDALY</div>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="mb-4">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm text-gray-600">
                        Share of this meal&apos;s |total burden|
                      </span>
                      <span className="text-sm font-medium text-gray-800">
                        {category.sharePct}%
                      </span>
                    </div>
                    <Progress
                      value={category.sharePct}
                      className="h-2 bg-gray-100"
                    />
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700">
                      Contributing GBD outcomes (kernel-emitted, μDALY)
                    </h4>
                    {category.outcomes.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
                        {category.outcomes.map((o, idx) => (
                          <div key={idx} className="text-xs text-gray-600 flex items-center justify-between gap-2 pr-2">
                            <span className="flex items-center gap-2">
                              <div className="w-1 h-1 bg-gray-400 rounded-full" />
                              {o.name}
                            </span>
                            <span className={o.impactUdaly > 0 ? 'text-red-600' : 'text-green-600'}>
                              {o.impactUdaly > 0 ? '+' : ''}{o.impactUdaly.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 italic">
                        {category.conditions.join(', ')}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {chartType === 'timeline' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk-Factor Persistence Windows</CardTitle>
            </CardHeader>
            <CardContent>
              {/* FIX (audit bug #5): the previous panel asserted definitive
                  "heart disease, diabetes, cancer, stroke, dementia" outcomes
                  even for Neutral-classified foods. Per Stylianou et al. 2021
                  (Nature Food, Discussion p. 622) the HENI marginal-impact
                  framework is explicitly NOT applicable to substantial diet
                  changes and a single serving cannot be projected onto chronic-
                  disease incidence. We retain the schematic time-window
                  context but no longer claim disease-incidence outcomes. */}
              <Alert className="mb-4 border-amber-200 bg-amber-50">
                <Info className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800 text-xs leading-relaxed">
                  <strong>Marginality caveat (Stylianou 2021 Discussion p. 622):</strong>
                  {' '}HENI quantifies the marginal health-life impact of one serving relative
                  to the eaten alternative; the framework is <em>not</em> applicable to
                  substantial diet changes or to forecasting chronic-disease incidence
                  for a single eating occasion. The time windows below are
                  mechanistic context for the risk factors present, not predicted
                  disease outcomes for this meal.
                </AlertDescription>
              </Alert>
              <div className="space-y-4">
                {/* Short Term (Days to Weeks) */}
                <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-lg">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm font-medium text-blue-700">Days</div>
                    <div className="text-xs text-blue-600">1-30</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-800">Acute Metabolic Pathways</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Blood glucose, lipid profile, inflammation markers, blood pressure
                    </p>
                    <div className="flex gap-2 mt-2">
                      {['sugar_sweetened_beverages', 'trans_fat', 'sodium'].map(factor => (
                        factorContrib[factor] && (
                          <Badge key={factor} variant="secondary" className="text-xs bg-red-100 text-red-700">
                            {factor.replace('_', ' ')}
                          </Badge>
                        )
                      ))}
                    </div>
                  </div>
                </div>

                {/* Medium Term (Months) */}
                <div className="flex items-start gap-4 p-4 bg-amber-50 rounded-lg">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm font-medium text-amber-700">Months</div>
                    <div className="text-xs text-amber-600">1-12</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-amber-800">Intermediate Biomarker Pathways</h4>
                    <p className="text-sm text-amber-700 mt-1">
                      Sustained inflammation, insulin sensitivity, arterial stiffness
                    </p>
                    <div className="flex gap-2 mt-2">
                      {['processed_meat', 'red_meat'].map(factor => (
                        factorContrib[factor] && (
                          <Badge key={factor} variant="secondary" className="text-xs bg-amber-100 text-amber-700">
                            {factor.replace('_', ' ')}
                          </Badge>
                        )
                      ))}
                    </div>
                  </div>
                </div>

                {/* Long Term — schematic, NOT disease projection */}
                <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm font-medium text-gray-700">Years</div>
                    <div className="text-xs text-gray-600">5-20+</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800">Population-level GBD outcomes (context)</h4>
                    <p className="text-sm text-gray-700 mt-1">
                      The Stylianou 2021 DRFs are derived from GBD meta-analyses of
                      population-level risk-disease associations over years to decades.
                      A single-serving HENI score quantifies the marginal contribution
                      to this aggregate, not a prediction for any one consumer.
                    </p>
                    <div className="text-sm font-medium text-gray-800 mt-2">
                      Marginal HENI score for this meal:{' '}
                      {healthImpact.health_impact_minutes > 0 ? '+' : ''}
                      {(healthImpact.health_impact_minutes || 0).toFixed(2)} minutes
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {chartType === 'comparison' && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* FIX (audit bug #1+#2): partition by actual μDALY sign — positive
              means harm under post-HENI-CODE-1 convention. The previous panel
              split by a hardcoded whitelist of risk-factor names and then
              forced a "-" prefix onto grams mislabelled as μDALY. */}
          <Card>
            <CardHeader>
              <CardTitle className="text-red-700 flex items-center gap-2">
                <TrendingDown className="h-5 w-5" />
                Harmful Contributions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(factorContrib)
                  .filter(([, v]) => v > 0)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 5)
                  .map(([factor, value]) => (
                    <div key={factor} className="flex items-center justify-between p-2 bg-red-50 rounded">
                      <span className="text-sm capitalize">{factor.replace('_', ' ')}</span>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={Math.min(100, value * 10)}
                          className="w-16 h-2 bg-red-200"
                        />
                        <span className="text-sm font-medium text-red-700 min-w-[60px] text-right">
                          +{value.toFixed(1)} μDALY
                        </span>
                      </div>
                    </div>
                  ))}
                {Object.values(factorContrib).filter(v => v > 0).length === 0 && (
                  <div className="text-xs text-gray-500 italic">No harmful μDALY contributions in this meal.</div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-green-700 flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Beneficial Contributions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(factorContrib)
                  .filter(([, v]) => v < 0)
                  .sort(([, a], [, b]) => a - b)
                  .slice(0, 5)
                  .map(([factor, value]) => (
                    <div key={factor} className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm capitalize">{factor.replace('_', ' ')}</span>
                      <div className="flex items-center gap-2">
                        <Progress
                          value={Math.min(100, Math.abs(value) * 10)}
                          className="w-16 h-2 bg-green-200"
                        />
                        <span className="text-sm font-medium text-green-700 min-w-[60px] text-right">
                          {value.toFixed(1)} μDALY
                        </span>
                      </div>
                    </div>
                  ))}
                {Object.values(factorContrib).filter(v => v < 0).length === 0 && (
                  <div className="text-xs text-gray-500 italic">No beneficial μDALY contributions in this meal.</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Key Insights — derived from this meal's actual disease_breakdown.
          FIX (audit bug #4): no more hardcoded "Cardiovascular 45 %" claim;
          the top-burden disease is computed from the kernel output. */}
      {sortedCategories.length > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Disease Impact Insights</h4>
                <ul className="space-y-1 text-sm text-blue-700">
                  <li>• HENI breakdown for this meal covers {sortedCategories.length} non-zero disease categor{sortedCategories.length === 1 ? 'y' : 'ies'}</li>
                  <li>
                    • Largest contributor: {sortedCategories[0][1].name}
                    {' '}({sortedCategories[0][1].sharePct}% of |total burden|,
                    {' '}{sortedCategories[0][1].impactUdaly > 0 ? 'harm' : 'benefit'})
                  </li>
                  <li>• Net μDALY across diseases: {totalImpact > 0 ? '+' : ''}{totalImpact.toFixed(1)} ({totalImpact > 0 ? 'net harm' : 'net benefit'})</li>
                  <li>
                    • Marginal health-life impact: {Math.abs(healthImpact.health_impact_minutes || 0).toFixed(2)} minutes
                    {' '}{(healthImpact.health_impact_minutes ?? 0) > 0 ? 'gained' : 'lost'}
                    {' '}(per Stylianou 2021 marginality framework — single serving, not a chronic-disease projection)
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};