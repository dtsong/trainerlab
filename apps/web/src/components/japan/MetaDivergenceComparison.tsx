"use client";

import { useState } from "react";
import { AlertCircle, Clock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceBadge } from "@/components/ui/confidence-badge";
import { ArchetypeSprites } from "@/components/meta/ArchetypeSprites";
import { useMetaComparison } from "@/hooks/useMeta";
import type { ApiArchetypeComparison } from "@trainerlab/shared-types";

function ShareBar({
  share,
  maxShare,
  color,
}: {
  share: number;
  maxShare: number;
  color: "rose" | "teal";
}) {
  const width = maxShare > 0 ? (share / maxShare) * 100 : 0;
  const colorClass =
    color === "rose"
      ? "bg-rose-500/60 dark:bg-rose-400/50"
      : "bg-teal-500/60 dark:bg-teal-400/50";

  return (
    <div className="h-1.5 w-16 rounded-full bg-muted">
      <div
        className={`h-full rounded-full ${colorClass}`}
        style={{ width: `${Math.min(width, 100)}%` }}
      />
    </div>
  );
}

function ComparisonRow({
  comparison,
  maxShare,
}: {
  comparison: ApiArchetypeComparison;
  maxShare: number;
}) {
  const jpPercent = (comparison.region_a_share * 100).toFixed(1);
  const enPercent = (comparison.region_b_share * 100).toFixed(1);
  const divPP = (comparison.divergence * 100).toFixed(1);
  const isJpOnly = comparison.region_b_share === 0;
  const isEnOnly = comparison.region_a_share === 0;
  const isDivergent = Math.abs(comparison.divergence) > 0.05;

  return (
    <div className="flex items-center gap-2 py-2 text-sm">
      {comparison.sprite_urls.length > 0 && (
        <ArchetypeSprites
          spriteUrls={comparison.sprite_urls}
          archetypeName={comparison.archetype}
          size="sm"
        />
      )}
      <span className="min-w-0 flex-1 truncate font-medium">
        {comparison.archetype}
      </span>

      {/* JP share */}
      <div className="flex items-center gap-1.5">
        <ShareBar
          share={comparison.region_a_share}
          maxShare={maxShare}
          color="rose"
        />
        <span className="w-12 text-right tabular-nums text-muted-foreground">
          {jpPercent}%
        </span>
      </div>

      {/* EN share */}
      <div className="flex items-center gap-1.5">
        <ShareBar
          share={comparison.region_b_share}
          maxShare={maxShare}
          color="teal"
        />
        <span className="w-12 text-right tabular-nums text-muted-foreground">
          {enPercent}%
        </span>
      </div>

      {/* Divergence / region tag */}
      <div className="w-20 text-right">
        {isJpOnly ? (
          <Badge
            variant="outline"
            className="text-xs border-red-300 text-red-600 dark:border-red-700 dark:text-red-400"
          >
            JP Only
          </Badge>
        ) : isEnOnly ? (
          <Badge
            variant="outline"
            className="text-xs border-blue-300 text-blue-600 dark:border-blue-700 dark:text-blue-400"
          >
            EN Only
          </Badge>
        ) : isDivergent ? (
          <Badge
            variant="secondary"
            className="text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
          >
            {comparison.divergence > 0 ? "+" : ""}
            {divPP}pp
          </Badge>
        ) : (
          <span className="text-xs tabular-nums text-muted-foreground">
            {comparison.divergence > 0 ? "+" : ""}
            {divPP}pp
          </span>
        )}
      </div>
    </div>
  );
}

interface MetaDivergenceComparisonProps {
  className?: string;
}

export function MetaDivergenceComparison({
  className,
}: MetaDivergenceComparisonProps) {
  const [showLag, setShowLag] = useState(false);

  const {
    data: comparison,
    isLoading,
    error,
  } = useMetaComparison({ region_a: "JP" });

  const { data: lagComparison, isLoading: lagLoading } = useMetaComparison(
    showLag ? { region_a: "JP", lag_days: 14 } : { region_a: "JP" }
  );

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            JP vs International Meta
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load meta comparison
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className={className}>
        <h2 className="text-xl font-semibold mb-4">JP vs International Meta</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {[0, 1].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-48 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const comparisons = comparison?.comparisons ?? [];
  const maxShare = Math.max(
    ...comparisons.map((c) => Math.max(c.region_a_share, c.region_b_share)),
    0.01
  );

  const lagData = showLag ? lagComparison?.lag_analysis : null;

  return (
    <div className={className} data-testid="meta-divergence">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">JP vs International Meta</h2>
          <p className="text-sm text-muted-foreground">
            Server-side archetype comparison — divergent archetypes highlighted
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowLag(!showLag)}
          className="shrink-0"
        >
          <Clock className="mr-1 h-3.5 w-3.5" />
          {showLag ? "Hide Lag" : "14-Day Lag"}
        </Button>
      </div>

      {/* Comparison table */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-sm">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-rose-500" />
                Japan (BO1)
                {comparison && (
                  <ConfidenceBadge
                    confidence={comparison.region_a_confidence.confidence}
                    sampleSize={comparison.region_a_confidence.sample_size}
                    freshnessLabel={`updated ${comparison.region_a_confidence.data_freshness_days}d ago`}
                  />
                )}
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-teal-500" />
                International (BO3)
                {comparison && (
                  <ConfidenceBadge
                    confidence={comparison.region_b_confidence.confidence}
                    sampleSize={comparison.region_b_confidence.sample_size}
                    freshnessLabel={`updated ${comparison.region_b_confidence.data_freshness_days}d ago`}
                  />
                )}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {comparisons.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No data available
            </p>
          ) : (
            <div className="divide-y">
              {comparisons.map((c) => (
                <ComparisonRow
                  key={c.archetype}
                  comparison={c}
                  maxShare={maxShare}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lag Analysis */}
      {showLag && lagData && (
        <Card className="mt-4" data-testid="lag-analysis">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Lag Analysis ({lagData.lag_days}-day offset)
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              JP data from {lagData.jp_snapshot_date} vs EN data from{" "}
              {lagData.en_snapshot_date}
            </p>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {lagData.lagged_comparisons.map((c) => (
                <ComparisonRow
                  key={c.archetype}
                  comparison={c}
                  maxShare={Math.max(
                    ...lagData.lagged_comparisons.map((lc) =>
                      Math.max(lc.region_a_share, lc.region_b_share)
                    ),
                    0.01
                  )}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {showLag && lagLoading && (
        <Card className="mt-4">
          <CardContent className="pt-6">
            <div className="h-32 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
