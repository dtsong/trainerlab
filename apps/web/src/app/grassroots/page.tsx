"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { TournamentList } from "@/components/tournaments";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { TournamentSearchParams } from "@/lib/api";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
  parseIntParam,
} from "@/lib/url-state";

type RegionFilter = "all" | "NA" | "EU" | "JP" | "LATAM" | "OCE";
type FormatFilter = "all" | "standard" | "expanded";
type BestOfFilter = "all" | "1" | "3";

const REGION_VALUES: RegionFilter[] = ["all", "NA", "EU", "JP", "LATAM", "OCE"];
const FORMAT_VALUES: FormatFilter[] = ["all", "standard", "expanded"];
const BEST_OF_VALUES: BestOfFilter[] = ["all", "1", "3"];

const REGION_OPTIONS: Array<{ value: RegionFilter; label: string }> = [
  { value: "all", label: "All Regions" },
  { value: "NA", label: "North America" },
  { value: "EU", label: "Europe" },
  { value: "JP", label: "Japan" },
  { value: "LATAM", label: "Latin America" },
  { value: "OCE", label: "Oceania" },
];

const FORMAT_OPTIONS: Array<{ value: FormatFilter; label: string }> = [
  { value: "all", label: "All Formats" },
  { value: "standard", label: "Standard" },
  { value: "expanded", label: "Expanded" },
];

const BEST_OF_OPTIONS: Array<{ value: BestOfFilter; label: string }> = [
  { value: "all", label: "All Match Formats" },
  { value: "1", label: "BO1" },
  { value: "3", label: "BO3" },
];

export default function GrassrootsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const urlRegion = parseEnumParam(
    searchParams.get("region"),
    REGION_VALUES,
    "all"
  );
  const urlFormat = parseEnumParam(
    searchParams.get("format"),
    FORMAT_VALUES,
    "all"
  );
  const urlBestOf = parseEnumParam(
    searchParams.get("best_of"),
    BEST_OF_VALUES,
    "all"
  );
  const urlPage = parseIntParam(searchParams.get("page"), {
    defaultValue: 1,
    min: 1,
  });

  const [region, setRegion] = useState<RegionFilter>(urlRegion);
  const [format, setFormat] = useState<FormatFilter>(urlFormat);
  const [bestOf, setBestOf] = useState<BestOfFilter>(urlBestOf);
  const [page, setPage] = useState(urlPage);

  useEffect(() => {
    if (region !== urlRegion) {
      setRegion(urlRegion);
    }
  }, [region, urlRegion]);

  useEffect(() => {
    if (format !== urlFormat) {
      setFormat(urlFormat);
    }
  }, [format, urlFormat]);

  useEffect(() => {
    if (bestOf !== urlBestOf) {
      setBestOf(urlBestOf);
    }
  }, [bestOf, urlBestOf]);

  useEffect(() => {
    if (page !== urlPage) {
      setPage(urlPage);
    }
  }, [page, urlPage]);

  const updateUrl = (
    updates: {
      region?: RegionFilter;
      format?: FormatFilter;
      bestOf?: BestOfFilter;
      page?: number;
    },
    navigationMode: "replace" | "push"
  ) => {
    const query = mergeSearchParams(
      searchParams,
      {
        region: updates.region,
        format: updates.format,
        best_of: updates.bestOf,
        page: updates.page,
      },
      {
        region: "all",
        format: "all",
        best_of: "all",
        page: 1,
      }
    );

    const href = buildPathWithQuery("/grassroots", query);
    if (navigationMode === "replace") {
      router.replace(href, { scroll: false });
      return;
    }

    router.push(href, { scroll: false });
  };

  const apiParams: TournamentSearchParams = useMemo(
    () => ({
      tier: "grassroots",
      region: region === "all" ? undefined : region,
      format: format === "all" ? undefined : format,
      best_of: bestOf === "1" ? 1 : bestOf === "3" ? 3 : undefined,
    }),
    [bestOf, format, region]
  );

  return (
    <div className="container mx-auto py-8 px-4 space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Grassroots Analysis</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Community tournaments tracked separately from official major roadmap
            views.
          </p>
        </div>
        <Link
          href="/tournaments"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Back to Official Tournaments
        </Link>
      </div>

      <Card>
        <CardContent className="pt-6 text-sm text-muted-foreground">
          Grassroots snapshots refresh on community cadence. Use filters to
          inspect local weekly trends without mixing them into
          Regional/IC/Worlds coverage.
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Select
          value={region}
          onValueChange={(value) => {
            const nextValue = value as RegionFilter;
            setRegion(nextValue);
            setPage(1);
            updateUrl({ region: nextValue, page: 1 }, "replace");
          }}
        >
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Region" />
          </SelectTrigger>
          <SelectContent>
            {REGION_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={format}
          onValueChange={(value) => {
            const nextValue = value as FormatFilter;
            setFormat(nextValue);
            setPage(1);
            updateUrl({ format: nextValue, page: 1 }, "replace");
          }}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Format" />
          </SelectTrigger>
          <SelectContent>
            {FORMAT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={bestOf}
          onValueChange={(value) => {
            const nextValue = value as BestOfFilter;
            setBestOf(nextValue);
            setPage(1);
            updateUrl({ bestOf: nextValue, page: 1 }, "replace");
          }}
        >
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Best Of" />
          </SelectTrigger>
          <SelectContent>
            {BEST_OF_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <TournamentList
        apiParams={apiParams}
        page={page}
        onPageChange={(nextPage) => {
          const normalizedPage = Math.max(1, nextPage);
          setPage(normalizedPage);
          updateUrl({ page: normalizedPage }, "push");
        }}
      />
    </div>
  );
}
