"use client";

import {
  TrendingUp,
  TrendingDown,
  Minus,
  Star,
  AlertCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useJPCardInnovations } from "@/hooks/useJapan";
import type { ApiJPCardInnovation } from "@trainerlab/shared-types";

function TrendIcon({ trend }: { trend: string | null | undefined }) {
  if (trend === "rising") {
    return <TrendingUp className="h-4 w-4 text-green-500" />;
  }
  if (trend === "falling") {
    return <TrendingDown className="h-4 w-4 text-red-500" />;
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

function ImpactRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-3 w-3 ${
            i < rating
              ? "fill-yellow-400 text-yellow-400"
              : "text-muted-foreground"
          }`}
        />
      ))}
    </div>
  );
}

function CardRow({ card }: { card: ApiJPCardInnovation }) {
  const adoptionPercent = (card.adoption_rate * 100).toFixed(1);

  return (
    <TableRow>
      <TableCell className="font-medium">
        <div className="flex flex-col">
          <span>{card.card_name}</span>
          {card.card_name_jp && (
            <span className="text-xs text-muted-foreground">
              {card.card_name_jp}
            </span>
          )}
        </div>
      </TableCell>
      <TableCell>
        <Badge variant="outline">{card.set_code}</Badge>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <TrendIcon trend={card.adoption_trend} />
          <span>{adoptionPercent}%</span>
        </div>
      </TableCell>
      <TableCell>
        <ImpactRating rating={card.competitive_impact_rating} />
      </TableCell>
      <TableCell>
        {card.is_legal_en ? (
          <Badge variant="secondary">Legal</Badge>
        ) : (
          <Badge variant="outline" className="text-muted-foreground">
            JP Only
          </Badge>
        )}
      </TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-1">
          {card.archetypes_using?.slice(0, 3).map((archetype) => (
            <Badge key={archetype} variant="secondary" className="text-xs">
              {archetype}
            </Badge>
          ))}
          {card.archetypes_using && card.archetypes_using.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{card.archetypes_using.length - 3}
            </Badge>
          )}
        </div>
      </TableCell>
    </TableRow>
  );
}

interface CardInnovationTrackerProps {
  className?: string;
  limit?: number;
  showJpOnly?: boolean;
}

export function CardInnovationTracker({
  className,
  limit = 20,
  showJpOnly = false,
}: CardInnovationTrackerProps) {
  const { data, isLoading, error } = useJPCardInnovations({
    limit,
    en_legal: showJpOnly ? false : undefined,
  });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Card Innovation Tracker (BO1)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load card innovations
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Card Innovation Tracker (BO1)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const cards = data?.items ?? [];

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Card Innovation Tracker (BO1)</CardTitle>
        <p className="text-sm text-muted-foreground">
          New cards seeing competitive play in Japan City Leagues
        </p>
      </CardHeader>
      <CardContent>
        {cards.length === 0 ? (
          <p className="py-8 text-center text-muted-foreground">
            No card innovations tracked yet
          </p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Card</TableHead>
                  <TableHead>Set</TableHead>
                  <TableHead>Adoption</TableHead>
                  <TableHead>Impact</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Archetypes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cards.map((card) => (
                  <CardRow key={card.id} card={card} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
