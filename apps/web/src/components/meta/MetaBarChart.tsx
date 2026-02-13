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
import { useCallback, useEffect, useMemo, useState } from "react";
import type { CardUsageSummary } from "@trainerlab/shared-types";
import { getChartColor } from "@/lib/chart-colors";

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
    imageSmall?: string;
  };
}

const THUMB_W = 24;
const THUMB_H = 34;
const THUMB_GAP = 8;

function safeTickLabel(label: unknown): string {
  return typeof label === "string" ? label : String(label ?? "");
}

function YAxisTick({
  x,
  y,
  payload,
  yAxisWidth,
  showThumbnails,
  imageSmall,
}: {
  x?: number | string;
  y?: number | string;
  payload?: { value?: unknown };
  yAxisWidth: number;
  showThumbnails: boolean;
  imageSmall?: string;
}) {
  const label = safeTickLabel(payload?.value);
  const hasThumb =
    showThumbnails && typeof imageSmall === "string" && imageSmall;

  // Recharts provides x/y near the right edge of the Y axis area.
  // We shift left by the allocated width so we can render image + label within it.
  const xNum = typeof x === "number" ? x : Number(x ?? 0);
  const yNum = typeof y === "number" ? y : Number(y ?? 0);
  const gx = xNum - yAxisWidth + 8;
  const gy = yNum;

  const textX = hasThumb ? THUMB_W + THUMB_GAP : 0;
  const clipped = label.length > 26 ? `${label.slice(0, 25)}...` : label;

  return (
    <g transform={`translate(${gx},${gy})`}>
      {hasThumb ? (
        <image
          href={imageSmall}
          xlinkHref={imageSmall}
          width={THUMB_W}
          height={THUMB_H}
          y={-THUMB_H / 2}
          preserveAspectRatio="xMidYMid slice"
        />
      ) : null}
      <text
        x={textX}
        y={0}
        dy={4}
        textAnchor="start"
        fontSize={12}
        fill="currentColor"
        className="text-muted-foreground"
      >
        {clipped}
      </text>
    </g>
  );
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

  const [showThumbnails, setShowThumbnails] = useState(() => {
    if (
      typeof window === "undefined" ||
      typeof window.matchMedia !== "function"
    ) {
      return false;
    }
    return window.matchMedia("(min-width: 640px)").matches;
  });

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      typeof window.matchMedia !== "function"
    ) {
      return;
    }
    const mq = window.matchMedia("(min-width: 640px)");
    const update = () => setShowThumbnails(mq.matches);
    update();
    mq.addEventListener?.("change", update);
    return () => mq.removeEventListener?.("change", update);
  }, []);

  const chartData = data
    .slice(0, limit)
    .map((card) => ({
      cardId: card.cardId,
      name: cardNames[card.cardId] || card.cardId,
      inclusionRate: card.inclusionRate,
      avgCopies: card.avgCopies,
      value: card.inclusionRate * 100,
      imageSmall: card.imageSmall,
    }))
    .sort((a, b) => b.inclusionRate - a.inclusionRate);

  const imageByName = useMemo(() => {
    const m = new Map<string, string>();
    for (const item of chartData) {
      if (typeof item.imageSmall === "string" && item.imageSmall) {
        m.set(item.name, item.imageSmall);
      }
    }
    return m;
  }, [chartData]);

  const yAxisWidth = showThumbnails ? 170 : 110;

  const renderYAxisTick = useCallback(
    (props: {
      x?: number | string;
      y?: number | string;
      payload?: { value?: unknown };
    }) => {
      const label = safeTickLabel(props.payload?.value);
      return (
        <YAxisTick
          {...props}
          yAxisWidth={yAxisWidth}
          showThumbnails={showThumbnails}
          imageSmall={imageByName.get(label)}
        />
      );
    },
    [imageByName, showThumbnails, yAxisWidth]
  );

  const handleBarClick = (data: Record<string, unknown>) => {
    if (typeof data.cardId === "string") {
      router.push(`/investigate/card/${encodeURIComponent(data.cardId)}`);
    }
  };

  return (
    <div className={className} data-testid="meta-bar-chart">
      <ResponsiveContainer width="100%" height={350}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{
            left: showThumbnails ? 160 : 120,
            right: 20,
            top: 10,
            bottom: 10,
          }}
        >
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={(value: number) => `${value}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={yAxisWidth}
            tick={renderYAxisTick}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="value"
            fill={getChartColor(0)}
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
              <Cell key={`cell-${index}`} fill={getChartColor(index)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
