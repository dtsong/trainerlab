import { cn } from "@/lib/utils";

interface CardFiltersSkeletonProps {
  className?: string;
}

export function CardFiltersSkeleton({ className }: CardFiltersSkeletonProps) {
  return (
    <div className={cn("flex flex-wrap gap-3 items-center", className)}>
      {/* Four filter dropdowns */}
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-10 rounded-md bg-muted animate-pulse",
            i === 2 ? "w-[180px]" : "w-[140px]"
          )}
        />
      ))}
    </div>
  );
}
