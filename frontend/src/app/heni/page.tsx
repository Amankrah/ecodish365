'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { CNFApiService, DatabaseStats } from '@/lib/api';
import {
  Calculator,
  LayoutGrid,
  Heart,
  TrendingUp,
  AlertTriangle,
  CalendarClock,
  BarChart3,
} from 'lucide-react';

// Illustrative per-serving values from Stylianou 2021 (Nature Food 2:616-627),
// Supplementary Table 3. Positive minutes add to healthy life, negative subtract.
const heniExamples = [
  { food: 'A hot dog',                   minutes: -36,   color: 'red'   },
  { food: 'A 12 oz sugary drink',        minutes: -12,   color: 'red'   },
  { food: 'A slice of white bread',      minutes: -1.8,  color: 'amber' },
  { food: 'A scrambled egg',             minutes: -0.6,  color: 'amber' },
  { food: 'A chicken wing',              minutes:  0.1,  color: 'gray'  },
  { food: 'A medium apple',              minutes:  2.0,  color: 'green' },
  { food: 'A cup of broccoli',           minutes:  4.9,  color: 'green' },
  { food: 'A handful of walnuts (1 oz)', minutes:  7.6,  color: 'green' },
];

const colorClasses: Record<string, string> = {
  red:   'border-red-200 bg-red-50 text-red-900',
  amber: 'border-amber-200 bg-amber-50 text-amber-900',
  gray:  'border-gray-200 bg-gray-50 text-gray-800',
  green: 'border-green-200 bg-green-50 text-green-900',
};

const formatNumber = (num: number) => new Intl.NumberFormat().format(num);

