"use client";

import { format, parseISO } from "date-fns";
import { Calendar, Trophy, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ApiEvolutionSnapshot } from "@trainerlab/shared-types";

interface EvolutionTimelineProps {
  snapshots: ApiEvolutionSnapshot[];
  className?: string;
  onSnapshotClick?: (snapshot: ApiEvolutionSnapshot) => void;
}

export function EvolutionTimeline({
  snapshots,
  className = "",
  onSnapshotClick,
}: EvolutionTimelineProps) {
  if (!snapshots.length) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No evolution data available
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

      <div className="space-y-6">
        {snapshots.map((snapshot, index) => {
          const date = snapshot.created_at
            ? format(parseISO(snapshot.created_at), "MMM d, yyyy")
            : "Unknown date";
          const hasAdaptations = snapshot.adaptations.length > 0;

          return (
            <div
              key={snapshot.id}
              className={`relative pl-10 ${onSnapshotClick ? "cursor-pointer hover:bg-muted/50 rounded-lg -ml-2 pl-12 py-2" : ""}`}
              onClick={() => onSnapshotClick?.(snapshot)}
            >
              <div
                className={`absolute left-2 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                  index === 0
                    ? "bg-teal-500 border-teal-500"
                    : "bg-background border-border"
                }`}
              >
                {index === 0 && (
                  <div className="w-2 h-2 rounded-full bg-white" />
                )}
              </div>

              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>{date}</span>
                    {snapshot.best_placement &&
                      snapshot.best_placement <= 8 && (
                        <Badge
                          variant="outline"
                          className="ml-2 bg-yellow-500/10 text-yellow-600 border-yellow-500/30"
                        >
                          <Trophy className="h-3 w-3 mr-1" />#
                          {snapshot.best_placement}
                        </Badge>
                      )}
                  </div>

                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-lg font-semibold">
                      {snapshot.meta_share
                        ? `${(snapshot.meta_share * 100).toFixed(1)}%`
                        : "—"}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {snapshot.deck_count} decks sampled
                    </span>
                  </div>

                  {snapshot.meta_context && (
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {snapshot.meta_context}
                    </p>
                  )}

                  {hasAdaptations && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {snapshot.adaptations.slice(0, 3).map((adaptation) => (
                        <Badge
                          key={adaptation.id}
                          variant="outline"
                          className={getAdaptationBadgeClass(adaptation.type)}
                        >
                          {adaptation.type}
                        </Badge>
                      ))}
                      {snapshot.adaptations.length > 3 && (
                        <Badge variant="outline">
                          +{snapshot.adaptations.length - 3}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>

                {onSnapshotClick && (
                  <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0 hidden sm:block" />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getAdaptationBadgeClass(type: string): string {
  switch (type) {
    case "tech":
      return "bg-blue-500/10 text-blue-600 border-blue-500/30";
    case "consistency":
      return "bg-green-500/10 text-green-600 border-green-500/30";
    case "engine":
      return "bg-purple-500/10 text-purple-600 border-purple-500/30";
    case "removal":
      return "bg-red-500/10 text-red-600 border-red-500/30";
    default:
      return "";
  }
}
