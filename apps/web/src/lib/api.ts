/**
 * API client for TrainerLab backend.
 */

import type {
  ApiCard,
  ApiCardSummary,
  ApiSet,
  ApiPaginatedResponse,
  ApiMetaSnapshot,
  ApiMetaHistoryResponse,
  ApiMetaComparisonResponse,
  ApiFormatForecastResponse,
  ApiArchetypeDetailResponse,
  ApiArchetype,
  ApiFormatConfig,
  ApiUpcomingFormat,
  ApiRotationImpactList,
  ApiRotationImpact,
  ApiTournamentListResponse,
  ApiTournamentDetail,
  ApiDecklistResponse,
  TournamentTier,
  ApiLabNoteListResponse,
  ApiLabNote,
  ApiLabNoteRevision,
  ApiLabNoteCreateRequest,
  ApiLabNoteUpdateRequest,
  ApiLabNoteStatusUpdate,
  LabNoteType,
  LabNoteStatus,
  ApiJPCardInnovationList,
  ApiJPCardInnovationDetail,
  ApiJPNewArchetypeList,
  ApiJPSetImpactList,
  ApiPredictionList,
  ApiCardCountEvolutionResponse,
  ApiEvolutionTimeline,
  ApiArchetypePrediction,
  ApiEvolutionArticleListItem,
  ApiEvolutionArticle,
  ApiPredictionAccuracy,
  ApiJPAdoptionRateList,
  ApiJPUnreleasedCardList,
  ApiTranslatedContent,
  ApiTranslatedContentList,
  ApiSubmitTranslationRequest,
  ApiUpdateTranslationRequest,
  ApiGlossaryTermOverride,
  ApiGlossaryTermOverrideList,
  ApiGlossaryTermCreateRequest,
  ContentType,
  ApiJPContentList,
  ApiWidgetCreate,
  ApiWidgetUpdate,
  ApiWidgetResponse,
  ApiWidgetDataResponse,
  ApiWidgetEmbedCodeResponse,
  ApiWidgetListResponse,
  ApiExportCreate,
  ApiExportResponse,
  ApiExportDownloadResponse,
  ApiExportListResponse,
  ApiApiKeyCreate,
  ApiApiKeyResponse,
  ApiApiKeyCreatedResponse,
  ApiApiKeyListResponse,
  ApiEventSummary,
  ApiEventDetail,
  ApiEventListResponse,
  ApiTripCreate,
  ApiTripUpdate,
  ApiTripEventAdd,
  ApiTripSummary,
  ApiTripDetail,
  ApiSharedTripView,
  EventStatus,
} from "@trainerlab/shared-types";
import type { z } from "zod";

import {
  validateApiResponse,
  PaginatedCardSummarySchema,
  MetaSnapshotSchema,
  MetaHistoryResponseSchema,
  ArchetypeSchema,
  LabNoteListResponseSchema,
  LabNoteSchema,
  TournamentListResponseSchema,
} from "./api-validation";

// Admin data dashboard types
interface AdminTableInfo {
  name: string;
  row_count: number;
  latest_date: string | null;
  detail: string | null;
}

interface AdminDataOverview {
  tables: AdminTableInfo[];
  generated_at: string;
}

interface AdminMetaSnapshotSummary {
  id: string;
  snapshot_date: string;
  region: string | null;
  format: string;
  best_of: number;
  sample_size: number;
  archetype_count: number;
  diversity_index: number | null;
}

interface AdminMetaSnapshotList {
  items: AdminMetaSnapshotSummary[];
  total: number;
}

interface AdminMetaSnapshotDetail extends AdminMetaSnapshotSummary {
  archetype_shares: Record<string, number>;
  tier_assignments: Record<string, string> | null;
  card_usage: Record<string, unknown> | null;
  jp_signals: Record<string, unknown> | null;
  trends: Record<string, unknown> | null;
  tournaments_included: string[] | null;
}

interface AdminPipelineHealthItem {
  name: string;
  status: string;
  last_run: string | null;
  days_since_run: number | null;
}

interface AdminPipelineHealth {
  pipelines: AdminPipelineHealthItem[];
  checked_at: string;
}

