// Meta dashboard types (matching backend schemas)

export interface ApiArchetype {
  name: string;
  share: number;
  sample_decks?: string[] | null;
  key_cards?: string[] | null;
  sprite_urls?: string[] | null;
}

export interface ApiCardUsageSummary {
  card_id: string;
  inclusion_rate: number;
  avg_copies: number;
}

export interface ApiMetaSnapshot {
  snapshot_date: string;
  /** Raw region from API - validated to Region type in transformSnapshot */
  region: string | null;
  format: "standard" | "expanded";
  best_of: 1 | 3;
  archetype_breakdown: ApiArchetype[];
  card_usage: ApiCardUsageSummary[];
  sample_size: number;
  tournaments_included?: string[] | null;
}

export interface ApiMetaHistoryResponse {
  snapshots: ApiMetaSnapshot[];
}

// Frontend types (camelCase)

export type Region = "global" | "NA" | "EU" | "JP" | "LATAM" | "OCE";

export interface Archetype {
  name: string;
  share: number;
  sampleDecks?: string[];
  keyCards?: string[];
  spriteUrls?: string[];
}

export interface CardUsageSummary {
  cardId: string;
  inclusionRate: number;
  avgCopies: number;
}

export interface MetaSnapshot {
  snapshotDate: string;
  region: Region | null;
  format: "standard" | "expanded";
  bestOf: 1 | 3;
  archetypeBreakdown: Archetype[];
  cardUsage: CardUsageSummary[];
  sampleSize: number;
  tournamentsIncluded?: string[];
}

export interface MetaFilters {
  region: Region;
  format: "standard" | "expanded";
  bestOf: 1 | 3;
  days: number;
}
