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
  const now = new Date();

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

  return (
    <div className="rounded-lg border border-teal-500/20 bg-teal-500/5 p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-teal-600 dark:text-teal-400" />
        <div className="space-y-3">
          <p className="text-sm leading-relaxed text-foreground/90">
            Japan entered the{" "}
            <span className="font-semibold text-teal-700 dark:text-teal-300">
              SV9+ format
            </span>{" "}
            on January 23 when Nihil Zero released — the same rotation coming to
            international play on April 10. All data below reflects
            post-rotation tournaments only.
          </p>

          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-500/10 px-3 py-1 text-xs font-medium text-teal-700 dark:text-teal-300">
              <Calendar className="h-3 w-3" />
              {daysOfData} days of post-rotation data
            </span>
            {daysUntilRotation > 0 && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-700 dark:text-amber-300">
                <Globe className="h-3 w-3" />
                {daysUntilRotation} days until international rotation
              </span>
            )}
          </div>

          <p className="text-[11px] text-muted-foreground">
            Sources: Limitless TCG tournaments · Pokecabook · Pokekameshi
          </p>
        </div>
      </div>
    </div>
  );
}
