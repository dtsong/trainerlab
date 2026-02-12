"use client";

import { Suspense, useMemo, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Flag, Trophy, Users } from "lucide-react";

import { TournamentFilters, TournamentList } from "@/components/tournaments";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { BO1ContextBanner } from "@/components/meta";
import { useState } from "react";
import type { TournamentSearchParams } from "@/lib/api";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
  parseIntParam,
} from "@/lib/url-state";

type TabCategory = "tpci" | "japan" | "grassroots";

function TournamentsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const VALID_TABS: TabCategory[] = ["tpci", "japan", "grassroots"];
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

  const [format, setFormat] = useState<"standard" | "expanded" | "all">(
    urlFormat
  );
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

  const updateUrl = (
    updates: {
      category?: TabCategory;
      format?: "standard" | "expanded" | "all";
      page?: number;
    },
    navigationMode: "replace" | "push"
  ) => {
    const query = mergeSearchParams(
      searchParams,
      {
        category: updates.category,
        format: updates.format,
        page: updates.page,
      },
      {
        category: "tpci",
        format: "all",
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

  const handlePageChange = (nextPage: number) => {
    const normalizedPage = Math.max(1, nextPage);
    setPage(normalizedPage);
    updateUrl({ page: normalizedPage }, "push");
  };

  const formatParam = format === "all" ? undefined : format;

  const tpciParams: TournamentSearchParams = useMemo(
    () => ({ tier: "major", format: formatParam }),
    [formatParam]
  );

  const japanParams: TournamentSearchParams = useMemo(
    () => ({ region: "JP", best_of: 1, format: formatParam }),
    [formatParam]
  );

  const grassrootsParams: TournamentSearchParams = useMemo(
    () => ({ tier: "grassroots", format: formatParam }),
    [formatParam]
  );

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-3xl font-bold">Tournaments</h1>
        <TournamentFilters
          format={format}
          onFormatChange={handleFormatChange}
        />
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="mb-6">
          <TabsTrigger value="tpci" className="gap-1.5">
            <Trophy className="h-4 w-4" />
            TPCI
          </TabsTrigger>
          <TabsTrigger value="japan" className="gap-1.5">
            <Flag className="h-4 w-4" />
            Japan
          </TabsTrigger>
          <TabsTrigger value="grassroots" className="gap-1.5">
            <Users className="h-4 w-4" />
            Grassroots
          </TabsTrigger>
        </TabsList>

        <TabsContent value="tpci">
          <TournamentList
            apiParams={tpciParams}
            page={page}
            onPageChange={handlePageChange}
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

        <TabsContent value="grassroots">
          <TournamentList
            apiParams={grassrootsParams}
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
