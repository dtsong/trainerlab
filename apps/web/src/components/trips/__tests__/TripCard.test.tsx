import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TripCard } from "../TripCard";

import type { ApiTripSummary } from "@trainerlab/shared-types";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("TripCard", () => {
  const mockTrip: ApiTripSummary = {
    id: "trip-1",
    name: "Spring 2026 Season",
    status: "planning",
    visibility: "private",
    event_count: 3,
    next_event: {
      id: "event-456",
      name: "NAIC 2026",
      date: "2026-06-20T00:00:00Z",
      region: "NA",
      country: "US",
      city: "Columbus",
      format: "standard",
      tier: "major",
      status: "registration_open",
    },
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-01-20T14:00:00Z",
  };

  it("should render trip name", () => {
    render(<TripCard trip={mockTrip} />);

    expect(screen.getByText("Spring 2026 Season")).toBeInTheDocument();
  });

  it("should link to trip detail page", () => {
    render(<TripCard trip={mockTrip} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/trips/trip-1");
  });

  it("should display planning status badge", () => {
    render(<TripCard trip={mockTrip} />);

    expect(screen.getByText("Planning")).toBeInTheDocument();
  });

  it("should display confirmed status badge", () => {
    const confirmedTrip: ApiTripSummary = {
      ...mockTrip,
      status: "confirmed",
    };

    render(<TripCard trip={confirmedTrip} />);

    expect(screen.getByText("Confirmed")).toBeInTheDocument();
  });

  it("should display completed status badge", () => {
    const completedTrip: ApiTripSummary = {
      ...mockTrip,
      status: "completed",
    };

    render(<TripCard trip={completedTrip} />);

    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("should display cancelled status badge", () => {
    const cancelledTrip: ApiTripSummary = {
      ...mockTrip,
      status: "cancelled",
    };

    render(<TripCard trip={cancelledTrip} />);

    expect(screen.getByText("Cancelled")).toBeInTheDocument();
  });

  it("should display event count with plural", () => {
    render(<TripCard trip={mockTrip} />);

    expect(screen.getByText("3 events")).toBeInTheDocument();
  });

  it("should display event count with singular", () => {
    const singleEventTrip: ApiTripSummary = {
      ...mockTrip,
      event_count: 1,
    };

    render(<TripCard trip={singleEventTrip} />);

    expect(screen.getByText("1 event")).toBeInTheDocument();
  });

  it("should display next event info", () => {
    render(<TripCard trip={mockTrip} />);

    expect(screen.getByText("Next Event")).toBeInTheDocument();
    expect(screen.getByText("NAIC 2026")).toBeInTheDocument();
  });

  it("should display next event region", () => {
    render(<TripCard trip={mockTrip} />);

    expect(screen.getByText("NA")).toBeInTheDocument();
  });

  it("should not show next event section when no next event", () => {
    const noNextTrip: ApiTripSummary = {
      ...mockTrip,
      next_event: null,
    };

    render(<TripCard trip={noNextTrip} />);

    expect(screen.queryByText("Next Event")).not.toBeInTheDocument();
  });
});
