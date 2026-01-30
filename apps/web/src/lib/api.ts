/**
 * API client for TrainerLab backend.
 */

import type {
  ApiCard,
  ApiCardSummary,
  ApiSet,
  ApiPaginatedResponse,
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
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => undefined);
    throw new ApiError(
      `API request failed: ${response.status} ${response.statusText}`,
      response.status,
      body,
    );
  }

  return response.json();
}

// Card search parameters
export interface CardSearchParams {
  q?: string;
  supertype?: string;
  types?: string;
  set_id?: string;
  standard_legal?: boolean;
  expanded_legal?: boolean;
  page?: number;
  page_size?: number;
}

// Cards API
export const cardsApi = {
  search: (params: CardSearchParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.q) searchParams.set("q", params.q);
    if (params.supertype) searchParams.set("supertype", params.supertype);
    if (params.types) searchParams.set("types", params.types);
    if (params.set_id) searchParams.set("set_id", params.set_id);
    if (params.standard_legal !== undefined)
      searchParams.set("standard_legal", String(params.standard_legal));
    if (params.expanded_legal !== undefined)
      searchParams.set("expanded_legal", String(params.expanded_legal));
    if (params.page) searchParams.set("page", String(params.page));
    if (params.page_size)
      searchParams.set("page_size", String(params.page_size));

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

  getCards: (id: string, page = 1, pageSize = 20) => {
    return fetchApi<ApiPaginatedResponse<ApiCardSummary>>(
      `/api/v1/sets/${encodeURIComponent(id)}/cards?page=${page}&page_size=${pageSize}`,
    );
  },
};

export { ApiError };
