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
  RegionFilter,
  DateRangePicker,
} from "@/components/meta";
import { metaApi } from "@/lib/api";
import type {
  Region,
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

export default function MetaPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Parse URL params with defaults
  const initialRegion = (searchParams.get("region") as Region) || "global";
  const initialDays = parseInt(searchParams.get("days") || "30", 10);

  const [region, setRegion] = useState<Region>(initialRegion);
  const [dateRange, setDateRange] = useState({
    start: startOfDay(subDays(new Date(), initialDays)),
    end: endOfDay(new Date()),
  });

  // Calculate days from date range
  const days = useMemo(() => {
    const diffMs = dateRange.end.getTime() - dateRange.start.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }, [dateRange]);

  // Update URL when filters change
  const updateUrl = (newRegion: Region, newDays: number) => {
    const params = new URLSearchParams();
    if (newRegion !== "global") params.set("region", newRegion);
    if (newDays !== 30) params.set("days", String(newDays));
    const query = params.toString();
    router.push(`/meta${query ? `?${query}` : ""}`);
  };

  const handleRegionChange = (newRegion: Region) => {
    setRegion(newRegion);
    updateUrl(newRegion, days);
  };

  const handleDateRangeChange = (newRange: { start: Date; end: Date }) => {
    setDateRange(newRange);
    const newDays = Math.ceil(
      (newRange.end.getTime() - newRange.start.getTime()) /
        (1000 * 60 * 60 * 24),
    );
    updateUrl(region, newDays);
  };

  // Fetch current meta snapshot
  const {
    data: currentMeta,
    isLoading: isLoadingCurrent,
    error: currentError,
  } = useQuery({
    queryKey: ["meta", "current", region],
    queryFn: () =>
      metaApi.getCurrent({
        region: region === "global" ? undefined : region,
        format: "standard",
        best_of: region === "JP" ? 1 : 3,
      }),
  });

  // Fetch meta history for trends
  const {
    data: metaHistory,
    isLoading: isLoadingHistory,
    error: historyError,
  } = useQuery({
    queryKey: ["meta", "history", region, days],
    queryFn: () =>
      metaApi.getHistory({
        region: region === "global" ? undefined : region,
        format: "standard",
        best_of: region === "JP" ? 1 : 3,
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
          <h1 className="text-3xl font-bold tracking-tight">Meta Dashboard</h1>
          <p className="text-muted-foreground">
            Explore the current competitive meta
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <RegionFilter
            value={region}
            onChange={handleRegionChange}
            className="w-[180px]"
          />
          <DateRangePicker value={dateRange} onChange={handleDateRangeChange} />
        </div>
      </div>

      {/* Error state */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load meta data. Please try again later.
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
                <CardTitle>Archetype Breakdown</CardTitle>
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
              <CardTitle>Meta Trends</CardTitle>
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
            <h2 className="mb-4 text-2xl font-semibold">Top Archetypes</h2>
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
