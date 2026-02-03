import { cn } from "@/lib/utils";

interface CardGridSkeletonProps {
  count?: number;
  className?: string;
}

function CardSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      {/* Card image skeleton */}
      <div
        className="relative overflow-hidden rounded-lg bg-muted animate-pulse"
        style={{ width: 160, height: 224 }}
      >
        <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-[shimmer_2s_infinite]" />
      </div>
      {/* Card name skeleton */}
      <div className="h-4 w-3/4 rounded bg-muted animate-pulse" />
      {/* Card type skeleton */}
      <div className="h-3 w-1/2 rounded bg-muted animate-pulse" />
    </div>
  );
}

export function CardGridSkeleton({
  count = 12,
  className,
}: CardGridSkeletonProps) {
  return (
    <div
      className={cn(
        "grid gap-4",
        "grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6",
        className
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