export default function HENIHomePage() {
  const [catalogueStats, setCatalogueStats] = useState<Pick<
    DatabaseStats,
    'food_count' | 'cnf_food_count' | 'wafct_food_count'
  > | null>(null);

  useEffect(() => {
    CNFApiService.getDatabaseStatistics()
      .then((data) =>
        setCatalogueStats({
          food_count: data.food_count,
          cnf_food_count: data.cnf_food_count,
          wafct_food_count: data.wafct_food_count,
        }),
      )
      .catch((error) => {
        console.error('Failed to load catalogue stats:', error);
      });
  }, []);

  const foodCountLabel =
    catalogueStats != null ? formatNumber(catalogueStats.food_count) : '—';
  const cnfCountLabel =
    catalogueStats?.cnf_food_count != null
      ? formatNumber(catalogueStats.cnf_food_count)
      : null;
  const wafctCountLabel =
    catalogueStats?.wafct_food_count != null
      ? formatNumber(catalogueStats.wafct_food_count)
      : null;
  const catalogueBreakdown =
    cnfCountLabel != null && wafctCountLabel != null
      ? `${cnfCountLabel} Canadian foods plus ${wafctCountLabel} West African foods.`
      : 'Canadian Nutrient File plus the West African Food Composition Table.';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="relative py-12 max-w-7xl mx-auto px-6">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-4">
            <Heart className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
            Health Nutritional Index (HENI)
          </h1>
          <p className="text-lg text-gray-700 max-w-3xl mx-auto leading-relaxed">
            How many <strong>minutes of healthy life</strong> does this food add or subtract,
            on average, if it shows up in a typical day&apos;s eating? HENI takes the
            best-known links between food and disease, and turns each serving into a
            number of minutes you can feel in your bones.
          </p>
          <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mt-5 text-sm text-amber-900 text-left">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              The minutes are a population estimate, not a personal forecast. HENI assumes
              each food adds or subtracts a small, independent effect on top of a typical
              eating pattern, and it draws on US data, so the picture for any one person
              will differ. For Food Guide adherence on a full day of eating, try{' '}
              <Link href="/hefi" className="underline">HEFI-2019</Link>.
            </span>
          </div>
        </div>

        {/* Primary CTAs */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-12">
          <Link href="/heni/calculate" className="group">
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 group-hover:border-blue-200 h-full">
              <div className="inline-flex items-center justify-center p-3 bg-blue-100 rounded-full mb-3 group-hover:bg-blue-200 transition-colors">
                <Calculator className="h-7 w-7 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Score a food, meal, or day</h3>
              <p className="text-gray-600 leading-relaxed text-sm">
                Build the food list, pick serving sizes, and get the total minutes added or
                subtracted. You can break the result down by which foods drove it.
              </p>
              <div className="mt-3 text-blue-700 font-medium group-hover:text-blue-800 text-sm">
                Start analysis →
              </div>
            </div>
          </Link>

          <Link href="/scorecard" className="group">
            <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 group-hover:border-purple-200 h-full">
              <div className="inline-flex items-center justify-center p-3 bg-purple-100 rounded-full mb-3 group-hover:bg-purple-200 transition-colors">
                <LayoutGrid className="h-7 w-7 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">See it next to other lenses</h3>
              <p className="text-gray-600 leading-relaxed text-sm">
                The Scorecard runs HENI alongside HEFI, Food Compass, HSR, environmental
                impact, and dietary pattern, on the same list of foods. Different questions,
                one page.
              </p>
              <div className="mt-3 text-purple-700 font-medium group-hover:text-purple-800 text-sm">
                Open Scorecard →
              </div>
            </div>
          </Link>
        </div>

        {/* Secondary CTAs */}
        <div className="grid md:grid-cols-2 gap-4 max-w-4xl mx-auto mb-12">
          <Link
            href="/recall-24h?then=heni"
            className="bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 hover:shadow-md transition flex items-center gap-3"
          >
            <CalendarClock className="h-6 w-6 text-blue-700 flex-shrink-0" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-gray-900">Build a 24-hour recall</div>
              <div className="text-xs text-gray-600">
                Log a full day one meal at a time, then read the total minutes across the day.
              </div>
            </div>
          </Link>
          <Link
            href="/heni/policy-dashboard"
            className="bg-white border border-gray-200 rounded-xl p-4 hover:border-purple-300 hover:shadow-md transition flex items-center gap-3"
          >
            <BarChart3 className="h-6 w-6 text-purple-700 flex-shrink-0" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-gray-900">Policy view</div>
              <div className="text-xs text-gray-600">
                Population-level framing for procurement, food taxation, and menu policy work.
              </div>
            </div>
          </Link>
        </div>

        {/* Worked examples */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-1">What does &ldquo;minutes of healthy life&rdquo; feel like?</h2>
          <p className="text-sm text-gray-600 mb-4">
            A few published per-serving examples to set the scale. Positive numbers add
            time. Negative numbers subtract. Most foods sit close to zero. A single
            serving rarely moves the needle on its own. It is the day, the week, and the
            year that add up.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {heniExamples.map((ex) => (
              <div
                key={ex.food}
                className={`border rounded-lg p-3 ${colorClasses[ex.color]}`}
              >
                <div className="text-2xl font-bold leading-tight">
                  {ex.minutes >= 0 ? '+' : '−'}{Math.abs(ex.minutes).toFixed(ex.minutes < 1 && ex.minutes > -1 ? 1 : 0)} min
                </div>
                <div className="text-xs mt-1">{ex.food}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Methodology summary */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">How the number is built</h2>
          <ol className="space-y-4 text-sm text-gray-700 list-decimal list-inside">
            <li>
              <strong className="text-gray-900">Look at fifteen ways food affects health.</strong>{' '}
              These are the dietary factors the Global Burden of Disease research has the
              strongest evidence for: fruit, vegetables, legumes, nuts and seeds, whole
              grains, milk, red meat, processed meat, sugary drinks, fibre, omega-3 fats,
              polyunsaturated fats, trans fats, calcium, and sodium.
            </li>
            <li>
              <strong className="text-gray-900">Translate to lost or gained healthy life.</strong>{' '}
              For each factor your food carries, we apply a coefficient from the published
              research that says how much disease burden one serving adds or removes,
              on average, in the population.
            </li>
            <li>
              <strong className="text-gray-900">Turn the burden into time.</strong> A
              published conversion (Stylianou 2021) turns one micro-unit of disease
              burden into about half a minute of healthy life. The sign is set so that
              a positive number adds time and a negative number subtracts.
            </li>
            <li>
              <strong className="text-gray-900">Add up across your foods.</strong> Each
              food contributes its own slice, plus or minus. The total is what shows in
              the result. The 24-hour recall is the cleanest input because it lets you
              see the day as a whole.
            </li>
          </ol>
        </div>

        {/* Stats */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-5">At a glance</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-1">15</div>
              <div className="text-sm text-gray-700 font-medium">Dietary factors</div>
              <div className="text-xs text-gray-500 mt-1">
                The strongest food-to-disease links in the global burden research.
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-1">{foodCountLabel}</div>
              <div className="text-sm text-gray-700 font-medium">Foods in the catalogue</div>
              <div className="text-xs text-gray-500 mt-1">
                {catalogueBreakdown}
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-1">½ min</div>
              <div className="text-sm text-gray-700 font-medium">Per micro-DALY of burden</div>
              <div className="text-xs text-gray-500 mt-1">
                The published constant that turns burden into time.
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-600 mb-1">US</div>
              <div className="text-sm text-gray-700 font-medium">Population base</div>
              <div className="text-xs text-gray-500 mt-1">
                Risk patterns are anchored to US adult eating. Canadian recalibration is on the roadmap.
              </div>
            </div>
          </div>
        </div>

        {/* Food databases */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-12">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Where the foods come from</h2>
          <p className="text-sm text-gray-700 mb-4">
            HENI runs on the same food catalogue used by every other tool here. The
            Canadian Nutrient File supplies most of it, and the FAO West African Food
            Composition Table covers staples like fonio, baobab pulp, and dried fish.
            When a West African food shows up in your meal, the researcher view flags
            the small measurement differences so nothing slips by quietly.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="border border-gray-100 rounded-lg p-3">
              <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Home base</div>
              <div className="text-sm font-medium text-gray-900 mt-1">Canadian Nutrient File</div>
              <div className="text-xs text-gray-600 mt-0.5">
                {cnfCountLabel != null
                  ? `${cnfCountLabel} foods from Health Canada.`
                  : 'Foods from Health Canada.'}
              </div>
            </div>
            <div className="border border-gray-100 rounded-lg p-3">
              <div className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Extension</div>
              <div className="text-sm font-medium text-gray-900 mt-1">FAO/INFOODS WAFCT 2019</div>
              <div className="text-xs text-gray-600 mt-0.5">
                {wafctCountLabel != null
                  ? `${wafctCountLabel} West African foods.`
                  : 'West African foods.'}
              </div>
            </div>
            <div className="border border-dashed border-gray-300 rounded-lg p-3 text-gray-500">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Planned</div>
              <div className="text-sm font-medium text-gray-700 mt-1">More regional tables</div>
              <div className="text-xs mt-0.5">Plus a future Canadian recalibration of the risk coefficients.</div>
            </div>
          </div>
        </div>

        {/* What HENI isn't */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 mb-12">
          <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            What HENI is not
          </h2>
          <ul className="space-y-2 text-sm text-amber-900 list-disc list-inside">
            <li>
              <strong>Not a personal life-expectancy prediction.</strong> The minutes are
              what you would see on average in the population, not what you will see in
              your own body. Your outcome depends on a lot HENI does not model.
            </li>
            <li>
              <strong>Not built for dramatic diet changes.</strong> HENI assumes you are
              adding or swapping a serving here and there. If you wholesale rebuild your
              eating, the simple add-up no longer holds.
            </li>
            <li>
              <strong>Not Canadian-validated.</strong> The risk coefficients are anchored
              to US adult eating. Adapting them for Canadian intake is documented future
              work.
            </li>
            <li>
              <strong>Not everything that matters.</strong> Saturated fat on its own,
              vitamin D, how food is processed, how it is cooked, and how well your
              body absorbs nutrients are all left out. The fifteen factors are what the
              evidence is strongest for, not the whole picture.
            </li>
          </ul>
        </div>

        {/* Audience modes + citations */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="inline-flex items-center justify-center p-2 bg-blue-100 rounded-lg mb-3">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Three ways to read every result</h3>
            <p className="text-sm text-gray-600">
              The numbers stay the same. The story around them changes. The everyday view
              gives you the minutes in plain English. The researcher view breaks the
              minutes down across the fifteen factors and shows the coefficients behind
              them. The policy view frames the same numbers for procurement, taxation,
              and food-environment work.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="inline-flex items-center justify-center p-2 bg-green-100 rounded-lg mb-3">
              <BarChart3 className="h-5 w-5 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Pair with other lenses</h3>
            <p className="text-sm text-gray-600">
              HENI answers &ldquo;how many minutes?&rdquo;. HEFI answers &ldquo;does this
              line up with Canada&apos;s Food Guide?&rdquo;. HSR answers &ldquo;is this
              product better than the others next to it on the shelf?&rdquo;. The{' '}
              <Link href="/scorecard" className="text-blue-700 underline">Scorecard</Link>{' '}
              runs all six in one go.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <div className="inline-flex items-center justify-center p-2 bg-purple-100 rounded-lg mb-3">
              <Heart className="h-5 w-5 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Where the science comes from</h3>
            <p className="text-sm text-gray-700 leading-relaxed">
              HENI was developed by Stylianou and colleagues and published in <em>Nature
              Food</em> in 2021. It builds on the Global Burden of Disease food research
              and on earlier life-cycle work that combined nutrition and environmental
              impact in a single frame.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
