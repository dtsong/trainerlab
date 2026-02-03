"use client";

import Link from "next/link";
import { ArrowRight, Flag, Globe } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";
import { JPSignalBadge } from "@/components/ui/jp-signal-badge";
import { Button } from "@/components/ui/button";
import { useHomeMetaData } from "@/hooks/useMeta";
import { usePredictions } from "@/hooks/useJapan";
import { buildJPComparisons, type JPComparison } from "@/lib/home-utils";
import { ComparisonRowSkeleton } from "./skeletons";

export function JPPreview() {
  const {
    globalMeta,
    jpMeta,
    isLoading: metaLoading,
    isError,
  } = useHomeMetaData();
  const { data: predictionsData } = usePredictions({ limit: 1 });

  const comparisons = buildJPComparisons(globalMeta, jpMeta, 3);
  const prediction = predictionsData?.items?.[0];

  // Hide section entirely if JP data unavailable and not loading (but not on error)
  if (!metaLoading && !isError && comparisons.length === 0) {
    return null;
  }

  return (
    <section className="bg-slate-900 py-12 md:py-16">
      <div className="container">
        <div className="mb-8 flex items-center justify-between">
          <SectionLabel
            label="Japan vs Global"
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
              Full JP Analysis
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {/* Comparison grid */}
        <div className="overflow-hidden rounded-xl border border-slate-700">
          {/* Header row */}
          <div className="grid grid-cols-2 border-b border-slate-700 bg-slate-800/50 text-sm font-medium">
            <div className="flex items-center gap-2 px-4 py-3 text-slate-300">
              <Flag className="h-4 w-4 text-rose-400" />
              Japan Top 3
            </div>
            <div className="flex items-center gap-2 border-l border-slate-700 px-4 py-3 text-slate-300">
              <Flag className="h-4 w-4 text-teal-400" />
              Global Top 3
            </div>
          </div>

          {/* Loading state */}
          {metaLoading && (
            <>
              <ComparisonRowSkeleton />
              <ComparisonRowSkeleton />
              <ComparisonRowSkeleton />
            </>
          )}

          {/* Data rows */}
          {!metaLoading &&
            comparisons.map((comparison, index) => (
              <div
                key={comparison.rank}
                className={`grid grid-cols-2 ${
                  index < comparisons.length - 1
                    ? "border-b border-slate-700/50"
                    : ""
                }`}
              >
                <div className="flex items-center gap-3 px-4 py-3">
                  <span className="font-mono text-sm text-slate-500">
                    {comparison.rank}
                  </span>
                  <div className="flex-1">
                    <span className="font-medium text-white">
                      {comparison.jpName}
                    </span>
                    <span className="ml-2 font-mono text-sm text-slate-400">
                      {comparison.jpShare}%
                    </span>
                  </div>
                  {comparison.divergence > 0 && (
                    <JPSignalBadge
                      jpShare={comparison.jpShare / 100}
                      enShare={comparison.enShare / 100}
                    />
                  )}
                </div>
                <div className="flex items-center gap-3 border-l border-slate-700/50 px-4 py-3">
                  <span className="font-mono text-sm text-slate-500">
                    {comparison.rank}
                  </span>
                  <div className="flex-1">
                    <span className="font-medium text-white">
                      {comparison.enName}
                    </span>
                    <span className="ml-2 font-mono text-sm text-slate-400">
                      {comparison.enShare}%
                    </span>
                  </div>
                </div>
              </div>
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
