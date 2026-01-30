/**
 * Set-related TypeScript types matching API schemas (snake_case).
 * These types match the JSON responses from the FastAPI backend.
 */

export interface ApiSet {
  // Identifiers
  id: string;
  name: string;
  series: string;

  // Release info
  release_date?: string | null;
  release_date_jp?: string | null;
  card_count?: number | null;

  // Images
  logo_url?: string | null;
  symbol_url?: string | null;

  // Legalities
  legalities?: Record<string, string> | null;

  // Timestamps
  created_at: string;
  updated_at: string;
}
