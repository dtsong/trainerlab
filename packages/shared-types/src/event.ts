// Event & Trip types (matching backend schemas)

export type EventStatus =
  | "announced"
  | "registration_open"
  | "registration_closed"
  | "active"
  | "completed";

export type TripStatus = "planning" | "confirmed" | "completed" | "cancelled";

export type TripVisibility = "private" | "link_only" | "public";

export type TripEventRole = "player" | "spectator" | "judge" | "coach";

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
  visibility: TripVisibility;
  event_count: number;
  next_event?: ApiEventSummary | null;
  created_at: string;
  updated_at: string;
}

/**
 * Trip event detail (event within a trip).
 */
export interface ApiTripEventDetail {
  id: string;
  trip_id: string;
  tournament_id: string;
  role: TripEventRole;
  notes?: string | null;
  event: ApiEventSummary;
  created_at: string;
  updated_at: string;
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
  share_url?: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Shared trip view (no auth required, read-only).
 */
export interface ApiSharedTripView {
  id: string;
  name: string;
  status: TripStatus;
  notes?: string | null;
  events: ApiTripEventDetail[];
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
  visibility: TripVisibility;
  eventCount: number;
  nextEvent?: EventSummary;
  createdAt: string;
  updatedAt: string;
}

/**
 * Trip event detail (frontend).
 */
export interface TripEventDetail {
  id: string;
  tripId: string;
  tournamentId: string;
  role: TripEventRole;
  notes?: string;
  event: EventSummary;
  createdAt: string;
  updatedAt: string;
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
  shareUrl?: string;
  createdAt: string;
  updatedAt: string;
}
