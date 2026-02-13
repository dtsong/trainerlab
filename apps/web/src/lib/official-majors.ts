import type { TournamentTier } from "@trainerlab/shared-types";

export const OFFICIAL_MAJOR_TIERS: TournamentTier[] = [
  "major",
  "worlds",
  "international",
  "regional",
  "special",
];

export const MAJOR_FORMAT_FILTER_OPTIONS = [
  { value: "all", label: "All Major Windows" },
  { value: "svi-pfl", label: "SVI-PFL (Feb 2026)" },
  { value: "svi-asc", label: "SVI-ASC (Mar 2026)" },
  { value: "tef-por", label: "TEF-POR (Apr-Jun 2026)" },
  { value: "chaos-rising", label: "TEF-COR (Jun 2026+)" },
] as const;

export const SEASON_FILTER_OPTIONS = [
  { value: "all", label: "All Seasons" },
  { value: "2026", label: "2026" },
] as const;

export type MajorFormatFilterValue =
  (typeof MAJOR_FORMAT_FILTER_OPTIONS)[number]["value"];

export type SeasonFilterValue = (typeof SEASON_FILTER_OPTIONS)[number]["value"];

export function isOfficialMajorTier(tier: string | null | undefined): boolean {
  if (!tier) {
    return false;
  }

  return OFFICIAL_MAJOR_TIERS.includes(tier as TournamentTier);
}

export function getMajorFormatBadgeText(
  majorFormatKey: string | null | undefined,
  majorFormatLabel: string | null | undefined
): string | null {
  if (majorFormatKey) {
    return majorFormatKey.toUpperCase();
  }

  if (majorFormatLabel) {
    return majorFormatLabel;
  }

  return null;
}