export interface ApiCurrentUser {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_beta_tester: boolean;
  is_creator: boolean;
  preferences: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiPublicTeaserArchetype {
  name: string;
  global_share: number;
  jp_share: number | null;
  divergence_pp: number | null;
}

export interface ApiPublicHomeTeaser {
  snapshot_date: string | null;
  delay_days: number;
  sample_size: number;
  top_archetypes: ApiPublicTeaserArchetype[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
  } catch (error) {
    console.error("Network error fetching", endpoint, error);
    throw new ApiError(
      "Network error: Unable to reach the server. Please check your connection.",
      0,
      { originalError: error }
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => undefined);
    console.error("API error", endpoint, response.status, body);
    throw new ApiError(
      `API request failed: ${response.status} ${response.statusText}`,
      response.status,
      body
    );
  }

  try {
    return await response.json();
  } catch (error) {
    console.error("JSON parse error", endpoint, error);
    throw new ApiError("Server returned invalid data format", response.status, {
      parseError: error,
    });
  }
}

async function fetchApiValidated<T, S>(
  endpoint: string,
  schema: z.ZodSchema<S>,
  options?: RequestInit
): Promise<T> {
  const data = await fetchApi<unknown>(endpoint, options);
  validateApiResponse(schema, data, endpoint);
  return data as T;
}

/**
 * Fetch the raw JWT from the NextAuth token endpoint.
 * Returns null if the user is not authenticated.
 */
async function getAuthToken(): Promise<string | null> {
  try {
    const res = await fetch("/api/auth/token");
    if (!res.ok) return null;
    const data = await res.json();
    return data.token ?? null;
  } catch (error) {
    console.error("Failed to retrieve auth token:", error);
    return null;
  }
}

/**
 * Authenticated fetch wrapper. Adds the JWT Bearer token automatically.
 * Throws ApiError if the user is not authenticated.
 */
async function fetchApiAuth<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = await getAuthToken();
  if (!token) {
    throw new ApiError("Not authenticated", 401);
  }
  return fetchApi<T>(endpoint, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}

// Card search parameters
export interface CardSearchParams {
  q?: string;
  supertype?: string;
  types?: string;
  set_id?: string;
  standard?: boolean;
  expanded?: boolean;
  page?: number;
  limit?: number;
}

// Cards API
export const cardsApi = {
  search: (params: CardSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.q) searchParams.set("q", params.q);
    if (params.supertype) searchParams.set("supertype", params.supertype);
    if (params.types) searchParams.set("types", params.types);
    if (params.set_id) searchParams.set("set_id", params.set_id);
    if (params.standard !== undefined)
      searchParams.set("standard", String(params.standard));
    if (params.expanded !== undefined)
      searchParams.set("expanded", String(params.expanded));
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApiValidated<ApiPaginatedResponse<ApiCardSummary>, unknown>(
      `/api/v1/cards${query ? `?${query}` : ""}`,
      PaginatedCardSummarySchema
    );
  },

  getById: (id: string) => {
    return fetchApi<ApiCard>(`/api/v1/cards/${encodeURIComponent(id)}`);
  },

  getBatch: (ids: string[]) => {
    return fetchApi<ApiCardSummary[]>(
      `/api/v1/cards/batch?ids=${ids.map(encodeURIComponent).join(",")}`
    );
  },
};

// Sets API
export const setsApi = {
  list: () => {
    return fetchApi<ApiSet[]>("/api/v1/sets");
  },

  getById: (id: string) => {
    return fetchApi<ApiSet>(`/api/v1/sets/${encodeURIComponent(id)}`);
  },

  getCards: (id: string, page = 1, limit = 20) => {
    return fetchApi<ApiPaginatedResponse<ApiCardSummary>>(
      `/api/v1/sets/${encodeURIComponent(id)}/cards?page=${page}&limit=${limit}`
    );
  },
};

// Meta search parameters
export interface MetaSearchParams {
  region?: string | null;
  format?: "standard" | "expanded";
  best_of?: 1 | 3;
  days?: number;
  era?: string;
  tournament_type?: "all" | "official" | "grassroots";
}

