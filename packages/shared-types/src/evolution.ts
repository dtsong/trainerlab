// Evolution API types (snake_case, matching backend schemas)

/**
 * Single adaptation in an evolution snapshot.
 */
export interface ApiAdaptation {
  id: string;
  type: string;
  description?: string | null;
  cards_added?: Record<string, unknown>[] | null;
  cards_removed?: Record<string, unknown>[] | null;
  target_archetype?: string | null;
  confidence?: number | null;
  source?: string | null;
}

/**
 * Evolution snapshot for a single tournament.
 */
export interface ApiEvolutionSnapshot {
  id: string;
  archetype: string;
  tournament_id: string;
  meta_share?: number | null;
  top_cut_conversion?: number | null;
  best_placement?: number | null;
  deck_count: number;
  consensus_list?: Record<string, unknown>[] | null;
  meta_context?: string | null;
  adaptations: ApiAdaptation[];
  created_at?: string | null;
}

/**
 * Timeline of evolution snapshots for an archetype.
 */
export interface ApiEvolutionTimeline {
  archetype: string;
  snapshots: ApiEvolutionSnapshot[];
}

/**
 * Archetype prediction for a tournament.
 */
export interface ApiArchetypePrediction {
  id: string;
  archetype_id: string;
  target_tournament_id: string;
  predicted_meta_share?: { low: number; mid: number; high: number } | null;
  predicted_day2_rate?: { low: number; mid: number; high: number } | null;
  predicted_tier?: string | null;
  likely_adaptations?: Record<string, unknown>[] | null;
  confidence?: number | null;
  methodology?: string | null;
  actual_meta_share?: number | null;
  accuracy_score?: number | null;
  created_at?: string | null;
}

/**
 * Summary of an evolution article for list endpoints.
 */
export interface ApiEvolutionArticleListItem {
  id: string;
  archetype_id: string;
  slug: string;
  title: string;
  excerpt?: string | null;
  status: string;
  is_premium: boolean;
  published_at?: string | null;
}

/**
 * Full evolution article response.
 */
export interface ApiEvolutionArticle {
  id: string;
  archetype_id: string;
  slug: string;
  title: string;
  excerpt?: string | null;
  introduction?: string | null;
  conclusion?: string | null;
  status: string;
  is_premium: boolean;
  published_at?: string | null;
  view_count: number;
  share_count: number;
  snapshots: ApiEvolutionSnapshot[];
}

/**
 * Prediction accuracy tracking summary.
 */
export interface ApiPredictionAccuracy {
  total_predictions: number;
  scored_predictions: number;
  average_accuracy?: number | null;
  predictions: ApiArchetypePrediction[];
}
