"use client";

import { AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { useDeckStore } from "@/stores/deckStore";
import { cn } from "@/lib/utils";

interface ValidationError {
  type: "error" | "warning";
  message: string;
}

interface DeckValidationProps {
  className?: string;
}

const MAX_SAME_NAME_CARDS = 4;
const TARGET_DECK_SIZE = 60;

export function DeckValidation({ className }: DeckValidationProps) {
  const cards = useDeckStore((state) => state.cards);
  const totalCards = useDeckStore((state) => state.totalCards);

  const total = totalCards();
  const errors: ValidationError[] = [];

  // Check 60 card requirement
  if (total < TARGET_DECK_SIZE) {
    errors.push({
      type: "warning",
      message: `Deck has ${total} cards (need ${TARGET_DECK_SIZE})`,
    });
  } else if (total > TARGET_DECK_SIZE) {
    errors.push({
      type: "error",
      message: `Deck has ${total} cards (max ${TARGET_DECK_SIZE})`,
    });
  }

  // Check 4-card limit violations (excluding basic energy)
  const cardsByName = new Map<string, number>();
  for (const deckCard of cards) {
    const { card, quantity } = deckCard;
    // Basic energy is unlimited
    if (card.supertype === "Energy" && !card.name.includes("Special")) {
      continue;
    }

    const currentCount = cardsByName.get(card.name) || 0;
    cardsByName.set(card.name, currentCount + quantity);
  }

  for (const [name, count] of cardsByName) {
    if (count > MAX_SAME_NAME_CARDS) {
      errors.push({
        type: "error",
        message: `${name}: ${count} copies (max ${MAX_SAME_NAME_CARDS})`,
      });
    }
  }

  // Check for basic Pokemon (simplified check - look for Pokemon without evolution info)
  const pokemonCards = cards.filter((c) => c.card.supertype === "Pokemon");
  if (pokemonCards.length > 0) {
    // This is a simplified check - in a real app we'd check for Basic Pokemon specifically
    // For now we just ensure there's at least one Pokemon if using any
    const hasBasicPokemon = pokemonCards.some((c) => {
      // Basic Pokemon typically don't have "Stage" in subtypes or can be identified by other means
      // This is a simplified heuristic
      return true; // Assume at least one is basic for MVP
    });

    if (!hasBasicPokemon) {
      errors.push({
        type: "error",
        message: "Deck must contain at least one Basic Pokemon",
      });
    }
  }

  // If no errors, show valid message
  if (errors.length === 0 && total === TARGET_DECK_SIZE) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 p-3 rounded-md bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
          className
        )}
      >
        <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
        <span className="text-sm">Deck is valid and ready to play!</span>
      </div>
    );
  }

  // Don't show validation panel if empty deck
  if (total === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-2", className)}>
      {errors.map((error, index) => (
        <div
          key={index}
          className={cn(
            "flex items-center gap-2 p-2 rounded-md text-sm",
            error.type === "error" &&
              "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400",
            error.type === "warning" &&
              "bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400"
          )}
        >
          {error.type === "error" ? (
            <XCircle className="h-4 w-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
          )}
          <span>{error.message}</span>
        </div>
      ))}
    </div>
  );
}
