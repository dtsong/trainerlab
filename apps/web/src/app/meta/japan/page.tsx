"use client";

import { Suspense, useState, useMemo, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  subDays,
  endOfDay,
  startOfDay,
  format,
  differenceInHours,
} from "date-fns";
import { useSearchParams, useRouter, usePathname } from "next/navigation";

import { Clock } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  MetaPieChart,
  MetaTrendChart,
  DateRangePicker,
  TournamentTypeFilter,
  TournamentTrackNav,
  BO1ContextBanner,
  ChartErrorBoundary,
} from "@/components/meta";
import {
  CityLeagueResultsFeed,
  CardCountEvolutionSection,
  CardAdoptionRates,
  UpcomingCards,
  RotationBriefingHeader,
  JPAnalysisTab,
} from "@/components/japan";
import { ConfidenceBadge } from "@/components/ui/confidence-badge";
import { metaApi } from "@/lib/api";
import {
  transformSnapshot,
  parseDays,
  parseTournamentType,
  getErrorMessage,
} from "@/lib/meta-utils";
import { buildPathWithQuery, mergeSearchParams } from "@/lib/url-state";
import { useArchetypeDetail } from "@/hooks/useMeta";
import { Button } from "@/components/ui/button";
import { CardReference } from "@/components/cards/CardReference";
import type {
  MetaSnapshot,
  Archetype,
  TournamentType,
} from "@trainerlab/shared-types";

/** JP Nihil Zero rotation date — all post-rotation data starts here. */
const JP_ROTATION_DATE = new Date("2026-01-23");
const TAB_VALUES = ["overview", "analysis"] as const;

