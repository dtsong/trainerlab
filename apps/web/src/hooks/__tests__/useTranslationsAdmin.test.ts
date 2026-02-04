import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api", () => ({
  translationsAdminApi: {
    list: vi.fn(),
    submit: vi.fn(),
    update: vi.fn(),
    listGlossary: vi.fn(),
    createGlossaryTerm: vi.fn(),
  },
}));

import { translationsAdminApi } from "@/lib/api";
import {
  useTranslationsAdmin,
  useSubmitTranslation,
  useUpdateTranslation,
  useGlossaryTerms,
  useCreateGlossaryTerm,
} from "../useTranslationsAdmin";

const mockTranslationList = {
  items: [
    {
      id: "trans-1",
      source_url: "https://example.com/article",
      status: "pending",
      content_type: "article",
      title: "JP Meta Report",
    },
  ],
  total: 1,
};

const mockTranslation = {
  id: "trans-1",
  source_url: "https://example.com/article",
  status: "completed",
  content_type: "article",
  title: "JP Meta Report",
  translated_content: "Translated text",
};

const mockGlossaryTerms = {
  items: [
    {
      id: "term-1",
      japanese_term: "ex",
      english_term: "ex",
      active: true,
    },
  ],
  total: 1,
};

const mockGlossaryTerm = {
  id: "term-2",
  japanese_term: "pokemon",
  english_term: "Pokemon",
  active: true,
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

describe("useTranslationsAdmin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch translations with default params", async () => {
    vi.mocked(translationsAdminApi.list).mockResolvedValue(mockTranslationList);

    const { result } = renderHook(() => useTranslationsAdmin(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockTranslationList);
    expect(translationsAdminApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch translations with params", async () => {
    vi.mocked(translationsAdminApi.list).mockResolvedValue(mockTranslationList);

    const params = { status: "pending", content_type: "article", limit: 10 };
    const { result } = renderHook(() => useTranslationsAdmin(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsAdminApi.list).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(translationsAdminApi.list).mockRejectedValue(
      new Error("Unauthorized")
    );

    const { result } = renderHook(() => useTranslationsAdmin(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useSubmitTranslation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should submit a translation request", async () => {
    vi.mocked(translationsAdminApi.submit).mockResolvedValue(mockTranslation);

    const { result } = renderHook(() => useSubmitTranslation(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        source_url: "https://example.com/article",
      } as Parameters<typeof translationsAdminApi.submit>[0]);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsAdminApi.submit).toHaveBeenCalledWith({
      source_url: "https://example.com/article",
    });
  });

  it("should handle submission errors", async () => {
    vi.mocked(translationsAdminApi.submit).mockRejectedValue(
      new Error("Invalid URL")
    );

    const { result } = renderHook(() => useSubmitTranslation(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        source_url: "bad-url",
      } as Parameters<typeof translationsAdminApi.submit>[0]);
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useUpdateTranslation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update a translation", async () => {
    vi.mocked(translationsAdminApi.update).mockResolvedValue({
      ...mockTranslation,
      status: "reviewed",
    });

    const { result } = renderHook(() => useUpdateTranslation(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "trans-1",
        data: { status: "reviewed" } as Parameters<
          typeof translationsAdminApi.update
        >[1],
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsAdminApi.update).toHaveBeenCalledWith("trans-1", {
      status: "reviewed",
    });
  });

  it("should handle update errors", async () => {
    vi.mocked(translationsAdminApi.update).mockRejectedValue(
      new Error("Update failed")
    );

    const { result } = renderHook(() => useUpdateTranslation(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "trans-1",
        data: { status: "reviewed" } as Parameters<
          typeof translationsAdminApi.update
        >[1],
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useGlossaryTerms", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch active glossary terms by default", async () => {
    vi.mocked(translationsAdminApi.listGlossary).mockResolvedValue(
      mockGlossaryTerms
    );

    const { result } = renderHook(() => useGlossaryTerms(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockGlossaryTerms);
    expect(translationsAdminApi.listGlossary).toHaveBeenCalledWith(true);
  });

  it("should fetch all glossary terms when activeOnly is false", async () => {
    vi.mocked(translationsAdminApi.listGlossary).mockResolvedValue(
      mockGlossaryTerms
    );

    const { result } = renderHook(() => useGlossaryTerms(false), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsAdminApi.listGlossary).toHaveBeenCalledWith(false);
  });

  it("should handle API errors", async () => {
    vi.mocked(translationsAdminApi.listGlossary).mockRejectedValue(
      new Error("Server error")
    );

    const { result } = renderHook(() => useGlossaryTerms(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCreateGlossaryTerm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create a glossary term", async () => {
    vi.mocked(translationsAdminApi.createGlossaryTerm).mockResolvedValue(
      mockGlossaryTerm
    );

    const { result } = renderHook(() => useCreateGlossaryTerm(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        japanese_term: "pokemon",
        english_term: "Pokemon",
      } as Parameters<typeof translationsAdminApi.createGlossaryTerm>[0]);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(translationsAdminApi.createGlossaryTerm).toHaveBeenCalledWith({
      japanese_term: "pokemon",
      english_term: "Pokemon",
    });
  });

  it("should handle creation errors", async () => {
    vi.mocked(translationsAdminApi.createGlossaryTerm).mockRejectedValue(
      new Error("Duplicate term")
    );

    const { result } = renderHook(() => useCreateGlossaryTerm(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        japanese_term: "ex",
        english_term: "ex",
      } as Parameters<typeof translationsAdminApi.createGlossaryTerm>[0]);
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
