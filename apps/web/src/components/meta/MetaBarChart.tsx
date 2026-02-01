"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useRouter } from "next/navigation";
import type { CardUsageSummary } from "@trainerlab/shared-types";

interface MetaBarChartProps {
  data: CardUsageSummary[];
  cardNames?: Record<string, string>;
  limit?: number;
  className?: string;
}

interface TooltipPayload {
  name: string;
  value: number;
  payload: {
    cardId: string;
    name: string;
    inclusionRate: number;
    avgCopies: number;
  };
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
          {(data.inclusionRate * 100).toFixed(1)}% inclusion rate
        </p>
        <p className="text-sm text-muted-foreground">
          {data.avgCopies.toFixed(1)} avg copies
        </p>
      </div>
    );
  }
  return null;
}

export function MetaBarChart({
  data,
  cardNames = {},
  limit = 10,
  className,
}: MetaBarChartProps) {
  const router = useRouter();

  const chartData = data
    .slice(0, limit)
    .map((card) => ({
      cardId: card.cardId,
      name: cardNames[card.cardId] || card.cardId,
      inclusionRate: card.inclusionRate,
      avgCopies: card.avgCopies,
      value: card.inclusionRate * 100,
    }))
    .sort((a, b) => b.inclusionRate - a.inclusionRate);

  const handleBarClick = (data: Record<string, unknown>) => {
    if (typeof data.cardId === "string") {
      router.push(`/cards/${encodeURIComponent(data.cardId)}`);
    }
  };

  return (
    <div className={className} data-testid="meta-bar-chart">
      <ResponsiveContainer width="100%" height={350}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ left: 100, right: 20, top: 10, bottom: 10 }}
        >
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(value: number) => `${value}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={90}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="value"
            fill="#8884d8"
            radius={[0, 4, 4, 0]}
            cursor="pointer"
            onClick={(_, index) => {
              const item = chartData[index];
              if (item) {
                handleBarClick({ cardId: item.cardId });
              }
            }}
          >
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={`hsl(${220 + index * 15}, 70%, ${60 - index * 3}%)`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
