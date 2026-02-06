"use client";

import { format, parseISO } from "date-fns";
import { ChevronDown, ChevronUp, Users, AlertCircle } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTournaments } from "@/hooks/useTournaments";
import { usePlacementDecklist } from "@/hooks/useTournaments";
import { DecklistViewer } from "./DecklistViewer";
import type {
  ApiTournamentSummary,
  ApiTopPlacement,
} from "@trainerlab/shared-types";

function PlacementRow({
  placement,
  tournamentId,
}: {
  placement: ApiTopPlacement & { id?: string; has_decklist?: boolean };
  tournamentId: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasDecklist = "has_decklist" in placement && placement.has_decklist;
  const placementId = "id" in placement ? (placement.id as string) : null;

  const { data: decklist, isLoading } = usePlacementDecklist(
    expanded && hasDecklist ? tournamentId : null,
    expanded && hasDecklist ? placementId : null
  );

  return (
    <div className="border-b last:border-0">
      <button
        type="button"
        className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-muted/50 transition-colors"
        onClick={() => hasDecklist && setExpanded(!expanded)}
        disabled={!hasDecklist}
      >
        <span className="w-6 text-center font-medium tabular-nums text-muted-foreground">
          {placement.placement}
        </span>
        <span className="flex-1 truncate">
          {placement.player_name ?? "Anonymous"}
        </span>
        <Badge variant="secondary" className="text-xs">
          {placement.archetype}
        </Badge>
        {hasDecklist &&
          (expanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ))}
      </button>
      {expanded && hasDecklist && (
        <div className="px-3 pb-3">
          {isLoading ? (
            <div className="h-24 animate-pulse rounded bg-muted" />
          ) : decklist ? (
            <DecklistViewer decklist={decklist} />
          ) : (
            <p className="text-sm text-muted-foreground py-2">
              Decklist not available
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function TournamentItem({ tournament }: { tournament: ApiTournamentSummary }) {
  const [expanded, setExpanded] = useState(false);
  const dateStr = format(parseISO(tournament.date), "MMM d, yyyy");

  return (
    <Card>
      <button
        type="button"
        className="w-full text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-base">{tournament.name}</CardTitle>
              <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                <span>{dateStr}</span>
                {tournament.participant_count && (
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {tournament.participant_count}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {expanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </div>
          {/* Archetype badges */}
          <div className="flex flex-wrap gap-1 mt-2">
            {[
              ...new Set(tournament.top_placements.map((p) => p.archetype)),
            ].map((archetype) => (
              <Badge key={archetype} variant="outline" className="text-xs">
                {archetype}
              </Badge>
            ))}
          </div>
        </CardHeader>
      </button>
      {expanded && (
        <CardContent className="pt-0">
          <div className="rounded border">
            {tournament.top_placements.map((placement, i) => (
              <PlacementRow
                key={`${placement.placement}-${i}`}
                placement={placement}
                tournamentId={tournament.id}
              />
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

interface CityLeagueResultsFeedProps {
  className?: string;
  startDate?: string;
  endDate?: string;
}

export function CityLeagueResultsFeed({
  className,
  startDate,
  endDate,
}: CityLeagueResultsFeedProps) {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useTournaments({
    region: "JP",
    best_of: 1,
    start_date: startDate,
    end_date: endDate,
    page,
    limit: 10,
    sort_by: "date",
    order: "desc",
  });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            City League Results (BO1)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load City League results
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className={className}>
        <h2 className="text-xl font-semibold mb-4">
          City League Results (BO1)
        </h2>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-24 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const tournaments = data?.items ?? [];

  return (
    <div className={className} data-testid="city-league-feed">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">City League Results (BO1)</h2>
        <p className="text-sm text-muted-foreground">
          Recent JP City League top cuts — expand to view decklists
        </p>
      </div>
      {tournaments.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">
              No City League results in this date range
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {tournaments.map((tournament) => (
              <TournamentItem key={tournament.id} tournament={tournament} />
            ))}
          </div>
          {data && (data.has_next || data.has_prev) && (
            <div className="flex justify-center gap-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={!data.has_prev}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.has_next}
              >
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
