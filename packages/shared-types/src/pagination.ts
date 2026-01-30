/**
 * Pagination types for API responses (snake_case).
 * These types match the JSON responses from the FastAPI backend.
 */

export interface ApiPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  total_pages: number;
  next_cursor?: string | null;
}
