"use client";

import { ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ApiDecklistResponse } from "@trainerlab/shared-types";

interface DecklistViewerProps {
  decklist: ApiDecklistResponse;
  className?: string;
}

function groupBySupertype(cards: ApiDecklistResponse["cards"]) {
  const groups: Record<string, ApiDecklistResponse["cards"]> = {
    Pokemon: [],
    Trainer: [],
    Energy: [],
  };

  for (const card of cards) {
    const key = card.supertype ?? "Trainer";
    if (key in groups) {
      groups[key].push(card);
    } else {
      groups["Trainer"].push(card);
    }
  }

  return groups;
}

export function DecklistViewer({ decklist, className }: DecklistViewerProps) {
  const groups = groupBySupertype(decklist.cards);

  return (
    <div className={className} data-testid="decklist-viewer">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {decklist.player_name && (
            <span className="text-sm font-medium">{decklist.player_name}</span>
          )}
          <Badge variant="outline">{decklist.archetype}</Badge>
          <span className="text-xs text-muted-foreground">
            {decklist.total_cards} cards
          </span>
        </div>
        {decklist.source_url && (
          <Button variant="ghost" size="sm" asChild>
            <a
              href={decklist.source_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="mr-1 h-3 w-3" />
              View on Limitless
            </a>
          </Button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3 font-mono text-sm">
        {(["Pokemon", "Trainer", "Energy"] as const).map((supertype) => {
          const cards = groups[supertype];
          if (cards.length === 0) return null;
          const count = cards.reduce((sum, c) => sum + c.quantity, 0);

          return (
            <div key={supertype}>
              <h4 className="mb-1 text-xs font-semibold uppercase text-muted-foreground">
                {supertype} ({count})
              </h4>
              <ul className="space-y-0.5">
                {cards.map((card) => (
                  <li
                    key={card.card_id}
                    className="flex justify-between text-foreground"
                  >
                    <span className="truncate">{card.card_name}</span>
                    <span className="ml-2 flex-shrink-0 tabular-nums text-muted-foreground">
                      {card.quantity}x
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
