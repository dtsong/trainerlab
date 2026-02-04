"use client";

import { useMemo } from "react";
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { safeFormatDate } from "@/lib/date-utils";
import type { ApiEvolutionSnapshot } from "@trainerlab/shared-types";

interface EvolutionChartProps {
  snapshots: ApiEvolutionSnapshot[];
  className?: string;
}

interface TooltipPayload {
  name: string;
  value: number;
  color: string;
  dataKey: string;
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
          {safeFormatDate(label, "MMM d, yyyy")}
        </p>
        {payload.map((entry) => (
          <div key={entry.dataKey} className="flex items-center gap-2 text-sm">
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

export function EvolutionChart({ snapshots, className }: EvolutionChartProps) {
  const chartData = useMemo(() => {
    return snapshots
      .filter((s) => s.created_at)
      .map((snapshot) => ({
        date: snapshot.created_at!,
        metaShare: snapshot.meta_share ? snapshot.meta_share * 100 : null,
        conversionRate: snapshot.top_cut_conversion
          ? snapshot.top_cut_conversion * 100
          : null,
      }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [snapshots]);

  if (!chartData.length) {
    return (
      <div
        className={`flex items-center justify-center h-64 text-muted-foreground ${className}`}
      >
        No chart data available
      </div>
    );
  }

  return (
    <div className={className} data-testid="evolution-chart">
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart
          data={chartData}
          margin={{ left: 10, right: 30, top: 10, bottom: 10 }}
        >
          <defs>
            <linearGradient id="metaShareGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="date"
            tickFormatter={(value: string) => safeFormatDate(value, "MMM d")}
            fontSize={12}
          />
          <YAxis
            yAxisId="left"
            domain={[0, "auto"]}
            tickFormatter={(value: number) => `${value}%`}
            fontSize={12}
            label={{
              value: "Meta Share",
              angle: -90,
              position: "insideLeft",
              style: { textAnchor: "middle", fontSize: 11 },
            }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[0, "auto"]}
            tickFormatter={(value: number) => `${value}%`}
            fontSize={12}
            label={{
              value: "Day 2 Rate",
              angle: 90,
              position: "insideRight",
              style: { textAnchor: "middle", fontSize: 11 },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="metaShare"
            name="Meta Share"
            stroke="#14b8a6"
            strokeWidth={2}
            fill="url(#metaShareGradient)"
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="conversionRate"
            name="Day 2 Conversion"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ fill: "#f59e0b", strokeWidth: 0, r: 3 }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
