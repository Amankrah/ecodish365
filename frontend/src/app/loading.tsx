// Default route-transition loading state. Next.js wraps every route in
// this Suspense fallback during navigation. Kept minimal because it
// flashes briefly on any nav; per-route loading.tsx files override this
// with a richer skeleton where the wait is noticeable.

export default function RootLoading() {
  return (
    <div
      className="min-h-[40vh] flex items-center justify-center px-4 py-12"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="flex items-center gap-3 text-gray-500">
        <div
          className="w-5 h-5 rounded-full border-2 border-gray-300 border-t-indigo-600 animate-spin"
          aria-hidden="true"
        />
        <span className="text-sm">Loading…</span>
      </div>
    </div>
  );
}
