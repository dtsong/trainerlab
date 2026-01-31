import type { MetaSnapshot, Region } from "@trainerlab/shared-types";

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
  defaultRegion: Region = "global",
): Region {
  if (value && isValidRegion(value)) {
    return value;
  }
  return defaultRegion;
}

/**
 * Parse and validate days from a string, returning a default if invalid.
 */
export function parseDays(
  value: string | null | undefined,
  defaultDays: number = 30,
): number {
  if (!value) return defaultDays;
  const parsed = parseInt(value, 10);
  if (isNaN(parsed) || parsed < 1 || parsed > 365) {
    return defaultDays;
  }
  return parsed;
}

export interface ApiMetaSnapshotData {
  snapshot_date: string;
  region: string | null;
  format: "standard" | "expanded";
  best_of: 1 | 3;
  archetype_breakdown: {
    name: string;
    share: number;
    key_cards?: string[] | null;
  }[];
  card_usage: {
    card_id: string;
    inclusion_rate: number;
    avg_copies: number;
  }[];
  sample_size: number;
}

export function transformSnapshot(data: ApiMetaSnapshotData): MetaSnapshot {
  return {
    snapshotDate: data.snapshot_date,
    region: isValidRegion(data.region) ? data.region : null,
    format: data.format,
    bestOf: data.best_of,
    archetypeBreakdown: data.archetype_breakdown.map((a) => ({
      name: a.name,
      share: a.share,
      keyCards: a.key_cards ?? undefined,
    })),
    cardUsage: data.card_usage.map((c) => ({
      cardId: c.card_id,
      inclusionRate: c.inclusion_rate,
      avgCopies: c.avg_copies,
    })),
    sampleSize: data.sample_size,
  };
}

/**
 * Safely format an ISO date string, returning the raw value if parsing fails.
 */
export function safeFormatDate(
  isoString: string,
  formatString: string,
  formatFn: (date: Date, format: string) => string,
  parseISOFn: (dateString: string) => Date,
): string {
  try {
    const parsed = parseISOFn(isoString);
    if (isNaN(parsed.getTime())) {
      return isoString;
    }
    return formatFn(parsed, formatString);
  } catch {
    return isoString;
  }
}
