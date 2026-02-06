"use client";

import { Suspense, useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { subDays, endOfDay, startOfDay, format } from "date-fns";
import { useSearchParams, useRouter } from "next/navigation";

import { AlertTriangle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MetaPieChart,
  MetaTrendChart,
  DateRangePicker,
  BO1ContextBanner,
  ChartErrorBoundary,
} from "@/components/meta";
import {
  CardInnovationTracker,
  NewArchetypeWatch,
  CityLeagueResultsFeed,
  MetaDivergenceComparison,
  CardCountEvolutionSection,
  CardAdoptionRates,
  UpcomingCards,
} from "@/components/japan";
import { ConfidenceBadge } from "@/components/ui/confidence-badge";
import { metaApi } from "@/lib/api";
import {
  transformSnapshot,
  parseDays,
  getErrorMessage,
} from "@/lib/meta-utils";
import { useArchetypeDetail } from "@/hooks/useMeta";
import { Button } from "@/components/ui/button";
import type { MetaSnapshot, Archetype } from "@trainerlab/shared-types";

function JapanMetaPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialDays = parseDays(searchParams.get("days"));

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
        (1000 * 60 * 60 * 24)
    );
    updateUrl(newDays);
  };

  // Fetch current Japan meta snapshot (BO1)
  const {
    data: currentMeta,
    isLoading: isLoadingCurrent,
    error: currentError,
    refetch: refetchCurrent,
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
    refetch: refetchHistory,
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

  // Default to top archetype when data loads
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

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">From Japan</h1>
          <p className="text-muted-foreground">
            JP metagame intelligence — competitive prep &amp; innovation
            scouting
          </p>
        </div>
        <DateRangePicker value={dateRange} onChange={handleDateRangeChange} />
      </div>

      {/* Persistent BO1 context strip */}
      <div
        className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300"
        data-testid="bo1-context-strip"
      >
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span>
          All Japan data uses <strong>Best-of-1</strong> format — ties count as
          double losses
        </span>
      </div>

      {/* BO1 Context Banner */}
      <BO1ContextBanner />

      {/* Section 1: JP vs EN Divergence */}
      <section>
        <MetaDivergenceComparison />
      </section>

      {/* Section 2: JP Meta Overview */}
      <section>
        <div className="mb-4 flex items-center gap-3">
          <h2 className="text-xl font-semibold">JP Meta Overview (BO1)</h2>
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

      {/* Section 2.5: Tech Card Insights */}
      {top5Archetypes.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Tech Card Insights</h2>
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-wrap gap-2">
                {top5Archetypes.map((name) => (
                  <Button
                    key={name}
                    variant={
                      name === effectiveTechArchetype ? "default" : "outline"
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
                  {/* Core cards (>80% inclusion) */}
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
                              <span className="font-medium">
                                {card.card_id}
                              </span>
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

                  {/* Tech cards (<=80% inclusion) */}
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
                              <span className="font-medium">
                                {card.card_id}
                              </span>
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

      {/* Section 3: Card Adoption & Upcoming Cards */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Card Intelligence</h2>
        <div className="grid gap-6 lg:grid-cols-2">
          <CardAdoptionRates days={days} limit={15} />
          <UpcomingCards limit={8} />
        </div>
      </section>

      {/* Section 4: City League Results */}
      <section>
        <CityLeagueResultsFeed startDate={startDateStr} endDate={endDateStr} />
      </section>

      {/* Section 5: Card Count Evolution */}
      <section>
        <CardCountEvolutionSection
          archetypes={archetypeNames}
          selectedArchetype={effectiveArchetype}
          onArchetypeChange={setSelectedArchetype}
        />
      </section>

      {/* Section 6: Card Innovation Tracker */}
      <section>
        <CardInnovationTracker limit={20} />
      </section>

      {/* Section 7: New Archetype Watch */}
      <section>
        <NewArchetypeWatch limit={9} />
      </section>

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
        </p>
      </footer>
    </div>
  );
}

function JapanMetaPageLoading() {
  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="h-9 w-48 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-5 w-80 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-10 w-[240px] animate-pulse rounded bg-muted" />
      </div>
      <div className="h-20 animate-pulse rounded bg-muted" />
      <div className="grid gap-6 md:grid-cols-2">
        <div className="h-[400px] animate-pulse rounded bg-muted" />
        <div className="h-[400px] animate-pulse rounded bg-muted" />
      </div>
      <div className="h-64 animate-pulse rounded bg-muted" />
      <div className="h-64 animate-pulse rounded bg-muted" />
      <div className="h-96 animate-pulse rounded bg-muted" />
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
