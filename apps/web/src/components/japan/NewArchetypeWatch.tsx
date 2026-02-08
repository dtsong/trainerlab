"use client";

import { format, parseISO } from "date-fns";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Trophy,
  AlertCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CardReference } from "@/components/cards/CardReference";
import { useJPNewArchetypes } from "@/hooks/useJapan";
import type { ApiJPNewArchetype } from "@trainerlab/shared-types";

function TrendIcon({ trend }: { trend: string | null | undefined }) {
  if (trend === "rising") {
    return <TrendingUp className="h-4 w-4 text-green-500" />;
  }
  if (trend === "falling") {
    return <TrendingDown className="h-4 w-4 text-red-500" />;
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

function ArchetypeCard({ archetype }: { archetype: ApiJPNewArchetype }) {
  const metaSharePercent = (archetype.jp_meta_share * 100).toFixed(1);
  const estimatedDate = archetype.estimated_en_legal_date
    ? format(parseISO(archetype.estimated_en_legal_date), "MMM yyyy")
    : null;

  // Get top placements from city league results
  const topPlacements = archetype.city_league_results
    ?.flatMap((r) => r.placements)
    .filter((p) => p <= 8)
    .slice(0, 5);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{archetype.name}</CardTitle>
            {archetype.name_jp && (
              <p className="text-sm text-muted-foreground">
                {archetype.name_jp}
              </p>
            )}
          </div>
          <Badge variant="secondary" className="flex items-center gap-1">
            <TrendIcon trend={archetype.jp_trend} />
            {metaSharePercent}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Key cards */}
        {(archetype.key_card_details ?? archetype.key_cards) && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Key Cards
            </p>
            <div className="flex flex-wrap gap-1">
              {(
                archetype.key_card_details ??
                archetype.key_cards?.map((c) => ({
                  card_id: c,
                  card_name: c,
                })) ??
                []
              ).map((card) => (
                <CardReference
                  key={card.card_id}
                  cardId={card.card_id}
                  cardName={card.card_name}
                  imageSmall={
                    "image_small" in card ? card.image_small : undefined
                  }
                  variant="badge"
                />
              ))}
            </div>
          </div>
        )}

        {/* Enabled by set */}
        {archetype.enabled_by_set && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Enabled by:</span>
            <Badge variant="secondary">{archetype.enabled_by_set}</Badge>
          </div>
        )}

        {/* City League results */}
        {topPlacements && topPlacements.length > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <Trophy className="h-4 w-4 text-yellow-500" />
            <span className="text-muted-foreground">
              Top 8s: {topPlacements.join(", ")}
            </span>
          </div>
        )}

        {/* Estimated EN date */}
        {estimatedDate && (
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              Est. EN Legal: {estimatedDate}
            </span>
          </div>
        )}

        {/* Analysis preview */}
        {archetype.analysis && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {archetype.analysis}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

interface NewArchetypeWatchProps {
  className?: string;
  limit?: number;
}

export function NewArchetypeWatch({
  className,
  limit = 6,
}: NewArchetypeWatchProps) {
  const { data, isLoading, error } = useJPNewArchetypes({ limit });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            New Archetype Watch (BO1)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load new archetypes
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className={className}>
        <h2 className="text-xl font-semibold mb-4">
          New Archetype Watch (BO1)
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-32 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const archetypes = data?.items ?? [];

  return (
    <div className={className}>
      <div className="mb-4">
        <h2 className="text-xl font-semibold">New Archetype Watch (BO1)</h2>
        <p className="text-sm text-muted-foreground">
          JP-exclusive archetypes not yet in the English meta
        </p>
      </div>
      {archetypes.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">
              No new archetypes tracked yet
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {archetypes.map((archetype) => (
            <ArchetypeCard key={archetype.id} archetype={archetype} />
          ))}
        </div>
      )}
    </div>
  );
}
