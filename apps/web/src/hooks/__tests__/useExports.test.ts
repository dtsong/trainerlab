import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api", () => ({
  exportsApi: {
    create: vi.fn(),
    list: vi.fn(),
    getById: vi.fn(),
    getDownloadUrl: vi.fn(),
  },
}));

import { exportsApi } from "@/lib/api";
import {
  useExports,
  useExport,
  useCreateExport,
  useExportDownloadUrl,
} from "../useExports";

const mockExportList = {
  items: [
    {
      id: "e-1",
      user_id: "u-1",
      export_type: "meta_snapshot",
      config: {},
      format: "json",
      status: "completed",
      file_path: "/exports/e-1.json",
      file_size_bytes: 1024,
      error_message: null,
      expires_at: "2024-02-01T00:00:00Z",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
  ],
  total: 1,
};

const mockExport = mockExportList.items[0];

const mockDownload = {
  export_id: "e-1",
  download_url: "https://storage.example.com/exports/e-1.json",
  expires_in_hours: 24,
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

describe("useExports", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch exports with default params", async () => {
    vi.mocked(exportsApi.list).mockResolvedValue(mockExportList);

    const { result } = renderHook(() => useExports(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockExportList);
    expect(exportsApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch exports with search params", async () => {
    vi.mocked(exportsApi.list).mockResolvedValue(mockExportList);

    const params = { page: 1, limit: 10 };
    const { result } = renderHook(() => useExports(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(exportsApi.list).toHaveBeenCalledWith(params);
  });

  it("should handle API errors", async () => {
    vi.mocked(exportsApi.list).mockRejectedValue(new Error("Unauthorized"));

    const { result } = renderHook(() => useExports(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useExport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch export by ID", async () => {
    vi.mocked(exportsApi.getById).mockResolvedValue(mockExport);

    const { result } = renderHook(() => useExport("e-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockExport);
    expect(exportsApi.getById).toHaveBeenCalledWith("e-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useExport(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(exportsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(exportsApi.getById).mockRejectedValue(new Error("Not found"));

    const { result } = renderHook(() => useExport("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCreateExport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create an export", async () => {
    vi.mocked(exportsApi.create).mockResolvedValue(mockExport);

    const { result } = renderHook(() => useCreateExport(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        export_type: "meta_snapshot",
        format: "json",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(exportsApi.create).toHaveBeenCalledWith({
      export_type: "meta_snapshot",
      format: "json",
    });
  });

  it("should handle creation errors", async () => {
    vi.mocked(exportsApi.create).mockRejectedValue(
      new Error("Validation failed")
    );

    const { result } = renderHook(() => useCreateExport(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ export_type: "meta_snapshot" });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useExportDownloadUrl", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch download URL", async () => {
    vi.mocked(exportsApi.getDownloadUrl).mockResolvedValue(mockDownload);

    const { result } = renderHook(() => useExportDownloadUrl("e-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockDownload);
    expect(exportsApi.getDownloadUrl).toHaveBeenCalledWith("e-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useExportDownloadUrl(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(exportsApi.getDownloadUrl).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(exportsApi.getDownloadUrl).mockRejectedValue(
      new Error("Not found")
    );

    const { result } = renderHook(() => useExportDownloadUrl("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
