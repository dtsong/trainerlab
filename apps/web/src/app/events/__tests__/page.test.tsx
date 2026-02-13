import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import EventsPage from "../page";

const mockUseEvents = vi.fn();

vi.mock("@/hooks/useEvents", () => ({
  useEvents: (...args: unknown[]) => mockUseEvents(...args),
}));

vi.mock("@/components/events", () => ({
  EventCard: ({ event }: { event: { name: string } }) => (
    <div>{event.name}</div>
  ),
  EventFilters: ({
    onMajorFormatChange,
    onSeasonChange,
  }: {
    onMajorFormatChange: (value: "svi-asc") => void;
    onSeasonChange: (value: "2026") => void;
  }) => (
    <div>
      <button onClick={() => onMajorFormatChange("svi-asc")}>Set Window</button>
      <button onClick={() => onSeasonChange("2026")}>Set Season</button>
    </div>
  ),
}));

describe("EventsPage filters", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseEvents.mockReturnValue({
      data: {
        items: [
          {
            id: "event-1",
            name: "NAIC 2026",
          },
        ],
        total: 1,
        page: 1,
        limit: 20,
        has_next: false,
        has_prev: false,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it("applies major window and season filters", () => {
    render(<EventsPage />);

    fireEvent.click(screen.getByText("Set Window"));
    fireEvent.click(screen.getByText("Set Season"));

    expect(mockUseEvents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        major_format_key: "svi-asc",
        season: 2026,
      })
    );
  });
});
