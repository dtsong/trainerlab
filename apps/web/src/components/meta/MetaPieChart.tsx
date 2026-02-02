"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { Archetype } from "@trainerlab/shared-types";
import { CHART_COLORS } from "@/lib/chart-colors";

interface MetaPieChartProps {
  data: Archetype[];
  className?: string;
}

interface TooltipPayload {
  name: string;
  value: number;
  payload: { name: string; share: number };
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

export function MetaPieChart({ data, className }: MetaPieChartProps) {
  const chartData = data.map((archetype) => ({
    name: archetype.name,
    share: archetype.share,
    value: archetype.share * 100,
  }));

  return (
    <div className={className} data-testid="meta-pie-chart">
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={120}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
            label={(props) => {
              const { name, percent } = props;
              if (percent && percent > 0.05) {
                return `${name} (${(percent * 100).toFixed(0)}%)`;
              }
              return "";
            }}
            labelLine={false}
          >
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={CHART_COLORS[index % CHART_COLORS.length]}
                stroke="hsl(var(--background))"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            formatter={(value: string) => (
              <span className="text-sm text-foreground">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
