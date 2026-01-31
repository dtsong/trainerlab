"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardImage } from "@/components/cards/CardImage";
import { cn } from "@/lib/utils";
import type { Archetype } from "@trainerlab/shared-types";

interface ArchetypeCardProps {
  archetype: Archetype;
  cardImages?: Record<string, { src: string; name: string }>;
  className?: string;
}

export function ArchetypeCard({
  archetype,
  cardImages = {},
  className,
}: ArchetypeCardProps) {
  const sharePercent = (archetype.share * 100).toFixed(1);
  const keyCards = archetype.keyCards?.slice(0, 3) || [];

  return (
    <Link href={`/meta/archetype/${encodeURIComponent(archetype.name)}`}>
      <Card
        className={cn(
          "cursor-pointer transition-all hover:shadow-lg hover:border-primary/50",
          className,
        )}
        data-testid="archetype-card"
      >
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between">
            <span className="truncate text-lg">{archetype.name}</span>
            <span className="shrink-0 text-2xl font-bold text-primary">
              {sharePercent}%
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {keyCards.map((cardId) => {
              const cardInfo = cardImages[cardId];
              return (
                <div key={cardId} className="relative">
                  <CardImage
                    src={cardInfo?.src}
                    alt={cardInfo?.name || cardId}
                    size="small"
                    className="h-[80px] w-[57px]"
                  />
                </div>
              );
            })}
            {keyCards.length === 0 && (
              <div className="flex h-[80px] items-center text-sm text-muted-foreground">
                No key cards defined
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
