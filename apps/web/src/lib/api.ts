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
} from "@trainerlab/shared-types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit,
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
      { originalError: error },
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => undefined);
    console.error("API error", endpoint, response.status, body);
    throw new ApiError(
      `API request failed: ${response.status} ${response.statusText}`,
      response.status,
      body,
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
      `/api/v1/cards${query ? `?${query}` : ""}`,
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
      `/api/v1/sets/${encodeURIComponent(id)}/cards?page=${page}&limit=${limit}`,
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
      `/api/v1/meta/current${query ? `?${query}` : ""}`,
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
      `/api/v1/meta/history${query ? `?${query}` : ""}`,
    );
  },

  getArchetypes: (params: MetaSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.region) searchParams.set("region", params.region);
    if (params.format) searchParams.set("format", params.format);
    if (params.best_of) searchParams.set("best_of", String(params.best_of));

    const query = searchParams.toString();
    return fetchApi<ApiArchetype[]>(
      `/api/v1/meta/archetypes${query ? `?${query}` : ""}`,
    );
  },
};

export { ApiError };
