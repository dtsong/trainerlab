"use client";

import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { Input } from "@/components/ui/input";

import type {
  ApiRotationImpact,
  ApiRotatingCard,
} from "@trainerlab/shared-types";

interface CardWithArchetype extends ApiRotatingCard {
  archetype_name: string;
  archetype_id: string;
}

interface CardRotationListProps {
  impacts: ApiRotationImpact[];
}

export function CardRotationList({ impacts }: CardRotationListProps) {
  const [searchQuery, setSearchQuery] = useState("");

  // Flatten all rotating cards from all archetypes
  const allCards = useMemo(() => {
    const cards: CardWithArchetype[] = [];

    for (const impact of impacts) {
      if (impact.rotating_cards) {
        for (const card of impact.rotating_cards) {
          cards.push({
            ...card,
            archetype_name: impact.archetype_name,
            archetype_id: impact.archetype_id,
          });
        }
      }
    }

    // Group by card name and aggregate archetypes
    const cardMap = new Map<
      string,
      {
        card: ApiRotatingCard;
        archetypes: { name: string; id: string }[];
        totalCount: number;
      }
    >();

    for (const card of cards) {
      const existing = cardMap.get(card.card_name);
      if (existing) {
        existing.archetypes.push({
          name: card.archetype_name,
          id: card.archetype_id,
        });
        existing.totalCount += card.count;
      } else {
        cardMap.set(card.card_name, {
          card,
          archetypes: [{ name: card.archetype_name, id: card.archetype_id }],
          totalCount: card.count,
        });
      }
    }

    return Array.from(cardMap.values()).sort(
      (a, b) => b.archetypes.length - a.archetypes.length,
    );
  }, [impacts]);

  // Filter cards based on search
  const filteredCards = useMemo(() => {
    if (!searchQuery.trim()) return allCards;

    const query = searchQuery.toLowerCase();
    return allCards.filter(
      (item) =>
        item.card.card_name.toLowerCase().includes(query) ||
        item.archetypes.some((a) => a.name.toLowerCase().includes(query)),
    );
  }, [allCards, searchQuery]);

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search cards or archetypes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      <div className="text-sm text-muted-foreground">
        {filteredCards.length} cards rotating
      </div>

      <div className="divide-y divide-border rounded-lg border">
        {filteredCards.map((item) => (
          <div
            key={item.card.card_name}
            className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <div className="font-medium">{item.card.card_name}</div>
              <div className="flex flex-wrap gap-1 mt-1">
                {item.archetypes.slice(0, 5).map((arch) => (
                  <span
                    key={arch.id}
                    className="text-xs bg-muted px-2 py-0.5 rounded-full"
                  >
                    {arch.name}
                  </span>
                ))}
                {item.archetypes.length > 5 && (
                  <span className="text-xs text-muted-foreground">
                    +{item.archetypes.length - 5} more
                  </span>
                )}
              </div>
            </div>
            <div className="text-sm text-muted-foreground">
              {item.archetypes.length} archetype
              {item.archetypes.length > 1 ? "s" : ""} affected
            </div>
          </div>
        ))}

        {filteredCards.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            No cards found matching "{searchQuery}"
          </div>
        )}
      </div>
    </div>
  );
}
