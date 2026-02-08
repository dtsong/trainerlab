"use client";

import { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { Archetype } from "@trainerlab/shared-types";
import { CHART_COLORS, OTHER_COLOR } from "@/lib/chart-colors";
import { groupArchetypes } from "@/lib/meta-utils";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { ArchetypeSprites } from "./ArchetypeSprites";

interface MetaPieChartProps {
  data: Archetype[];
  topN?: number;
  className?: string;
}

interface SliceData {
  name: string;
  share: number;
  value: number;
  color: string;
  isOther?: boolean;
  spriteUrls?: string[];
}

interface TooltipPayload {
  name: string;
  value: number;
  payload: SliceData;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="rounded-lg border bg-background p-3 shadow-md">
        <p className="font-medium">{data.name}</p>
        <p className="text-sm text-muted-foreground">
          {(data.share * 100).toFixed(1)}% of meta
        </p>
      </div>
    );
  }
  return null;
}

export function MetaPieChart({ data, topN = 8, className }: MetaPieChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [isOtherExpanded, setIsOtherExpanded] = useState(false);

  const { displayed, other } = groupArchetypes(data, { topN, minShare: 0.02 });

  const slices: SliceData[] = displayed.map((archetype, i) => ({
    name: archetype.name,
    share: archetype.share,
    value: archetype.share * 100,
    color: CHART_COLORS[i % CHART_COLORS.length],
    spriteUrls: archetype.spriteUrls,
  }));

  if (other) {
    slices.push({
      name: `Other (${other.count})`,
      share: other.share,
      value: other.share * 100,
      color: OTHER_COLOR,
      isOther: true,
    });
  }

  // Top archetype for center label
  const topArchetype = displayed[0];

  return (
    <div
      className={cn("min-h-[350px]", className)}
      data-testid="meta-pie-chart"
    >
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={slices}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={110}
            paddingAngle={1}
            dataKey="value"
            nameKey="name"
            onMouseEnter={(_, index) => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(null)}
          >
            {slices.map((slice, index) => (
              <Cell
                key={`cell-${index}`}
                fill={slice.color}
                stroke="hsl(var(--background))"
                strokeWidth={2}
                opacity={
                  activeIndex === null || activeIndex === index ? 1 : 0.4
                }
                style={{ transition: "opacity 150ms ease" }}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {/* Center label */}
          {topArchetype && (
            <>
              <text
                x="50%"
                y="47%"
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-foreground text-sm font-medium"
              >
                {topArchetype.name}
              </text>
              <text
                x="50%"
                y="56%"
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-muted-foreground text-xs"
              >
                {(topArchetype.share * 100).toFixed(1)}%
              </text>
            </>
          )}
        </PieChart>
      </ResponsiveContainer>

      {/* Custom 2-column legend */}
      <div
        className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 px-2 text-sm"
        data-testid="pie-legend"
      >
        {slices.map((slice, index) => (
          <button
            key={slice.name}
            type="button"
            className={cn(
              "flex items-center gap-2 rounded px-1 py-0.5 text-left transition-opacity",
              slice.isOther && "cursor-pointer hover:bg-muted/50",
              activeIndex !== null && activeIndex !== index && "opacity-40"
            )}
            onMouseEnter={() => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(null)}
            onClick={
              slice.isOther
                ? () => setIsOtherExpanded((prev) => !prev)
                : undefined
            }
          >
            <span
              className="inline-block h-2.5 w-2.5 flex-shrink-0 rounded-full"
              style={{ backgroundColor: slice.color }}
            />
            {slice.spriteUrls && slice.spriteUrls.length > 0 && (
              <ArchetypeSprites
                spriteUrls={slice.spriteUrls}
                archetypeName={slice.name}
                size="sm"
              />
            )}
            <span className="truncate text-foreground">{slice.name}</span>
            <span className="ml-auto flex-shrink-0 tabular-nums text-muted-foreground">
              {(slice.share * 100).toFixed(1)}%
            </span>
            {slice.isOther &&
              (isOtherExpanded ? (
                <ChevronUp className="h-3 w-3 flex-shrink-0 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-3 w-3 flex-shrink-0 text-muted-foreground" />
              ))}
          </button>
        ))}
      </div>

      {/* Expandable "Other" detail list */}
      {isOtherExpanded && other && (
        <div
          className="mt-2 max-h-[200px] overflow-y-auto rounded border bg-muted/30 px-3 py-2 text-xs"
          data-testid="other-detail"
        >
          {other.archetypes
            .sort((a, b) => b.share - a.share)
            .map((arch) => (
              <div
                key={arch.name}
                className="flex items-center justify-between py-0.5"
              >
                <span className="truncate text-foreground">{arch.name}</span>
                <span className="ml-2 flex-shrink-0 tabular-nums text-muted-foreground">
                  {(arch.share * 100).toFixed(1)}%
                </span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
