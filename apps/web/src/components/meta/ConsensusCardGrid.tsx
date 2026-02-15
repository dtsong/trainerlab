"use client";

import { memo } from "react";
import { CardImage } from "@/components/cards/CardImage";
import { cn } from "@/lib/utils";
import type { ApiConsensusDecklistCard } from "@trainerlab/shared-types";

interface CardCellProps {
  card: ApiConsensusDecklistCard;
  onClick?: (card: ApiConsensusDecklistCard) => void;
}

const CardCell = memo(function CardCell({ card, onClick }: CardCellProps) {
  return (
    <button
      type="button"
      onClick={() => onClick?.(card)}
      className={cn(
        "group relative flex flex-col items-center transition-transform",
        "hover:scale-105 focus:outline-none focus:ring-2 focus:ring-terminal-accent focus:ring-offset-1 focus:ring-offset-terminal-bg",
        "rounded-lg"
      )}
      title={`${card.card_name ?? card.card_id} — ${Math.round(card.inclusion_rate * 100)}% inclusion, ×${card.avg_copies.toFixed(1)}`}
    >
      <div className="relative">
        <CardImage
          src={card.image_small}
          alt={card.card_name ?? card.card_id}
          size="small"
          className="rounded-lg"
        />

        {/* Inclusion rate badge — top right */}
        <span className="absolute -right-1 -top-1 rounded-full bg-terminal-accent px-1.5 py-0.5 font-mono text-[10px] font-bold text-black shadow-sm">
          {Math.round(card.inclusion_rate * 100)}%
        </span>

        {/* Average copies badge — bottom center */}
        <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 rounded-full bg-terminal-surface/90 px-1.5 py-0.5 font-mono text-[10px] font-medium text-terminal-text shadow-sm ring-1 ring-terminal-border">
          ×{card.avg_copies.toFixed(1)}
        </span>
      </div>
    </button>
  );
});

interface CardSectionProps {
  title: string;
  cards: ApiConsensusDecklistCard[];
  onCardClick?: (card: ApiConsensusDecklistCard) => void;
}

function CardSection({ title, cards, onCardClick }: CardSectionProps) {
  if (cards.length === 0) return null;

  return (
    <div>
      <h4 className="mb-3 font-mono text-xs uppercase tracking-widest text-terminal-muted">
        {title}
        <span className="ml-2 text-terminal-accent">{cards.length}</span>
      </h4>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6">
        {cards.map((card) => (
          <CardCell key={card.card_id} card={card} onClick={onCardClick} />
        ))}
      </div>
    </div>
  );
}

export interface ConsensusCardGridProps {
  pokemon: ApiConsensusDecklistCard[];
  trainers: ApiConsensusDecklistCard[];
  energy: ApiConsensusDecklistCard[];
  decklistsAnalyzed: number;
  onCardClick?: (card: ApiConsensusDecklistCard) => void;
  className?: string;
}

export function ConsensusCardGrid({
  pokemon,
  trainers,
  energy,
  decklistsAnalyzed,
  onCardClick,
  className,
}: ConsensusCardGridProps) {
  return (
    <div className={cn("space-y-6", className)}>
      {decklistsAnalyzed < 5 && (
        <p className="rounded bg-terminal-surface px-3 py-2 text-xs text-terminal-muted">
          Limited data — {decklistsAnalyzed} decklist
          {decklistsAnalyzed === 1 ? "" : "s"} analyzed
        </p>
      )}
      <CardSection title="Pokémon" cards={pokemon} onCardClick={onCardClick} />
      <CardSection
        title="Trainers"
        cards={trainers}
        onCardClick={onCardClick}
      />
      <CardSection title="Energy" cards={energy} onCardClick={onCardClick} />
    </div>
  );
}
