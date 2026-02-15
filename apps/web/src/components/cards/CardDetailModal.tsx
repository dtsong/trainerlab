"use client";

import { useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { CardImage } from "@/components/cards/CardImage";
import { cardsApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  ApiCard,
  ApiConsensusDecklistCard,
} from "@trainerlab/shared-types";

interface CardDetailModalProps {
  cardId: string | null;
  isOpen: boolean;
  onClose: () => void;
  /** All cards in the grid for prev/next navigation */
  cards?: ApiConsensusDecklistCard[];
  onNavigate?: (cardId: string) => void;
}

function AttackDisplay({
  attack,
}: {
  attack: { name: string; cost?: string[]; damage?: string; effect?: string };
}) {
  return (
    <div className="rounded bg-terminal-surface p-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {attack.cost && attack.cost.length > 0 && (
            <span className="font-mono text-[10px] text-terminal-muted">
              [{attack.cost.join("")}]
            </span>
          )}
          <span className="text-sm font-medium text-terminal-text">
            {attack.name}
          </span>
        </div>
        {attack.damage && (
          <span className="font-mono text-sm font-bold text-terminal-accent">
            {attack.damage}
          </span>
        )}
      </div>
      {attack.effect && (
        <p className="mt-1 text-xs text-terminal-muted">{attack.effect}</p>
      )}
    </div>
  );
}

function AbilityDisplay({
  ability,
}: {
  ability: { name: string; type?: string; effect?: string };
}) {
  return (
    <div className="rounded border border-terminal-accent/30 bg-terminal-surface p-2">
      <div className="flex items-center gap-2">
        <span className="rounded bg-terminal-accent/20 px-1.5 py-0.5 text-[10px] font-bold uppercase text-terminal-accent">
          {ability.type ?? "Ability"}
        </span>
        <span className="text-sm font-medium text-terminal-text">
          {ability.name}
        </span>
      </div>
      {ability.effect && (
        <p className="mt-1 text-xs text-terminal-muted">{ability.effect}</p>
      )}
    </div>
  );
}

function CardStats({ card }: { card: ApiCard }) {
  return (
    <div className="space-y-4">
      {/* Name + basic info */}
      <div>
        <h3 className="text-lg font-semibold text-white">{card.name}</h3>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          {card.supertype && (
            <span className="text-xs text-terminal-muted">
              {card.supertype}
            </span>
          )}
          {card.subtypes && card.subtypes.length > 0 && (
            <span className="text-xs text-terminal-muted">
              — {card.subtypes.join(", ")}
            </span>
          )}
          {card.hp != null && (
            <span className="font-mono text-xs text-terminal-accent">
              HP {card.hp}
            </span>
          )}
          {card.types && card.types.length > 0 && (
            <span className="text-xs text-terminal-muted">
              {card.types.join("/")}
            </span>
          )}
        </div>
      </div>

      {/* Abilities */}
      {card.abilities && card.abilities.length > 0 && (
        <div className="space-y-2">
          {card.abilities.map((a, i) => (
            <AbilityDisplay key={i} ability={a} />
          ))}
        </div>
      )}

      {/* Attacks */}
      {card.attacks && card.attacks.length > 0 && (
        <div className="space-y-2">
          {card.attacks.map((a, i) => (
            <AttackDisplay key={i} attack={a} />
          ))}
        </div>
      )}

      {/* Rules */}
      {card.rules && card.rules.length > 0 && (
        <div className="rounded bg-terminal-surface p-2">
          {card.rules.map((rule, i) => (
            <p key={i} className="text-xs italic text-terminal-muted">
              {rule}
            </p>
          ))}
        </div>
      )}

      {/* Weakness / Resistance / Retreat */}
      <div className="flex flex-wrap gap-3 text-xs text-terminal-muted">
        {card.weaknesses && card.weaknesses.length > 0 && (
          <span>
            Weakness:{" "}
            {card.weaknesses.map((w) => `${w.type} ${w.value}`).join(", ")}
          </span>
        )}
        {card.resistances && card.resistances.length > 0 && (
          <span>
            Resistance:{" "}
            {card.resistances.map((r) => `${r.type} ${r.value}`).join(", ")}
          </span>
        )}
        {card.retreat_cost != null && <span>Retreat: {card.retreat_cost}</span>}
      </div>

      {/* Set + rarity */}
      <div className="text-xs text-terminal-muted">
        {card.set_id}
        {card.number ? ` #${card.number}` : ""}
        {card.rarity ? ` — ${card.rarity}` : ""}
      </div>
    </div>
  );
}

export function CardDetailModal({
  cardId,
  isOpen,
  onClose,
  cards,
  onNavigate,
}: CardDetailModalProps) {
  const { data: card, isLoading } = useQuery({
    queryKey: ["card", cardId],
    queryFn: () => cardsApi.getById(cardId!),
    enabled: !!cardId && isOpen,
    staleTime: 1000 * 60 * 10,
  });

  // Keyboard navigation
  const currentIndex = cards?.findIndex((c) => c.card_id === cardId) ?? -1;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!cards || !onNavigate) return;
      if (e.key === "ArrowLeft" && currentIndex > 0) {
        e.preventDefault();
        onNavigate(cards[currentIndex - 1].card_id);
      } else if (e.key === "ArrowRight" && currentIndex < cards.length - 1) {
        e.preventDefault();
        onNavigate(cards[currentIndex + 1].card_id);
      }
    },
    [cards, onNavigate, currentIndex]
  );

  useEffect(() => {
    if (!isOpen) return;
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, handleKeyDown]);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className={cn(
          "max-w-4xl border-terminal-border bg-terminal-bg text-terminal-text",
          "p-0 overflow-hidden"
        )}
      >
        <DialogTitle className="sr-only">
          {card?.name ?? "Card Details"}
        </DialogTitle>

        {isLoading ? (
          <div className="flex h-[400px] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-terminal-accent border-t-transparent" />
          </div>
        ) : card ? (
          <div className="grid grid-cols-1 gap-0 md:grid-cols-[320px_1fr]">
            {/* Card image */}
            <div className="flex items-center justify-center bg-black/20 p-6">
              <CardImage
                src={card.image_large ?? card.image_small}
                alt={card.name}
                size="large"
                priority
              />
            </div>

            {/* Stats panel */}
            <div className="overflow-y-auto p-6">
              <CardStats card={card} />

              {/* Navigation hint */}
              {cards && cards.length > 1 && (
                <p className="mt-4 text-center text-[10px] text-terminal-muted">
                  ← → arrow keys to navigate
                  {currentIndex >= 0 && (
                    <span className="ml-1">
                      ({currentIndex + 1}/{cards.length})
                    </span>
                  )}
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="flex h-[300px] items-center justify-center text-terminal-muted">
            Card not found
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
