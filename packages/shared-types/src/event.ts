// Event & Trip types (matching backend schemas)

export type EventStatus =
  | "announced"
  | "registration_open"
  | "registration_closed"
  | "active"
  | "completed";

export type TripStatus = "planning" | "upcoming" | "active" | "completed";

export type TripVisibility = "private" | "shared";

export type TripEventRole = "attendee" | "competitor" | "judge" | "spectator";

// ---------------------------------------------------------------------------
// API types (snake_case, matching backend Pydantic schemas)
// ---------------------------------------------------------------------------

/**
 * Event summary for calendar listings.
 */
export interface ApiEventSummary {
  id: string;
  name: string;
  date: string;
  region: string;
  country?: string | null;
  city?: string | null;
  format: string;
  tier?: string | null;
  status: EventStatus;
  registration_opens_at?: string | null;
  registration_closes_at?: string | null;
  registration_url?: string | null;
  participant_count?: number | null;
  event_source?: string | null;
}

/**
 * Full event detail with venue info.
 */
export interface ApiEventDetail extends ApiEventSummary {
  venue_name?: string | null;
  venue_address?: string | null;
  source_url?: string | null;
}

/**
 * Paginated list of events.
 */
export interface ApiEventListResponse {
  items: ApiEventSummary[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * Request body to create a new trip.
 */
export interface ApiTripCreate {
  name: string;
  notes?: string | null;
}

/**
 * Request body to update an existing trip.
 */
export interface ApiTripUpdate {
  name?: string | null;
  status?: TripStatus | null;
  visibility?: TripVisibility | null;
  notes?: string | null;
}

/**
 * Request body to add an event to a trip.
 */
export interface ApiTripEventAdd {
  tournament_id: string;
  role?: TripEventRole | null;
  notes?: string | null;
}

/**
 * Trip summary for list views.
 */
export interface ApiTripSummary {
  id: string;
  name: string;
  status: TripStatus;
  event_count: number;
  next_event_date?: string | null;
  created_at: string;
}

/**
 * Trip event detail (event within a trip).
 */
export interface ApiTripEventDetail {
  id: string;
  tournament_id: string;
  tournament_name: string;
  tournament_date: string;
  tournament_region: string;
  tournament_city?: string | null;
  tournament_status: string;
  role: TripEventRole;
  notes?: string | null;
  days_until?: number | null;
}

/**
 * Full trip detail with events.
 */
export interface ApiTripDetail {
  id: string;
  name: string;
  status: TripStatus;
  visibility: TripVisibility;
  notes?: string | null;
  events: ApiTripEventDetail[];
  share_token?: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Shared trip view (no auth required, read-only).
 */
export interface ApiSharedTripView {
  name: string;
  events: ApiTripEventDetail[];
  created_at: string;
}

// ---------------------------------------------------------------------------
// Frontend types (camelCase)
// ---------------------------------------------------------------------------

/**
 * Event summary for calendar listings (frontend).
 */
export interface EventSummary {
  id: string;
  name: string;
  date: string;
  region: string;
  country?: string;
  city?: string;
  format: string;
  tier?: string;
  status: EventStatus;
  registrationOpensAt?: string;
  registrationClosesAt?: string;
  registrationUrl?: string;
  participantCount?: number;
  eventSource?: string;
}

/**
 * Full event detail (frontend).
 */
export interface EventDetail extends EventSummary {
  venueName?: string;
  venueAddress?: string;
  sourceUrl?: string;
}

/**
 * Trip summary for list views (frontend).
 */
export interface TripSummary {
  id: string;
  name: string;
  status: TripStatus;
  eventCount: number;
  nextEventDate?: string;
  createdAt: string;
}

/**
 * Trip event detail (frontend).
 */
export interface TripEventDetail {
  id: string;
  tournamentId: string;
  tournamentName: string;
  tournamentDate: string;
  tournamentRegion: string;
  tournamentCity?: string;
  tournamentStatus: string;
  role: TripEventRole;
  notes?: string;
  daysUntil?: number;
}

/**
 * Full trip detail (frontend).
 */
export interface TripDetail {
  id: string;
  name: string;
  status: TripStatus;
  visibility: TripVisibility;
  notes?: string;
  events: TripEventDetail[];
  shareToken?: string;
  createdAt: string;
  updatedAt: string;
}
