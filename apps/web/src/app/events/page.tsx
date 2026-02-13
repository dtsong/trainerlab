"use client";

import {
  AlertCircle,
  ArrowRight,
  CalendarDays,
  RefreshCw,
  Trophy,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { EventCard, EventFilters } from "@/components/events";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useEvents } from "@/hooks/useEvents";
import {
  type MajorFormatFilterValue,
  type SeasonFilterValue,
} from "@/lib/official-majors";
import {
  getMajorFormatBadgeText,
  isOfficialMajorTier,
} from "@/lib/official-majors";

import type { ApiEventSummary } from "@trainerlab/shared-types";

const REGION_ORDER = ["NA", "EU", "JP", "LATAM", "OCE"] as const;
const REGION_LABELS: Record<string, string> = {
  NA: "North America",
  EU: "Europe",
  JP: "Japan",
  LATAM: "Latin America",
  OCE: "Oceania",
};

function formatEventDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function ChampionshipBanner({ events }: { events: ApiEventSummary[] }) {
  const top = events.slice(0, 3);
  if (top.length === 0) return null;

  return (
    <Card className="mb-6 overflow-hidden border-primary/30">
      <CardContent className="p-0">
        <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="p-6 bg-gradient-to-br from-primary/10 via-background to-background">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Trophy className="h-4 w-4" />
              <span>Championship Spotlight</span>
              <Badge variant="outline" className="ml-1">
                Official
              </Badge>
            </div>

            <div className="mt-3">
              <h2 className="text-xl sm:text-2xl font-semibold tracking-tight">
                {top[0]?.name}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {formatEventDate(top[0]?.date ?? "")} -{" "}
                {REGION_LABELS[top[0]?.region ?? ""] ?? top[0]?.region}
              </p>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2">
              {top[0]?.tier ? (
                <Badge variant="outline" className="capitalize">
                  {top[0].tier}
                </Badge>
              ) : null}
              {top[0]?.major_format_key || top[0]?.major_format_label ? (
                <Badge variant="outline">
                  {getMajorFormatBadgeText(
                    top[0].major_format_key,
                    top[0].major_format_label
                  ) ?? ""}
                </Badge>
              ) : null}
            </div>

            {top[0] ? (
              <div className="mt-5">
                <Button asChild>
                  <Link href={`/events/${top[0].id}`}>
                    View event
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Link>
                </Button>
              </div>
            ) : null}
          </div>

          <div className="p-6">
            <div className="text-sm font-medium">More upcoming majors</div>
            <div className="mt-3 space-y-3">
              {top.slice(1).map((e) => (
                <Link
                  key={e.id}
                  href={`/events/${e.id}`}
                  className="block rounded-lg border p-3 hover:border-primary/40 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium leading-snug line-clamp-2">
                        {e.name}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {formatEventDate(e.date)} -{" "}
                        {REGION_LABELS[e.region] ?? e.region}
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function EventsPage() {
  const [region, setRegion] = useState<string>("all");
  const [format, setFormat] = useState<"standard" | "expanded" | "all">("all");
  const [tier, setTier] = useState<string>("all");
  const [majorFormatKey, setMajorFormatKey] =
    useState<MajorFormatFilterValue>("all");
  const [season, setSeason] = useState<SeasonFilterValue>("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useEvents({
    region: region === "all" ? undefined : region,
    format: format === "all" ? undefined : format,
    tier: tier === "all" ? undefined : tier,
    major_format_key: majorFormatKey === "all" ? undefined : majorFormatKey,
    season: season === "all" ? undefined : Number.parseInt(season, 10),
    page,
    limit: 20,
  });

  const championshipEvents = useMemo(() => {
    if (!data?.items) return [];
    return [...data.items]
      .filter((e) => isOfficialMajorTier(e.tier))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [data?.items]);

  const groupedByRegion = useMemo(() => {
    if (!data?.items) {
      return [] as Array<{
        region: string;
        label: string;
        items: ApiEventSummary[];
      }>;
    }

    const groups = new Map<string, ApiEventSummary[]>();
    for (const e of data.items) {
      const key = e.region || "OTHER";
      const arr = groups.get(key) ?? [];
      arr.push(e);
      groups.set(key, arr);
    }
    for (const [, items] of groups) {
      items.sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      );
    }

    const keys = Array.from(groups.keys());
    const ordered = [
      ...REGION_ORDER.filter((r) => groups.has(r)),
      ...keys
        .filter(
          (k) => !REGION_ORDER.includes(k as (typeof REGION_ORDER)[number])
        )
        .sort(),
    ];

    return ordered.map((k) => ({
      region: k,
      label: REGION_LABELS[k] ?? k,
      items: groups.get(k) ?? [],
    }));
  }, [data?.items]);

  const handleFilterChange = () => {
    setPage(1);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Upcoming Events</h1>
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
        <h1 className="text-3xl font-bold mb-8">Upcoming Events</h1>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load events</p>
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
        <h1 className="text-3xl font-bold">Upcoming Events</h1>
        <EventFilters
          region={region}
          format={format}
          tier={tier}
          majorFormatKey={majorFormatKey}
          season={season}
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
          onMajorFormatChange={(v) => {
            setMajorFormatKey(v);
            handleFilterChange();
          }}
          onSeasonChange={(v) => {
            setSeason(v);
            handleFilterChange();
          }}
        />
      </div>

      {championshipEvents.length > 0 ? (
        <ChampionshipBanner events={championshipEvents} />
      ) : null}

      {data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <CalendarDays className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No upcoming events found matching your filters.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {region === "all" ? (
            <div className="space-y-10">
              {groupedByRegion.map((group) => (
                <section key={group.region} className="space-y-4">
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-semibold tracking-tight">
                        {group.label}
                      </h2>
                      <p className="text-sm text-muted-foreground">
                        {group.items.length} events
                      </p>
                    </div>
                  </div>
                  <Separator />
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {group.items.map((event) => (
                      <EventCard key={event.id} event={event} />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data?.items.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}

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
