// Tournament types (matching backend schemas)

import type { ApiDataFreshness } from "./freshness";

export type TournamentTier =
  | "major"
  | "premier"
  | "league"
  | "grassroots"
  | "worlds"
  | "international"
  | "regional"
  | "special";
export type GameFormat = "standard" | "expanded";

export interface ApiTopPlacement {
  placement: number;
  player_name?: string | null;
  archetype: string;
}

export interface ApiPlacementDetail {
  id: string;
  placement: number;
  player_name?: string | null;
  archetype: string;
  has_decklist: boolean;
}

export interface ApiArchetypeMeta {
  archetype: string;
  count: number;
  share: number;
}

export interface ApiTournamentSummary {
  id: string;
  name: string;
  date: string;
  region: string;
  country?: string | null;
  format: GameFormat;
  best_of: 1 | 3;
  tier?: TournamentTier | null;
  participant_count?: number | null;
  major_format_key?: string | null;
  major_format_label?: string | null;
  top_placements: ApiTopPlacement[];
}

export interface ApiTournamentDetail {
  id: string;
  name: string;
  date: string;
  region: string;
  country?: string | null;
  format: GameFormat;
  best_of: 1 | 3;
  tier?: TournamentTier | null;
  participant_count?: number | null;
  major_format_key?: string | null;
  major_format_label?: string | null;
  source?: string | null;
  source_url?: string | null;
  placements: ApiPlacementDetail[];
  meta_breakdown: ApiArchetypeMeta[];
}

export interface ApiTournamentListResponse {
  items: ApiTournamentSummary[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  freshness?: ApiDataFreshness | null;
}

export interface ApiDecklistCard {
  card_id: string;
  card_name: string;
  quantity: number;
  supertype?: string | null;
}

export interface ApiDecklistResponse {
  placement_id: string;
  player_name?: string | null;
  archetype: string;
  tournament_name: string;
  tournament_date: string;
  source_url?: string | null;
  cards: ApiDecklistCard[];
  total_cards: number;
}

// Frontend types (camelCase)

export interface TopPlacement {
  placement: number;
  playerName?: string;
  archetype: string;
}

export interface TournamentSummary {
  id: string;
  name: string;
  date: string;
  region: string;
  country?: string;
  format: GameFormat;
  bestOf: 1 | 3;
  tier?: TournamentTier;
  participantCount?: number;
  topPlacements: TopPlacement[];
}
