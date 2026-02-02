"use client";

import { StatBlock } from "@/components/ui/stat-block";
import { JPSignalBadge } from "@/components/ui/jp-signal-badge";
import { cn } from "@/lib/utils";

export interface HealthIndicatorsProps {
  diversityIndex: number;
  topDeckShare: number;
  topDeckName: string;
  biggestMoverName: string;
  biggestMoverChange: number;
  jpSignalValue: number;
  enSignalValue: number;
  className?: string;
}

export function HealthIndicators({
  diversityIndex,
  topDeckShare,
  topDeckName,
  biggestMoverName,
  biggestMoverChange,
  jpSignalValue,
  enSignalValue,
  className,
}: HealthIndicatorsProps) {
  const moverTrend =
    biggestMoverChange > 0 ? "up" : biggestMoverChange < 0 ? "down" : "stable";

  return (
    <div className={cn("grid grid-cols-2 gap-4 md:grid-cols-4", className)}>
      {/* Diversity Index */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <StatBlock
          value={diversityIndex.toFixed(0)}
          label="Diversity Index"
          subtext="Higher = healthier"
        />
      </div>

      {/* Top Deck Share */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <StatBlock
          value={`${topDeckShare.toFixed(1)}%`}
          label="Top Deck Share"
          subtext={topDeckName}
        />
      </div>

      {/* Biggest Mover */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <StatBlock
          value={`${biggestMoverChange > 0 ? "+" : ""}${biggestMoverChange.toFixed(1)}%`}
          label="Biggest Mover"
          subtext={biggestMoverName}
          trend={moverTrend}
        />
      </div>

      {/* JP Signal */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-4xl font-mono font-semibold">
              {Math.abs(jpSignalValue - enSignalValue).toFixed(0)}
            </span>
            {Math.abs(jpSignalValue - enSignalValue) > 5 && (
              <JPSignalBadge
                jpShare={jpSignalValue}
                enShare={enSignalValue}
                threshold={5}
              />
            )}
          </div>
          <span className="text-sm text-muted-foreground">JP Signal</span>
          <span className="text-sm text-muted-foreground/70">
            Meta divergence score
          </span>
        </div>
      </div>
    </div>
  );
}
