"use client";

import { ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type {
  ApiDecklistCard,
  ApiDecklistResponse,
} from "@trainerlab/shared-types";

interface DecklistViewerProps {
  decklist: ApiDecklistResponse;
  className?: string;
}

function normalizeEnergyName(name: string): string {
  return name.replace(/^Basic\s+/i, "");
}

function collapseEnergy(cards: ApiDecklistCard[]): ApiDecklistCard[] {
  const collapsed = new Map<string, ApiDecklistCard>();

  for (const card of cards) {
    const normalized = normalizeEnergyName(card.card_name);
    const existing = collapsed.get(normalized);
    if (existing) {
      existing.quantity += card.quantity;
    } else {
      collapsed.set(normalized, { ...card, card_name: normalized });
    }
  }

  return Array.from(collapsed.values());
}

function isUnreleasedCard(card: ApiDecklistCard): boolean {
  return (
    card.set_id?.startsWith("POR") === true ||
    card.set_id?.startsWith("ME") === true
  );
}

function groupBySupertype(cards: ApiDecklistResponse["cards"]) {
  const groups: Record<string, ApiDecklistCard[]> = {
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

  groups["Energy"] = collapseEnergy(groups["Energy"]);

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
                    <span className="flex items-center gap-1.5 truncate">
                      {card.card_name}
                      {isUnreleasedCard(card) && card.set_id && (
                        <Badge
                          variant="outline"
                          className="text-[10px] px-1 py-0 text-red-400 border-red-400/40"
                        >
                          {card.set_id}
                          {card.set_name ? ` ${card.set_name}` : ""}
                        </Badge>
                      )}
                    </span>
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
