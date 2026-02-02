"use client";

import { format, parseISO } from "date-fns";
import { ChevronDown, ChevronUp, Calendar, AlertCircle } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useJPSetImpacts } from "@/hooks/useJapan";
import type {
  ApiJPSetImpact,
  ApiMetaBreakdownEntry,
} from "@trainerlab/shared-types";

function MetaComparisonBar({
  before,
  after,
}: {
  before: ApiMetaBreakdownEntry[] | null | undefined;
  after: ApiMetaBreakdownEntry[] | null | undefined;
}) {
  if (!before || !after || before.length === 0 || after.length === 0) {
    return null;
  }

  // Get top 5 archetypes from after, compare with before
  const topAfter = after.slice(0, 5);

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground">
        Meta Shift (Before → After)
      </p>
      {topAfter.map((item) => {
        const beforeItem = before.find((b) => b.archetype === item.archetype);
        const beforeShare = beforeItem?.share ?? 0;
        const change = item.share - beforeShare;
        const changePercent = (change * 100).toFixed(1);
        const isNew = beforeShare === 0;
        const isRising = change > 0.01;
        const isFalling = change < -0.01;

        return (
          <div key={item.archetype} className="flex items-center gap-2 text-sm">
            <span className="w-24 truncate">{item.archetype}</span>
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full"
                style={{ width: `${item.share * 100}%` }}
              />
            </div>
            <span className="w-12 text-right">
              {(item.share * 100).toFixed(0)}%
            </span>
            <span
              className={`w-14 text-right text-xs ${
                isNew
                  ? "text-blue-500"
                  : isRising
                    ? "text-green-500"
                    : isFalling
                      ? "text-red-500"
                      : "text-muted-foreground"
              }`}
            >
              {isNew ? "NEW" : `${change >= 0 ? "+" : ""}${changePercent}%`}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function SetImpactCard({ impact }: { impact: ApiJPSetImpact }) {
  const [expanded, setExpanded] = useState(false);

  const jpDate = format(parseISO(impact.jp_release_date), "MMM d, yyyy");
  const enDate = impact.en_release_date
    ? format(parseISO(impact.en_release_date), "MMM d, yyyy")
    : "TBD";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{impact.set_name}</CardTitle>
            <p className="text-sm text-muted-foreground">{impact.set_code}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Release dates */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">JP:</span>
            <span>{jpDate}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">EN:</span>
            <span>{enDate}</span>
          </div>
        </div>

        {/* Key innovations */}
        {impact.key_innovations && impact.key_innovations.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Key Innovations
            </p>
            <div className="flex flex-wrap gap-1">
              {impact.key_innovations.map((card) => (
                <Badge key={card} variant="secondary" className="text-xs">
                  {card}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* New archetypes */}
        {impact.new_archetypes && impact.new_archetypes.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              New Archetypes
            </p>
            <div className="flex flex-wrap gap-1">
              {impact.new_archetypes.map((archetype) => (
                <Badge
                  key={archetype}
                  variant="outline"
                  className="text-xs border-blue-500 text-blue-600"
                >
                  {archetype}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Expanded: Meta comparison */}
        {expanded && (
          <div className="pt-2 border-t">
            <MetaComparisonBar
              before={impact.jp_meta_before}
              after={impact.jp_meta_after}
            />
            {impact.analysis && (
              <div className="mt-3">
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  Analysis
                </p>
                <p className="text-sm text-muted-foreground">
                  {impact.analysis}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface SetImpactTimelineProps {
  className?: string;
  limit?: number;
}

export function SetImpactTimeline({
  className,
  limit = 10,
}: SetImpactTimelineProps) {
  const { data, isLoading, error } = useJPSetImpacts({ limit });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Set Impact History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load set impacts
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className={className}>
        <h2 className="text-xl font-semibold mb-4">Set Impact History</h2>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-24 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const impacts = data?.items ?? [];

  return (
    <div className={className}>
      <div className="mb-4">
        <h2 className="text-xl font-semibold">Set Impact History</h2>
        <p className="text-sm text-muted-foreground">
          How each set changed the JP meta — and what it means for EN
        </p>
      </div>
      {impacts.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">
              No set impacts tracked yet
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {impacts.map((impact) => (
            <SetImpactCard key={impact.id} impact={impact} />
          ))}
        </div>
      )}
    </div>
  );
}
