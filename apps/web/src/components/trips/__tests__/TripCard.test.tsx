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
    event_count: 3,
    next_event_date: "2026-06-20",
    created_at: "2026-01-15T10:00:00Z",
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

  it("should display upcoming status badge", () => {
    const upcomingTrip: ApiTripSummary = {
      ...mockTrip,
      status: "upcoming",
    };

    render(<TripCard trip={upcomingTrip} />);

    expect(screen.getByText("Upcoming")).toBeInTheDocument();
  });

  it("should display completed status badge", () => {
    const completedTrip: ApiTripSummary = {
      ...mockTrip,
      status: "completed",
    };

    render(<TripCard trip={completedTrip} />);

    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("should display active status badge", () => {
    const activeTrip: ApiTripSummary = {
      ...mockTrip,
      status: "active",
    };

    render(<TripCard trip={activeTrip} />);

    expect(screen.getByText("Active")).toBeInTheDocument();
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

  it("should display next event date section", () => {
    render(<TripCard trip={mockTrip} />);

    expect(screen.getByText("Next Event")).toBeInTheDocument();
  });

  it("should not show next event section when no next event date", () => {
    const noNextTrip: ApiTripSummary = {
      ...mockTrip,
      next_event_date: null,
    };

    render(<TripCard trip={noNextTrip} />);

    expect(screen.queryByText("Next Event")).not.toBeInTheDocument();
  });
});
