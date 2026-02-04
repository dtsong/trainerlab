import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

vi.mock("@/lib/api", () => ({
  labNotesAdminApi: {
    list: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateStatus: vi.fn(),
    delete: vi.fn(),
    listRevisions: vi.fn(),
  },
}));

import { labNotesAdminApi } from "@/lib/api";
import {
  useLabNotesAdmin,
  useLabNoteAdmin,
  useCreateLabNote,
  useUpdateLabNote,
  useUpdateLabNoteStatus,
  useDeleteLabNote,
  useLabNoteRevisions,
} from "../useLabNotesAdmin";

const mockLabNoteList = {
  items: [
    {
      id: "note-1",
      title: "Meta Analysis",
      slug: "meta-analysis",
      note_type: "analysis",
      status: "published",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-02T00:00:00Z",
    },
  ],
  total: 1,
  page: 1,
  limit: 20,
  has_next: false,
  has_prev: false,
};

const mockLabNote = {
  id: "note-1",
  title: "Meta Analysis",
  slug: "meta-analysis",
  note_type: "analysis",
  status: "published",
  content: "Some content here",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-02T00:00:00Z",
};

const mockRevisions = [
  {
    id: "rev-1",
    lab_note_id: "note-1",
    content: "Revision content",
    created_at: "2024-01-01T00:00:00Z",
  },
];

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

describe("useLabNotesAdmin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch lab notes with default params", async () => {
    vi.mocked(labNotesAdminApi.list).mockResolvedValue(mockLabNoteList);

    const { result } = renderHook(() => useLabNotesAdmin(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockLabNoteList);
    expect(labNotesAdminApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch lab notes with search params", async () => {
    vi.mocked(labNotesAdminApi.list).mockResolvedValue(mockLabNoteList);

    const params = { page: 1, limit: 10, status: "draft" as const };
    const { result } = renderHook(() => useLabNotesAdmin(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesAdminApi.list).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(labNotesAdminApi.list).mockRejectedValue(
      new Error("Unauthorized")
    );

    const { result } = renderHook(() => useLabNotesAdmin(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useLabNoteAdmin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch lab note by ID", async () => {
    vi.mocked(labNotesAdminApi.getById).mockResolvedValue(mockLabNote);

    const { result } = renderHook(() => useLabNoteAdmin("note-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockLabNote);
    expect(labNotesAdminApi.getById).toHaveBeenCalledWith("note-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useLabNoteAdmin(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(labNotesAdminApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(labNotesAdminApi.getById).mockRejectedValue(
      new Error("Not found")
    );

    const { result } = renderHook(() => useLabNoteAdmin("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCreateLabNote", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create a lab note", async () => {
    vi.mocked(labNotesAdminApi.create).mockResolvedValue(mockLabNote);

    const { result } = renderHook(() => useCreateLabNote(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        title: "New Note",
        content: "Content",
        note_type: "analysis",
      } as Parameters<typeof labNotesAdminApi.create>[0]);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesAdminApi.create).toHaveBeenCalledWith({
      title: "New Note",
      content: "Content",
      note_type: "analysis",
    });
  });

  it("should handle creation errors", async () => {
    vi.mocked(labNotesAdminApi.create).mockRejectedValue(
      new Error("Validation failed")
    );

    const { result } = renderHook(() => useCreateLabNote(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        title: "",
        content: "",
        note_type: "analysis",
      } as Parameters<typeof labNotesAdminApi.create>[0]);
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useUpdateLabNote", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update a lab note", async () => {
    vi.mocked(labNotesAdminApi.update).mockResolvedValue({
      ...mockLabNote,
      title: "Updated Title",
    });

    const { result } = renderHook(() => useUpdateLabNote(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "note-1",
        data: { title: "Updated Title" } as Parameters<
          typeof labNotesAdminApi.update
        >[1],
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesAdminApi.update).toHaveBeenCalledWith("note-1", {
      title: "Updated Title",
    });
  });

  it("should handle update errors", async () => {
    vi.mocked(labNotesAdminApi.update).mockRejectedValue(
      new Error("Update failed")
    );

    const { result } = renderHook(() => useUpdateLabNote(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "note-1",
        data: { title: "Updated Title" } as Parameters<
          typeof labNotesAdminApi.update
        >[1],
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useUpdateLabNoteStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update lab note status", async () => {
    vi.mocked(labNotesAdminApi.updateStatus).mockResolvedValue({
      ...mockLabNote,
      status: "draft",
    });

    const { result } = renderHook(() => useUpdateLabNoteStatus(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: "note-1", status: "draft" as const });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesAdminApi.updateStatus).toHaveBeenCalledWith("note-1", {
      status: "draft",
    });
  });

  it("should handle status update errors", async () => {
    vi.mocked(labNotesAdminApi.updateStatus).mockRejectedValue(
      new Error("Status update failed")
    );

    const { result } = renderHook(() => useUpdateLabNoteStatus(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: "note-1", status: "published" as const });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useDeleteLabNote", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should delete a lab note and redirect", async () => {
    vi.mocked(labNotesAdminApi.delete).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteLabNote(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("note-1");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(labNotesAdminApi.delete).toHaveBeenCalledWith("note-1");
    expect(mockPush).toHaveBeenCalledWith("/admin/lab-notes");
  });

  it("should handle deletion errors", async () => {
    vi.mocked(labNotesAdminApi.delete).mockRejectedValue(
      new Error("Delete failed")
    );

    const { result } = renderHook(() => useDeleteLabNote(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("note-1");
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
    expect(mockPush).not.toHaveBeenCalled();
  });
});

describe("useLabNoteRevisions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch revisions for a lab note", async () => {
    vi.mocked(labNotesAdminApi.listRevisions).mockResolvedValue(mockRevisions);

    const { result } = renderHook(() => useLabNoteRevisions("note-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockRevisions);
    expect(labNotesAdminApi.listRevisions).toHaveBeenCalledWith("note-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useLabNoteRevisions(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(labNotesAdminApi.listRevisions).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(labNotesAdminApi.listRevisions).mockRejectedValue(
      new Error("Failed to fetch revisions")
    );

    const { result } = renderHook(() => useLabNoteRevisions("note-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
