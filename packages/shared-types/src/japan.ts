// Japan intelligence API types (snake_case, matching backend schemas)

export type AdoptionTrend = "rising" | "stable" | "falling";
export type PredictionOutcome = "correct" | "partial" | "incorrect";
export type PredictionConfidence = "high" | "medium" | "low";

/**
 * JP card innovation tracker response.
 */
export interface ApiJPCardInnovation {
  id: string;
  card_id: string;
  card_name: string;
  card_name_jp?: string | null;
  set_code: string;
  set_release_jp?: string | null;
  set_release_en?: string | null;
  is_legal_en: boolean;
  adoption_rate: number;
  adoption_trend?: AdoptionTrend | null;
  archetypes_using?: string[] | null;
  competitive_impact_rating: number;
  sample_size: number;
}

/**
 * JP card innovation with full analysis.
 */
export interface ApiJPCardInnovationDetail extends ApiJPCardInnovation {
  impact_analysis?: string | null;
}

/**
 * List of JP card innovations.
 */
export interface ApiJPCardInnovationList {
  items: ApiJPCardInnovation[];
  total: number;
}

/**
 * City League tournament result.
 */
export interface ApiCityLeagueResult {
  tournament: string;
  date: string;
  placements: number[];
}

/**
 * JP-only archetype not in EN meta.
 */
export interface ApiJPNewArchetype {
  id: string;
  archetype_id: string;
  name: string;
  name_jp?: string | null;
  key_cards?: string[] | null;
  enabled_by_set?: string | null;
  jp_meta_share: number;
  jp_trend?: AdoptionTrend | null;
  city_league_results?: ApiCityLeagueResult[] | null;
  estimated_en_legal_date?: string | null;
  analysis?: string | null;
}

/**
 * List of JP-only archetypes.
 */
export interface ApiJPNewArchetypeList {
  items: ApiJPNewArchetype[];
  total: number;
}

/**
 * Meta breakdown entry.
 */
export interface ApiMetaBreakdownEntry {
  archetype: string;
  share: number;
}

/**
 * JP set impact history.
 */
export interface ApiJPSetImpact {
  id: string;
  set_code: string;
  set_name: string;
  jp_release_date: string;
  en_release_date?: string | null;
  jp_meta_before?: ApiMetaBreakdownEntry[] | null;
  jp_meta_after?: ApiMetaBreakdownEntry[] | null;
  key_innovations?: string[] | null;
  new_archetypes?: string[] | null;
  analysis?: string | null;
}

/**
 * List of JP set impacts.
 */
export interface ApiJPSetImpactList {
  items: ApiJPSetImpact[];
  total: number;
}

/**
 * Prediction with outcome.
 */
export interface ApiPrediction {
  id: string;
  prediction_text: string;
  target_event: string;
  target_date?: string | null;
  created_at: string;
  resolved_at?: string | null;
  outcome?: PredictionOutcome | null;
  confidence?: PredictionConfidence | null;
  category?: string | null;
  reasoning?: string | null;
  outcome_notes?: string | null;
}

/**
 * List of predictions with accuracy stats.
 */
export interface ApiPredictionList {
  items: ApiPrediction[];
  total: number;
  resolved: number;
  correct: number;
  partial: number;
  incorrect: number;
  accuracy_rate?: number | null;
}

/**
 * Card count data point for a specific snapshot date.
 */
export interface ApiCardCountDataPoint {
  snapshot_date: string;
  avg_copies: number;
  inclusion_rate: number;
  sample_size: number;
}

/**
 * Card count evolution for a single card within an archetype.
 */
export interface ApiCardCountEvolution {
  card_id: string;
  card_name: string;
  data_points: ApiCardCountDataPoint[];
  total_change: number;
  current_avg: number;
}

/**
 * Card count evolution response for an archetype.
 */
export interface ApiCardCountEvolutionResponse {
  archetype: string;
  cards: ApiCardCountEvolution[];
  tournaments_analyzed: number;
}

// JP Content API types
export interface ApiJPContentItem {
  id: string;
  source_url: string;
  content_type: string;
  title_en: string | null;
  title_jp: string | null;
  translated_text: string | null;
  published_date: string | null;
  source_name: string | null;
  tags: string[] | null;
  archetype_refs: string[] | null;
  era_label: string | null;
  review_status: string;
  translated_at: string | null;
}

export interface ApiJPContentList {
  items: ApiJPContentItem[];
  total: number;
}
