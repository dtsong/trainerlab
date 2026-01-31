// Meta dashboard types (matching backend schemas)

export interface ApiArchetype {
  name: string;
  share: number;
  sample_decks?: string[] | null;
  key_cards?: string[] | null;
}

export interface ApiCardUsageSummary {
  card_id: string;
  inclusion_rate: number;
  avg_copies: number;
}

export interface ApiMetaSnapshot {
  snapshot_date: string;
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

export interface Archetype {
  name: string;
  share: number;
  sampleDecks?: string[];
  keyCards?: string[];
}

export interface CardUsageSummary {
  cardId: string;
  inclusionRate: number;
  avgCopies: number;
}

export interface MetaSnapshot {
  snapshotDate: string;
  region: string | null;
  format: "standard" | "expanded";
  bestOf: 1 | 3;
  archetypeBreakdown: Archetype[];
  cardUsage: CardUsageSummary[];
  sampleSize: number;
  tournamentsIncluded?: string[];
}

export type Region = "global" | "NA" | "EU" | "JP" | "LATAM" | "OCE";

export interface MetaFilters {
  region: Region;
  format: "standard" | "expanded";
  bestOf: 1 | 3;
  days: number;
}
