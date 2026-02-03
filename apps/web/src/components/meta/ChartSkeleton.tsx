import { cn } from "@/lib/utils";

interface ChartSkeletonProps {
  height?: number;
  className?: string;
}

export function ChartSkeleton({ height = 350, className }: ChartSkeletonProps) {
  return (
    <div
      className={cn(
        "w-full rounded-lg bg-muted animate-pulse flex items-center justify-center",
        className
      )}
      style={{ height }}
    >
      <div className="text-muted-foreground text-sm">Loading chart...</div>
    </div>
  );
}
