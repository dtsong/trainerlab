"use client";

import { useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import { ImageOff, Edit, Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { SavedDeck } from "@/types/deck";

interface DeckCardProps {
  deck: SavedDeck;
}

const FEATURED_CARD_SIZE = { width: 48, height: 67 };
const MAX_FEATURED_CARDS = 3;

export function DeckCard({ deck }: DeckCardProps) {
  const totalCards = useMemo(() => {
    return deck.cards.reduce((sum, c) => sum + c.quantity, 0);
  }, [deck.cards]);

  // Get featured Pokemon cards to display
  const featuredCards = useMemo(() => {
    const pokemonCards = deck.cards
      .filter((c) => c.card.supertype === "Pokemon")
      .slice(0, MAX_FEATURED_CARDS);

    // If not enough Pokemon, add Trainers/Energy
    if (pokemonCards.length < MAX_FEATURED_CARDS) {
      const otherCards = deck.cards
        .filter((c) => c.card.supertype !== "Pokemon")
        .slice(0, MAX_FEATURED_CARDS - pokemonCards.length);
      return [...pokemonCards, ...otherCards];
    }

    return pokemonCards;
  }, [deck.cards]);

  const formatBadgeVariant = deck.format === "standard" ? "default" : "outline";

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base truncate">{deck.name}</CardTitle>
          <Badge variant={formatBadgeVariant} className="shrink-0">
            {deck.format === "standard" ? "Standard" : "Expanded"}
          </Badge>
        </div>
        {deck.description && (
          <CardDescription className="line-clamp-2 text-xs">
            {deck.description}
          </CardDescription>
        )}
      </CardHeader>

      <CardContent className="pb-2">
        {/* Featured card images */}
        <div className="flex gap-1 mb-3">
          {featuredCards.length > 0 ? (
            featuredCards.map((dc) => (
              <FeaturedCardImage
                key={dc.card.id}
                src={dc.card.image_small}
                alt={dc.card.name}
              />
            ))
          ) : (
            <div
              className="flex items-center justify-center bg-muted rounded"
              style={{
                width: FEATURED_CARD_SIZE.width * MAX_FEATURED_CARDS + 8,
                height: FEATURED_CARD_SIZE.height,
              }}
            >
              <span className="text-xs text-muted-foreground">No cards</span>
            </div>
          )}
        </div>

        {/* Card count */}
        <div className="text-sm text-muted-foreground">
          {totalCards} card{totalCards !== 1 ? "s" : ""}
        </div>
      </CardContent>

      <CardFooter className="pt-2 gap-2">
        <Button variant="outline" size="sm" className="flex-1" asChild>
          <Link href={`/decks/${deck.id}`}>
            <Eye className="h-4 w-4 mr-1" />
            View
          </Link>
        </Button>
        <Button variant="default" size="sm" className="flex-1" asChild>
          <Link href={`/decks/${deck.id}?edit=true`}>
            <Edit className="h-4 w-4 mr-1" />
            Edit
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}

interface FeaturedCardImageProps {
  src: string | null | undefined;
  alt: string;
}

function FeaturedCardImage({ src, alt }: FeaturedCardImageProps) {
  if (!src) {
    return (
      <div
        className="flex items-center justify-center bg-muted rounded overflow-hidden"
        style={FEATURED_CARD_SIZE}
      >
        <ImageOff className="h-4 w-4 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div
      className="relative rounded overflow-hidden"
      style={FEATURED_CARD_SIZE}
    >
      <Image
        src={src}
        alt={alt}
        width={FEATURED_CARD_SIZE.width}
        height={FEATURED_CARD_SIZE.height}
        className="object-cover"
        unoptimized
      />
    </div>
  );
}
