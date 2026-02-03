export function SpecimenCardSkeleton() {
  return (
    <div className="relative flex flex-col items-center rounded-lg border border-notebook-grid bg-notebook-cream p-4 shadow-sm">
      {/* Rank badge skeleton */}
      <div className="absolute -top-3 -left-3 h-8 w-8 rounded-full bg-notebook-grid animate-pulse" />

      {/* Tape effect */}
      <div className="absolute -top-1 right-3 w-8 h-3 bg-notebook-grid/40 rounded-sm rotate-12" />

      {/* Card image skeleton */}
      <div className="relative mb-4 mt-2">
        <div className="h-24 w-16 rounded bg-notebook-grid/50 animate-pulse" />
      </div>

      {/* Name skeleton */}
      <div className="h-4 w-20 rounded bg-notebook-grid/50 animate-pulse" />

      {/* Stats skeleton */}
      <div className="mt-2 flex items-center gap-2 px-2 py-1">
        <div className="h-4 w-12 rounded bg-notebook-grid/50 animate-pulse" />
        <div className="h-3 w-6 rounded bg-notebook-grid/40 animate-pulse" />
      </div>

      {/* Button skeleton */}
      <div className="mt-3 h-6 w-16 rounded bg-notebook-grid/30 animate-pulse" />
    </div>
  );
}

export function IndexCardSkeleton() {
  return (
    <div className="relative rounded-lg border border-notebook-grid bg-notebook-cream p-5 shadow-sm">
      {/* Paper clip */}
      <div className="absolute -top-1 right-8 w-5 h-8 border-2 border-pencil/20 rounded-t-full" />

      {/* Ruled lines background */}
      <div className="absolute inset-0 rounded-lg overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-ruled-lines opacity-30" />
      </div>

      <div className="relative">
        {/* Header skeleton */}
        <div className="mb-4 flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-notebook-grid/50 animate-pulse" />
          <div className="h-4 w-24 rounded bg-notebook-grid/50 animate-pulse" />
        </div>

        {/* Items skeleton */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-3 w-12 rounded bg-notebook-grid/30 animate-pulse mb-1" />
              <div className="h-4 w-full rounded bg-notebook-grid/50 animate-pulse mb-1" />
              <div className="h-3 w-3/4 rounded bg-notebook-grid/30 animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ComparisonRowSkeleton() {
  return (
    <div className="grid grid-cols-2">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="h-4 w-4 rounded bg-slate-700 animate-pulse" />
        <div className="flex-1 flex items-center gap-2">
          <div className="h-4 w-24 rounded bg-slate-700 animate-pulse" />
          <div className="h-3 w-10 rounded bg-slate-800 animate-pulse" />
        </div>
      </div>
      <div className="flex items-center gap-3 border-l border-slate-700/50 px-4 py-3">
        <div className="h-4 w-4 rounded bg-slate-700 animate-pulse" />
        <div className="flex-1 flex items-center gap-2">
          <div className="h-4 w-24 rounded bg-slate-700 animate-pulse" />
          <div className="h-3 w-10 rounded bg-slate-800 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
