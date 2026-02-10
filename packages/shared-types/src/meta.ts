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
  card_name?: string | null;
  image_small?: string | null;
  inclusion_rate: number;
  avg_copies: number;
}

export interface ApiMetaSnapshot {
  snapshot_date: string;
  /** Raw region from API - validated to Region type in transformSnapshot */
  region: string | null;
  format: "standard" | "expanded";
  best_of: 1 | 3;
  tournament_type?: TournamentType;
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

export type TournamentType = "all" | "official" | "grassroots";

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
  tournamentType?: TournamentType;
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
  tournamentType?: TournamentType;
}

// --- Archetype Detail API types ---

export interface ApiKeyCardResponse {
  card_id: string;
  card_name?: string | null;
  image_small?: string | null;
  inclusion_rate: number;
  avg_copies: number;
}

export interface ApiArchetypeHistoryPoint {
  snapshot_date: string;
  share: number;
  sample_size: number;
}

export interface ApiArchetypeDetailResponse {
  name: string;
  current_share: number;
  history: ApiArchetypeHistoryPoint[];
  key_cards: ApiKeyCardResponse[];
  sample_decks: {
    deck_id: string;
    tournament_name: string | null;
    placement: number | null;
    player_name: string | null;
  }[];
}

// --- Comparison & Forecast API types ---

export interface ApiConfidenceIndicator {
  sample_size: number;
  data_freshness_days: number;
  confidence: "high" | "medium" | "low";
}

export interface ApiArchetypeComparison {
  archetype: string;
  region_a_share: number;
  region_b_share: number;
  divergence: number;
  region_a_tier: string | null;
  region_b_tier: string | null;
  sprite_urls: string[];
}

export interface ApiLagAnalysis {
  lag_days: number;
  jp_snapshot_date: string;
  en_snapshot_date: string;
  lagged_comparisons: ApiArchetypeComparison[];
}

export interface ApiMetaComparisonResponse {
  region_a: string;
  region_b: string;
  region_a_snapshot_date: string;
  region_b_snapshot_date: string;
  comparisons: ApiArchetypeComparison[];
  region_a_confidence: ApiConfidenceIndicator;
  region_b_confidence: ApiConfidenceIndicator;
  lag_analysis: ApiLagAnalysis | null;
}

export interface ApiFormatForecastEntry {
  archetype: string;
  jp_share: number;
  en_share: number;
  divergence: number;
  tier: string | null;
  trend_direction: "up" | "down" | "stable" | null;
  sprite_urls: string[];
  confidence: "high" | "medium" | "low";
}

export interface ApiFormatForecastResponse {
  forecast_archetypes: ApiFormatForecastEntry[];
  jp_snapshot_date: string;
  en_snapshot_date: string;
  jp_sample_size: number;
  en_sample_size: number;
}
