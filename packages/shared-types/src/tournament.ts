// Tournament types (matching backend schemas)

export type TournamentTier = "major" | "premier" | "league";
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
