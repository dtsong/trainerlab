"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";
import type { TournamentType } from "@trainerlab/shared-types";

interface TournamentTrackNavProps {
  basePath: "/meta" | "/meta/japan";
  activeType: TournamentType;
  className?: string;
}

const TRACKS: { type: TournamentType; label: string }[] = [
  { type: "all", label: "Combined" },
  { type: "official", label: "Official" },
  { type: "grassroots", label: "Grassroots" },
];

function buildTrackHref(
  basePath: TournamentTrackNavProps["basePath"],
  type: TournamentType
) {
  if (type === "all") return basePath;
  return `${basePath}/${type}`;
}

export function TournamentTrackNav({
  basePath,
  activeType,
  className,
}: TournamentTrackNavProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {TRACKS.map((track) => {
        const isActive = activeType === track.type;

        return (
          <Link
            key={track.type}
            href={buildTrackHref(basePath, track.type)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              isActive
                ? "border-teal-500 bg-teal-50 text-teal-700"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900"
            )}
          >
            {track.label}
          </Link>
        );
      })}
    </div>
  );
}
