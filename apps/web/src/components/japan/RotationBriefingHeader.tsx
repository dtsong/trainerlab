"use client";

import { useMemo } from "react";
import { differenceInDays } from "date-fns";
import { Globe, Calendar, FlaskConical } from "lucide-react";

// The JP Nihil Zero rotation date
const JP_ROTATION_DATE = new Date("2026-01-23");
// The international rotation date
const EN_ROTATION_DATE = new Date("2026-04-10");

interface RotationBriefingHeaderProps {
  phase: "pre-rotation" | "post-rotation" | "unified";
}

export function RotationBriefingHeader({ phase }: RotationBriefingHeaderProps) {
  const now = useMemo(() => new Date(), []);

  const daysOfData = useMemo(
    () => differenceInDays(now, JP_ROTATION_DATE),
    [now]
  );

  const daysUntilRotation = useMemo(
    () => Math.max(0, differenceInDays(EN_ROTATION_DATE, now)),
    [now]
  );

  if (phase === "unified") {
    return null;
  }

  const isUrgent = daysUntilRotation > 0 && daysUntilRotation <= 14;
  const isPast = daysUntilRotation === 0;

  return (
    <div
      className="relative overflow-hidden rounded-lg border border-teal-500/20 bg-teal-500/5"
      data-testid="rotation-briefing-header"
    >
      <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
        {/* Left: context */}
        <div className="flex items-start gap-3">
          <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-teal-600 dark:text-teal-400" />
          <div className="space-y-2">
            <p className="text-sm leading-relaxed text-foreground/90">
              Japan entered the{" "}
              <span className="font-semibold text-teal-700 dark:text-teal-300">
                SV9+ format
              </span>{" "}
              on January 23. International rotation hits{" "}
              <span className="font-semibold">April 10</span>. All data reflects
              post-rotation tournaments only.
            </p>

            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-500/10 px-3 py-1 text-xs font-medium text-teal-700 dark:text-teal-300">
                <Calendar className="h-3 w-3" />
                {daysOfData} days of post-rotation data
              </span>
            </div>

            <p className="text-[11px] text-muted-foreground">
              Sources: Limitless TCG · Pokecabook · Pokekameshi
            </p>
          </div>
        </div>

        {/* Right: countdown */}
        {!isPast && (
          <div
            className={`flex shrink-0 flex-col items-center rounded-lg px-5 py-3 ${
              isUrgent
                ? "border border-amber-500/30 bg-amber-500/10"
                : "border border-teal-500/20 bg-teal-500/5"
            }`}
            data-testid="rotation-countdown"
          >
            <span
              className={`font-mono text-3xl font-bold tabular-nums tracking-tight ${
                isUrgent
                  ? "text-amber-600 dark:text-amber-400"
                  : "text-teal-600 dark:text-teal-400"
              }`}
            >
              {daysUntilRotation}
            </span>
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              days until
            </span>
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-muted-foreground">
              <Globe className="h-2.5 w-2.5" />
              EN rotation
            </span>
          </div>
        )}

        {isPast && (
          <div
            className="flex shrink-0 flex-col items-center rounded-lg border border-teal-500/30 bg-teal-500/10 px-5 py-3"
            data-testid="rotation-unified"
          >
            <span className="text-xs font-semibold text-teal-700 dark:text-teal-300">
              Formats Unified
            </span>
            <span className="text-[10px] text-muted-foreground">
              JP + EN on SV9+
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
