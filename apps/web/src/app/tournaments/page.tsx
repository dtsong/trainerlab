"use client";

import { Suspense, useMemo, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Flag, Trophy } from "lucide-react";
import Link from "next/link";

import { TournamentFilters, TournamentList } from "@/components/tournaments";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { BO1ContextBanner } from "@/components/meta";
import { useState } from "react";
import type { TournamentSearchParams } from "@/lib/api";
import {
  MAJOR_FORMAT_FILTER_OPTIONS,
  SEASON_FILTER_OPTIONS,
  type MajorFormatFilterValue,
  type SeasonFilterValue,
} from "@/lib/official-majors";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
  parseIntParam,
} from "@/lib/url-state";

type TabCategory = "tpci" | "japan";

function TournamentsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const VALID_TABS: TabCategory[] = ["tpci", "japan"];
  const FORMAT_VALUES = ["all", "standard", "expanded"] as const;
  const activeTab = parseEnumParam(
    searchParams.get("category"),
    VALID_TABS,
    "tpci"
  );
  const urlFormat = parseEnumParam(
    searchParams.get("format"),
    FORMAT_VALUES,
    "all"
  );
  const urlPage = parseIntParam(searchParams.get("page"), {
    defaultValue: 1,
    min: 1,
  });
  const MAJOR_FORMAT_VALUES = MAJOR_FORMAT_FILTER_OPTIONS.map(
    (option) => option.value
  ) as readonly MajorFormatFilterValue[];
  const SEASON_VALUES = SEASON_FILTER_OPTIONS.map(
    (option) => option.value
  ) as readonly SeasonFilterValue[];

  const urlMajorFormatKey = parseEnumParam(
    searchParams.get("major_format"),
    MAJOR_FORMAT_VALUES,
    "all"
  );
  const urlSeason = parseEnumParam(
    searchParams.get("season"),
    SEASON_VALUES,
    "all"
  );

  const [format, setFormat] = useState<"standard" | "expanded" | "all">(
    urlFormat
  );
  const [majorFormatKey, setMajorFormatKey] =
    useState<MajorFormatFilterValue>(urlMajorFormatKey);
  const [season, setSeason] = useState<SeasonFilterValue>(urlSeason);
  const [page, setPage] = useState(urlPage);

  useEffect(() => {
    if (format !== urlFormat) {
      setFormat(urlFormat);
    }
  }, [format, urlFormat]);

  useEffect(() => {
    if (page !== urlPage) {
      setPage(urlPage);
    }
  }, [page, urlPage]);

  useEffect(() => {
    if (majorFormatKey !== urlMajorFormatKey) {
      setMajorFormatKey(urlMajorFormatKey);
    }
  }, [majorFormatKey, urlMajorFormatKey]);

  useEffect(() => {
    if (season !== urlSeason) {
      setSeason(urlSeason);
    }
  }, [season, urlSeason]);

  const updateUrl = (
    updates: {
      category?: TabCategory;
      format?: "standard" | "expanded" | "all";
      majorFormatKey?: MajorFormatFilterValue;
      season?: SeasonFilterValue;
      page?: number;
    },
    navigationMode: "replace" | "push"
  ) => {
    const query = mergeSearchParams(
      searchParams,
      {
        category: updates.category,
        format: updates.format,
        major_format: updates.majorFormatKey,
        season: updates.season,
        page: updates.page,
      },
      {
        category: "tpci",
        format: "all",
        major_format: "all",
        season: "all",
        page: 1,
      }
    );

    const href = buildPathWithQuery("/tournaments", query);
    if (navigationMode === "replace") {
      router.replace(href, { scroll: false });
      return;
    }

    router.push(href, { scroll: false });
  };

  const handleTabChange = (value: string) => {
    const nextTab = parseEnumParam(value, VALID_TABS, "tpci");
    setPage(1);
    updateUrl({ category: nextTab, page: 1 }, "push");
  };

  const handleFormatChange = (nextFormat: "standard" | "expanded" | "all") => {
    setFormat(nextFormat);
    setPage(1);
    updateUrl({ format: nextFormat, page: 1 }, "replace");
  };

  const handleMajorFormatChange = (
    nextMajorFormatKey: MajorFormatFilterValue
  ) => {
    setMajorFormatKey(nextMajorFormatKey);
    setPage(1);
    updateUrl({ majorFormatKey: nextMajorFormatKey, page: 1 }, "replace");
  };

  const handleSeasonChange = (nextSeason: SeasonFilterValue) => {
    setSeason(nextSeason);
    setPage(1);
    updateUrl({ season: nextSeason, page: 1 }, "replace");
  };

  const handlePageChange = (nextPage: number) => {
    const normalizedPage = Math.max(1, nextPage);
    setPage(normalizedPage);
    updateUrl({ page: normalizedPage }, "push");
  };

  const formatParam = format === "all" ? undefined : format;
  const seasonParam =
    season === "all" ? undefined : Number.parseInt(season, 10);
  const majorFormatParam =
    majorFormatKey === "all" ? undefined : majorFormatKey;

  const tpciParams: TournamentSearchParams = useMemo(
    () => ({
      tier: "major",
      format: formatParam,
      major_format_key: majorFormatParam,
      season: seasonParam,
      official_only: true,
    }),
    [formatParam, majorFormatParam, seasonParam]
  );

  const japanParams: TournamentSearchParams = useMemo(
    () => ({ region: "JP", best_of: 1, format: formatParam }),
    [formatParam]
  );

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-3xl font-bold">Tournaments</h1>
        <TournamentFilters
          format={format}
          majorFormatKey={majorFormatKey}
          season={season}
          onFormatChange={handleFormatChange}
          onMajorFormatChange={handleMajorFormatChange}
          onSeasonChange={handleSeasonChange}
          showMajorFilters={activeTab === "tpci"}
        />
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <div className="mb-6 flex items-center justify-between gap-3">
          <TabsList>
            <TabsTrigger value="tpci" className="gap-1.5">
              <Trophy className="h-4 w-4" />
              TPCI
            </TabsTrigger>
            <TabsTrigger value="japan" className="gap-1.5">
              <Flag className="h-4 w-4" />
              Japan
            </TabsTrigger>
          </TabsList>

          <Button asChild variant="outline" size="sm">
            <Link href="/grassroots">Grassroots Analysis</Link>
          </Button>
        </div>

        <TabsContent value="tpci">
          <TournamentList
            apiParams={tpciParams}
            page={page}
            onPageChange={handlePageChange}
            showMajorFormatBadge={true}
          />
        </TabsContent>

        <TabsContent value="japan">
          <BO1ContextBanner className="mb-4" />
          <TournamentList
            apiParams={japanParams}
            showRegion={false}
            page={page}
            onPageChange={handlePageChange}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function TournamentsPageLoading() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Tournaments</h1>
      <div className="animate-pulse space-y-4">
        <div className="h-10 w-72 bg-muted rounded" />
        <div className="h-64 bg-muted rounded-lg" />
      </div>
    </div>
  );
}

export default function TournamentsPage() {
  return (
    <Suspense fallback={<TournamentsPageLoading />}>
      <TournamentsPageContent />
    </Suspense>
  );
}
