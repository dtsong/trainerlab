"use client";

import { Suspense, useState, useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
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
  ChartErrorBoundary,
} from "@/components/meta";
import { metaApi } from "@/lib/api";
import {
  transformSnapshot,
  parseRegion,
  parseDays,
  getErrorMessage,
} from "@/lib/meta-utils";
import { Button } from "@/components/ui/button";
import type {
  Region,
  MetaSnapshot,
  Archetype,
  CardUsageSummary,
} from "@trainerlab/shared-types";

function MetaPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Parse URL params with validation
  const initialRegion = parseRegion(searchParams.get("region"));
  const initialDays = parseDays(searchParams.get("days"));

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
        (1000 * 60 * 60 * 24)
    );
    updateUrl(region, newDays);
  };

  // Fetch current meta snapshot and history in parallel
  // Japan uses Best-of-1 format; all other regions use Best-of-3
  const bestOf = region === "JP" ? 1 : 3;

  const [currentMetaQuery, metaHistoryQuery] = useQueries({
    queries: [
      {
        queryKey: ["meta", "current", region],
        queryFn: () =>
          metaApi.getCurrent({
            region: region === "global" ? undefined : region,
            format: "standard",
            best_of: bestOf,
          }),
      },
      {
        queryKey: ["meta", "history", region, days],
        queryFn: () =>
          metaApi.getHistory({
            region: region === "global" ? undefined : region,
            format: "standard",
            best_of: bestOf,
            days,
          }),
      },
    ],
  });

  const {
    data: currentMeta,
    isLoading: isLoadingCurrent,
    error: currentError,
    refetch: refetchCurrent,
  } = currentMetaQuery;

  const {
    data: metaHistory,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory,
  } = metaHistoryQuery;

  const handleRetry = () => {
    refetchCurrent();
    refetchHistory();
  };

  // Transform API data
  const archetypes: Archetype[] =
    currentMeta?.archetype_breakdown.map((a) => ({
      name: a.name,
      share: a.share,
      keyCards: a.key_cards ?? undefined,
    })) ?? [];

  const cardUsage: CardUsageSummary[] =
    currentMeta?.card_usage.map((c) => ({
      cardId: c.card_id,
      inclusionRate: c.inclusion_rate,
      avgCopies: c.avg_copies,
    })) ?? [];

  const snapshots: MetaSnapshot[] =
    metaHistory?.snapshots.map(transformSnapshot) ?? [];

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
            <p className="font-medium text-destructive">
              Failed to load meta data
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {getErrorMessage(error)}
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={handleRetry}
            >
              Try Again
            </Button>
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
              <div className="h-[280px] md:h-[350px] animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Top Cards</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[280px] md:h-[350px] animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts section */}
      {!isLoading && !error && (
        <>
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Archetype Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                {archetypes.length > 0 ? (
                  <ChartErrorBoundary chartName="MetaPieChart">
                    <MetaPieChart data={archetypes} />
                  </ChartErrorBoundary>
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
                  <ChartErrorBoundary chartName="MetaBarChart">
                    <MetaBarChart data={cardUsage} limit={10} />
                  </ChartErrorBoundary>
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
                <ChartErrorBoundary chartName="MetaTrendChart">
                  <MetaTrendChart snapshots={snapshots} />
                </ChartErrorBoundary>
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
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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

function MetaPageLoading() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="h-9 w-48 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-5 w-64 animate-pulse rounded bg-muted" />
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="h-10 w-[180px] animate-pulse rounded bg-muted" />
          <div className="h-10 w-[200px] animate-pulse rounded bg-muted" />
        </div>
      </div>
      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Archetype Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] md:h-[350px] animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Top Cards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] md:h-[350px] animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function MetaPage() {
  return (
    <Suspense fallback={<MetaPageLoading />}>
      <MetaPageContent />
    </Suspense>
  );
}
