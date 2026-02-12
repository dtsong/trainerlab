export type ApiFreshnessStatus = "fresh" | "stale" | "partial" | "no_data";

export type ApiCadenceProfile =
  | "jp_daily_cadence"
  | "grassroots_daily_cadence"
  | "tpci_event_cadence"
  | "default_cadence";

export interface ApiDataFreshness {
  status: ApiFreshnessStatus;
  cadence_profile: ApiCadenceProfile;
  snapshot_date?: string | null;
  sample_size?: number | null;
  staleness_days?: number | null;
  source_coverage?: string[] | null;
  message?: string | null;
}
