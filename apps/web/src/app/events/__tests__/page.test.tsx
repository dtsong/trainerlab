import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import EventsPage from "../page";

const mockUseEvents = vi.fn();

vi.mock("@/hooks/useEvents", () => ({
  useEvents: (...args: unknown[]) => mockUseEvents(...args),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
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
            date: "2026-03-01",
            region: "NA",
            format: "standard",
            tier: "international",
            status: "announced",
          },
          {
            id: "event-2",
            name: "EU Regional",
            date: "2026-03-08",
            region: "EU",
            format: "standard",
            tier: "premier",
            status: "announced",
          },
        ],
        total: 2,
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

  it("groups events by region when showing all regions", () => {
    render(<EventsPage />);

    expect(screen.getByText("North America")).toBeInTheDocument();
    expect(screen.getByText("Europe")).toBeInTheDocument();
    // Appears in both the championship banner and the region group.
    expect(screen.getAllByText("NAIC 2026").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("EU Regional")).toBeInTheDocument();
  });

  it("shows a championship banner when official majors exist", () => {
    render(<EventsPage />);
    expect(screen.getByText("Championship Spotlight")).toBeInTheDocument();
    expect(screen.getByText("More upcoming majors")).toBeInTheDocument();
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
