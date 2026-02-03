// Lab Note types (matching backend schemas)

export type LabNoteType =
  | "weekly_report"
  | "jp_dispatch"
  | "set_analysis"
  | "rotation_preview"
  | "tournament_recap"
  | "tournament_preview"
  | "archetype_evolution";

export type LabNoteStatus = "draft" | "review" | "published" | "archived";

export interface ApiRelatedContent {
  archetypes: string[];
  cards: string[];
  sets: string[];
}

export interface ApiLabNoteSummary {
  id: string;
  slug: string;
  note_type: LabNoteType;
  title: string;
  summary?: string | null;
  author_name?: string | null;
  status: LabNoteStatus;
  is_published: boolean;
  published_at?: string | null;
  featured_image_url?: string | null;
  tags?: string[] | null;
  is_premium: boolean;
  created_at: string;
}

export interface ApiLabNote {
  id: string;
  slug: string;
  note_type: LabNoteType;
  title: string;
  summary?: string | null;
  content: string;
  author_name?: string | null;
  status: LabNoteStatus;
  version: number;
  is_published: boolean;
  published_at?: string | null;
  meta_description?: string | null;
  featured_image_url?: string | null;
  tags?: string[] | null;
  related_content?: ApiRelatedContent | null;
  is_premium: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiLabNoteListResponse {
  items: ApiLabNoteSummary[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiLabNoteRevision {
  id: string;
  lab_note_id: string;
  version: number;
  title: string;
  content: string;
  summary?: string | null;
  author_id?: string | null;
  change_description?: string | null;
  created_at: string;
}

// Request types for admin operations
export interface ApiLabNoteCreateRequest {
  slug?: string;
  note_type: LabNoteType;
  title: string;
  summary?: string | null;
  content: string;
  author_name?: string | null;
  status?: LabNoteStatus;
  is_published?: boolean;
  meta_description?: string | null;
  featured_image_url?: string | null;
  tags?: string[] | null;
  related_content?: ApiRelatedContent | null;
  is_premium?: boolean;
}

export interface ApiLabNoteUpdateRequest {
  title?: string;
  summary?: string | null;
  content?: string;
  author_name?: string | null;
  status?: LabNoteStatus;
  is_published?: boolean;
  meta_description?: string | null;
  featured_image_url?: string | null;
  tags?: string[] | null;
  related_content?: ApiRelatedContent | null;
  is_premium?: boolean;
}

export interface ApiLabNoteStatusUpdate {
  status: LabNoteStatus;
}

// Frontend types (camelCase)

export interface LabNoteSummary {
  id: string;
  slug: string;
  noteType: LabNoteType;
  title: string;
  summary?: string;
  authorName?: string;
  status: LabNoteStatus;
  isPublished: boolean;
  publishedAt?: string;
  featuredImageUrl?: string;
  tags?: string[];
  isPremium: boolean;
  createdAt: string;
}

export interface LabNote {
  id: string;
  slug: string;
  noteType: LabNoteType;
  title: string;
  summary?: string;
  content: string;
  authorName?: string;
  status: LabNoteStatus;
  version: number;
  isPublished: boolean;
  publishedAt?: string;
  metaDescription?: string;
  featuredImageUrl?: string;
  tags?: string[];
  relatedContent?: {
    archetypes: string[];
    cards: string[];
    sets: string[];
  };
  isPremium: boolean;
  createdAt: string;
  updatedAt: string;
}

// Lab note type labels for display
export const labNoteTypeLabels: Record<LabNoteType, string> = {
  weekly_report: "Weekly Report",
  jp_dispatch: "JP Dispatch",
  set_analysis: "Set Analysis",
  rotation_preview: "Rotation Preview",
  tournament_recap: "Tournament Recap",
  tournament_preview: "Tournament Preview",
  archetype_evolution: "Archetype Evolution",
};
