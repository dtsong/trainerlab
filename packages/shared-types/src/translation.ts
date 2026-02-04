// Translation API types (snake_case, matching backend schemas)

export type TranslationStatus = "pending" | "completed" | "failed";
export type ContentType =
  | "article"
  | "tournament_result"
  | "tier_list"
  | "deck_list"
  | "meta_report"
  | "card_text";

/**
 * JP card adoption rate from meta sources.
 */
export interface ApiJPAdoptionRate {
  id: string;
  card_id: string;
  card_name_jp: string | null;
  card_name_en: string | null;
  inclusion_rate: number;
  avg_copies: number | null;
  archetype_context: string | null;
  period_start: string;
  period_end: string;
  source: string | null;
}

/**
 * List of JP adoption rates.
 */
export interface ApiJPAdoptionRateList {
  rates: ApiJPAdoptionRate[];
  total: number;
}

/**
 * JP unreleased card not yet available internationally.
 */
export interface ApiJPUnreleasedCard {
  id: string;
  jp_card_id: string;
  jp_set_id: string | null;
  name_jp: string;
  name_en: string | null;
  card_type: string | null;
  competitive_impact: number;
  affected_archetypes: string[] | null;
  notes: string | null;
  expected_release_set: string | null;
  is_released: boolean;
}

/**
 * List of JP unreleased cards.
 */
export interface ApiJPUnreleasedCardList {
  cards: ApiJPUnreleasedCard[];
  total: number;
}

/**
 * Translated content item.
 */
export interface ApiTranslatedContent {
  id: string;
  source_id: string;
  source_url: string;
  content_type: string;
  original_text: string;
  translated_text: string | null;
  status: TranslationStatus;
  translated_at: string | null;
  uncertainties: string[] | null;
}

/**
 * List of translated content.
 */
export interface ApiTranslatedContentList {
  content: ApiTranslatedContent[];
  total: number;
}

/**
 * Request to submit a URL for translation.
 */
export interface ApiSubmitTranslationRequest {
  url: string;
  content_type: ContentType;
  context?: string | null;
}

/**
 * Request to update a translation.
 */
export interface ApiUpdateTranslationRequest {
  translated_text?: string | null;
  status?: TranslationStatus | null;
}

/**
 * Glossary term override.
 */
export interface ApiGlossaryTermOverride {
  id: string;
  term_jp: string;
  term_en: string;
  context: string | null;
  source: string | null;
  is_active: boolean;
}

/**
 * List of glossary term overrides.
 */
export interface ApiGlossaryTermOverrideList {
  terms: ApiGlossaryTermOverride[];
  total: number;
}

/**
 * Request to create/update a glossary term.
 */
export interface ApiGlossaryTermCreateRequest {
  term_jp: string;
  term_en: string;
  context?: string | null;
}
