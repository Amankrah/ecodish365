'use client';

import React from 'react';
import Link from 'next/link';
import {
  Card, CardContent, CardHeader, CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Leaf, Globe, Calculator, BarChart3, Droplets, TreePine,
  Users, BookOpen, ArrowRight, CheckCircle, Target,
  Sparkles, CalendarClock, Camera, AlertTriangle,
} from 'lucide-react';

export default function EnvironmentalMainPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-emerald-50">
      {/* Hero */}
      <section className="relative py-16 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center mb-5">
            <Leaf className="h-12 w-12 text-green-500 mr-3" />
            <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Environmental impact
            </h1>
          </div>
          <p className="text-lg text-gray-700 max-w-3xl mx-auto mb-5 leading-relaxed">
            What does it cost the planet to put this food on your plate? We measure three
            things you can hold in your head: the climate cost in carbon dioxide, the
            land it takes to grow, and the water it drinks up. The numbers come from
            published life-cycle research, with honest ranges so you can see how much
            wiggle room each estimate has.
          </p>
          <div className="inline-flex items-start gap-2 max-w-2xl mx-auto bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-6 text-sm text-amber-900 text-left">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              This measures the cost of <strong>producing</strong> the food. What happens
              after it leaves the farm, like trucking, refrigeration, cooking, and
              packaging waste, is not yet in the number. The ranges shown are how much
              real producers actually vary from one farm or fishery to the next.
            </span>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            <Badge className="bg-green-100 text-green-700 px-3 py-1 text-xs">
              <CheckCircle className="h-3 w-3 mr-1" />
              Three indicators
            </Badge>
            <Badge className="bg-blue-100 text-blue-700 px-3 py-1 text-xs">
              <Globe className="h-3 w-3 mr-1" />
              2,425 food entries in the LCA catalogue
            </Badge>
            <Badge className="bg-purple-100 text-purple-700 px-3 py-1 text-xs">
              Honest uncertainty ranges
            </Badge>
          </div>
        </div>
      </section>

      {/* Tools */}
      <section className="py-12 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Four ways to score</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              One food, two foods side by side, a full day of eating, or every metric at once.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mb-3">
                  <Calculator className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">Score a food or meal</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  Pick foods from our catalogue, set serving sizes, and read the climate,
                  land, and water cost. Switch between per serving, per calorie, per
                  100 g, and per gram of protein to see the picture from different angles.
                </p>
                <Link href="/environmental/calculate">
                  <Button className="w-full bg-green-600 hover:bg-green-700 text-white" size="sm">
                    Open the calculator
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-3">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">Compare two foods</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  Stack two foods side by side. The right tool for &ldquo;beef or lentils?&rdquo;
                  and &ldquo;rice or quinoa?&rdquo;. The uncertainty ranges keep you from
                  reading too much into a single point estimate.
                </p>
                <Link href="/environmental/compare">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white" size="sm">
                    Compare
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center mb-3">
                  <CalendarClock className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">Score a full day</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  Walk through your day one meal at a time. The wizard adds up the
                  footprint across breakfast, lunch, dinner, and whatever else
                  happened, so you see the day as one number.
                </p>
                <Link href="/recall-24h?then=environmental">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white" size="sm">
                    Build a food diary
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-lg transition-all border border-gray-100">
              <CardHeader className="pb-3">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mb-3">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <CardTitle className="text-base">See it next to the rest</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3 leading-snug">
                  All scores lines up environmental impact next to healthy eating, health impact,
                  Food Compass, star ratings, and eating style. One food list, six different
                  questions, all in one place.
                </p>
                <Link href="/scorecard">
                  <Button className="w-full bg-amber-600 hover:bg-amber-700 text-white" size="sm">
                    Open all scores
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Three indicators */}
      <section className="py-14 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Three things we measure</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              Life-cycle research can measure many things, but only some have strong
              enough per-food evidence to publish honestly. We start with the three you
              probably already think about: climate, land, and water.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border border-red-200 shadow-sm">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-3">
                  <Globe className="h-6 w-6 text-red-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Climate</h3>
                <Badge variant="outline" className="text-xs mb-2">kg of CO₂ equivalent</Badge>
                <p className="text-sm text-gray-600 leading-snug">
                  The greenhouse gases released to grow, raise, and harvest the food,
                  added up as if they were all carbon dioxide. Beef is around 10 kg per
                  100 g you eat. Lentils are around 0.4 kg.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-green-200 shadow-sm">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-3">
                  <TreePine className="h-6 w-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Land</h3>
                <Badge variant="outline" className="text-xs mb-2">square metres for one year</Badge>
                <p className="text-sm text-gray-600 leading-snug">
                  How much farmland it takes to produce the food, weighted by how long
                  the land is held. Beef sits near 9 square-metre-years per 100 g. A
                  head of lettuce is closer to half a square metre.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-blue-200 shadow-sm">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mb-3">
                  <Droplets className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">Water</h3>
                <Badge variant="outline" className="text-xs mb-2">cubic metres of scarce water</Badge>
                <p className="text-sm text-gray-600 leading-snug">
                  The freshwater drawn from rivers and aquifers to grow the food,
                  weighted by how scarce that water is locally. Almonds in California
                  carry a much higher water cost than the same almonds in Spain.
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-6 bg-white border border-gray-200 rounded-lg p-4 text-sm text-gray-700">
            <strong>Not yet shown.</strong> Air quality, water pollution, ozone-layer
            damage, fossil-fuel and mineral scarcity, and chemical toxicity all matter,
            and life-cycle science has methods for them. We do not show numbers for
            those yet because the per-food data we trust is not there. Pesticide
            residues in your food, regenerative-farming credit, and what happens after
            your meal hits the bin are different questions that need different tools.
          </div>
        </div>
      </section>

      {/* How it actually works */}
      <section className="py-14 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">How the number is built</h2>
            <p className="text-base text-gray-600 max-w-3xl mx-auto">
              Five things happen behind the scenes when you score a food.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Pick the right reference number</h3>
                <p className="text-sm text-gray-600">
                  Every food has a published climate, land, and water figure based on
                  averages from many real farms and producers. When the matching is
                  uncertain, we fall back to the average for the food group, which is a
                  less precise but still defensible number.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Show the range, not just a single number</h3>
                <p className="text-sm text-gray-600">
                  Real farms vary a lot. A litre of milk from one dairy can carry many
                  times the climate cost of a litre from another. We show a low, a
                  central, and a high estimate so you see how much that variability
                  matters. These are envelopes from published farm-level data, not
                  statistical confidence intervals.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Compare on a fair basis</h3>
                <p className="text-sm text-gray-600">
                  You can ask the same question four ways: per serving, per 100 calories,
                  per 100 grams, or per gram of protein. Per-calorie is the default
                  because it stops a cucumber from looking artificially cheap next to a
                  bowl of pasta.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Make water local</h3>
                <p className="text-sm text-gray-600">
                  Climate is the same wherever the gases come from, but water scarcity
                  is not. You can score a food with global average water-scarcity weights
                  or pick a country so the water number reflects where the food is
                  actually grown.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Match smart, never invent</h3>
                <p className="text-sm text-gray-600">
                  When you score a food from the Canadian catalogue, we use a language
                  model to choose the best life-cycle entry from a shortlist of real
                  candidates, not to make one up. If the model is not confident enough,
                  we fall back to the group average and flag the match openly.
                </p>
              </CardContent>
            </Card>

            <Card className="border border-gray-100">
              <CardContent className="p-5">
                <h3 className="font-semibold text-gray-900 mb-1">Break composite dishes apart</h3>
                <p className="text-sm text-gray-600">
                  Pizza, stew, and casserole are not a single ingredient. When you score
                  one, we break it into the ingredients that make it up, score each, and
                  combine them by mass. The breakdown is shown so you can see what is
                  driving the total.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Audience modes */}
      <section className="py-14 px-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Three ways to read every result</h2>
            <p className="text-base text-gray-600 max-w-2xl mx-auto">
              The numbers do not change. The explanation does. Pick the view that
              fits why you are looking.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <Card className="border-l-4 border-l-blue-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-base">Everyday</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 leading-snug">
                  Climate, land, and water in plain language, with a quick read on
                  whether this food sits low, medium, or high for its group. No formulas,
                  no acronyms.
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-green-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-base">Researcher</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 leading-snug">
                  Full life-cycle method, how the food was matched, the data quality
                  rating behind the matched entry, and a parallel set of values from a
                  second method as a cross-check.
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-purple-600" />
                  <CardTitle className="text-base">Policy</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 leading-snug">
                  Population-level framing for procurement, taxation, and labelling
                  decisions. Includes an optional dollar value of the climate impact
                  using the Government of Canada&apos;s published social cost of carbon.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* What it is not */}
      <section className="py-14 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              What this is not
            </h2>
            <ul className="space-y-2 text-sm text-amber-900 list-disc list-inside">
              <li>
                <strong>Not the whole life of the food.</strong> Only the production
                stage. What happens after, like driving, refrigeration, cooking, and
                disposal, is left out for now.
              </li>
              <li>
                <strong>Not a statistical margin of error.</strong> The low and high
                bounds reflect how much real producers vary, drawn from published
                farm-level meta-analyses. They are honest envelopes, not confidence
                intervals.
              </li>
              <li>
                <strong>Not a toxicity score.</strong> The life-cycle methods for
                toxicity are still considered provisional in the underlying research,
                so we keep them out rather than show a number we cannot defend.
              </li>
              <li>
                <strong>Not a pesticide-residue check.</strong> What you might be
                eating from your food is a different question from what was released
                growing it. We do not answer the residue question yet.
              </li>
              <li>
                <strong>Not regenerative agriculture.</strong> The data behind the
                numbers comes from conventional farming. If you are eating something
                grown regeneratively, the climate and land numbers may be too high
                for your specific case.
              </li>
              <li>
                <strong>Group averages when matching is uncertain.</strong> When the
                tool cannot pin down a specific life-cycle entry for your food, it
                falls back to the average for its group. Within a group, real foods
                can vary widely. Skim milk and aged cheddar belong to the same group
                but their climate footprints differ by roughly ten times.
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Data + integrations */}
      <section className="py-14 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Where the foods come from</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700 space-y-2">
                <p>
                  Every food you score is drawn from the same catalogue used by every
                  other tool here. That is 5,691 foods from Canada&apos;s national
                  food file, plus 1,028 West African staples from the FAO regional
                  table. The matcher resolves either source against the life-cycle
                  catalogue the same way.
                </p>
                <p>
                  Other regional food tables can plug in later through the same setup.
                </p>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Where the life-cycle numbers come from</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700 space-y-2">
                <p>
                  Climate and land numbers come from a peer-reviewed meta-analysis of
                  thousands of real farms (Poore &amp; Nemecek, <em>Science</em>,
                  2018), combined with France&apos;s national life-cycle catalogue
                  AGRIBALYSE, which holds 2,425 commodity-level entries. Water uses
                  a separate published source that tracks scarcity by region.
                </p>
                <p>
                  Each catalogue entry carries a data-quality rating, and most entries
                  meet a good-enough bar. A handful of entries are known to have
                  published errors in the source data, and we flag those clearly when
                  they appear in your result.
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-6 grid md:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Camera className="h-5 w-5 text-amber-700" />
                  Scan a packaged product
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700">
                <p>
                  Take a photo of the Nutrition Facts panel and ingredient list of a
                  packaged product. The app reads the label, suggests what is in it,
                  you confirm, and the result feeds the environmental scorer along
                  with the other five lenses.
                </p>
                <Link href="/scan-product">
                  <Button variant="outline" size="sm" className="mt-3">
                    Scan a product →
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-emerald-700" />
                  See it next to the rest
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-700">
                <p>
                  Environmental impact is one of six measures on{' '}
                  <Link href="/scorecard" className="text-emerald-700 underline">all scores</Link>.
                  Sustainability decisions rarely live alone. Diet quality, healthy-life
                  minutes, product-level ratings, and a Food Guide read travel with the
                  environmental view on the same panel.
                </p>
                <Link href="/scorecard">
                  <Button variant="outline" size="sm" className="mt-3">
                    Open all scores →
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* References */}
      <section className="py-14 px-6 bg-gradient-to-r from-green-700 to-blue-700">
        <div className="max-w-5xl mx-auto text-white">
          <h2 className="text-2xl font-bold mb-5 text-center">Where the science comes from</h2>
          <div className="grid md:grid-cols-2 gap-5 text-sm">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-5">
              <h3 className="font-semibold mb-2">Method</h3>
              <ul className="space-y-2 list-disc list-inside">
                <li>
                  The life-cycle assessment method is ReCiPe 2016, developed by
                  Huijbregts and colleagues for the Dutch national institute RIVM and
                  published in the <em>International Journal of Life Cycle Assessment</em>{' '}
                  in 2017.
                </li>
                <li>
                  The per-food climate and land numbers come from Poore &amp; Nemecek&apos;s
                  2018 meta-analysis in <em>Science</em>, the largest of its kind.
                </li>
              </ul>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-5">
              <h3 className="font-semibold mb-2">Data and matching</h3>
              <ul className="space-y-2 list-disc list-inside">
                <li>
                  AGRIBALYSE is the French government&apos;s national life-cycle
                  catalogue, maintained by ADEME and updated to version 3.2 in 2024.
                </li>
                <li>
                  The matching layer that connects food databases to life-cycle entries
                  is informed by recent work on retrieval-then-rank methods by Zhou
                  and colleagues (2025) and earlier interlinking research by Furrer
                  and colleagues (2024).
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6 bg-gray-900 text-white text-center">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Ready to see the footprint?</h2>
          <p className="text-base mb-6 opacity-90 max-w-2xl mx-auto">
            A single food, a homemade meal, or a whole day of eating. Same pipeline,
            same honesty about what we know and what we do not.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link href="/environmental/calculate">
              <Button size="lg" className="bg-green-600 hover:bg-green-700">
                <Calculator className="mr-2 h-5 w-5" />
                Score a food
              </Button>
            </Link>
            <Link href="/recall-24h?then=environmental">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700">
                <CalendarClock className="mr-2 h-5 w-5" />
                Score a full day
              </Button>
            </Link>
            <Link href="/scorecard">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-gray-900">
                <Sparkles className="mr-2 h-5 w-5" />
                See all six lenses
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