export interface MetaCompareParams {
  region_a?: string;
  region_b?: string;
  format?: "standard" | "expanded";
  lag_days?: number;
  top_n?: number;
}

export interface MetaForecastParams {
  format?: "standard" | "expanded";
  top_n?: number;
}

// Meta API
export const metaApi = {
  getCurrent: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));
    if (params.era) searchParams.set("era", params.era);
    if (params.tournament_type && params.tournament_type !== "all")
      searchParams.set("tournament_type", params.tournament_type);

    const query = searchParams.toString();
    return fetchApiValidated<ApiMetaSnapshot, unknown>(
      `/api/v1/meta/current${query ? `?${query}` : ""}`,
      MetaSnapshotSchema
    );
  },

  getHistory: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));
    if (params.days) searchParams.set("days", String(params.days));
    if (params.era) searchParams.set("era", params.era);
    if (params.tournament_type && params.tournament_type !== "all")
      searchParams.set("tournament_type", params.tournament_type);

    const query = searchParams.toString();
    return fetchApiValidated<ApiMetaHistoryResponse, unknown>(
      `/api/v1/meta/history${query ? `?${query}` : ""}`,
      MetaHistoryResponseSchema
    );
  },

  getArchetypes: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));
    if (params.tournament_type && params.tournament_type !== "all")
      searchParams.set("tournament_type", params.tournament_type);

    const query = searchParams.toString();
    return fetchApiValidated<ApiArchetype[], unknown>(
      `/api/v1/meta/archetypes${query ? `?${query}` : ""}`,
      ArchetypeSchema.array()
    );
  },

  getArchetypeDetail: (name: string, params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));
    if (params.tournament_type && params.tournament_type !== "all")
      searchParams.set("tournament_type", params.tournament_type);

    const query = searchParams.toString();
    return fetchApi<ApiArchetypeDetailResponse>(
      `/api/v1/meta/archetypes/${encodeURIComponent(name)}${query ? `?${query}` : ""}`
    );
  },

  compare: (params: MetaCompareParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region_a) searchParams.set("region_a", params.region_a);
    if (params.region_b) searchParams.set("region_b", params.region_b);
    if (params.format) searchParams.set("format", params.format);
    if (params.lag_days) searchParams.set("lag_days", String(params.lag_days));
    if (params.top_n) searchParams.set("top_n", String(params.top_n));

    const query = searchParams.toString();
    return fetchApi<ApiMetaComparisonResponse>(
      `/api/v1/meta/compare${query ? `?${query}` : ""}`
    );
  },

  getForecast: (params: MetaForecastParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.format) searchParams.set("format", params.format);
    if (params.top_n) searchParams.set("top_n", String(params.top_n));

    const query = searchParams.toString();
    return fetchApi<ApiFormatForecastResponse>(
      `/api/v1/meta/forecast${query ? `?${query}` : ""}`
    );
  },
};

// Tournament search parameters
export interface TournamentSearchParams {
  region?: string;
  format?: "standard" | "expanded";
  start_date?: string;
  end_date?: string;
  best_of?: 1 | 3;
  tier?: TournamentTier;
  sort_by?: string;
  order?: "asc" | "desc";
  page?: number;
  limit?: number;
}

// Tournaments API
export const tournamentsApi = {
  list: (params: TournamentSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.start_date) searchParams.set("start_date", params.start_date);
    if (params.end_date) searchParams.set("end_date", params.end_date);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));
    if (params.tier) searchParams.set("tier", params.tier);
    if (params.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params.order) searchParams.set("order", params.order);
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApiValidated<ApiTournamentListResponse, unknown>(
      `/api/v1/tournaments${query ? `?${query}` : ""}`,
      TournamentListResponseSchema
    );
  },

  getById: (id: string) => {
    return fetchApi<ApiTournamentDetail>(
      `/api/v1/tournaments/${encodeURIComponent(id)}`
    );
  },

  getPlacementDecklist: (tournamentId: string, placementId: string) => {
    return fetchApi<ApiDecklistResponse>(
      `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/placements/${encodeURIComponent(placementId)}/decklist`
    );
  },
};

// Lab Notes search parameters
export interface LabNotesSearchParams {
  page?: number;
  limit?: number;
  note_type?: LabNoteType;
  tag?: string;
}

