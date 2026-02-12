"use client";

import { AlertCircle, CalendarDays, RefreshCw } from "lucide-react";
import { Suspense, useMemo, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { ArchetypeSurvival, CardRotationList } from "@/components/rotation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useCurrentFormat,
  useUpcomingFormat,
  useRotationImpacts,
} from "@/hooks/useFormat";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
} from "@/lib/url-state";

import type { SurvivalRating } from "@trainerlab/shared-types";

const TAB_VALUES = ["overview", "cards"] as const;
const RATING_VALUES = [
  "all",
  "dies",
  "crippled",
  "adapts",
  "thrives",
  "unknown",
] as const;

function RotationPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlTab = parseEnumParam(
    searchParams.get("tab"),
    TAB_VALUES,
    "overview"
  );
  const urlRating = parseEnumParam(
    searchParams.get("rating"),
    RATING_VALUES,
    "all"
  );

  const [optimisticTab, setOptimisticTab] = useState<string | null>(null);
  const [optimisticRating, setOptimisticRating] = useState<
    SurvivalRating | "all" | null
  >(null);

  useEffect(() => {
    if (optimisticTab === urlTab) {
      setOptimisticTab(null);
    }
  }, [optimisticTab, urlTab]);

  useEffect(() => {
    if (optimisticRating === urlRating) {
      setOptimisticRating(null);
    }
  }, [optimisticRating, urlRating]);

  const activeTab = optimisticTab ?? urlTab;
  const ratingFilter = optimisticRating ?? urlRating;

  const updateUrl = (
    updates: { tab?: string; rating?: SurvivalRating | "all" },
    navigationMode: "replace" | "push"
  ) => {
    const query = mergeSearchParams(searchParams, updates, {
      tab: "overview",
      rating: "all",
    });
    const href = buildPathWithQuery("/rotation", query);
    if (navigationMode === "replace") {
      router.replace(href, { scroll: false });
      return;
    }
    router.push(href, { scroll: false });
  };

  const handleTabChange = (nextTab: string) => {
    const normalizedTab = parseEnumParam(nextTab, TAB_VALUES, "overview");
    setOptimisticTab(normalizedTab);
    updateUrl({ tab: normalizedTab }, "push");
  };

  const handleRatingFilterChange = (nextRating: SurvivalRating | "all") => {
    setOptimisticRating(nextRating);
    updateUrl({ rating: nextRating }, "replace");
  };

  const { data: currentFormat } = useCurrentFormat();
  const { data: upcomingFormat, isLoading: loadingUpcoming } =
    useUpcomingFormat();

  // Build the transition string from current -> upcoming format
  const transition = useMemo(() => {
    if (!currentFormat || !upcomingFormat) return "";
    return `${currentFormat.name}-to-${upcomingFormat.format.name}`;
  }, [currentFormat, upcomingFormat]);

  const {
    data: impacts,
    isLoading: loadingImpacts,
    isError,
    refetch,
  } = useRotationImpacts(transition);

  // Filter impacts by survival rating
  const filteredImpacts = useMemo(() => {
    if (!impacts) return [];
    if (ratingFilter === "all") return impacts.impacts;
    return impacts.impacts.filter((i) => i.survival_rating === ratingFilter);
  }, [impacts, ratingFilter]);

  // Count by survival rating
  const survivalCounts = useMemo(() => {
    if (!impacts)
      return { dies: 0, crippled: 0, adapts: 0, thrives: 0, unknown: 0 };
    const counts = { dies: 0, crippled: 0, adapts: 0, thrives: 0, unknown: 0 };
    for (const impact of impacts.impacts) {
      counts[impact.survival_rating]++;
    }
    return counts;
  }, [impacts]);

  const isLoading = loadingUpcoming || loadingImpacts;

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 bg-muted rounded" />
          <div className="h-4 w-96 bg-muted rounded" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mt-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!upcomingFormat) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-4">Rotation Impact</h1>
        <Card>
          <CardContent className="py-8 text-center">
            <CalendarDays className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No upcoming rotation announced yet.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-4">Rotation Impact</h1>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">
              Failed to load rotation data
            </p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const rotationDate = new Date(upcomingFormat.rotation_date);
  const formattedDate = rotationDate.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          {upcomingFormat.format.display_name} Rotation Impact
        </h1>
        <p className="text-muted-foreground">
          Format rotation on {formattedDate} •{" "}
          {upcomingFormat.days_until_rotation} days remaining
        </p>
      </div>

      {/* Survival Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 mb-8">
        <button
          onClick={() => handleRatingFilterChange("all")}
          className={`p-4 rounded-lg border transition-colors text-left ${
            ratingFilter === "all"
              ? "border-primary bg-primary/10"
              : "border-border hover:border-primary/50"
          }`}
        >
          <div className="text-2xl font-bold">
            {impacts?.total_archetypes || 0}
          </div>
          <div className="text-sm text-muted-foreground">Total Archetypes</div>
        </button>
        <button
          onClick={() => handleRatingFilterChange("thrives")}
          className={`p-4 rounded-lg border transition-colors text-left ${
            ratingFilter === "thrives"
              ? "border-green-500 bg-green-500/10"
              : "border-border hover:border-green-500/50"
          }`}
        >
          <div className="text-2xl font-bold text-green-400">
            {survivalCounts.thrives}
          </div>
          <div className="text-sm text-muted-foreground">Thrives</div>
        </button>
        <button
          onClick={() => handleRatingFilterChange("adapts")}
          className={`p-4 rounded-lg border transition-colors text-left ${
            ratingFilter === "adapts"
              ? "border-yellow-500 bg-yellow-500/10"
              : "border-border hover:border-yellow-500/50"
          }`}
        >
          <div className="text-2xl font-bold text-yellow-400">
            {survivalCounts.adapts}
          </div>
          <div className="text-sm text-muted-foreground">Adapts</div>
        </button>
        <button
          onClick={() => handleRatingFilterChange("crippled")}
          className={`p-4 rounded-lg border transition-colors text-left ${
            ratingFilter === "crippled"
              ? "border-orange-500 bg-orange-500/10"
              : "border-border hover:border-orange-500/50"
          }`}
        >
          <div className="text-2xl font-bold text-orange-400">
            {survivalCounts.crippled}
          </div>
          <div className="text-sm text-muted-foreground">Crippled</div>
        </button>
        <button
          onClick={() => handleRatingFilterChange("dies")}
          className={`p-4 rounded-lg border transition-colors text-left ${
            ratingFilter === "dies"
              ? "border-red-500 bg-red-500/10"
              : "border-border hover:border-red-500/50"
          }`}
        >
          <div className="text-2xl font-bold text-red-400">
            {survivalCounts.dies}
          </div>
          <div className="text-sm text-muted-foreground">Dies</div>
        </button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="overview">Archetype Overview</TabsTrigger>
          <TabsTrigger value="cards">Rotating Cards</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {filteredImpacts.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No archetypes match the selected filter.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredImpacts.map((impact) => (
                <ArchetypeSurvival key={impact.id} impact={impact} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="cards" className="mt-6">
          {impacts && <CardRotationList impacts={impacts.impacts} />}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function RotationPageFallback() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="animate-pulse space-y-4">
        <div className="h-8 w-64 bg-muted rounded" />
        <div className="h-4 w-96 bg-muted rounded" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mt-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function RotationPage() {
  return (
    <Suspense fallback={<RotationPageFallback />}>
      <RotationPageContent />
    </Suspense>
  );
}
