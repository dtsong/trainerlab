"use client";

import { Suspense, useState, useMemo, useEffect } from "react";
import { useQueries } from "@tanstack/react-query";
import { subDays, endOfDay, startOfDay } from "date-fns";
import { useSearchParams, useRouter, usePathname } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MetaPieChart,
  MetaBarChart,
  MetaTrendChart,
  ArchetypeCard,
  RegionFilter,
  TournamentTypeFilter,
  TournamentTrackNav,
  DateRangePicker,
  DataFreshnessBanner,
  ChartErrorBoundary,
} from "@/components/meta";
import { metaApi } from "@/lib/api";
import {
  transformSnapshot,
  parseRegion,
  parseDays,
  parseTournamentType,
  getErrorMessage,
} from "@/lib/meta-utils";
import { buildPathWithQuery, mergeSearchParams } from "@/lib/url-state";
import { Button } from "@/components/ui/button";
import type {
  Region,
  TournamentType,
  MetaSnapshot,
  Archetype,
  CardUsageSummary,
} from "@trainerlab/shared-types";

function MetaPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const getTournamentTypeFromPath = (path: string): TournamentType | null => {
    if (path.endsWith("/official")) return "official";
    if (path.endsWith("/grassroots")) return "grassroots";
    return null;
  };

  const getMetaPathByType = (type: TournamentType): string => {
    if (type === "official") return "/meta/official";
    if (type === "grassroots") return "/meta/grassroots";
    return "/meta";
  };

  // Parse URL params with validation
  const urlRegion = parseRegion(searchParams.get("region"));
  const urlDays = parseDays(searchParams.get("days"));
  const pathTournamentType = getTournamentTypeFromPath(pathname);
  const urlTournamentType =
    pathTournamentType ??
    parseTournamentType(searchParams.get("tournament_type"));

  const [region, setRegion] = useState<Region>(urlRegion);
  const [tournamentType, setTournamentType] =
    useState<TournamentType>(urlTournamentType);
  const [dateRange, setDateRange] = useState({
    start: startOfDay(subDays(new Date(), urlDays)),
    end: endOfDay(new Date()),
  });

  const tournamentTypeCopy: Record<
    TournamentType,
    { title: string; description: string }
  > = {
    all: {
      title: "Meta Dashboard",
      description: "Explore the full competitive meta across all events",
    },
    official: {
      title: "Official Meta Dashboard",
      description:
        "Regionals, Internationals, and Worlds-focused competitive signals",
    },
    grassroots: {
      title: "Grassroots Meta Dashboard",
      description:
        "League, local, and community tournament trends and experimentation",
    },
  };

  // Calculate days from date range
  const days = useMemo(() => {
    const diffMs = dateRange.end.getTime() - dateRange.start.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }, [dateRange]);

  useEffect(() => {
    if (region !== urlRegion) {
      setRegion(urlRegion);
    }
  }, [region, urlRegion]);

  useEffect(() => {
    if (tournamentType !== urlTournamentType) {
      setTournamentType(urlTournamentType);
    }
  }, [tournamentType, urlTournamentType]);

  useEffect(() => {
    if (days === urlDays) return;
    setDateRange({
      start: startOfDay(subDays(new Date(), urlDays)),
      end: endOfDay(new Date()),
    });
  }, [days, urlDays]);

  // Update URL when filters change
  const updateUrl = (
    newRegion: Region,
    newDays: number,
    newTournamentType: TournamentType = tournamentType,
    navigationMode: "replace" | "push" = "replace"
  ) => {
    const query = mergeSearchParams(
      searchParams,
      {
        region: newRegion,
        days: newDays,
        tournament_type: null,
      },
      { region: "global", days: 30 }
    );
    const basePath = getMetaPathByType(newTournamentType);
    const href = buildPathWithQuery(basePath, query);

    if (navigationMode === "push") {
      router.push(href, { scroll: false });
      return;
    }

    router.replace(href, { scroll: false });
  };

  const handleRegionChange = (newRegion: Region) => {
    setRegion(newRegion);
    updateUrl(newRegion, days);
  };

  const handleTournamentTypeChange = (newType: TournamentType) => {
    setTournamentType(newType);
    updateUrl(region, days, newType, "push");
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
        queryKey: ["meta", "current", region, tournamentType],
        queryFn: () =>
          metaApi.getCurrent({
            region: region === "global" ? undefined : region,
            format: "standard",
            best_of: bestOf,
            tournament_type: tournamentType,
          }),
      },
      {
        queryKey: ["meta", "history", region, days, tournamentType],
        queryFn: () =>
          metaApi.getHistory({
            region: region === "global" ? undefined : region,
            format: "standard",
            best_of: bestOf,
            days,
            tournament_type: tournamentType,
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
      spriteUrls: a.sprite_urls ?? undefined,
      signatureCardImage: a.signature_card_image ?? undefined,
    })) ?? [];

  const cardUsage: CardUsageSummary[] =
    currentMeta?.card_usage.map((c) => ({
      cardId: c.card_id,
      cardName: c.card_name ?? undefined,
      imageSmall: c.image_small ?? undefined,
      inclusionRate: c.inclusion_rate,
      avgCopies: c.avg_copies,
    })) ?? [];

  const cardNameMap = Object.fromEntries(
    cardUsage.filter((c) => c.cardName).map((c) => [c.cardId, c.cardName!])
  );

  const snapshots: MetaSnapshot[] =
    metaHistory?.snapshots.map(transformSnapshot) ?? [];

  const isLoading = isLoadingCurrent || isLoadingHistory;
  const error = currentError || historyError;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {tournamentTypeCopy[tournamentType].title}
          </h1>
          <p className="text-muted-foreground">
            {tournamentTypeCopy[tournamentType].description}
          </p>
          <TournamentTrackNav
            basePath="/meta"
            activeType={tournamentType}
            className="mt-3"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <RegionFilter
            value={region}
            onChange={handleRegionChange}
            className="w-[180px]"
          />
          <TournamentTypeFilter
            value={tournamentType}
            onChange={handleTournamentTypeChange}
            className="w-[220px]"
          />
          <DateRangePicker value={dateRange} onChange={handleDateRangeChange} />
        </div>
      </div>

      {!error && currentMeta?.freshness && (
        <DataFreshnessBanner freshness={currentMeta.freshness} />
      )}

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
                    <MetaBarChart
                      data={cardUsage}
                      cardNames={cardNameMap}
                      limit={10}
                    />
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
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
    <div className="space-y-6">
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
