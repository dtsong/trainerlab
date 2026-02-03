"use client";

import { useMemo } from "react";
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

import { CHART_COLORS } from "@/lib/chart-colors";
import { safeFormatDate } from "@/lib/meta-utils";
import type { ApiCardCountEvolution } from "@trainerlab/shared-types";

interface CardCountEvolutionChartProps {
  cards: ApiCardCountEvolution[];
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
        <p className="mb-2 text-xs font-medium text-muted-foreground">
          {safeFormatDate(label, "MMM d, yyyy", format, parseISO)}
        </p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="truncate">{entry.name}</span>
            <span className="ml-auto font-medium tabular-nums">
              {entry.value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export function CardCountEvolutionChart({
  cards,
  className,
}: CardCountEvolutionChartProps) {
  const chartData = useMemo(() => {
    // Collect all unique dates
    const dateSet = new Set<string>();
    cards.forEach((card) => {
      card.data_points.forEach((dp) => dateSet.add(dp.snapshot_date));
    });

    const sortedDates = [...dateSet].sort();

    return sortedDates.map((dateStr) => {
      const point: Record<string, string | number> = { date: dateStr };
      cards.forEach((card) => {
        const dp = card.data_points.find((d) => d.snapshot_date === dateStr);
        if (dp) {
          point[card.card_name] = dp.avg_copies;
        }
      });
      return point;
    });
  }, [cards]);

  if (cards.length === 0) {
    return (
      <div className={className} data-testid="card-count-chart">
        <div className="flex h-[300px] items-center justify-center rounded border border-dashed text-sm text-muted-foreground">
          Not enough data to display chart
        </div>
      </div>
    );
  }

  return (
    <div className={className} data-testid="card-count-chart">
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
            domain={[0, 4]}
            tickFormatter={(value: number) => `${value}`}
            fontSize={12}
            label={{
              value: "Avg Copies",
              angle: -90,
              position: "insideLeft",
              fontSize: 11,
              fill: "hsl(var(--muted-foreground))",
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {cards.map((card, index) => (
            <Line
              key={card.card_id}
              type="monotone"
              dataKey={card.card_name}
              stroke={CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
