"use client";

import { AlertCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArchetypeSprites } from "@/components/meta/ArchetypeSprites";
import { useCurrentMeta } from "@/hooks/useMeta";
import type { ApiArchetype } from "@trainerlab/shared-types";

function ArchetypeRow({
  archetype,
  divergentShare,
  regionTag,
}: {
  archetype: ApiArchetype;
  divergentShare?: number;
  regionTag?: "JP Only" | "EN Only";
}) {
  const sharePercent = (archetype.share * 100).toFixed(1);
  const isDivergent =
    divergentShare !== undefined && Math.abs(divergentShare) > 5;
  const spriteUrls = archetype.sprite_urls ?? [];

  return (
    <div className="flex items-center gap-2 py-1.5 text-sm">
      {spriteUrls.length > 0 && (
        <ArchetypeSprites
          spriteUrls={spriteUrls}
          archetypeName={archetype.name}
          size="sm"
        />
      )}
      <span className="flex-1 truncate font-medium">{archetype.name}</span>
      <span className="tabular-nums text-muted-foreground">
        {sharePercent}%
      </span>
      {regionTag && (
        <Badge
          variant="outline"
          className={`text-xs ${
            regionTag === "JP Only"
              ? "border-red-300 text-red-600 dark:border-red-700 dark:text-red-400"
              : "border-blue-300 text-blue-600 dark:border-blue-700 dark:text-blue-400"
          }`}
        >
          {regionTag}
        </Badge>
      )}
      {isDivergent && !regionTag && (
        <Badge
          variant="secondary"
          className="text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        >
          JP Signal
        </Badge>
      )}
    </div>
  );
}

interface MetaDivergenceComparisonProps {
  className?: string;
}

export function MetaDivergenceComparison({
  className,
}: MetaDivergenceComparisonProps) {
  const {
    data: jpMeta,
    isLoading: jpLoading,
    error: jpError,
  } = useCurrentMeta({ region: "JP", best_of: 1 });

  const {
    data: globalMeta,
    isLoading: globalLoading,
    error: globalError,
  } = useCurrentMeta({ best_of: 3 });

  const isLoading = jpLoading || globalLoading;
  const error = jpError || globalError;

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

  const jpArchetypes = (jpMeta?.archetype_breakdown ?? []).slice(0, 10);
  const globalArchetypes = (globalMeta?.archetype_breakdown ?? []).slice(0, 10);

  // Build lookup maps for divergence detection
  const jpMap = new Map(
    jpArchetypes.map((a: ApiArchetype) => [a.name, a.share * 100])
  );
  const globalMap = new Map(
    globalArchetypes.map((a: ApiArchetype) => [a.name, a.share * 100])
  );

  return (
    <div className={className} data-testid="meta-divergence">
      <div className="mb-4">
        <h2 className="text-xl font-semibold">JP vs International Meta</h2>
        <p className="text-sm text-muted-foreground">
          Side-by-side archetype comparison — divergent archetypes highlighted
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {/* Japan Column */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Japan (BO1)</CardTitle>
          </CardHeader>
          <CardContent>
            {jpArchetypes.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No data available
              </p>
            ) : (
              <div className="divide-y">
                {jpArchetypes.map((archetype: ApiArchetype) => {
                  const globalShare = globalMap.get(archetype.name);
                  const isJpOnly = globalShare === undefined;
                  const divergence =
                    globalShare !== undefined
                      ? archetype.share * 100 - globalShare
                      : undefined;

                  return (
                    <ArchetypeRow
                      key={archetype.name}
                      archetype={archetype}
                      divergentShare={divergence}
                      regionTag={isJpOnly ? "JP Only" : undefined}
                    />
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* International Column */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">International (BO3)</CardTitle>
          </CardHeader>
          <CardContent>
            {globalArchetypes.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No data available
              </p>
            ) : (
              <div className="divide-y">
                {globalArchetypes.map((archetype: ApiArchetype) => {
                  const jpShare = jpMap.get(archetype.name);
                  const isEnOnly = jpShare === undefined;
                  const divergence =
                    jpShare !== undefined
                      ? archetype.share * 100 - jpShare
                      : undefined;

                  return (
                    <ArchetypeRow
                      key={archetype.name}
                      archetype={archetype}
                      divergentShare={divergence}
                      regionTag={isEnOnly ? "EN Only" : undefined}
                    />
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
