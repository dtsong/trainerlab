import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api", () => ({
  apiKeysApi: {
    create: vi.fn(),
    list: vi.fn(),
    getById: vi.fn(),
    revoke: vi.fn(),
  },
}));

import { apiKeysApi } from "@/lib/api";
import {
  useApiKeys,
  useApiKey,
  useCreateApiKey,
  useRevokeApiKey,
} from "../useApiKeys";

const mockApiKeyList = {
  items: [
    {
      id: "k-1",
      user_id: "u-1",
      key_prefix: "tl_abc",
      name: "My API Key",
      monthly_limit: 1000,
      requests_this_month: 42,
      is_active: true,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-02T00:00:00Z",
    },
  ],
  total: 1,
};

const mockApiKey = mockApiKeyList.items[0];

const mockCreatedKey = {
  api_key: mockApiKey,
  full_key: "tl_abc123def456",
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

describe("useApiKeys", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch API keys", async () => {
    vi.mocked(apiKeysApi.list).mockResolvedValue(mockApiKeyList);

    const { result } = renderHook(() => useApiKeys(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockApiKeyList);
    expect(apiKeysApi.list).toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(apiKeysApi.list).mockRejectedValue(new Error("Unauthorized"));

    const { result } = renderHook(() => useApiKeys(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useApiKey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch API key by ID", async () => {
    vi.mocked(apiKeysApi.getById).mockResolvedValue(mockApiKey);

    const { result } = renderHook(() => useApiKey("k-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockApiKey);
    expect(apiKeysApi.getById).toHaveBeenCalledWith("k-1");
  });

  it("should not fetch when ID is empty", async () => {
    const { result } = renderHook(() => useApiKey(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(apiKeysApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(apiKeysApi.getById).mockRejectedValue(new Error("Not found"));

    const { result } = renderHook(() => useApiKey("bad-id"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCreateApiKey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create an API key", async () => {
    vi.mocked(apiKeysApi.create).mockResolvedValue(mockCreatedKey);

    const { result } = renderHook(() => useCreateApiKey(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ name: "My API Key", monthly_limit: 1000 });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiKeysApi.create).toHaveBeenCalledWith({
      name: "My API Key",
      monthly_limit: 1000,
    });
    expect(result.current.data).toEqual(mockCreatedKey);
  });

  it("should handle creation errors", async () => {
    vi.mocked(apiKeysApi.create).mockRejectedValue(
      new Error("Validation failed")
    );

    const { result } = renderHook(() => useCreateApiKey(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ name: "" });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useRevokeApiKey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should revoke an API key", async () => {
    vi.mocked(apiKeysApi.revoke).mockResolvedValue(undefined);

    const { result } = renderHook(() => useRevokeApiKey(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("k-1");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiKeysApi.revoke).toHaveBeenCalledWith("k-1");
  });

  it("should handle revocation errors", async () => {
    vi.mocked(apiKeysApi.revoke).mockRejectedValue(new Error("Revoke failed"));

    const { result } = renderHook(() => useRevokeApiKey(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("k-1");
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});
