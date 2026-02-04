"use client";

import { Plus, Minus, Equal } from "lucide-react";
import { cn } from "@/lib/utils";

interface CardChange {
  name: string;
  count?: number;
}

interface DecklistDiffProps {
  cardsAdded?: CardChange[] | null;
  cardsRemoved?: CardChange[] | null;
  className?: string;
}

export function DecklistDiff({
  cardsAdded,
  cardsRemoved,
  className,
}: DecklistDiffProps) {
  const hasChanges =
    (cardsAdded && cardsAdded.length > 0) ||
    (cardsRemoved && cardsRemoved.length > 0);

  if (!hasChanges) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 text-sm text-muted-foreground py-4",
          className
        )}
      >
        <Equal className="h-4 w-4" />
        <span>No card changes detected</span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "font-mono text-sm rounded-lg border bg-slate-950 p-4",
        className
      )}
    >
      <div className="space-y-1">
        {cardsRemoved?.map((card, index) => (
          <div
            key={`removed-${index}`}
            className="flex items-center gap-2 text-red-400"
          >
            <Minus className="h-3.5 w-3.5 flex-shrink-0" />
            <span>
              {card.count && card.count > 1 ? `${card.count}x ` : ""}
              {card.name}
            </span>
          </div>
        ))}
        {cardsAdded?.map((card, index) => (
          <div
            key={`added-${index}`}
            className="flex items-center gap-2 text-green-400"
          >
            <Plus className="h-3.5 w-3.5 flex-shrink-0" />
            <span>
              {card.count && card.count > 1 ? `${card.count}x ` : ""}
              {card.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
