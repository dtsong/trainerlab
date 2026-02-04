import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiLabNoteListResponse,
  ApiLabNoteSummary,
  ApiLabNote,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  labNotesApi: {
    list: vi.fn(),
    getBySlug: vi.fn(),
  },
}));

import { labNotesApi } from "@/lib/api";
import { useLabNotes, useLabNote } from "../useLabNotes";

const mockLabNoteSummary: ApiLabNoteSummary = {
  id: "note-123",
  slug: "charizard-meta-analysis",
  note_type: "analysis",
  title: "Charizard ex Meta Analysis",
  summary: "Deep dive into the Charizard ex archetype",
  author_name: "Test Author",
  status: "published",
  is_published: true,
  published_at: "2024-06-15T12:00:00Z",
  featured_image_url: null,
  tags: ["meta", "charizard"],
  is_premium: false,
  created_at: "2024-06-01T10:00:00Z",
};

const mockListResponse: ApiLabNoteListResponse = {
  items: [mockLabNoteSummary],
  total: 50,
  page: 1,
  limit: 20,
  has_next: true,
  has_prev: false,
};

const mockLabNote: ApiLabNote = {
  ...mockLabNoteSummary,
  content: "# Charizard ex Analysis\n\nDetailed content here...",
  version: 1,
  meta_description: "Analysis of Charizard ex",
  related_content: null,
  updated_at: "2024-06-15T12:00:00Z",
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe("useLabNotes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch lab notes with default params", async () => {
    vi.mocked(labNotesApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useLabNotes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockListResponse);
    expect(labNotesApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch lab notes with note_type filter", async () => {
    vi.mocked(labNotesApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(
      () => useLabNotes({ note_type: "analysis" }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesApi.list).toHaveBeenCalledWith({ note_type: "analysis" });
  });

  it("should fetch lab notes with tag filter", async () => {
    vi.mocked(labNotesApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useLabNotes({ tag: "meta" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesApi.list).toHaveBeenCalledWith({ tag: "meta" });
  });

  it("should handle pagination", async () => {
    vi.mocked(labNotesApi.list).mockResolvedValue({
      ...mockListResponse,
      page: 2,
      has_prev: true,
    });

    const { result } = renderHook(() => useLabNotes({ page: 2, limit: 10 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesApi.list).toHaveBeenCalledWith({ page: 2, limit: 10 });
    expect(result.current.data?.page).toBe(2);
  });

  it("should handle multiple filters", async () => {
    vi.mocked(labNotesApi.list).mockResolvedValue(mockListResponse);

    const params = {
      note_type: "analysis" as const,
      tag: "meta",
      page: 1,
      limit: 20,
    };

    const { result } = renderHook(() => useLabNotes(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesApi.list).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(labNotesApi.list).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => useLabNotes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should return empty list when no notes found", async () => {
    vi.mocked(labNotesApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_next: false,
      has_prev: false,
    });

    const { result } = renderHook(() => useLabNotes(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items).toEqual([]);
    expect(result.current.data?.total).toBe(0);
  });
});

describe("useLabNote", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch lab note by slug", async () => {
    vi.mocked(labNotesApi.getBySlug).mockResolvedValue(mockLabNote);

    const { result } = renderHook(
      () => useLabNote("charizard-meta-analysis"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockLabNote);
    expect(labNotesApi.getBySlug).toHaveBeenCalledWith(
      "charizard-meta-analysis"
    );
  });

  it("should not fetch when slug is empty", async () => {
    const { result } = renderHook(() => useLabNote(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(labNotesApi.getBySlug).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(labNotesApi.getBySlug).mockRejectedValue(
      new Error("Note not found")
    );

    const { result } = renderHook(() => useLabNote("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should return note with full content", async () => {
    vi.mocked(labNotesApi.getBySlug).mockResolvedValue(mockLabNote);

    const { result } = renderHook(
      () => useLabNote("charizard-meta-analysis"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.content).toBe(
      "# Charizard ex Analysis\n\nDetailed content here..."
    );
    expect(result.current.data?.version).toBe(1);
  });

  it("should handle note with related content", async () => {
    const noteWithRelated: ApiLabNote = {
      ...mockLabNote,
      related_content: {
        archetypes: ["Charizard ex", "Lugia VSTAR"],
        cards: ["sv3-125"],
        sets: ["sv3"],
      },
    };

    vi.mocked(labNotesApi.getBySlug).mockResolvedValue(noteWithRelated);

    const { result } = renderHook(
      () => useLabNote("charizard-meta-analysis"),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.related_content?.archetypes).toContain(
      "Charizard ex"
    );
  });
});
