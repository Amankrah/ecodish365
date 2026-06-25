// Route-transition skeleton for /cnf/search. Mirrors the search box +
// filter chip row + result list so the page does not flash blank during
// the initial JS load. Per-result loading during typing/filter changes
// is handled in-page by the existing AIEnhancedSearch component.

export default function CnfSearchLoading() {
  return (
    <div
      className="min-h-screen bg-gray-50"
      role="status"
      aria-busy="true"
      aria-label="Loading food search"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="animate-pulse space-y-2">
          <div className="h-7 w-48 bg-gray-200 rounded" />
          <div className="h-3 w-80 max-w-full bg-gray-100 rounded" />
        </div>

        {/* Search bar */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse">
          <div className="h-11 w-full bg-gray-100 rounded-lg" />
          <div className="mt-3 flex flex-wrap gap-2">
            <div className="h-7 w-24 bg-gray-100 rounded-full" />
            <div className="h-7 w-32 bg-gray-100 rounded-full" />
            <div className="h-7 w-28 bg-gray-100 rounded-full" />
            <div className="h-7 w-20 bg-gray-100 rounded-full" />
          </div>
        </div>

        {/* Result rows */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-100 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="px-4 py-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gray-100 flex-shrink-0" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-3/4 max-w-md bg-gray-200 rounded" />
                <div className="h-3 w-1/3 max-w-xs bg-gray-100 rounded" />
              </div>
              <div className="h-6 w-16 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      </div>

      <span className="sr-only">Loading food search…</span>
    </div>
  );
}
