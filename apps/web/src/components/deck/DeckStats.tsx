"use client";

import { useDeckStore } from "@/stores/deckStore";
import { cn } from "@/lib/utils";

interface DeckStatsProps {
  className?: string;
}

const TARGET_DECK_SIZE = 60;

export function DeckStats({ className }: DeckStatsProps) {
  // Get getter functions from store
  const totalCards = useDeckStore((state) => state.totalCards);
  const supertypeCounts = useDeckStore((state) => state.supertypeCounts);
  const isValid = useDeckStore((state) => state.isValid);

  // Call getters to compute values
  const total = totalCards();
  const counts = supertypeCounts();
  const valid = isValid();
  const progress = Math.min((total / TARGET_DECK_SIZE) * 100, 100);

  return (
    <div className={cn("space-y-3", className)}>
      {/* Total cards with progress bar */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium">Total Cards</span>
          <span
            className={cn(
              "text-sm font-bold",
              total < TARGET_DECK_SIZE && "text-amber-600",
              total === TARGET_DECK_SIZE && "text-green-600",
              total > TARGET_DECK_SIZE && "text-red-600",
            )}
          >
            {total}/{TARGET_DECK_SIZE}
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full transition-all duration-300",
              total < TARGET_DECK_SIZE && "bg-amber-500",
              total === TARGET_DECK_SIZE && "bg-green-500",
              total > TARGET_DECK_SIZE && "bg-red-500",
            )}
            style={{ width: `${progress}%` }}
            role="progressbar"
            aria-valuenow={total}
            aria-valuemin={0}
            aria-valuemax={TARGET_DECK_SIZE}
          />
        </div>
      </div>

      {/* Type breakdown */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 bg-muted/50 rounded-md">
          <div className="text-lg font-bold">{counts.Pokemon}</div>
          <div className="text-xs text-muted-foreground">Pokemon</div>
        </div>
        <div className="p-2 bg-muted/50 rounded-md">
          <div className="text-lg font-bold">{counts.Trainer}</div>
          <div className="text-xs text-muted-foreground">Trainer</div>
        </div>
        <div className="p-2 bg-muted/50 rounded-md">
          <div className="text-lg font-bold">{counts.Energy}</div>
          <div className="text-xs text-muted-foreground">Energy</div>
        </div>
      </div>

      {/* Validation status */}
      {total > 0 && (
        <div
          className={cn(
            "text-sm text-center py-1 px-2 rounded",
            valid
              ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
              : "bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400",
          )}
        >
          {valid
            ? "Deck is valid"
            : `Need ${TARGET_DECK_SIZE - total} more card${TARGET_DECK_SIZE - total !== 1 ? "s" : ""}`}
        </div>
      )}
    </div>
  );
}