/** Compute days since JP rotation for default lookback. */
function daysSinceRotation(): number {
  const now = new Date();
  const diffMs = now.getTime() - JP_ROTATION_DATE.getTime();
  return Math.max(1, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}

function JapanMetaPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const getTournamentTypeFromPath = (path: string): TournamentType | null => {
    if (path.endsWith("/official")) return "official";
    if (path.endsWith("/grassroots")) return "grassroots";
    return null;
  };

  const getJapanMetaPathByType = (type: TournamentType): string => {
    if (type === "official") return "/meta/japan/official";
    if (type === "grassroots") return "/meta/japan/grassroots";
    return "/meta/japan";
  };

  const defaultDays = daysSinceRotation();
  const rawDays = searchParams.get("days");
  const urlDays = rawDays ? parseDays(rawDays, defaultDays) : defaultDays;
  const tabParam = searchParams.get("tab");
  const activeTab: (typeof TAB_VALUES)[number] = TAB_VALUES.includes(
    tabParam as (typeof TAB_VALUES)[number]
  )
    ? (tabParam as (typeof TAB_VALUES)[number])
    : "overview";
  const pathTournamentType = getTournamentTypeFromPath(pathname);
  const urlTournamentType =
    pathTournamentType ??
    parseTournamentType(searchParams.get("tournament_type"));

  const [tournamentType, setTournamentType] =
    useState<TournamentType>(urlTournamentType);
  const [dateRange, setDateRange] = useState({
    start: startOfDay(subDays(new Date(), urlDays)),
    end: endOfDay(new Date()),
  });

  const tournamentTypeCopy: Record<TournamentType, string> = {
    all: "What's winning in the SV9+ format — competitive prep & innovation scouting",
    official:
      "Official JP tournaments only — high-stakes signal for major-event preparation",
    grassroots:
      "Grassroots JP tournaments only — innovation and local adaptation discovery",
  };

  const days = useMemo(() => {
    const diffMs = dateRange.end.getTime() - dateRange.start.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }, [dateRange]);

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

  const updateUrl = useCallback(
    (params: {
      days?: number;
      tab?: string;
      tournament_type?: TournamentType;
      navigationMode?: "replace" | "push";
    }) => {
      const query = mergeSearchParams(
        searchParams,
        {
          days: params.days,
          tab: params.tab,
          tournament_type: null,
        },
        { days: defaultDays, tab: "overview" }
      );
      const basePath = getJapanMetaPathByType(
        params.tournament_type ?? tournamentType
      );
      const href = buildPathWithQuery(basePath, query);

      if (params.navigationMode === "replace") {
        router.replace(href, { scroll: false });
        return;
      }

      router.push(href, { scroll: false });
    },
    [defaultDays, router, searchParams, tournamentType]
  );

  const handleDateRangeChange = (newRange: { start: Date; end: Date }) => {
    setDateRange(newRange);
    const newDays = Math.ceil(
      (newRange.end.getTime() - newRange.start.getTime()) /
        (1000 * 60 * 60 * 24)
    );
    updateUrl({ days: newDays, navigationMode: "replace" });
  };

  const handleTabChange = (value: string) => {
    updateUrl({ tab: value });
  };

  const handleTournamentTypeChange = (newType: TournamentType) => {
    setTournamentType(newType);
    updateUrl({ tournament_type: newType, navigationMode: "push" });
  };

  // Era label for post-rotation JP data scoping
  const era = "post-nihil-zero";

  // Fetch current Japan meta snapshot (BO1, era-scoped)
  const {
    data: currentMeta,
    isLoading: isLoadingCurrent,
    error: currentError,
    refetch: refetchCurrent,
  } = useQuery({
    queryKey: ["meta", "current", "JP", 1, era, tournamentType],
    queryFn: () =>
      metaApi.getCurrent({
        region: "JP",
        format: "standard",
        best_of: 1,
        era,
        tournament_type: tournamentType,
      }),
  });

  // Fetch Japan meta history for trends (BO1, era-scoped)
  const {
    data: metaHistory,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ["meta", "history", "JP", 1, days, era, tournamentType],
    queryFn: () =>
      metaApi.getHistory({
        region: "JP",
        format: "standard",
        best_of: 1,
        days,
        era,
        tournament_type: tournamentType,
      }),
  });

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
    })) ?? [];

  const snapshots: MetaSnapshot[] =
    metaHistory?.snapshots.map(transformSnapshot) ?? [];

  const isLoadingMeta = isLoadingCurrent || isLoadingHistory;
  const metaError = currentError || historyError;

  // Card count evolution: archetype list and selection
  const archetypeNames = archetypes.map((a) => a.name);
  const [selectedArchetype, setSelectedArchetype] = useState<string>("");
  const effectiveArchetype = selectedArchetype || archetypeNames[0] || "";

  // Tech Card Insights: archetype selector for top 5
  const [techArchetype, setTechArchetype] = useState<string | null>(null);
  const top5Archetypes = archetypeNames.slice(0, 5);
  const effectiveTechArchetype = techArchetype || top5Archetypes[0] || null;
  const { data: archetypeDetail, isLoading: isLoadingDetail } =
    useArchetypeDetail(effectiveTechArchetype, {
      region: "JP",
      format: "standard",
      best_of: 1,
    });

  // Format dates for feed filtering
  const startDateStr = format(dateRange.start, "yyyy-MM-dd");
  const endDateStr = format(dateRange.end, "yyyy-MM-dd");

  // Data freshness: check if latest snapshot is >48 hours old
  const dataStaleHours = useMemo(() => {
    if (!currentMeta?.snapshot_date) return null;
    const snapshotDate = new Date(currentMeta.snapshot_date);
    return differenceInHours(new Date(), snapshotDate);
  }, [currentMeta?.snapshot_date]);

  return (
    <div className="space-y-8">
      {/* Rotation Briefing Header */}
      <RotationBriefingHeader phase="post-rotation" />

      {/* Header row with controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Post-Rotation Japan
          </h1>
          <p className="text-muted-foreground">
            {tournamentTypeCopy[tournamentType]}
          </p>
          <TournamentTrackNav
            basePath="/meta/japan"
            activeType={tournamentType}
            className="mt-3"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <TournamentTypeFilter
            value={tournamentType}
            onChange={handleTournamentTypeChange}
            className="w-[220px]"
          />
          <DateRangePicker value={dateRange} onChange={handleDateRangeChange} />
        </div>
      </div>

      {/* Data freshness warning */}
      {dataStaleHours !== null && dataStaleHours > 48 && (
        <div
          className="flex items-center gap-2 rounded-md border border-orange-500/30 bg-orange-500/10 px-3 py-2 text-xs text-orange-700 dark:text-orange-300"
          data-testid="data-freshness-warning"
        >
          <Clock className="h-3.5 w-3.5 shrink-0" />
          <span>
            Data may be stale — last snapshot is{" "}
            {Math.floor(dataStaleHours / 24)} days old
          </span>
        </div>
      )}

      {/* BO1 Context Banner (dismissible) */}
      <BO1ContextBanner />

      {/* Tabbed Layout */}
      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="w-full"
      >
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="overview">Meta Overview</TabsTrigger>
          <TabsTrigger value="analysis">JP Analysis</TabsTrigger>
        </TabsList>

        {/* Tab 1: Meta Overview */}
        <TabsContent value="overview" className="mt-6 space-y-10">
          {/* Meta Snapshot (pie + trends) */}
          <section>
            <div className="mb-4 flex items-center gap-3">
              <h2 className="text-xl font-semibold">
                What&apos;s Winning in Post-Rotation
              </h2>
              {currentMeta && (
                <ConfidenceBadge
                  confidence={
                    currentMeta.sample_size >= 200
                      ? "high"
                      : currentMeta.sample_size >= 50
                        ? "medium"
                        : "low"
                  }
                  sampleSize={currentMeta.sample_size}
                />
              )}
            </div>
            {metaError && (
              <Card className="border-destructive">
                <CardContent className="pt-6">
                  <p className="font-medium text-destructive">
                    Failed to load Japan meta data
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {getErrorMessage(metaError, "Japan meta")}
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

            {isLoadingMeta && !metaError && (
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
                    <CardTitle>Meta Trends</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[350px] animate-pulse rounded bg-muted" />
                  </CardContent>
                </Card>
              </div>
            )}

            {!isLoadingMeta && !metaError && (
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Archetype Breakdown (BO1)</CardTitle>
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
                    <CardTitle>Meta Trends (BO1)</CardTitle>
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
              </div>
            )}
          </section>

          {/* Trend Chart (already in pie/trends above) */}

          {/* Tech Card Insights */}
          {top5Archetypes.length > 0 && (
            <section>
              <h2 className="mb-4 text-xl font-semibold">Tech Card Insights</h2>
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap gap-2">
                    {top5Archetypes.map((name) => (
                      <Button
                        key={name}
                        variant={
                          name === effectiveTechArchetype
                            ? "default"
                            : "outline"
                        }
                        size="sm"
                        onClick={() => setTechArchetype(name)}
                      >
                        {name}
                      </Button>
                    ))}
                  </div>
                </CardHeader>
                <CardContent>
                  {isLoadingDetail && (
                    <div className="space-y-2">
                      <div className="h-4 w-48 animate-pulse rounded bg-muted" />
                      <div className="h-4 w-64 animate-pulse rounded bg-muted" />
                      <div className="h-4 w-56 animate-pulse rounded bg-muted" />
                    </div>
                  )}
                  {!isLoadingDetail && archetypeDetail && (
                    <div className="space-y-4">
                      {archetypeDetail.key_cards.filter(
                        (c) => c.inclusion_rate > 0.8
                      ).length > 0 && (
                        <div>
                          <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                            Core ({">"} 80% inclusion)
                          </h4>
                          <div className="space-y-1">
                            {archetypeDetail.key_cards
                              .filter((c) => c.inclusion_rate > 0.8)
                              .map((card) => (
                                <div
                                  key={card.card_id}
                                  className="flex items-center justify-between rounded-md px-3 py-1.5 text-sm odd:bg-muted/50"
                                >
                                  <CardReference
                                    cardId={card.card_id}
                                    cardName={card.card_name}
                                    imageSmall={card.image_small}
                                    variant="inline"
                                    showThumbnail
                                  />
                                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <span>
                                      {(card.inclusion_rate * 100).toFixed(0)}%
                                      included
                                    </span>
                                    <span>
                                      ~{card.avg_copies.toFixed(1)} copies
                                    </span>
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {archetypeDetail.key_cards.filter(
                        (c) => c.inclusion_rate <= 0.8
                      ).length > 0 && (
                        <div>
                          <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                            Tech (flex slots)
                          </h4>
                          <div className="space-y-1">
                            {archetypeDetail.key_cards
                              .filter((c) => c.inclusion_rate <= 0.8)
                              .map((card) => (
                                <div
                                  key={card.card_id}
                                  className="flex items-center justify-between rounded-md px-3 py-1.5 text-sm odd:bg-muted/50"
                                >
                                  <CardReference
                                    cardId={card.card_id}
                                    cardName={card.card_name}
                                    imageSmall={card.image_small}
                                    variant="inline"
                                    showThumbnail
                                  />
                                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <span>
                                      {(card.inclusion_rate * 100).toFixed(0)}%
                                      included
                                    </span>
                                    <span>
                                      ~{card.avg_copies.toFixed(1)} copies
                                    </span>
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {archetypeDetail.key_cards.length === 0 && (
                        <p className="text-sm text-muted-foreground">
                          No card data available for this archetype
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </section>
          )}

          {/* Card Intelligence */}
          <section>
            <h2 className="mb-4 text-xl font-semibold">Card Intelligence</h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <CardAdoptionRates days={days} limit={15} />
              <UpcomingCards limit={8} />
            </div>
          </section>

          {/* City League Results */}
          <section>
            <CityLeagueResultsFeed
              startDate={startDateStr}
              endDate={endDateStr}
            />
          </section>

          {/* Card Count Evolution */}
          <section>
            <CardCountEvolutionSection
              archetypes={archetypeNames}
              selectedArchetype={effectiveArchetype}
              onArchetypeChange={setSelectedArchetype}
            />
          </section>
        </TabsContent>

        {/* Tab 2: JP Analysis */}
        <TabsContent value="analysis" className="mt-6">
          <JPAnalysisTab era="post-nihil-zero" />
        </TabsContent>
      </Tabs>

      {/* Footer Attribution */}
      <footer className="border-t pt-4 pb-8">
        <p className="text-center text-xs text-muted-foreground">
          Data sourced from{" "}
          <a
            href="https://limitlesstcg.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground"
          >
            Limitless TCG
          </a>
          {" · "}
          <a
            href="https://pokecabook.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground"
          >
            Pokecabook
          </a>
          {" · "}
          <a
            href="https://pokekameshi.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground"
          >
            Pokekameshi
          </a>
        </p>
      </footer>
    </div>
  );
}

function JapanMetaPageLoading() {
  return (
    <div className="space-y-8">
      <div className="h-24 animate-pulse rounded-lg bg-muted" />
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="h-9 w-48 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-5 w-80 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-10 w-[240px] animate-pulse rounded bg-muted" />
      </div>
      <div className="h-10 w-64 animate-pulse rounded bg-muted" />
      <div className="grid gap-6 md:grid-cols-2">
        <div className="h-[400px] animate-pulse rounded bg-muted" />
        <div className="h-[400px] animate-pulse rounded bg-muted" />
      </div>
      <div className="h-64 animate-pulse rounded bg-muted" />
      <div className="h-64 animate-pulse rounded bg-muted" />
    </div>
  );
}

export default function JapanMetaPage() {
  return (
    <Suspense fallback={<JapanMetaPageLoading />}>
      <JapanMetaPageContent />
    </Suspense>
  );
}
