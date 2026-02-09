import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api", () => ({
  widgetsApi: {
    create: vi.fn(),
    list: vi.fn(),
    getById: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getData: vi.fn(),
    getEmbedCode: vi.fn(),
  },
}));

import { widgetsApi } from "@/lib/api";
import {
  useWidgets,
  useWidget,
  useWidgetData,
  useCreateWidget,
  useUpdateWidget,
  useDeleteWidget,
  useWidgetEmbedCode,
} from "../useWidgets";

const mockWidgetList = {
  items: [
    {
      id: "w-1",
      user_id: "u-1",
      type: "meta_snapshot",
      config: {},
      theme: "dark",
      accent_color: null,
      show_attribution: true,
      embed_count: 0,
      view_count: 0,
      is_active: true,
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

const mockWidget = mockWidgetList.items[0];

const mockWidgetData = {
  widget_id: "w-1",
  type: "meta_snapshot",
  theme: "dark",
  accent_color: null,
  show_attribution: true,
  data: { archetypes: [] },
  error: null,
};

const mockEmbedCode = {
  widget_id: "w-1",
  iframe_code: '<iframe src="/embed/w-1"></iframe>',
  script_code: '<script src="/embed.js"></script>',
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
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

describe("useWidgets", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch widgets with default params", async () => {
    vi.mocked(widgetsApi.list).mockResolvedValue(mockWidgetList);

    const { result } = renderHook(() => useWidgets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockWidgetList);
    expect(widgetsApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch widgets with search params", async () => {
    vi.mocked(widgetsApi.list).mockResolvedValue(mockWidgetList);

    const params = { page: 1, limit: 10 };
    const { result } = renderHook(() => useWidgets(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(widgetsApi.list).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(widgetsApi.list).mockRejectedValue(new Error("Unauthorized"));

    const { result } = renderHook(() => useWidgets(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch widget by ID", async () => {
    vi.mocked(widgetsApi.getById).mockResolvedValue(mockWidget);

    const { result } = renderHook(() => useWidget("w-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockWidget);
    expect(widgetsApi.getById).toHaveBeenCalledWith("w-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useWidget(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(widgetsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(widgetsApi.getById).mockRejectedValue(new Error("Not found"));

    const { result } = renderHook(() => useWidget("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useWidgetData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch widget data", async () => {
    vi.mocked(widgetsApi.getData).mockResolvedValue(mockWidgetData);

    const { result } = renderHook(() => useWidgetData("w-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockWidgetData);
    expect(widgetsApi.getData).toHaveBeenCalledWith("w-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useWidgetData(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(widgetsApi.getData).not.toHaveBeenCalled();
  });
});

describe("useCreateWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create a widget", async () => {
    vi.mocked(widgetsApi.create).mockResolvedValue(mockWidget);

    const { result } = renderHook(() => useCreateWidget(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        type: "meta_snapshot",
        config: {},
        theme: "dark",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(widgetsApi.create).toHaveBeenCalledWith({
      type: "meta_snapshot",
      config: {},
      theme: "dark",
    });
  });

  it("should handle creation errors", async () => {
    vi.mocked(widgetsApi.create).mockRejectedValue(
      new Error("Validation failed")
    );

    const { result } = renderHook(() => useCreateWidget(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ type: "meta_snapshot" });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useUpdateWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update a widget", async () => {
    vi.mocked(widgetsApi.update).mockResolvedValue({
      ...mockWidget,
      theme: "light",
    });

    const { result } = renderHook(() => useUpdateWidget(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "w-1",
        data: { theme: "light" },
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(widgetsApi.update).toHaveBeenCalledWith("w-1", {
      theme: "light",
    });
  });

  it("should handle update errors", async () => {
    vi.mocked(widgetsApi.update).mockRejectedValue(new Error("Update failed"));

    const { result } = renderHook(() => useUpdateWidget(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "w-1",
        data: { theme: "light" },
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useDeleteWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should delete a widget", async () => {
    vi.mocked(widgetsApi.delete).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteWidget(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("w-1");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(widgetsApi.delete).toHaveBeenCalledWith("w-1");
  });

  it("should handle deletion errors", async () => {
    vi.mocked(widgetsApi.delete).mockRejectedValue(new Error("Delete failed"));

    const { result } = renderHook(() => useDeleteWidget(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("w-1");
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useWidgetEmbedCode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch embed code", async () => {
    vi.mocked(widgetsApi.getEmbedCode).mockResolvedValue(mockEmbedCode);

    const { result } = renderHook(() => useWidgetEmbedCode("w-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockEmbedCode);
    expect(widgetsApi.getEmbedCode).toHaveBeenCalledWith("w-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useWidgetEmbedCode(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(widgetsApi.getEmbedCode).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(widgetsApi.getEmbedCode).mockRejectedValue(
      new Error("Not found")
    );

    const { result } = renderHook(() => useWidgetEmbedCode("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
