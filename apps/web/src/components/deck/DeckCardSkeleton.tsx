import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface DeckCardSkeletonProps {
  className?: string;
}

export function DeckCardSkeleton({ className }: DeckCardSkeletonProps) {
  return (
    <Card className={cn("animate-pulse", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          {/* Title */}
          <div className="h-5 w-32 rounded bg-muted" />
          {/* Badge */}
          <div className="h-5 w-16 rounded-full bg-muted" />
        </div>
        {/* Description */}
        <div className="h-3 w-full mt-2 rounded bg-muted" />
      </CardHeader>

      <CardContent className="pb-2">
        {/* Featured card images */}
        <div className="flex gap-1 mb-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="rounded bg-muted"
              style={{ width: 48, height: 67 }}
            />
          ))}
        </div>

        {/* Card count */}
        <div className="h-4 w-16 rounded bg-muted" />
      </CardContent>

      <CardFooter className="pt-2 gap-2">
        <div className="h-8 flex-1 rounded bg-muted" />
        <div className="h-8 flex-1 rounded bg-muted" />
      </CardFooter>
    </Card>
  );
}

interface DeckGridSkeletonProps {
  count?: number;
  className?: string;
}

export function DeckGridSkeleton({
  count = 6,
  className,
}: DeckGridSkeletonProps) {
  return (
    <div
      className={cn(
        "grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
        className
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <DeckCardSkeleton key={i} />
      ))}
    </div>
  );
}