// Lab Notes API
export const labNotesApi = {
  list: (params: LabNotesSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.note_type) searchParams.set("note_type", params.note_type);
    if (params.tag) searchParams.set("tag", params.tag);

    const query = searchParams.toString();
    return fetchApiValidated<ApiLabNoteListResponse, unknown>(
      `/api/v1/lab-notes${query ? `?${query}` : ""}`,
      LabNoteListResponseSchema
    );
  },

  getBySlug: (slug: string) => {
    return fetchApiValidated<ApiLabNote, unknown>(
      `/api/v1/lab-notes/${encodeURIComponent(slug)}`,
      LabNoteSchema
    );
  },
};

// Format API
export const formatApi = {
  getCurrent: () => {
    return fetchApi<ApiFormatConfig>("/api/v1/format/current");
  },

  getUpcoming: () => {
    return fetchApi<ApiUpcomingFormat>("/api/v1/format/upcoming");
  },
};

// Rotation API
export const rotationApi = {
  getImpacts: (transition: string) => {
    return fetchApi<ApiRotationImpactList>(
      `/api/v1/rotation/impact?transition=${encodeURIComponent(transition)}`
    );
  },

  getArchetypeImpact: (archetypeId: string, transition?: string) => {
    const params = transition
      ? `?transition=${encodeURIComponent(transition)}`
      : "";
    return fetchApi<ApiRotationImpact>(
      `/api/v1/rotation/impact/${encodeURIComponent(archetypeId)}${params}`
    );
  },
};

// Japan intelligence search parameters
export interface JapanInnovationParams {
  set_code?: string;
  en_legal?: boolean;
  min_impact?: number;
  limit?: number;
}

export interface JapanArchetypeParams {
  set_code?: string;
  limit?: number;
}

export interface JapanSetImpactParams {
  set_code?: string;
  limit?: number;
}

export interface JapanPredictionParams {
  category?: string;
  resolved_only?: boolean;
  limit?: number;
}

export interface CardCountEvolutionParams {
  archetype: string;
  days?: number;
  top_cards?: number;
}

export interface JapanContentParams {
  source?: string;
  content_type?: string;
  era?: string;
  limit?: number;
}

// Japan API
export const japanApi = {
  listInnovations: (params: JapanInnovationParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.set_code) searchParams.set("set_code", params.set_code);
    if (params.en_legal !== undefined)
      searchParams.set("en_legal", String(params.en_legal));
    if (params.min_impact)
      searchParams.set("min_impact", String(params.min_impact));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiJPCardInnovationList>(
      `/api/v1/japan/innovation${query ? `?${query}` : ""}`
    );
  },

  getInnovationDetail: (cardId: string) => {
    return fetchApi<ApiJPCardInnovationDetail>(
      `/api/v1/japan/innovation/${encodeURIComponent(cardId)}`
    );
  },

  listNewArchetypes: (params: JapanArchetypeParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.set_code) searchParams.set("set_code", params.set_code);
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiJPNewArchetypeList>(
      `/api/v1/japan/archetypes/new${query ? `?${query}` : ""}`
    );
  },

  listSetImpacts: (params: JapanSetImpactParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.set_code) searchParams.set("set_code", params.set_code);
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiJPSetImpactList>(
      `/api/v1/japan/set-impact${query ? `?${query}` : ""}`
    );
  },

  listPredictions: (params: JapanPredictionParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.category) searchParams.set("category", params.category);
    if (params.resolved_only !== undefined)
      searchParams.set("resolved_only", String(params.resolved_only));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiPredictionList>(
      `/api/v1/japan/predictions${query ? `?${query}` : ""}`
    );
  },

  getCardCountEvolution: (params: CardCountEvolutionParams) => {
    const searchParams = new URLSearchParams();
    searchParams.set("archetype", params.archetype);
    if (params.days) searchParams.set("days", String(params.days));
    if (params.top_cards)
      searchParams.set("top_cards", String(params.top_cards));

    return fetchApi<ApiCardCountEvolutionResponse>(
      `/api/v1/japan/card-count-evolution?${searchParams.toString()}`
    );
  },

  getContent: (params: JapanContentParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.source) searchParams.set("source", params.source);
    if (params.content_type)
      searchParams.set("content_type", params.content_type);
    if (params.era) searchParams.set("era", params.era);
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiJPContentList>(
      `/api/v1/japan/content${query ? `?${query}` : ""}`
    );
  },
};

