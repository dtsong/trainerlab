"use client";

import {
  AlertCircle,
  CalendarDays,
  ExternalLink,
  MapPin,
  RefreshCw,
  Users,
} from "lucide-react";
import Link from "next/link";
import { use } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTournament } from "@/hooks/useTournaments";
import {
  getMajorFormatBadgeText,
  isOfficialMajorTier,
} from "@/lib/official-majors";

interface TournamentDetailPageProps {
  params: Promise<{ id: string }>;
}

const tierColors: Record<string, string> = {
  major: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  premier: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  league: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

export default function TournamentDetailPage({
  params,
}: TournamentDetailPageProps) {
  const { id } = use(params);
  const { data: tournament, isLoading, isError, refetch } = useTournament(id);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-96 bg-muted rounded" />
          <div className="h-4 w-64 bg-muted rounded" />
          <div className="grid gap-4 lg:grid-cols-3 mt-8">
            <div className="lg:col-span-2 h-96 bg-muted rounded-lg" />
            <div className="h-48 bg-muted rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !tournament) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load tournament</p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const date = new Date(tournament.date);
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  const majorFormatBadgeText = getMajorFormatBadgeText(
    tournament.major_format_key,
    tournament.major_format_label
  );
  const shouldShowMajorFormatBadge = Boolean(
    isOfficialMajorTier(tournament.tier) && majorFormatBadgeText
  );

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">{tournament.name}</h1>
            <div className="flex flex-wrap items-center gap-4 text-muted-foreground">
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
                  <span>{tournament.participant_count} players</span>
                </div>
              )}
            </div>
          </div>
          {tournament.tier && (
            <Badge
              variant="outline"
              className={tierColors[tournament.tier] || tierColors.league}
            >
              {tournament.tier}
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{tournament.format}</Badge>
          <Badge variant="outline">BO{tournament.best_of}</Badge>
          {shouldShowMajorFormatBadge && (
            <Badge
              variant="outline"
              title={tournament.major_format_label ?? undefined}
              aria-label={`Major format window ${majorFormatBadgeText ?? ""}`}
            >
              {majorFormatBadgeText ?? ""}
            </Badge>
          )}
          {tournament.source_url && (
            <a
              href={tournament.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              Source
            </a>
          )}
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Placements */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-y divide-border">
                {tournament.placements.map((placement) => (
                  <div
                    key={placement.id}
                    className="flex items-center justify-between py-3"
                  >
                    <div className="flex items-center gap-4">
                      <span
                        className={`w-8 text-center font-bold ${
                          placement.placement <= 3
                            ? "text-primary"
                            : "text-muted-foreground"
                        }`}
                      >
                        #{placement.placement}
                      </span>
                      <div>
                        <div className="font-medium">{placement.archetype}</div>
                        {placement.player_name && (
                          <div className="text-sm text-muted-foreground">
                            {placement.player_name}
                          </div>
                        )}
                      </div>
                    </div>
                    {placement.has_decklist && (
                      <Badge variant="secondary">Decklist</Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Meta Breakdown */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Meta Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {tournament.meta_breakdown.slice(0, 10).map((meta) => (
                  <div key={meta.archetype}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">
                        {meta.archetype}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {(meta.share * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${meta.share * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="mt-8">
        <Link
          href="/tournaments"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to Tournaments
        </Link>
      </div>
    </div>
  );
}
