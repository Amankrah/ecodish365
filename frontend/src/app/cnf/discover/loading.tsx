// Route-transition skeleton for /cnf/discover. Mirrors the multi-criteria
// nutrient builder + results grid so the page does not flash blank during
// the initial JS load.

export default function CnfDiscoverLoading() {
  return (
    <div
      className="min-h-screen bg-gray-50"
      role="status"
      aria-busy="true"
      aria-label="Loading nutrient discovery"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="animate-pulse space-y-2">
          <div className="h-7 w-64 bg-gray-200 rounded" />
          <div className="h-3 w-96 max-w-full bg-gray-100 rounded" />
        </div>

        {/* Criteria builder card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse space-y-3">
          <div className="h-4 w-40 bg-gray-200 rounded" />
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="grid grid-cols-1 sm:grid-cols-4 gap-2">
              <div className="h-9 sm:col-span-2 bg-gray-100 rounded-lg" />
              <div className="h-9 bg-gray-100 rounded-lg" />
              <div className="h-9 bg-gray-100 rounded-lg" />
            </div>
          ))}
          <div className="flex items-center justify-between pt-2">
            <div className="h-3 w-32 bg-gray-100 rounded" />
            <div className="h-9 w-28 bg-gray-200 rounded-lg" />
          </div>
        </div>

        {/* Results grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
              <div className="h-4 w-3/4 bg-gray-200 rounded" />
              <div className="h-3 w-1/2 bg-gray-100 rounded" />
              <div className="h-3 w-full bg-gray-100 rounded" />
              <div className="h-3 w-5/6 bg-gray-100 rounded" />
              <div className="flex items-center justify-between pt-2">
                <div className="h-3 w-16 bg-gray-100 rounded" />
                <div className="h-6 w-14 bg-gray-100 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <span className="sr-only">Loading nutrient discovery…</span>
    </div>
  );
}
