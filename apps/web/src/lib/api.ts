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
} from "@trainerlab/shared-types";

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
    return fetchApi<ApiPaginatedResponse<ApiCardSummary>>(
      `/api/v1/cards${query ? `?${query}` : ""}`
    );
  },

  getById: (id: string) => {
    return fetchApi<ApiCard>(`/api/v1/cards/${encodeURIComponent(id)}`);
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
}

// Meta API
export const metaApi = {
  getCurrent: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));

    const query = searchParams.toString();
    return fetchApi<ApiMetaSnapshot>(
      `/api/v1/meta/current${query ? `?${query}` : ""}`
    );
  },

  getHistory: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));
    if (params.days) searchParams.set("days", String(params.days));

    const query = searchParams.toString();
    return fetchApi<ApiMetaHistoryResponse>(
      `/api/v1/meta/history${query ? `?${query}` : ""}`
    );
  },

  getArchetypes: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));

    const query = searchParams.toString();
    return fetchApi<ApiArchetype[]>(
      `/api/v1/meta/archetypes${query ? `?${query}` : ""}`
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
    return fetchApi<ApiTournamentListResponse>(
      `/api/v1/tournaments${query ? `?${query}` : ""}`
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
    return fetchApi<ApiLabNoteListResponse>(
      `/api/v1/lab-notes${query ? `?${query}` : ""}`
    );
  },

  getBySlug: (slug: string) => {
    return fetchApi<ApiLabNote>(
      `/api/v1/lab-notes/${encodeURIComponent(slug)}`
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
    return fetchApi<ApiPredictionAccuracy>(`/api/v1/evolution/accuracy${params}`);
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

export { ApiError, fetchApiAuth, getAuthToken };
