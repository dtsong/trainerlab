"use client";

import { useEffect, useState } from "react";
import { PillToggle } from "@/components/ui/pill-toggle";
import { cn } from "@/lib/utils";

const formatOptions = [
  { value: "standard", label: "Standard" },
  { value: "expanded", label: "Expanded" },
];

const regionOptions = [
  { value: "global", label: "Global" },
  { value: "NA", label: "NA" },
  { value: "EU", label: "EU" },
  { value: "JP", label: "JP" },
  { value: "LATAM", label: "LATAM" },
  { value: "APAC", label: "APAC" },
];

const periodOptions = [
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "season", label: "Season" },
];

export type Format = "standard" | "expanded";
export type Region = "global" | "NA" | "EU" | "JP" | "LATAM" | "APAC";
export type Period = "week" | "month" | "season";

export interface FilterBarProps {
  format: Format;
  region: Region;
  period: Period;
  onFormatChange: (format: Format) => void;
  onRegionChange: (region: Region) => void;
  onPeriodChange: (period: Period) => void;
  className?: string;
}

export function FilterBar({
  format,
  region,
  period,
  onFormatChange,
  onRegionChange,
  onPeriodChange,
  className,
}: FilterBarProps) {
  const [isSticky, setIsSticky] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      // Sticky when scrolled past 64px (nav height)
      setIsSticky(window.scrollY > 64);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div
      className={cn(
        "z-40 -mx-4 px-4 py-3 transition-all duration-200 md:-mx-6 md:px-6",
        isSticky
          ? "sticky top-16 bg-slate-800 shadow-lg"
          : "bg-slate-800/95 rounded-lg",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-4">
        {/* Format filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Format
          </span>
          <PillToggle
            options={formatOptions}
            value={format}
            onChange={(v) => onFormatChange(v as Format)}
            className="bg-slate-700"
          />
        </div>

        {/* Region filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Region
          </span>
          <PillToggle
            options={regionOptions}
            value={region}
            onChange={(v) => onRegionChange(v as Region)}
            className="bg-slate-700"
          />
        </div>

        {/* Period filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Period
          </span>
          <PillToggle
            options={periodOptions}
            value={period}
            onChange={(v) => onPeriodChange(v as Period)}
            className="bg-slate-700"
          />
        </div>
      </div>
    </div>
  );
}
