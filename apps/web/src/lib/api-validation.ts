/**
 * Zod schemas for runtime validation of API responses.
 *
 * These schemas validate data at the API boundary to catch type mismatches
 * and ensure data integrity before it enters the application.
 */

import { z } from "zod";

export const DataFreshnessSchema = z.object({
  status: z.enum(["fresh", "stale", "partial", "no_data"]),
  cadence_profile: z.enum([
    "jp_daily_cadence",
    "grassroots_daily_cadence",
    "tpci_event_cadence",
    "default_cadence",
  ]),
  snapshot_date: z.string().nullable().optional(),
  sample_size: z.number().nullable().optional(),
  staleness_days: z.number().nullable().optional(),
  source_coverage: z.array(z.string()).nullable().optional(),
  message: z.string().nullable().optional(),
});

export const PaginationFieldsSchema = z.object({
  total: z.number(),
  page: z.number(),
  limit: z.number(),
  has_next: z.boolean(),
  has_prev: z.boolean(),
  total_pages: z.number(),
  next_cursor: z.string().nullable().optional(),
  freshness: DataFreshnessSchema.nullable().optional(),
});

export const CardSummarySchema = z.object({
  id: z.string(),
  name: z.string(),
  supertype: z.string(),
  types: z.array(z.string()).nullable().optional(),
  set_id: z.string(),
  set_name: z.string(),
  number: z.string(),
  rarity: z.string().nullable().optional(),
  image_small: z.string().nullable().optional(),
  image_large: z.string().nullable().optional(),
});

export const PaginatedCardSummarySchema = PaginationFieldsSchema.extend({
  items: z.array(CardSummarySchema),
});

export const ArchetypeSchema = z.object({
  name: z.string(),
  share: z.number(),
  sprite_urls: z.array(z.string()).nullable().optional(),
  signature_card_image: z.string().nullable().optional(),
  sample_decks: z.array(z.string()).nullable().optional(),
  key_cards: z.array(z.string()).nullable().optional(),
});

export const CardUsageSummarySchema = z.object({
  card_id: z.string(),
  inclusion_rate: z.number(),
  avg_copies: z.number().nullable().optional(),
});

export const FormatNotesSchema = z.object({
  tie_rules: z.string().nullable().optional(),
  typical_regions: z.array(z.string()).nullable().optional(),
  notes: z.string().nullable().optional(),
});

export const TrendInfoSchema = z.object({
  direction: z.enum(["rising", "falling", "stable"]),
  change: z.number(),
  period_days: z.number().optional(),
});

export const JPSignalsSchema = z.object({
  leading_indicators: z.array(z.string()).optional(),
  deck_innovations: z.array(z.string()).optional(),
  format_specific_notes: z.string().nullable().optional(),
});

export const MetaSnapshotSchema = z.object({
  snapshot_date: z.string(),
  region: z.string().nullable().optional(),
  format: z.enum(["standard", "expanded"]),
  best_of: z.number(),
  tournament_type: z.enum(["all", "official", "grassroots"]).optional(),
  archetype_breakdown: z.array(ArchetypeSchema),
  card_usage: z.array(CardUsageSummarySchema).optional(),
  sample_size: z.number(),
  tournaments_included: z.array(z.string()).optional(),
  format_notes: FormatNotesSchema.nullable().optional(),
  diversity_index: z.number().nullable().optional(),
  tier_assignments: z.record(z.string(), z.string()).nullable().optional(),
  jp_signals: JPSignalsSchema.nullable().optional(),
  trends: z.record(z.string(), TrendInfoSchema).nullable().optional(),
  freshness: DataFreshnessSchema.nullable().optional(),
});

export const MetaHistoryResponseSchema = z.object({
  snapshots: z.array(MetaSnapshotSchema),
});

export const LabNoteSchema = z
  .object({
    id: z.string(),
    title: z.string(),
    slug: z.string(),
    note_type: z.string(),
    status: z.string(),
    created_at: z.string(),
    updated_at: z.string(),
  })
  .passthrough();

export const LabNoteListResponseSchema = PaginationFieldsSchema.extend({
  items: z.array(LabNoteSchema),
}).passthrough();

export const TournamentSummarySchema = z
  .object({
    id: z.string(),
    name: z.string(),
    date: z.string(),
    format: z.string(),
    best_of: z.number(),
  })
  .passthrough();

export const TournamentListResponseSchema = PaginationFieldsSchema.extend({
  items: z.array(TournamentSummarySchema),
}).passthrough();

export class ValidationError extends Error {
  constructor(
    message: string,
    public issues: z.ZodIssue[]
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

export function validateApiResponse<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
  endpoint: string
): T {
  const result = schema.safeParse(data);

  if (!result.success) {
    console.error(
      `API validation failed for ${endpoint}:`,
      result.error.issues
    );

    if (process.env.NODE_ENV === "development") {
      throw new ValidationError(
        `API response validation failed for ${endpoint}`,
        result.error.issues
      );
    }

    console.warn(
      `Validation warning for ${endpoint}: returning data despite validation errors`
    );
    return data as T;
  }

  return result.data;
}
