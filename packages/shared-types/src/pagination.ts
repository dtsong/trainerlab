/**
 * Pagination types for API responses (snake_case).
 * These types match the JSON responses from the FastAPI backend.
 */

export interface ApiPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
