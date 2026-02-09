"use client";

import { format, parseISO } from "date-fns";
import { ChevronDown, ChevronRight, Users } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import type {
  ApiTournamentSummary,
  ApiTopPlacement,
} from "@trainerlab/shared-types";

function formatTournamentDate(dateStr: string): string {
  const date = parseISO(dateStr);
  const currentYear = new Date().getFullYear();
  return date.getFullYear() === currentYear
    ? format(date, "MMM d")
    : format(date, "MMM d, yyyy");
}

function PlacementItem({ placement }: { placement: ApiTopPlacement }) {
  return (
    <div className="flex items-center gap-3 px-3 py-1.5 text-sm">
      <span className="w-6 text-center font-medium tabular-nums text-muted-foreground">
        #{placement.placement}
      </span>
      <Badge variant="secondary" className="text-xs">
        {placement.archetype}
      </Badge>
      <span className="text-muted-foreground truncate">
        {placement.player_name ?? "Anonymous"}
      </span>
    </div>
  );
}

interface TournamentRowProps {
  tournament: ApiTournamentSummary;
  expanded: boolean;
  onToggle: () => void;
  showRegion?: boolean;
}

export function TournamentRow({
  tournament,
  expanded,
  onToggle,
  showRegion = true,
}: TournamentRowProps) {
  const dateStr = formatTournamentDate(tournament.date);
  const winner = tournament.top_placements[0];
  // Larger events (64+ players) run more Swiss rounds, show top 8
  const placementsToShow =
    (tournament.participant_count ?? 0) >= 64
      ? tournament.top_placements.slice(0, 8)
      : tournament.top_placements.slice(0, 4);

  return (
    <div className="border-b last:border-0">
      <button
        type="button"
        aria-expanded={expanded}
        className="flex w-full items-center gap-4 px-4 py-3 text-left text-sm hover:bg-muted/50 transition-colors"
        onClick={onToggle}
      >
        {/* Date */}
        <span className="w-20 shrink-0 tabular-nums text-muted-foreground hidden sm:block">
          {dateStr}
        </span>

        {/* Name */}
        <span className="flex-1 font-medium truncate min-w-0">
          {tournament.name}
          {/* Mobile date */}
          <span className="sm:hidden text-muted-foreground font-normal text-xs ml-2">
            {dateStr}
          </span>
        </span>

        {/* Region */}
        {showRegion && (
          <span className="w-14 shrink-0 text-center text-xs text-muted-foreground hidden sm:block">
            {tournament.region}
          </span>
        )}

        {/* Players */}
        {tournament.participant_count != null && (
          <span className="w-16 shrink-0 flex items-center gap-1 text-xs text-muted-foreground hidden sm:flex">
            <Users className="h-3 w-3" />
            {tournament.participant_count}
          </span>
        )}

        {/* Winner badge */}
        {winner && (
          <Badge variant="secondary" className="text-xs shrink-0">
            {winner.archetype}
          </Badge>
        )}

        {/* Chevron */}
        {expanded ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        )}
      </button>

      {/* Mobile metadata row */}
      {(showRegion || tournament.participant_count != null) && (
        <div className="flex sm:hidden items-center gap-3 px-4 pb-2 text-xs text-muted-foreground -mt-1">
          {showRegion && <span>{tournament.region}</span>}
          {tournament.participant_count != null && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {tournament.participant_count}
            </span>
          )}
        </div>
      )}

      {/* Expanded placements */}
      {expanded && (
        <div className="bg-muted/30 border-t px-4 py-3 animate-in slide-in-from-top-1 duration-200">
          <div className="space-y-0.5">
            {placementsToShow.map((placement, i) => (
              <PlacementItem
                key={`${placement.placement}-${i}`}
                placement={placement}
              />
            ))}
          </div>
          <div className="mt-3 px-3">
            <Link
              href={`/tournaments/${tournament.id}`}
              className="text-sm text-primary hover:underline font-medium"
            >
              View Full Results &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
