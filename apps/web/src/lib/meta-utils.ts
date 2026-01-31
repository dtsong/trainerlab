import type { MetaSnapshot } from "@trainerlab/shared-types";

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
    region: data.region,
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
