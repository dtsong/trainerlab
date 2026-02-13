import type {
  Archetype,
  MetaSnapshot,
  Region,
  TournamentType,
  ApiMetaSnapshot,
} from "@trainerlab/shared-types";
import { ApiError } from "./api";

const VALID_REGIONS: Region[] = ["global", "NA", "EU", "JP", "LATAM", "OCE"];

/**
 * Type guard to check if a string is a valid Region.
 */
export function isValidRegion(value: string | null): value is Region {
  return value !== null && VALID_REGIONS.includes(value as Region);
}

/**
 * Parse and validate a region from a string, returning a default if invalid.
 */
export function parseRegion(
  value: string | null | undefined,
  defaultRegion: Region = "global"
): Region {
  if (value && isValidRegion(value)) {
    return value;
  }
  if (value) {
    console.warn(
      `[parseRegion] Invalid region "${value}", using default "${defaultRegion}"`
    );
  }
  return defaultRegion;
}

/**
 * Parse and validate days from a string, returning a default if invalid.
 * Valid range is 1-365 days.
 */
export function parseDays(
  value: string | null | undefined,
  defaultDays: number = 30
): number {
  if (!value) return defaultDays;
  const parsed = parseInt(value, 10);
  if (isNaN(parsed) || parsed < 1 || parsed > 365) {
    console.warn(
      `[parseDays] Invalid days value "${value}", using default ${defaultDays}`
    );
    return defaultDays;
  }
  return parsed;
}

/**
 * Get a user-friendly error message from an API error.
 * @param error The error to extract a message from
 * @param context Optional context for 404 errors (e.g., "Japan meta")
 */
export function getErrorMessage(error: unknown, context?: string): string {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return "Unable to connect to the server. Please check your internet connection.";
    }
    if (error.status >= 500) {
      return "Server error. Please try again later.";
    }
    if (error.status === 404) {
      return context
        ? `${context} data not found for the selected filters.`
        : "Meta data not found for the selected filters.";
    }
    return `Error loading data (${error.status}). Please try again.`;
  }
  return "An unexpected error occurred. Please try again.";
}

/**
 * Transforms API response data (snake_case) to frontend format (camelCase).
 * Validates region values and converts null arrays to undefined.
 */
export function transformSnapshot(data: ApiMetaSnapshot): MetaSnapshot {
  return {
    snapshotDate: data.snapshot_date,
    region: isValidRegion(data.region) ? data.region : null,
    format: data.format,
    bestOf: data.best_of,
    tournamentType: data.tournament_type,
    archetypeBreakdown: data.archetype_breakdown.map((a) => ({
      name: a.name,
      share: a.share,
      keyCards: a.key_cards ?? undefined,
      spriteUrls: a.sprite_urls ?? undefined,
    })),
    cardUsage: data.card_usage.map((c) => ({
      cardId: c.card_id,
      cardName: c.card_name ?? undefined,
      imageSmall: c.image_small ?? undefined,
      inclusionRate: c.inclusion_rate,
      avgCopies: c.avg_copies,
    })),
    sampleSize: data.sample_size,
  };
}

const VALID_TOURNAMENT_TYPES: TournamentType[] = [
  "all",
  "official",
  "grassroots",
];

export function isValidTournamentType(
  value: string | null
): value is TournamentType {
  return (
    value !== null && VALID_TOURNAMENT_TYPES.includes(value as TournamentType)
  );
}

export function parseTournamentType(
  value: string | null | undefined,
  defaultType: TournamentType = "all"
): TournamentType {
  if (value && isValidTournamentType(value)) {
    return value;
  }
  return defaultType;
}

/**
 * Safely format an ISO date string, returning the raw value if parsing fails.
 */
export function safeFormatDate(
  isoString: string,
  formatString: string,
  formatFn: (date: Date, format: string) => string,
  parseISOFn: (dateString: string) => Date
): string {
  try {
    const parsed = parseISOFn(isoString);
    if (isNaN(parsed.getTime())) {
      console.warn("[safeFormatDate] Invalid date value:", isoString);
      return isoString;
    }
    return formatFn(parsed, formatString);
  } catch (error) {
    console.warn("[safeFormatDate] Failed to parse date:", isoString, error);
    return isoString;
  }
}

/**
 * Result of grouping archetypes into top N + "Other".
 */
export interface GroupedArchetypes {
  displayed: Archetype[];
  other: { share: number; count: number; archetypes: Archetype[] } | null;
}

/**
 * Group archetypes into displayed + "Other".
 *
 * When `minShare` is provided, only archetypes meeting the threshold are
 * displayed (up to `topN`). Otherwise falls back to a simple top-N split.
 */
export function groupArchetypes(
  archetypes: Archetype[],
  { topN = 15, minShare }: { topN?: number; minShare?: number } = {}
): GroupedArchetypes {
  const sorted = [...archetypes].sort((a, b) => b.share - a.share);

  let displayed: Archetype[];
  let rest: Archetype[];

  if (minShare !== undefined) {
    const aboveThreshold = sorted.filter((a) => a.share >= minShare);
    displayed = aboveThreshold.slice(0, topN);
    rest = sorted.filter((a) => !displayed.includes(a));
  } else {
    if (sorted.length <= topN) {
      return { displayed: sorted, other: null };
    }
    displayed = sorted.slice(0, topN);
    rest = sorted.slice(topN);
  }

  if (rest.length === 0) {
    return { displayed, other: null };
  }

  const otherShare = rest.reduce((sum, a) => sum + a.share, 0);

  return {
    displayed,
    other: { share: otherShare, count: rest.length, archetypes: rest },
  };
}
