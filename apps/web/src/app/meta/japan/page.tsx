"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { subDays, endOfDay, startOfDay } from "date-fns";
import { useSearchParams, useRouter } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MetaPieChart,
  MetaBarChart,
  MetaTrendChart,
  ArchetypeCard,
  DateRangePicker,
  BO1ContextBanner,
} from "@/components/meta";
import { metaApi } from "@/lib/api";
import type {
  MetaSnapshot,
  Archetype,
  CardUsageSummary,
} from "@trainerlab/shared-types";

function transformSnapshot(data: {
  snapshot_date: string;
  region: string | null;
  format: "standard" | "expanded";
  best_of: 1 | 3;
  archetype_breakdown: {
    name: string;
    share: number;
    key_cards?: string[] | null;
  }[];
  card_usage: { card_id: string; inclusion_rate: number; avg_copies: number }[];
  sample_size: number;
}): MetaSnapshot {
  return {
    snapshotDate: data.snapshot_date,
    region: data.region,
    format: data.format,
    bestOf: data.best_of,
    archetypeBreakdown: data.archetype_breakdown.map((a) => ({
      name: a.name,
      share: a.share,
      keyCards: a.key_cards ?? undefined,
    })),
    cardUsage: data.card_usage.map((c) => ({
      cardId: c.card_id,
      inclusionRate: c.inclusion_rate,
      avgCopies: c.avg_copies,
    })),
    sampleSize: data.sample_size,
  };
}

export default function JapanMetaPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialDays = parseInt(searchParams.get("days") || "30", 10);

  const [dateRange, setDateRange] = useState({
    start: startOfDay(subDays(new Date(), initialDays)),
    end: endOfDay(new Date()),
  });

  const days = useMemo(() => {
    const diffMs = dateRange.end.getTime() - dateRange.start.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }, [dateRange]);

  const updateUrl = (newDays: number) => {
    const params = new URLSearchParams();
    if (newDays !== 30) params.set("days", String(newDays));
    const query = params.toString();
    router.push(`/meta/japan${query ? `?${query}` : ""}`);
  };

  const handleDateRangeChange = (newRange: { start: Date; end: Date }) => {
    setDateRange(newRange);
    const newDays = Math.ceil(
      (newRange.end.getTime() - newRange.start.getTime()) /
        (1000 * 60 * 60 * 24),
    );
    updateUrl(newDays);
  };

  // Fetch current Japan meta snapshot (BO1)
  const {
    data: currentMeta,
    isLoading: isLoadingCurrent,
    error: currentError,
  } = useQuery({
    queryKey: ["meta", "current", "JP", 1],
    queryFn: () =>
      metaApi.getCurrent({
        region: "JP",
        format: "standard",
        best_of: 1,
      }),
  });

  // Fetch Japan meta history for trends (BO1)
  const {
    data: metaHistory,
    isLoading: isLoadingHistory,
    error: historyError,
  } = useQuery({
    queryKey: ["meta", "history", "JP", 1, days],
    queryFn: () =>
      metaApi.getHistory({
        region: "JP",
        format: "standard",
        best_of: 1,
        days,
      }),
  });

  // Transform API data
  const archetypes: Archetype[] =
    currentMeta?.archetype_breakdown.map((a) => ({
      name: a.name,
      share: a.share,
      keyCards: a.key_cards ?? undefined,
    })) || [];

  const cardUsage: CardUsageSummary[] =
    currentMeta?.card_usage.map((c) => ({
      cardId: c.card_id,
      inclusionRate: c.inclusion_rate,
      avgCopies: c.avg_copies,
    })) || [];

  const snapshots: MetaSnapshot[] =
    metaHistory?.snapshots.map(transformSnapshot) || [];

  const isLoading = isLoadingCurrent || isLoadingHistory;
  const error = currentError || historyError;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Japan Meta Dashboard
          </h1>
          <p className="text-muted-foreground">
            Best-of-1 competitive meta analysis
          </p>
        </div>
        <div className="flex gap-3">
          <DateRangePicker value={dateRange} onChange={handleDateRangeChange} />
        </div>
      </div>

      {/* BO1 Context Banner */}
      <BO1ContextBanner />

      {/* Error state */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load Japan meta data. Please try again later.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Loading state */}
      {isLoading && !error && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Archetype Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[350px] animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Top Cards</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[350px] animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts section */}
      {!isLoading && !error && (
        <>
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Archetype Breakdown (BO1)</CardTitle>
              </CardHeader>
              <CardContent>
                {archetypes.length > 0 ? (
                  <MetaPieChart data={archetypes} />
                ) : (
                  <p className="py-12 text-center text-muted-foreground">
                    No archetype data available
                  </p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Top Cards by Inclusion Rate</CardTitle>
              </CardHeader>
              <CardContent>
                {cardUsage.length > 0 ? (
                  <MetaBarChart data={cardUsage} limit={10} />
                ) : (
                  <p className="py-12 text-center text-muted-foreground">
                    No card usage data available
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Trend chart */}
          <Card>
            <CardHeader>
              <CardTitle>Japan Meta Trends (BO1)</CardTitle>
            </CardHeader>
            <CardContent>
              {snapshots.length > 1 ? (
                <MetaTrendChart snapshots={snapshots} />
              ) : (
                <p className="py-12 text-center text-muted-foreground">
                  Not enough historical data for trends
                </p>
              )}
            </CardContent>
          </Card>

          {/* Archetype cards grid */}
          <section>
            <h2 className="mb-4 text-2xl font-semibold">
              Top Japan Archetypes
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {archetypes.slice(0, 8).map((archetype) => (
                <ArchetypeCard key={archetype.name} archetype={archetype} />
              ))}
            </div>
            {archetypes.length === 0 && (
              <p className="py-8 text-center text-muted-foreground">
                No archetypes available
              </p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
