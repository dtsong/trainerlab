"use client";

import { TrendingUp } from "lucide-react";

import { SectionLabel } from "@/components/ui/section-label";
import { TrendArrow } from "@/components/ui/trend-arrow";
import { useHomeMetaData } from "@/hooks/useMeta";
import { computeMetaMovers } from "@/lib/home-utils";
import { cn } from "@/lib/utils";

export function TrendingMovers({ className }: { className?: string }) {
  const { globalMeta, history, isLoading } = useHomeMetaData();

  const movers = computeMetaMovers(globalMeta, history, 3);

  if (isLoading || movers.length === 0) {
    return null;
  }

  return (
    <section
      className={cn("container mt-10", className)}
      data-testid="trending-movers"
    >
      <SectionLabel
        label="Trending Movers"
        variant="notebook"
        icon={<TrendingUp className="h-4 w-4" />}
      />

      <div className="mt-4 flex gap-3 overflow-x-auto pb-2">
        {movers.map((mover) => (
          <div
            key={mover.name}
            className="min-w-[220px] rounded-lg border border-notebook-grid bg-notebook-aged/40 px-4 py-3 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate font-display text-base font-semibold text-ink-black">
                  {mover.name}
                </div>
                <div className="mt-1 font-mono text-xs uppercase tracking-wide text-pencil">
                  {(mover.currentShare || 0).toFixed(1)}% share
                </div>
              </div>

              <TrendArrow
                direction={mover.changeDirection}
                value={mover.changeValue}
                size="sm"
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
