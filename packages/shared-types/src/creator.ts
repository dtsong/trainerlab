// Creator feature types (matching backend schemas)

export type WidgetType =
  | "meta_snapshot"
  | "archetype_card"
  | "meta_pie"
  | "meta_trend"
  | "jp_comparison"
  | "deck_cost"
  | "tournament_result"
  | "prediction"
  | "evolution_timeline";

export type WidgetTheme = "light" | "dark";

export interface ApiWidgetCreate {
  type: WidgetType;
  config?: Record<string, unknown>;
  theme?: WidgetTheme;
  accent_color?: string | null;
  show_attribution?: boolean;
}

export interface ApiWidgetUpdate {
  config?: Record<string, unknown> | null;
  theme?: WidgetTheme | null;
  accent_color?: string | null;
  show_attribution?: boolean | null;
  is_active?: boolean | null;
}

export interface ApiWidgetResponse {
  id: string;
  user_id: string;
  type: string;
  config: Record<string, unknown>;
  theme: string;
  accent_color: string | null;
  show_attribution: boolean;
  embed_count: number;
  view_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiWidgetDataResponse {
  widget_id: string;
  type: string;
  theme: string;
  accent_color: string | null;
  show_attribution: boolean;
  data: Record<string, unknown>;
  error: string | null;
}

export interface ApiWidgetEmbedCodeResponse {
  widget_id: string;
  iframe_code: string;
  script_code: string;
}

export interface ApiWidgetListResponse {
  items: ApiWidgetResponse[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Export types

export type ExportType =
  | "meta_snapshot"
  | "meta_history"
  | "tournament_results"
  | "archetype_evolution"
  | "card_usage"
  | "jp_data";

export type ExportFormat = "csv" | "json" | "xlsx";

export interface ApiExportCreate {
  export_type: ExportType;
  config?: Record<string, unknown>;
  format?: ExportFormat;
}

export interface ApiExportResponse {
  id: string;
  user_id: string;
  export_type: string;
  config: Record<string, unknown> | null;
  format: string;
  status: string;
  file_path: string | null;
  file_size_bytes: number | null;
  error_message: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiExportDownloadResponse {
  export_id: string;
  download_url: string;
  expires_in_hours: number;
}

export interface ApiExportListResponse {
  items: ApiExportResponse[];
  total: number;
}

// API Key types

export interface ApiApiKeyCreate {
  name: string;
  monthly_limit?: number;
}

export interface ApiApiKeyResponse {
  id: string;
  user_id: string;
  key_prefix: string;
  name: string;
  monthly_limit: number;
  requests_this_month: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiApiKeyCreatedResponse {
  api_key: ApiApiKeyResponse;
  full_key: string;
}

export interface ApiApiKeyListResponse {
  items: ApiApiKeyResponse[];
  total: number;
}
