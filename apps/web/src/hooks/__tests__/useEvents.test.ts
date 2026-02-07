import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiEventListResponse,
  ApiEventSummary,
  ApiEventDetail,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  eventsApi: {
    list: vi.fn(),
    getById: vi.fn(),
  },
}));

import { eventsApi } from "@/lib/api";
import { useEvents, useEvent } from "../useEvents";

const mockEventSummary: ApiEventSummary = {
  id: "event-123",
  name: "NAIC 2026",
  date: "2026-06-20",
  region: "NA",
  country: "US",
  city: "Columbus",
  format: "standard",
  tier: "major",
  status: "registration_open",
  registration_opens_at: "2026-04-01T12:00:00Z",
  registration_closes_at: "2026-06-01T23:59:00Z",
  registration_url: "https://rk9.gg/event/naic2026",
  participant_count: 2048,
  event_source: "rk9",
};

const mockListResponse: ApiEventListResponse = {
  items: [mockEventSummary],
  total: 15,
  page: 1,
  limit: 20,
  has_next: false,
  has_prev: false,
};

const mockEventDetail: ApiEventDetail = {
  ...mockEventSummary,
  venue_name: "Greater Columbus Convention Center",
  venue_address: "400 N High St, Columbus, OH 43215",
  source_url: "https://pokemon.com/naic2026",
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

describe("useEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch events with default params", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockListResponse);
    expect(eventsApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch events with region filter", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useEvents({ region: "EU" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(eventsApi.list).toHaveBeenCalledWith({ region: "EU" });
  });

  it("should fetch events with format filter", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useEvents({ format: "standard" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(eventsApi.list).toHaveBeenCalledWith({
      format: "standard",
    });
  });

  it("should fetch events with date range", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue(mockListResponse);

    const params = {
      date_from: "2026-03-01",
      date_to: "2026-12-31",
    };

    const { result } = renderHook(() => useEvents(params), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(eventsApi.list).toHaveBeenCalledWith(params);
  });

  it("should fetch events with tier filter", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue(mockListResponse);

    const { result } = renderHook(() => useEvents({ tier: "major" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(eventsApi.list).toHaveBeenCalledWith({ tier: "major" });
  });

  it("should handle pagination", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue({
      ...mockListResponse,
      page: 2,
      has_prev: true,
    });

    const { result } = renderHook(() => useEvents({ page: 2, limit: 10 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(eventsApi.list).toHaveBeenCalledWith({
      page: 2,
      limit: 10,
    });
    expect(result.current.data?.page).toBe(2);
  });

  it("should handle API errors", async () => {
    vi.mocked(eventsApi.list).mockRejectedValue(new Error("API Error"));

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should return empty list when no events found", async () => {
    vi.mocked(eventsApi.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_next: false,
      has_prev: false,
    });

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items).toEqual([]);
    expect(result.current.data?.total).toBe(0);
  });
});

describe("useEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch event by ID", async () => {
    vi.mocked(eventsApi.getById).mockResolvedValue(mockEventDetail);

    const { result } = renderHook(() => useEvent("event-123"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockEventDetail);
    expect(eventsApi.getById).toHaveBeenCalledWith("event-123");
  });

  it("should not fetch when ID is null", async () => {
    const { result } = renderHook(() => useEvent(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(eventsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(eventsApi.getById).mockRejectedValue(
      new Error("Event not found")
    );

    const { result } = renderHook(() => useEvent("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should return event with venue details", async () => {
    vi.mocked(eventsApi.getById).mockResolvedValue(mockEventDetail);

    const { result } = renderHook(() => useEvent("event-123"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.venue_name).toBe(
      "Greater Columbus Convention Center"
    );
    expect(result.current.data?.venue_address).toBe(
      "400 N High St, Columbus, OH 43215"
    );
  });
});
