"use client";

import { CalendarDays, MapPin, Users } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { ApiTournamentSummary } from "@trainerlab/shared-types";

interface TournamentCardProps {
  tournament: ApiTournamentSummary;
}

const tierColors: Record<string, string> = {
  major: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  premier: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  league: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

export function TournamentCard({ tournament }: TournamentCardProps) {
  const date = new Date(tournament.date);
  const formattedDate = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Link href={`/tournaments/${tournament.id}`}>
      <Card className="h-full transition-colors hover:border-primary/50">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg line-clamp-2">
              {tournament.name}
            </CardTitle>
            {tournament.tier && (
              <Badge
                variant="outline"
                className={tierColors[tournament.tier] || tierColors.league}
              >
                {tournament.tier}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-4">
            <div className="flex items-center gap-1.5">
              <CalendarDays className="h-4 w-4" />
              <span>{formattedDate}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              <span>
                {tournament.country
                  ? `${tournament.region} - ${tournament.country}`
                  : tournament.region}
              </span>
            </div>
            {tournament.participant_count && (
              <div className="flex items-center gap-1.5">
                <Users className="h-4 w-4" />
                <span>{tournament.participant_count}</span>
              </div>
            )}
          </div>

          {tournament.top_placements.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground mb-2">
                Top Finishers
              </div>
              {tournament.top_placements.slice(0, 4).map((placement) => (
                <div
                  key={placement.placement}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-muted-foreground">
                    #{placement.placement}
                  </span>
                  <span className="font-medium">{placement.archetype}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
