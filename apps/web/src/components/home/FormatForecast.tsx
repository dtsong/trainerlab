"use client";

import Link from "next/link";
import { ArrowRight, Globe } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfidenceBadge } from "@/components/ui/confidence-badge";
import { ArchetypeSprites } from "@/components/meta/ArchetypeSprites";
import { useFormatForecast } from "@/hooks/useMeta";
import { usePredictions } from "@/hooks/useJapan";
import { ComparisonRowSkeleton } from "./skeletons";
import type { ApiFormatForecastEntry } from "@trainerlab/shared-types";

function ShareBar({
  share,
  maxShare,
  color,
  label,
}: {
  share: number;
  maxShare: number;
  color: "rose" | "teal";
  label: string;
}) {
  const width = maxShare > 0 ? (share / maxShare) * 100 : 0;
  const colorClass = color === "rose" ? "bg-rose-400" : "bg-teal-400";

  return (
    <div className="flex items-center gap-1.5">
      <span className="w-6 text-[10px] font-medium uppercase tracking-wider text-slate-500">
        {label}
      </span>
      <div className="h-1.5 w-20 rounded-full bg-slate-700">
        <div
          className={`h-full rounded-full ${colorClass}`}
          style={{ width: `${Math.min(width, 100)}%` }}
        />
      </div>
      <span className="w-11 text-right font-mono text-xs text-slate-400">
        {(share * 100).toFixed(1)}%
      </span>
    </div>
  );
}

function ForecastRow({
  entry,
  maxShare,
}: {
  entry: ApiFormatForecastEntry;
  maxShare: number;
}) {
  const divPP = (entry.divergence * 100).toFixed(1);
  const isPositive = entry.divergence > 0;

  return (
    <div className="flex items-center gap-3 border-b border-slate-700/50 px-4 py-3 last:border-0">
      {/* Sprites + Name */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {entry.sprite_urls.length > 0 && (
          <ArchetypeSprites
            spriteUrls={entry.sprite_urls}
            archetypeName={entry.archetype}
            size="sm"
          />
        )}
        <span className="truncate font-medium text-white">
          {entry.archetype}
        </span>
      </div>

      {/* Share bars */}
      <div className="hidden space-y-0.5 sm:block">
        <ShareBar
          share={entry.jp_share}
          maxShare={maxShare}
          color="rose"
          label="JP"
        />
        <ShareBar
          share={entry.en_share}
          maxShare={maxShare}
          color="teal"
          label="EN"
        />
      </div>

      {/* Mobile: compact shares */}
      <div className="flex items-center gap-2 sm:hidden">
        <span className="font-mono text-xs text-rose-400">
          {(entry.jp_share * 100).toFixed(1)}%
        </span>
        <span className="text-slate-600">/</span>
        <span className="font-mono text-xs text-teal-400">
          {(entry.en_share * 100).toFixed(1)}%
        </span>
      </div>

      {/* Divergence badge */}
      <Badge
        variant="outline"
        className={`shrink-0 font-mono text-xs ${
          isPositive
            ? "border-rose-500/30 text-rose-300"
            : "border-teal-500/30 text-teal-300"
        }`}
      >
        {isPositive ? "+" : ""}
        {divPP}pp
      </Badge>

      {/* Confidence */}
      <ConfidenceBadge
        confidence={entry.confidence}
        sampleSize={0}
        className="hidden shrink-0 lg:inline-flex"
      />
    </div>
  );
}

export function FormatForecast() {
  const {
    data: forecast,
    isLoading,
    isError,
  } = useFormatForecast({ top_n: 5 });
  const { data: predictionsData } = usePredictions({ limit: 1 });

  const entries = forecast?.forecast_archetypes ?? [];
  const prediction = predictionsData?.items?.[0];

  // Hide section entirely if no data available and not loading
  if (!isLoading && entries.length === 0) {
    return null;
  }

  const maxShare =
    entries.length > 0
      ? Math.max(...entries.map((e) => Math.max(e.jp_share, e.en_share)))
      : 0.01;

  return (
    <section className="bg-slate-900 py-12 md:py-16">
      <div className="container">
        <div className="mb-8 flex items-center justify-between">
          <SectionLabel
            label="Format Forecast"
            icon={<Globe className="h-4 w-4" />}
            className="text-slate-200"
          />
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-white"
            asChild
          >
            <Link href="/meta/japan">
              Deep Dive: Full JP Analysis
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {/* Forecast table */}
        <div className="overflow-hidden rounded-xl border border-slate-700">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800/50 px-4 py-2.5 text-xs font-medium text-slate-400">
            <span>Archetypes to Watch</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-rose-400" />
                Japan
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-teal-400" />
                Global
              </span>
            </div>
          </div>

          {/* Loading skeleton */}
          {isLoading && (
            <>
              <ComparisonRowSkeleton />
              <ComparisonRowSkeleton />
              <ComparisonRowSkeleton />
            </>
          )}

          {/* Data rows */}
          {!isLoading &&
            entries.map((entry) => (
              <ForecastRow
                key={entry.archetype}
                entry={entry}
                maxShare={maxShare}
              />
            ))}
        </div>

        {/* Prediction callout */}
        {prediction && (
          <div className="mt-6 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3">
            <p className="text-sm text-amber-200">
              <strong className="font-medium">Prediction:</strong>{" "}
              {prediction.prediction_text}
              {prediction.confidence && (
                <span className="ml-2 inline-flex items-center rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-300">
                  {prediction.confidence} confidence
                </span>
              )}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
