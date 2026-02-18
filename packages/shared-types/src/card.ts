/**
 * Card-related TypeScript types matching API schemas (snake_case).
 * These types match the JSON responses from the FastAPI backend.
 */

export interface ApiAttack {
  name: string;
  cost: string[];
  damage?: string | null;
  effect?: string | null;
}

export interface ApiAbility {
  name: string;
  type?: string | null;
  effect?: string | null;
}

export interface ApiWeaknessResistance {
  type: string;
  value: string;
}

export interface ApiSetSummary {
  id: string;
  name: string;
  series: string;
  release_date?: string | null;
  logo_url?: string | null;
  symbol_url?: string | null;
}

export interface ApiCardSummary {
  id: string;
  name: string;
  supertype: string;
  types?: string[] | null;
  set_id: string;
  rarity?: string | null;
  image_small?: string | null;
}

export interface ApiCard {
  // Identifiers
  id: string;
  local_id: string;
  name: string;
  japanese_name?: string | null;

  // Card type
  supertype: string;
  subtypes?: string[] | null;
  types?: string[] | null;

  // Pokemon stats
  hp?: number | null;
  stage?: string | null;
  evolves_from?: string | null;
  evolves_to?: string[] | null;

  // Game mechanics
  attacks?: ApiAttack[] | null;
  abilities?: ApiAbility[] | null;
  weaknesses?: ApiWeaknessResistance[] | null;
  resistances?: ApiWeaknessResistance[] | null;
  retreat_cost?: number | null;
  rules?: string[] | null;

  // Set info
  set_id: string;
  rarity?: string | null;
  number?: string | null;

  // Images
  image_small?: string | null;
  image_large?: string | null;

  // Legality
  regulation_mark?: string | null;
  legalities?: Record<string, boolean> | null;

  // Timestamps
  created_at: string;
  updated_at: string;

  // Nested relationships
  set?: ApiSetSummary | null;
}

export interface ApiCardArchetypeUsage {
  archetype: string;
  inclusion_rate: number;
  avg_copies: number;
}

export interface ApiCardArchetypeUsageResponse {
  card_id: string;
  archetype_usage: ApiCardArchetypeUsage[];
}
