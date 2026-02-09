"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Flag, Trophy, Users } from "lucide-react";

import { TournamentFilters, TournamentList } from "@/components/tournaments";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { BO1ContextBanner } from "@/components/meta";
import { useState } from "react";
import type { TournamentSearchParams } from "@/lib/api";

type TabCategory = "tpci" | "japan" | "grassroots";

function TournamentsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const VALID_TABS: TabCategory[] = ["tpci", "japan", "grassroots"];
  const rawCategory = searchParams.get("category");
  const activeTab: TabCategory = VALID_TABS.includes(rawCategory as TabCategory)
    ? (rawCategory as TabCategory)
    : "tpci";
  const [format, setFormat] = useState<"standard" | "expanded" | "all">("all");

  const handleTabChange = (value: string) => {
    const sp = new URLSearchParams(searchParams.toString());
    if (value === "tpci") {
      sp.delete("category");
    } else {
      sp.set("category", value);
    }
    const query = sp.toString();
    router.push(`/tournaments${query ? `?${query}` : ""}`, {
      scroll: false,
    });
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
        <TournamentFilters format={format} onFormatChange={setFormat} />
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
          <TournamentList apiParams={tpciParams} />
        </TabsContent>

        <TabsContent value="japan">
          <BO1ContextBanner className="mb-4" />
          <TournamentList apiParams={japanParams} showRegion={false} />
        </TabsContent>

        <TabsContent value="grassroots">
          <TournamentList apiParams={grassrootsParams} />
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