// Admin Lab Notes search parameters
export interface AdminLabNotesSearchParams {
  page?: number;
  limit?: number;
  note_type?: LabNoteType;
  tag?: string;
  status?: LabNoteStatus;
}

// Admin Lab Notes API
export const labNotesAdminApi = {
  list: (params: AdminLabNotesSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.note_type) searchParams.set("note_type", params.note_type);
    if (params.tag) searchParams.set("tag", params.tag);
    if (params.status) searchParams.set("status", params.status);

    const query = searchParams.toString();
    return fetchApiAuth<ApiLabNoteListResponse>(
      `/api/v1/lab-notes/admin/all${query ? `?${query}` : ""}`
    );
  },

  getById: (id: string) => {
    return fetchApiAuth<ApiLabNote>(
      `/api/v1/lab-notes/admin/${encodeURIComponent(id)}`
    );
  },

  create: (data: ApiLabNoteCreateRequest) => {
    return fetchApiAuth<ApiLabNote>("/api/v1/lab-notes", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update: (id: string, data: ApiLabNoteUpdateRequest) => {
    return fetchApiAuth<ApiLabNote>(
      `/api/v1/lab-notes/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  updateStatus: (id: string, data: ApiLabNoteStatusUpdate) => {
    return fetchApiAuth<ApiLabNote>(
      `/api/v1/lab-notes/${encodeURIComponent(id)}/status`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  delete: (id: string) => {
    return fetchApiAuth<void>(`/api/v1/lab-notes/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },

  listRevisions: (id: string) => {
    return fetchApiAuth<ApiLabNoteRevision[]>(
      `/api/v1/lab-notes/${encodeURIComponent(id)}/revisions`
    );
  },
};

// Evolution article search parameters
export interface EvolutionArticlesParams {
  limit?: number;
  offset?: number;
}

// Evolution API
export const evolutionApi = {
  listArticles: (params: EvolutionArticlesParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.offset) searchParams.set("offset", String(params.offset));

    const query = searchParams.toString();
    return fetchApi<ApiEvolutionArticleListItem[]>(
      `/api/v1/evolution${query ? `?${query}` : ""}`
    );
  },

  getArticleBySlug: (slug: string) => {
    return fetchApi<ApiEvolutionArticle>(
      `/api/v1/evolution/${encodeURIComponent(slug)}`
    );
  },

  getAccuracy: (limit?: number) => {
    const params = limit ? `?limit=${limit}` : "";
    return fetchApi<ApiPredictionAccuracy>(
      `/api/v1/evolution/accuracy${params}`
    );
  },

  getArchetypeEvolution: (archetypeId: string, limit?: number) => {
    const params = limit ? `?limit=${limit}` : "";
    return fetchApi<ApiEvolutionTimeline>(
      `/api/v1/archetypes/${encodeURIComponent(archetypeId)}/evolution${params}`
    );
  },

  getArchetypePrediction: (archetypeId: string) => {
    return fetchApi<ApiArchetypePrediction>(
      `/api/v1/archetypes/${encodeURIComponent(archetypeId)}/prediction`
    );
  },
};

// Translation public params
export interface JPAdoptionRatesParams {
  days?: number;
  archetype?: string;
  limit?: number;
}

export interface JPUpcomingCardsParams {
  include_released?: boolean;
  min_impact?: number;
  limit?: number;
}

// Translation admin params
export interface AdminTranslationsParams {
  status?: string;
  content_type?: string;
  limit?: number;
  offset?: number;
}

// Translations public API
export const translationsApi = {
  getAdoptionRates: (params: JPAdoptionRatesParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.days) searchParams.set("days", String(params.days));
    if (params.archetype) searchParams.set("archetype", params.archetype);
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiJPAdoptionRateList>(
      `/api/v1/japan/adoption-rates${query ? `?${query}` : ""}`
    );
  },

  getUpcomingCards: (params: JPUpcomingCardsParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.include_released !== undefined)
      searchParams.set("include_released", String(params.include_released));
    if (params.min_impact)
      searchParams.set("min_impact", String(params.min_impact));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiJPUnreleasedCardList>(
      `/api/v1/japan/upcoming-cards${query ? `?${query}` : ""}`
    );
  },
};

