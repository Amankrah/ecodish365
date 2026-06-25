// Route-transition skeleton for /research/nutrient-analysis. Mirrors the
// empty-state layout (header + decomposer/picker + life-stage card) so
// the page does not flash blank during navigation.

export default function NutrientAnalysisLoading() {
  return (
    <div
      className="mx-auto max-w-7xl space-y-6 px-4 py-6"
      role="status"
      aria-busy="true"
      aria-label="Loading nutrient analysis"
    >
      <header className="space-y-2 animate-pulse">
        <div className="h-3 w-32 bg-indigo-100 rounded" />
        <div className="h-8 w-64 bg-gray-200 rounded" />
        <div className="h-3 w-full max-w-3xl bg-gray-100 rounded" />
        <div className="h-3 w-5/6 max-w-3xl bg-gray-100 rounded" />
        <div className="h-3 w-3/4 max-w-3xl bg-gray-100 rounded" />
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: meal source + ingredient list column */}
        <div className="space-y-4 lg:col-span-2">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm animate-pulse">
            <div className="h-5 w-56 bg-gray-200 rounded mb-3" />
            <div className="h-3 w-full bg-gray-100 rounded mb-2" />
            <div className="h-3 w-5/6 bg-gray-100 rounded mb-4" />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-4 h-24" />
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-4 h-24" />
            </div>
          </div>
        </div>

        {/* Right: life-stage card */}
        <div className="lg:col-span-1">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm animate-pulse space-y-3">
            <div className="h-4 w-24 bg-gray-200 rounded" />
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="space-y-1.5">
                <div className="h-3 w-16 bg-gray-100 rounded" />
                <div className="h-8 w-full bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      </section>

      <span className="sr-only">Loading the nutrient analysis page…</span>
    </div>
  );
}
