import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ArchetypeCardSkeletonProps {
  className?: string;
}

export function ArchetypeCardSkeleton({
  className,
}: ArchetypeCardSkeletonProps) {
  return (
    <Card className={cn("animate-pulse", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          {/* Name */}
          <div className="h-6 w-32 rounded bg-muted" />
          {/* Share percentage */}
          <div className="h-8 w-16 rounded bg-muted" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          {/* Key card images */}
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="rounded bg-muted"
              style={{ width: 57, height: 80 }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface ArchetypeGridSkeletonProps {
  count?: number;
  className?: string;
}

export function ArchetypeGridSkeleton({
  count = 6,
  className,
}: ArchetypeGridSkeletonProps) {
  return (
    <div
      className={cn(
        "grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
        className,
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <ArchetypeCardSkeleton key={i} />
      ))}
    </div>
  );
}
