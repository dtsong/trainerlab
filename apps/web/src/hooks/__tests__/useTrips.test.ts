import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type {
  ApiTripSummary,
  ApiTripDetail,
  ApiSharedTripView,
  ApiEventSummary,
} from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  tripsApi: {
    list: vi.fn(),
    create: vi.fn(),
    getById: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    addEvent: vi.fn(),
    removeEvent: vi.fn(),
    getShared: vi.fn(),
    share: vi.fn(),
  },
}));

import { tripsApi } from "@/lib/api";
import {
  useTrips,
  useTrip,
  useCreateTrip,
  useUpdateTrip,
  useDeleteTrip,
  useAddTripEvent,
  useRemoveTripEvent,
  useSharedTrip,
  useShareTrip,
} from "../useTrips";

const mockNextEvent: ApiEventSummary = {
  id: "event-456",
  name: "NAIC 2026",
  date: "2026-06-20",
  region: "NA",
  country: "US",
  city: "Columbus",
  format: "standard",
  tier: "major",
  status: "registration_open",
};

const mockTripSummary: ApiTripSummary = {
  id: "trip-123",
  name: "Spring 2026 Season",
  status: "planning",
  visibility: "private",
  event_count: 2,
  next_event: mockNextEvent,
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-01-20T14:00:00Z",
};

const mockTripDetail: ApiTripDetail = {
  id: "trip-123",
  name: "Spring 2026 Season",
  status: "planning",
  visibility: "private",
  notes: "Focus on Standard format",
  events: [
    {
      id: "te-1",
      trip_id: "trip-123",
      tournament_id: "event-456",
      role: "player",
      notes: null,
      event: mockNextEvent,
      created_at: "2026-01-15T10:00:00Z",
      updated_at: "2026-01-15T10:00:00Z",
    },
  ],
  share_url: null,
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-01-20T14:00:00Z",
};

const mockSharedTrip: ApiSharedTripView = {
  id: "trip-123",
  name: "Spring 2026 Season",
  status: "planning",
  notes: "Focus on Standard format",
  events: mockTripDetail.events,
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

describe("useTrips", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch trips with default params", async () => {
    vi.mocked(tripsApi.list).mockResolvedValue([mockTripSummary]);

    const { result } = renderHook(() => useTrips(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([mockTripSummary]);
    expect(tripsApi.list).toHaveBeenCalledWith({});
  });

  it("should fetch trips with status filter", async () => {
    vi.mocked(tripsApi.list).mockResolvedValue([mockTripSummary]);

    const { result } = renderHook(() => useTrips({ status: "planning" }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tripsApi.list).toHaveBeenCalledWith({
      status: "planning",
    });
  });

  it("should handle API errors", async () => {
    vi.mocked(tripsApi.list).mockRejectedValue(new Error("Not authenticated"));

    const { result } = renderHook(() => useTrips(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it("should return empty array when no trips", async () => {
    vi.mocked(tripsApi.list).mockResolvedValue([]);

    const { result } = renderHook(() => useTrips(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });
});

describe("useTrip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch trip by ID", async () => {
    vi.mocked(tripsApi.getById).mockResolvedValue(mockTripDetail);

    const { result } = renderHook(() => useTrip("trip-123"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockTripDetail);
    expect(tripsApi.getById).toHaveBeenCalledWith("trip-123");
  });

  it("should not fetch when ID is null", async () => {
    const { result } = renderHook(() => useTrip(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(tripsApi.getById).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(tripsApi.getById).mockRejectedValue(new Error("Trip not found"));

    const { result } = renderHook(() => useTrip("nonexistent"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useCreateTrip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should create a trip", async () => {
    vi.mocked(tripsApi.create).mockResolvedValue(mockTripDetail);

    const { result } = renderHook(() => useCreateTrip(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        name: "Spring 2026 Season",
        notes: "Focus on Standard format",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tripsApi.create).toHaveBeenCalledWith({
      name: "Spring 2026 Season",
      notes: "Focus on Standard format",
    });
  });
});

describe("useUpdateTrip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update a trip", async () => {
    vi.mocked(tripsApi.update).mockResolvedValue({
      ...mockTripDetail,
      name: "Updated Name",
    });

    const { result } = renderHook(() => useUpdateTrip(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: "trip-123",
        data: { name: "Updated Name" },
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tripsApi.update).toHaveBeenCalledWith("trip-123", {
      name: "Updated Name",
    });
  });
});

describe("useDeleteTrip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should delete a trip", async () => {
    vi.mocked(tripsApi.delete).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteTrip(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("trip-123");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tripsApi.delete).toHaveBeenCalledWith("trip-123");
  });
});

describe("useAddTripEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should add an event to a trip", async () => {
    vi.mocked(tripsApi.addEvent).mockResolvedValue(mockTripDetail);

    const { result } = renderHook(() => useAddTripEvent(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        tripId: "trip-123",
        data: { tournament_id: "event-789", role: "player" },
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tripsApi.addEvent).toHaveBeenCalledWith("trip-123", {
      tournament_id: "event-789",
      role: "player",
    });
  });
});

describe("useRemoveTripEvent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should remove an event from a trip", async () => {
    vi.mocked(tripsApi.removeEvent).mockResolvedValue(undefined);

    const { result } = renderHook(() => useRemoveTripEvent(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        tripId: "trip-123",
        eventId: "te-1",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tripsApi.removeEvent).toHaveBeenCalledWith("trip-123", "te-1");
  });
});

describe("useSharedTrip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch shared trip by token", async () => {
    vi.mocked(tripsApi.getShared).mockResolvedValue(mockSharedTrip);

    const { result } = renderHook(() => useSharedTrip("abc123token"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSharedTrip);
    expect(tripsApi.getShared).toHaveBeenCalledWith("abc123token");
  });

  it("should not fetch when token is null", async () => {
    const { result } = renderHook(() => useSharedTrip(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(tripsApi.getShared).not.toHaveBeenCalled();
  });

  it("should handle API errors", async () => {
    vi.mocked(tripsApi.getShared).mockRejectedValue(
      new Error("Trip not found")
    );

    const { result } = renderHook(() => useSharedTrip("invalid-token"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });
});

describe("useShareTrip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should generate share link", async () => {
    vi.mocked(tripsApi.share).mockResolvedValue({
      share_url: "https://trainerlab.gg/trips/shared/abc123",
    });

    const { result } = renderHook(() => useShareTrip(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate("trip-123");
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.share_url).toBe(
      "https://trainerlab.gg/trips/shared/abc123"
    );
    expect(tripsApi.share).toHaveBeenCalledWith("trip-123");
  });
});
