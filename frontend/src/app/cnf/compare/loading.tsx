// Route-transition skeleton for /cnf/compare. Mirrors the foods-picker
// row + horizontal-scroll comparison table so the page does not flash
// blank during the initial JS load.

export default function CnfCompareLoading() {
  return (
    <div
      className="min-h-screen bg-gray-50"
      role="status"
      aria-busy="true"
      aria-label="Loading food comparison"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="animate-pulse space-y-2">
          <div className="h-7 w-56 bg-gray-200 rounded" />
          <div className="h-3 w-96 max-w-full bg-gray-100 rounded" />
        </div>

        {/* Foods-picker row */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 animate-pulse">
          <div className="h-4 w-32 bg-gray-200 rounded mb-3" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 rounded-lg" />
            ))}
          </div>
        </div>

        {/* Comparison table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto animate-pulse">
          <div className="min-w-[760px] p-4">
            {/* Table header */}
            <div className="flex border-b border-gray-200 pb-2 mb-2 gap-3">
              <div className="h-4 w-40 bg-gray-200 rounded" />
              <div className="h-4 w-24 bg-gray-100 rounded" />
              <div className="h-4 w-24 bg-gray-100 rounded" />
              <div className="h-4 w-24 bg-gray-100 rounded" />
              <div className="h-4 w-24 bg-gray-100 rounded" />
            </div>
            {/* Table rows */}
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="flex py-2 border-b border-gray-100 gap-3">
                <div className="h-3 w-40 bg-gray-100 rounded" />
                <div className="h-3 w-24 bg-gray-100 rounded" />
                <div className="h-3 w-24 bg-gray-100 rounded" />
                <div className="h-3 w-24 bg-gray-100 rounded" />
                <div className="h-3 w-24 bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <span className="sr-only">Loading food comparison…</span>
    </div>
  );
}
