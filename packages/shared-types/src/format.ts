// Format and rotation types (matching backend schemas)

export type SurvivalRating =
  | "dies"
  | "crippled"
  | "adapts"
  | "thrives"
  | "unknown";

export interface ApiRotationDetails {
  rotating_out_sets: string[];
  new_set?: string | null;
}

export interface ApiFormatConfig {
  id: string;
  name: string;
  display_name: string;
  legal_sets: string[];
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  is_upcoming: boolean;
  rotation_details?: ApiRotationDetails | null;
}

export interface ApiUpcomingFormat {
  format: ApiFormatConfig;
  days_until_rotation: number;
  rotation_date: string;
}

export interface ApiRotatingCard {
  card_name: string;
  card_id?: string | null;
  count: number;
  role?: string | null;
  replacement?: string | null;
}

export interface ApiRotationImpact {
  id: string;
  format_transition: string;
  archetype_id: string;
  archetype_name: string;
  survival_rating: SurvivalRating;
  rotating_cards?: ApiRotatingCard[] | null;
  analysis?: string | null;
  jp_evidence?: string | null;
  jp_survival_share?: number | null;
}

export interface ApiRotationImpactList {
  format_transition: string;
  impacts: ApiRotationImpact[];
  total_archetypes: number;
}

// Frontend types (camelCase)

export interface RotationDetails {
  rotatingOutSets: string[];
  newSet?: string;
}

export interface FormatConfig {
  id: string;
  name: string;
  displayName: string;
  legalSets: string[];
  startDate?: string;
  endDate?: string;
  isCurrent: boolean;
  isUpcoming: boolean;
  rotationDetails?: RotationDetails;
}

export interface UpcomingFormat {
  format: FormatConfig;
  daysUntilRotation: number;
  rotationDate: string;
}

export interface RotatingCard {
  cardName: string;
  cardId?: string;
  count: number;
  role?: string;
  replacement?: string;
}

export interface RotationImpact {
  id: string;
  formatTransition: string;
  archetypeId: string;
  archetypeName: string;
  survivalRating: SurvivalRating;
  rotatingCards?: RotatingCard[];
  analysis?: string;
  jpEvidence?: string;
  jpSurvivalShare?: number;
}

export interface RotationImpactList {
  formatTransition: string;
  impacts: RotationImpact[];
  totalArchetypes: number;
}
