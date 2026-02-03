"use client";

import { useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import { ImageOff } from "lucide-react";
import type { SavedDeck, DeckCard } from "@/types/deck";
import { cn } from "@/lib/utils";

interface DeckListReadOnlyProps {
  deck: SavedDeck;
}

const SUPERTYPE_ORDER = ["Pokemon", "Trainer", "Energy"];
const THUMBNAIL_SIZE = { width: 48, height: 67 };

export function DeckListReadOnly({ deck }: DeckListReadOnlyProps) {
  const groupedCards = useMemo(() => {
    const groups: Record<string, DeckCard[]> = {
      Pokemon: [],
      Trainer: [],
      Energy: [],
    };

    for (const dc of deck.cards) {
      const type = dc.card.supertype;
      if (groups[type]) {
        groups[type].push(dc);
      }
    }

    return groups;
  }, [deck.cards]);

  const supertypeCounts = useMemo(() => {
    return {
      Pokemon: groupedCards.Pokemon.reduce((sum, c) => sum + c.quantity, 0),
      Trainer: groupedCards.Trainer.reduce((sum, c) => sum + c.quantity, 0),
      Energy: groupedCards.Energy.reduce((sum, c) => sum + c.quantity, 0),
    };
  }, [groupedCards]);

  const totalCards = useMemo(() => {
    return deck.cards.reduce((sum, c) => sum + c.quantity, 0);
  }, [deck.cards]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="container mx-auto py-8 px-4 max-w-3xl">
        {/* Deck Info */}
        <div className="mb-8">
          {deck.description && (
            <p className="text-muted-foreground mb-4">{deck.description}</p>
          )}

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 p-4 bg-muted rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold">{totalCards}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
            {SUPERTYPE_ORDER.map((type) => (
              <div key={type} className="text-center">
                <div className="text-2xl font-bold">
                  {supertypeCounts[type as keyof typeof supertypeCounts]}
                </div>
                <div className="text-xs text-muted-foreground">{type}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Card List */}
        <div className="space-y-6">
          {SUPERTYPE_ORDER.map((type) => {
            const cards = groupedCards[type];
            const count = supertypeCounts[type as keyof typeof supertypeCounts];

            if (cards.length === 0) return null;

            return (
              <section key={type}>
                <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  {type}
                  <span className="text-sm font-normal text-muted-foreground">
                    ({count})
                  </span>
                </h2>
                <div className="space-y-1">
                  {cards.map((dc) => (
                    <ReadOnlyCardRow key={dc.card.id} deckCard={dc} />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}

interface ReadOnlyCardRowProps {
  deckCard: DeckCard;
}

function ReadOnlyCardRow({ deckCard }: ReadOnlyCardRowProps) {
  const { card, quantity } = deckCard;

  return (
    <Link
      href={`/cards/${card.id}`}
      className="flex items-center gap-3 p-2 rounded-md hover:bg-accent transition-colors"
    >
      {/* Thumbnail */}
      <div className="relative rounded overflow-hidden" style={THUMBNAIL_SIZE}>
        {card.image_small ? (
          <Image
            src={card.image_small}
            alt={card.name}
            width={THUMBNAIL_SIZE.width}
            height={THUMBNAIL_SIZE.height}
            className="object-cover"
            unoptimized
          />
        ) : (
          <div className="w-full h-full bg-muted flex items-center justify-center">
            <ImageOff className="w-4 h-4 text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Card info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{card.name}</div>
        <div className="text-xs text-muted-foreground">
          {card.types && card.types.length > 0 && `${card.types.join("/")} - `}
          {card.set_id.toUpperCase()}
        </div>
      </div>

      {/* Quantity */}
      <div
        className={cn(
          "text-lg font-semibold w-8 text-center",
          quantity >= 4 && "text-amber-600"
        )}
      >
        {quantity}
      </div>
    </Link>
  );
}
