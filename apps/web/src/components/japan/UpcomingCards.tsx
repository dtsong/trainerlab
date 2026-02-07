"use client";

import { AlertCircle, Calendar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useJPUpcomingCards } from "@/hooks/useTranslations";
import type { ApiJPUnreleasedCard } from "@trainerlab/shared-types";

function CardItem({ card }: { card: ApiJPUnreleasedCard }) {
  return (
    <div className="flex items-start gap-4 rounded-lg border border-border/50 bg-card/50 p-4">
      <div className="flex-1 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h4 className="font-medium">{card.name_en || card.name_jp}</h4>
            {card.name_en && (
              <p className="text-sm text-muted-foreground">{card.name_jp}</p>
            )}
          </div>
          {card.expected_release_set && (
            <Badge variant="outline" className="shrink-0 text-xs">
              <Calendar className="mr-1 h-3 w-3" />
              {card.expected_release_set}
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {card.jp_set_id && (
            <Badge variant="secondary" className="text-xs">
              {card.jp_set_id}
            </Badge>
          )}
          {card.card_type && (
            <Badge variant="outline" className="text-xs">
              {card.card_type}
            </Badge>
          )}
          {card.competitive_impact >= 4 && (
            <Badge className="bg-amber-600 text-xs">High Impact</Badge>
          )}
        </div>

        {card.notes && (
          <p className="text-sm text-muted-foreground line-clamp-3">
            {card.notes}
          </p>
        )}

        {card.affected_archetypes && card.affected_archetypes.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {card.affected_archetypes.slice(0, 3).map((archetype) => (
              <Badge key={archetype} variant="outline" className="text-xs">
                {archetype}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface UpcomingCardsProps {
  className?: string;
  limit?: number;
}

export function UpcomingCards({ className, limit = 10 }: UpcomingCardsProps) {
  const { data, isLoading, error } = useJPUpcomingCards({ limit });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Upcoming Cards
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load upcoming cards
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Upcoming Cards</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const cards = data?.cards ?? [];

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Upcoming Cards</CardTitle>
        <p className="text-sm text-muted-foreground">
          Japanese cards not yet released internationally
        </p>
      </CardHeader>
      <CardContent>
        {cards.length === 0 ? (
          <p className="py-8 text-center text-muted-foreground">
            No upcoming cards tracked
          </p>
        ) : (
          <div className="space-y-3">
            {cards.map((card) => (
              <CardItem key={card.id} card={card} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
