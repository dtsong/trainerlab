"use client";

import Link from "next/link";
import Image from "next/image";
import { Minus, Plus, Trash2, ImageOff } from "lucide-react";
import { memo, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { DeckCard } from "@/types/deck";

interface DeckListItemProps {
  deckCard: DeckCard;
  onQuantityChange: (cardId: string, delta: number) => void;
  onRemove: (cardId: string) => void;
}

const THUMBNAIL_SIZE = { width: 48, height: 67 };

export const DeckListItem = memo(function DeckListItem({
  deckCard,
  onQuantityChange,
  onRemove,
}: DeckListItemProps) {
  const { card, quantity } = deckCard;
  const [imageError, setImageError] = useState(false);

  return (
    <div className="flex items-center gap-2 p-2 rounded-md hover:bg-accent group">
      {/* Card thumbnail */}
      <Link
        href={`/investigate/card/${card.id}`}
        className="relative flex-shrink-0 rounded overflow-hidden"
        style={THUMBNAIL_SIZE}
      >
        {card.image_small && !imageError ? (
          <Image
            src={card.image_small}
            alt={card.name}
            width={THUMBNAIL_SIZE.width}
            height={THUMBNAIL_SIZE.height}
            className="object-cover"
            onError={() => setImageError(true)}
            unoptimized
          />
        ) : (
          <div className="w-full h-full bg-muted flex items-center justify-center">
            <ImageOff className="w-4 h-4 text-muted-foreground" />
          </div>
        )}
      </Link>

      {/* Card name */}
      <Link
        href={`/investigate/card/${card.id}`}
        className="flex-1 min-w-0 hover:underline"
      >
        <span className="text-sm font-medium truncate block">{card.name}</span>
        <span className="text-xs text-muted-foreground truncate block">
          {card.supertype}
          {card.types && card.types.length > 0 && ` - ${card.types[0]}`}
        </span>
      </Link>

      {/* Quantity controls */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => onQuantityChange(card.id, -1)}
          disabled={quantity <= 1}
          aria-label="Decrease quantity"
        >
          <Minus className="h-3 w-3" />
        </Button>

        <span
          className={cn(
            "w-6 text-center text-sm font-medium",
            quantity >= 4 && "text-amber-600"
          )}
        >
          {quantity}
        </span>

        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => onQuantityChange(card.id, 1)}
          aria-label="Increase quantity"
        >
          <Plus className="h-3 w-3" />
        </Button>
      </div>

      {/* Delete button */}
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => onRemove(card.id)}
        aria-label="Remove card"
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
});
