"use client";

import { AlertCircle, RefreshCw, Trophy } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { DataFreshnessBanner } from "@/components/meta";
import { useTournaments } from "@/hooks/useTournaments";
import type { TournamentSearchParams } from "@/lib/api";

import { TournamentRow } from "./TournamentRow";

interface TournamentListProps {
  apiParams: TournamentSearchParams;
  page: number;
  onPageChange: (page: number) => void;
  showRegion?: boolean;
  showMajorFormatBadge?: boolean;
}

export function TournamentList({
  apiParams,
  page,
  onPageChange,
  showRegion = true,
  showMajorFormatBadge = false,
}: TournamentListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    setExpandedId(null);
  }, [apiParams, page]);

  const { data, isLoading, isError, refetch } = useTournaments({
    ...apiParams,
    page,
    limit: 20,
    sort_by: "date",
    order: "desc",
  });

  if (isLoading) {
    return (
      <div className="rounded-lg border">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-4 px-4 py-3 border-b last:border-0"
          >
            <div className="h-4 w-16 bg-muted rounded animate-pulse" />
            <div className="h-4 flex-1 bg-muted rounded animate-pulse" />
            <div className="h-5 w-24 bg-muted rounded animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Card className="border-destructive">
        <CardContent className="py-8 text-center">
          <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
          <p className="text-destructive mb-4">Failed to load tournaments</p>
          <Button onClick={() => refetch()} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data?.items.length) {
    return (
      <div className="space-y-4">
        {data?.freshness && <DataFreshnessBanner freshness={data.freshness} />}
        <Card>
          <CardContent className="py-12 text-center">
            <Trophy className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No tournaments found matching your filters.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data.freshness && <DataFreshnessBanner freshness={data.freshness} />}
      <div className="rounded-lg border">
        {data.items.map((tournament) => (
          <TournamentRow
            key={tournament.id}
            tournament={tournament}
            expanded={expandedId === tournament.id}
            onToggle={() =>
              setExpandedId(expandedId === tournament.id ? null : tournament.id)
            }
            showRegion={showRegion}
            showMajorFormatBadge={showMajorFormatBadge}
          />
        ))}
      </div>

      {(data.has_prev || data.has_next) && (
        <div className="flex items-center justify-center gap-4 mt-6">
          <Button
            variant="outline"
            size="sm"
            disabled={!data.has_prev}
            onClick={() => {
              onPageChange(page - 1);
              setExpandedId(null);
            }}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.page} of {Math.ceil(data.total / data.limit)}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!data.has_next}
            onClick={() => {
              onPageChange(page + 1);
              setExpandedId(null);
            }}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
