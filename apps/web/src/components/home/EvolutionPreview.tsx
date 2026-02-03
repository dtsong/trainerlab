"use client";

import Link from "next/link";
import { ArrowRight, GitBranch, TrendingUp, TrendingDown } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";
import { Button } from "@/components/ui/button";
import { useHomeMetaData } from "@/hooks/useMeta";
import { computeMetaMovers, type MetaMover } from "@/lib/home-utils";

export function EvolutionPreview() {
  const { globalMeta, history, isLoading, isError } = useHomeMetaData();

  const archetypes = globalMeta?.archetype_breakdown ?? [];
  const topArchetype = archetypes[0];
  const movers = computeMetaMovers(globalMeta, history, 3);

  // Compute top archetype's current vs previous share (convert API decimals to percentages)
  const currentShare = (topArchetype?.share ?? 0) * 100;
  const oldestSnapshot = history?.snapshots?.[0];
  const previousShare =
    (oldestSnapshot?.archetype_breakdown?.find(
      (a) => a.name === topArchetype?.name
    )?.share ?? 0) * 100;
  const changePercent = currentShare - previousShare;

  // Build sparkline data from history snapshots
  const sparklineData =
    history?.snapshots
      ?.map((s) => {
        const arch = s.archetype_breakdown?.find(
          (a) => a.name === topArchetype?.name
        );
        return (arch?.share ?? 0) * 100;
      })
      .filter((v) => v > 0) ?? [];

  // Determine if we have enough data to show
  const hasData = !isLoading && !isError && topArchetype;

  if (!isLoading && !isError && !topArchetype) {
    return null;
  }

  return (
    <section className="bg-slate-50 py-12 md:py-16">
      <div className="container">
        <SectionLabel
          label="Deck Evolution"
          icon={<TrendingUp className="h-4 w-4" />}
          className="mb-8"
        />

        <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
          {/* Left: Mini chart + stats */}
          <div className="rounded-xl bg-white p-6 shadow-sm">
            {isLoading ? (
              <div className="animate-pulse">
                <div className="mb-4 flex items-center justify-between">
                  <div className="h-6 w-32 rounded bg-slate-200" />
                  <div className="h-8 w-16 rounded bg-slate-200" />
                </div>
                <div className="mb-4 h-32 rounded-lg bg-slate-100" />
                <div className="h-4 w-48 rounded bg-slate-200" />
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="font-display text-xl font-semibold text-slate-900">
                    {topArchetype?.name}
                  </h3>
                  <span className="font-mono text-2xl font-bold text-teal-600">
                    {currentShare.toFixed(1)}%
                  </span>
                </div>

                {/* Mini sparkline from real data */}
                <div className="mb-4 h-32 rounded-lg bg-gradient-to-r from-slate-100 to-slate-50">
                  <div className="flex h-full items-end justify-around px-4 pb-2">
                    {(sparklineData.length > 0
                      ? sparklineData
                      : [currentShare]
                    ).map((share, i) => {
                      const maxShare = Math.max(...sparklineData, currentShare);
                      const height =
                        maxShare > 0 ? (share / maxShare) * 100 : 50;
                      return (
                        <div
                          key={i}
                          className="w-4 rounded-t bg-teal-400"
                          style={{ height: `${Math.max(height, 5)}%` }}
                        />
                      );
                    })}
                  </div>
                </div>

                <p className="text-sm text-slate-500">
                  {previousShare > 0 ? (
                    <>
                      <span
                        className={
                          changePercent >= 0 ? "text-green-600" : "text-red-600"
                        }
                      >
                        {changePercent >= 0 ? "+" : ""}
                        {changePercent.toFixed(1)}%
                      </span>{" "}
                      over the last 30 days
                    </>
                  ) : (
                    "Current meta share"
                  )}
                </p>
              </>
            )}
          </div>

          {/* Right: Meta Movers */}
          <div>
            <h4 className="mb-4 flex items-center gap-2 font-medium text-slate-700">
              <GitBranch className="h-4 w-4 text-teal-500" />
              Meta Movers (30 days)
            </h4>
            {isLoading ? (
              <div className="space-y-4 animate-pulse">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-4">
                    <div className="h-2 w-2 rounded-full bg-slate-300 mt-1.5" />
                    <div className="flex-1 pb-4">
                      <div className="h-3 w-20 rounded bg-slate-200 mb-1" />
                      <div className="h-4 w-48 rounded bg-slate-200" />
                    </div>
                  </div>
                ))}
              </div>
            ) : movers.length > 0 ? (
              <div className="space-y-4">
                {movers.map((mover, index) => (
                  <div key={mover.name} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={`h-2 w-2 rounded-full ${mover.changeDirection === "up" ? "bg-green-500" : "bg-red-500"}`}
                      />
                      {index < movers.length - 1 && (
                        <div className="h-full w-px bg-slate-200" />
                      )}
                    </div>
                    <div className="pb-4">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900">
                          {mover.name}
                        </span>
                        <span
                          className={`inline-flex items-center gap-0.5 text-xs font-mono ${mover.changeDirection === "up" ? "text-green-600" : "text-red-600"}`}
                        >
                          {mover.changeDirection === "up" ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {mover.changeDirection === "up" ? "+" : "-"}
                          {mover.changeValue}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-500">
                        Now at {mover.currentShare.toFixed(1)}% meta share
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">
                Not enough historical data yet
              </p>
            )}
            {hasData && topArchetype && (
              <Button variant="ghost" size="sm" className="mt-4" asChild>
                <Link
                  href={`/meta/archetypes/${encodeURIComponent(topArchetype.name)}`}
                >
                  View archetype details
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
