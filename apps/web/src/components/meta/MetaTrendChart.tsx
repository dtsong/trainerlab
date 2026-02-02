"use client";

import { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { MetaSnapshot } from "@trainerlab/shared-types";
import { safeFormatDate } from "@/lib/meta-utils";
import { CHART_COLORS } from "@/lib/chart-colors";

interface MetaTrendChartProps {
  snapshots: MetaSnapshot[];
  className?: string;
}

interface TooltipPayload {
  name: string;
  value: number;
  color: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}) {
  if (active && payload && payload.length && label) {
    return (
      <div className="rounded-lg border bg-background p-3 shadow-md">
        <p className="mb-2 font-medium">
          {safeFormatDate(label, "MMM d, yyyy", format, parseISO)}
        </p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span>{entry.name}:</span>
            <span className="font-medium">{entry.value.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export function MetaTrendChart({ snapshots, className }: MetaTrendChartProps) {
  // Extract all unique archetype names
  const archetypeNames = useMemo(() => {
    const names = new Set<string>();
    snapshots.forEach((snapshot) => {
      snapshot.archetypeBreakdown.forEach((archetype) => {
        names.add(archetype.name);
      });
    });
    return Array.from(names);
  }, [snapshots]);

  // Track which archetypes are visible
  const [visibleArchetypes, setVisibleArchetypes] = useState<Set<string>>(
    () => new Set(archetypeNames.slice(0, 5)), // Show top 5 by default
  );

  // Transform data for the chart
  const chartData = useMemo(() => {
    return snapshots
      .map((snapshot) => {
        const dataPoint: Record<string, string | number> = {
          date: snapshot.snapshotDate,
        };
        snapshot.archetypeBreakdown.forEach((archetype) => {
          dataPoint[archetype.name] = archetype.share * 100;
        });
        return dataPoint;
      })
      .sort((a, b) => (a.date as string).localeCompare(b.date as string));
  }, [snapshots]);

  const toggleArchetype = (name: string) => {
    setVisibleArchetypes((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  return (
    <div className={className} data-testid="meta-trend-chart">
      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={chartData}
          margin={{ left: 10, right: 30, top: 10, bottom: 10 }}
        >
          <XAxis
            dataKey="date"
            tickFormatter={(value: string) =>
              safeFormatDate(value, "MMM d", format, parseISO)
            }
            fontSize={12}
          />
          <YAxis
            domain={[0, "auto"]}
            tickFormatter={(value: number) => `${value}%`}
            fontSize={12}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            onClick={(e) => toggleArchetype(e.dataKey as string)}
            formatter={(value: string) => (
              <span
                className={`cursor-pointer text-sm ${
                  visibleArchetypes.has(value)
                    ? "text-foreground"
                    : "text-muted-foreground line-through"
                }`}
              >
                {value}
              </span>
            )}
          />
          {archetypeNames.map((name, index) => (
            <Line
              key={name}
              type="monotone"
              dataKey={name}
              stroke={CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={2}
              dot={false}
              hide={!visibleArchetypes.has(name)}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