// Translations admin API
export const translationsAdminApi = {
  list: (params: AdminTranslationsParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.status) searchParams.set("status_filter", params.status);
    if (params.content_type)
      searchParams.set("content_type", params.content_type);
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.offset) searchParams.set("offset", String(params.offset));

    const query = searchParams.toString();
    return fetchApiAuth<ApiTranslatedContentList>(
      `/api/v1/admin/translations${query ? `?${query}` : ""}`
    );
  },

  submit: (data: ApiSubmitTranslationRequest) => {
    return fetchApiAuth<ApiTranslatedContent>("/api/v1/admin/translations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update: (id: string, data: ApiUpdateTranslationRequest) => {
    return fetchApiAuth<ApiTranslatedContent>(
      `/api/v1/admin/translations/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  listGlossary: (activeOnly = true) => {
    const params = activeOnly ? "?active_only=true" : "";
    return fetchApiAuth<ApiGlossaryTermOverrideList>(
      `/api/v1/admin/translations/glossary${params}`
    );
  },

  createGlossaryTerm: (data: ApiGlossaryTermCreateRequest) => {
    return fetchApiAuth<ApiGlossaryTermOverride>(
      "/api/v1/admin/translations/glossary",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },
};

// Admin Data API
export const adminDataApi = {
  getOverview: () =>
    fetchApiAuth<AdminDataOverview>("/api/v1/admin/data/overview"),

  listMetaSnapshots: (
    params: {
      region?: string;
      format?: string;
      limit?: number;
      offset?: number;
    } = {}
  ) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.offset) searchParams.set("offset", String(params.offset));
    const query = searchParams.toString();
    return fetchApiAuth<AdminMetaSnapshotList>(
      `/api/v1/admin/data/meta-snapshots${query ? `?${query}` : ""}`
    );
  },

  getMetaSnapshotDetail: (id: string) =>
    fetchApiAuth<AdminMetaSnapshotDetail>(
      `/api/v1/admin/data/meta-snapshots/${id}`
    ),

  getPipelineHealth: () =>
    fetchApiAuth<AdminPipelineHealth>("/api/v1/admin/data/pipeline-health"),
};

// Widget search parameters
export interface WidgetSearchParams {
  page?: number;
  limit?: number;
}

// Widgets API
export const widgetsApi = {
  create: (data: ApiWidgetCreate) => {
    return fetchApiAuth<ApiWidgetResponse>("/api/v1/widgets", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  list: (params: WidgetSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));
    const query = searchParams.toString();
    return fetchApiAuth<ApiWidgetListResponse>(
      `/api/v1/widgets${query ? `?${query}` : ""}`
    );
  },

  getById: (id: string) => {
    return fetchApiAuth<ApiWidgetResponse>(
      `/api/v1/widgets/${encodeURIComponent(id)}`
    );
  },

  update: (id: string, data: ApiWidgetUpdate) => {
    return fetchApiAuth<ApiWidgetResponse>(
      `/api/v1/widgets/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      }
    );
  },

  delete: (id: string) => {
    return fetchApiAuth<void>(`/api/v1/widgets/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },

  getData: (id: string) => {
    return fetchApi<ApiWidgetDataResponse>(
      `/api/v1/widgets/${encodeURIComponent(id)}/data`
    );
  },

  getEmbedCode: (id: string) => {
    return fetchApiAuth<ApiWidgetEmbedCodeResponse>(
      `/api/v1/widgets/${encodeURIComponent(id)}/embed-code`
    );
  },
};

// Event search parameters
export interface EventSearchParams {
  region?: string;
  format?: "standard" | "expanded";
  tier?: string;
  status?: EventStatus;
  page?: number;
  limit?: number;
}

// Events API (upcoming event calendar)
export const eventsApi = {
  list: (params: EventSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.tier) searchParams.set("tier", params.tier);
    if (params.status) searchParams.set("status", params.status);
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApi<ApiEventListResponse>(
      `/api/v1/events${query ? `?${query}` : ""}`
    );
  },

  getById: (id: string) => {
    return fetchApi<ApiEventDetail>(`/api/v1/events/${encodeURIComponent(id)}`);
  },
};

// Trip search parameters
export interface TripSearchParams {
  status?: string;
  page?: number;
  limit?: number;
}

// Trips API (authenticated user trip management)
export const tripsApi = {
  list: (params: TripSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.status) searchParams.set("status", params.status);
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));

    const query = searchParams.toString();
    return fetchApiAuth<ApiTripSummary[]>(
      `/api/v1/trips${query ? `?${query}` : ""}`
    );
  },

  create: (data: ApiTripCreate) => {
    return fetchApiAuth<ApiTripDetail>("/api/v1/trips", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getById: (id: string) => {
    return fetchApiAuth<ApiTripDetail>(
      `/api/v1/trips/${encodeURIComponent(id)}`
    );
  },

  update: (id: string, data: ApiTripUpdate) => {
    return fetchApiAuth<ApiTripDetail>(
      `/api/v1/trips/${encodeURIComponent(id)}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  },

  delete: (id: string) => {
    return fetchApiAuth<void>(`/api/v1/trips/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },

  addEvent: (tripId: string, data: ApiTripEventAdd) => {
    return fetchApiAuth<ApiTripDetail>(
      `/api/v1/trips/${encodeURIComponent(tripId)}/events`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  removeEvent: (tripId: string, eventId: string) => {
    return fetchApiAuth<void>(
      `/api/v1/trips/${encodeURIComponent(tripId)}/events/${encodeURIComponent(eventId)}`,
      { method: "DELETE" }
    );
  },

  getShared: (token: string) => {
    return fetchApi<ApiSharedTripView>(
      `/api/v1/trips/shared/${encodeURIComponent(token)}`
    );
  },

  share: (id: string) => {
    return fetchApiAuth<ApiTripDetail>(
      `/api/v1/trips/${encodeURIComponent(id)}/share`,
      { method: "POST" }
    );
  },
};

// Export search parameters
export interface ExportSearchParams {
  page?: number;
  limit?: number;
}

// Exports API
export const exportsApi = {
  create: (data: ApiExportCreate) => {
    return fetchApiAuth<ApiExportResponse>("/api/v1/exports", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  list: (params: ExportSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));
    const query = searchParams.toString();
    return fetchApiAuth<ApiExportListResponse>(
      `/api/v1/exports${query ? `?${query}` : ""}`
    );
  },

  getById: (id: string) => {
    return fetchApiAuth<ApiExportResponse>(
      `/api/v1/exports/${encodeURIComponent(id)}`
    );
  },

  getDownloadUrl: (id: string) => {
    return fetchApiAuth<ApiExportDownloadResponse>(
      `/api/v1/exports/${encodeURIComponent(id)}/download`
    );
  },
};

// API Keys API
export const apiKeysApi = {
  create: (data: ApiApiKeyCreate) => {
    return fetchApiAuth<ApiApiKeyCreatedResponse>("/api/v1/api-keys", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  list: () => {
    return fetchApiAuth<ApiApiKeyListResponse>("/api/v1/api-keys");
  },

  getById: (id: string) => {
    return fetchApiAuth<ApiApiKeyResponse>(
      `/api/v1/api-keys/${encodeURIComponent(id)}`
    );
  },

  revoke: (id: string) => {
    return fetchApiAuth<void>(`/api/v1/api-keys/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },
};

export const usersApi = {
  getMe: () => {
    return fetchApiAuth<ApiCurrentUser>("/api/v1/users/me");
  },
};

export const publicApi = {
  getHomeTeaser: (format: "standard" | "expanded" = "standard") => {
    const searchParams = new URLSearchParams({ format });
    return fetchApi<ApiPublicHomeTeaser>(
      `/api/v1/public/teaser/home?${searchParams.toString()}`
    );
  },
};

export { ApiError, fetchApi, fetchApiAuth, getAuthToken };
