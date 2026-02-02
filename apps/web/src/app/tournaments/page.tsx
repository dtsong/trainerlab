"use client";

import { AlertCircle, RefreshCw, Trophy } from "lucide-react";
import { useState } from "react";

import { TournamentCard, TournamentFilters } from "@/components/tournaments";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTournaments } from "@/hooks/useTournaments";

import type { TournamentTier } from "@trainerlab/shared-types";

export default function TournamentsPage() {
  const [region, setRegion] = useState<string>("all");
  const [format, setFormat] = useState<"standard" | "expanded" | "all">("all");
  const [tier, setTier] = useState<TournamentTier | "all">("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useTournaments({
    region: region === "all" ? undefined : region,
    format: format === "all" ? undefined : format,
    tier: tier === "all" ? undefined : tier,
    page,
    limit: 20,
  });

  const handleFilterChange = () => {
    setPage(1);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Tournaments</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-10 w-96 bg-muted rounded" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Tournaments</h1>
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
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <h1 className="text-3xl font-bold">Tournaments</h1>
        <TournamentFilters
          region={region}
          format={format}
          tier={tier}
          onRegionChange={(v) => {
            setRegion(v);
            handleFilterChange();
          }}
          onFormatChange={(v) => {
            setFormat(v);
            handleFilterChange();
          }}
          onTierChange={(v) => {
            setTier(v);
            handleFilterChange();
          }}
        />
      </div>

      {data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Trophy className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No tournaments found matching your filters.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((tournament) => (
              <TournamentCard key={tournament.id} tournament={tournament} />
            ))}
          </div>

          {data && (data.has_prev || data.has_next) && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <Button
                variant="outline"
                disabled={!data.has_prev}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {data.page} of {Math.ceil(data.total / data.limit)}
              </span>
              <Button
                variant="outline"
                disabled={!data.has_next}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
