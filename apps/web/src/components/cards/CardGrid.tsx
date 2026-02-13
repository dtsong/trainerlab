"use client";

import Link from "next/link";
import type { ApiCardSummary } from "@trainerlab/shared-types";
import { CardImage } from "./CardImage";
import { cn } from "@/lib/utils";

interface CardGridProps {
  cards: ApiCardSummary[];
  className?: string;
}

interface CardGridItemProps {
  card: ApiCardSummary;
}

function CardGridItem({ card }: CardGridItemProps) {
  return (
    <Link
      href={`/investigate/card/${card.id}`}
      className="group flex flex-col gap-2 transition-transform hover:scale-105"
    >
      <CardImage
        src={card.image_small}
        alt={card.name}
        size="small"
        className="shadow-md group-hover:shadow-lg transition-shadow"
      />
      <div className="px-1">
        <h3 className="font-medium text-sm truncate">{card.name}</h3>
        <p className="text-xs text-muted-foreground">
          {card.supertype}
          {card.types && card.types.length > 0 && ` - ${card.types.join("/")}`}
        </p>
      </div>
    </Link>
  );
}

export function CardGrid({ cards, className }: CardGridProps) {
  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-lg font-medium text-muted-foreground">
          No cards found
        </p>
        <p className="text-sm text-muted-foreground">
          Try adjusting your search or filters
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "grid gap-4",
        "grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6",
        className
      )}
    >
      {cards.map((card) => (
        <CardGridItem key={card.id} card={card} />
      ))}
    </div>
  );
}
