"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Target,
  Wrench,
  Zap,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { DecklistDiff } from "./DecklistDiff";
import { cn } from "@/lib/utils";
import type { ApiAdaptation } from "@trainerlab/shared-types";

interface AdaptationLogProps {
  adaptations: ApiAdaptation[];
  className?: string;
}

const typeIcons: Record<string, typeof Target> = {
  tech: Target,
  consistency: Wrench,
  engine: Zap,
  removal: Trash2,
};

const typeColors: Record<string, string> = {
  tech: "bg-blue-500/10 text-blue-600 border-blue-500/30",
  consistency: "bg-green-500/10 text-green-600 border-green-500/30",
  engine: "bg-purple-500/10 text-purple-600 border-purple-500/30",
  removal: "bg-red-500/10 text-red-600 border-red-500/30",
};

export function AdaptationLog({ adaptations, className }: AdaptationLogProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  if (!adaptations.length) {
    return (
      <div className={cn("text-center text-muted-foreground py-8", className)}>
        No adaptations detected
      </div>
    );
  }

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className={cn("space-y-3", className)}>
      {adaptations.map((adaptation) => {
        const Icon = typeIcons[adaptation.type] || Wrench;
        const colorClass = typeColors[adaptation.type] || "";
        const isExpanded = expandedIds.has(adaptation.id);
        const hasDiff =
          (adaptation.cards_added && adaptation.cards_added.length > 0) ||
          (adaptation.cards_removed && adaptation.cards_removed.length > 0);

        return (
          <div
            key={adaptation.id}
            className="rounded-lg border bg-card overflow-hidden"
          >
            <button
              className="w-full flex items-start gap-3 p-4 text-left hover:bg-muted/50 transition-colors"
              onClick={() => toggleExpand(adaptation.id)}
            >
              <div
                className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0",
                  colorClass
                )}
              >
                <Icon className="h-4 w-4" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className={colorClass}>
                    {adaptation.type}
                  </Badge>
                  {adaptation.target_archetype && (
                    <span className="text-xs text-muted-foreground">
                      vs {adaptation.target_archetype}
                    </span>
                  )}
                  {adaptation.confidence && (
                    <span className="text-xs text-muted-foreground ml-auto">
                      {(adaptation.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>

                {adaptation.description && (
                  <p className="text-sm text-foreground">
                    {adaptation.description}
                  </p>
                )}
              </div>

              {hasDiff && (
                <div className="flex-shrink-0">
                  {isExpanded ? (
                    <ChevronUp className="h-5 w-5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
              )}
            </button>

            {isExpanded && hasDiff && (
              <div className="px-4 pb-4">
                <DecklistDiff
                  cardsAdded={adaptation.cards_added ?? null}
                  cardsRemoved={adaptation.cards_removed ?? null}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
