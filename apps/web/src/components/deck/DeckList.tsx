"use client";

import { useDeckStore } from "@/stores/deckStore";
import { DeckListItem } from "./DeckListItem";
import { cn } from "@/lib/utils";

const SUPERTYPE_ORDER = ["Pokemon", "Trainer", "Energy"] as const;

interface DeckListProps {
  className?: string;
}

export function DeckList({ className }: DeckListProps) {
  const cards = useDeckStore((state) => state.cards);
  const cardsByType = useDeckStore((state) => state.cardsByType);
  const supertypeCounts = useDeckStore((state) => state.supertypeCounts);
  const addCard = useDeckStore((state) => state.addCard);
  const removeCard = useDeckStore((state) => state.removeCard);

  const grouped = cardsByType();
  const counts = supertypeCounts();

  const handleQuantityChange = (cardId: string, delta: number) => {
    const deckCard = cards.find((c) => c.card.id === cardId);
    if (!deckCard) return;

    if (delta > 0) {
      addCard(deckCard.card);
    } else {
      removeCard(cardId);
    }
  };

  const handleRemove = (cardId: string) => {
    const deckCard = cards.find((c) => c.card.id === cardId);
    if (!deckCard) return;

    // Remove all copies by calling removeCard for each quantity
    for (let i = 0; i < deckCard.quantity; i++) {
      removeCard(cardId);
    }
  };

  if (cards.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center p-8 text-center border-2 border-dashed rounded-lg",
          className,
        )}
      >
        <p className="text-muted-foreground">No cards in deck</p>
        <p className="text-sm text-muted-foreground mt-1">
          Click cards to add them
        </p>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-4 overflow-y-auto", className)}>
      {SUPERTYPE_ORDER.map((supertype) => {
        const typeCards = grouped[supertype];
        const count = counts[supertype];

        if (typeCards.length === 0) return null;

        return (
          <section key={supertype}>
            <header className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded-md sticky top-0">
              <h3 className="text-sm font-semibold">{supertype}</h3>
              <span className="text-sm text-muted-foreground">{count}</span>
            </header>
            <div className="mt-1">
              {typeCards.map((deckCard) => (
                <DeckListItem
                  key={deckCard.card.id}
                  deckCard={deckCard}
                  onQuantityChange={handleQuantityChange}
                  onRemove={handleRemove}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
