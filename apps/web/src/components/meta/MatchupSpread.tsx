"use client";

import { cn } from "@/lib/utils";

export interface MatchupData {
  opponent: string;
  winRate: number;
  sampleSize: number;
  confidence: "high" | "medium" | "low";
}

interface MatchupBarProps {
  matchup: MatchupData;
}

function MatchupBar({ matchup }: MatchupBarProps) {
  const { opponent, winRate, sampleSize, confidence } = matchup;

  // Determine color based on win rate
  const barColor =
    winRate >= 0.55
      ? "bg-green-500"
      : winRate <= 0.45
        ? "bg-red-500"
        : "bg-slate-400";

  // Calculate bar width (centered at 50%)
  const percentage = winRate * 100;
  const barWidth = Math.abs(percentage - 50) * 2;
  const isPositive = winRate >= 0.5;

  return (
    <div className="flex items-center gap-3">
      {/* Opponent name */}
      <div className="w-24 flex-shrink-0 truncate text-sm text-terminal-text">
        {opponent}
      </div>

      {/* Bar visualization */}
      <div className="relative flex-1 h-5">
        {/* Center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-terminal-border" />

        {/* Background */}
        <div className="absolute inset-0 rounded bg-terminal-surface" />

        {/* Bar */}
        <div
          className={cn(
            "absolute top-0.5 bottom-0.5 rounded",
            barColor,
            confidence === "low" && "opacity-50"
          )}
          style={{
            width: `${barWidth}%`,
            left: isPositive ? "50%" : `${50 - barWidth}%`,
          }}
        />
      </div>

      {/* Win rate percentage */}
      <div className="w-12 text-right font-mono text-sm">
        <span
          className={cn(
            winRate >= 0.55
              ? "text-green-400"
              : winRate <= 0.45
                ? "text-red-400"
                : "text-terminal-muted"
          )}
        >
          {percentage.toFixed(0)}%
        </span>
      </div>

      {/* Sample size indicator */}
      <div
        className="w-8 text-right font-mono text-xs text-terminal-muted"
        title={`${sampleSize} games`}
      >
        n={sampleSize}
      </div>
    </div>
  );
}

export interface MatchupSpreadProps {
  matchups: MatchupData[];
  className?: string;
}

export function MatchupSpread({ matchups, className }: MatchupSpreadProps) {
  if (matchups.length === 0) {
    return (
      <p className="text-sm text-terminal-muted">
        No matchup data available yet
      </p>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {matchups.slice(0, 5).map((matchup) => (
        <MatchupBar key={matchup.opponent} matchup={matchup} />
      ))}
      <p className="mt-2 text-xs text-terminal-muted">
        Based on tournament results. Confidence: high (50+ games), medium
        (20-50), low (&lt;20)
      </p>
    </div>
  );
}
