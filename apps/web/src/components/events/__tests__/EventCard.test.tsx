import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { EventCard } from "../EventCard";

import type { ApiEventSummary } from "@trainerlab/shared-types";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("EventCard", () => {
  const mockEvent: ApiEventSummary = {
    id: "event-1",
    name: "NAIC 2026",
    date: "2026-06-20T00:00:00Z",
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
  };

  it("should render event name", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("NAIC 2026")).toBeInTheDocument();
  });

  it("should link to event detail page", () => {
    render(<EventCard event={mockEvent} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/events/event-1");
  });

  it("should display the formatted date", () => {
    render(<EventCard event={mockEvent} />);

    const expectedDate = new Date(mockEvent.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    expect(screen.getByText(expectedDate)).toBeInTheDocument();
  });

  it("should display location with city, country, and region", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("Columbus, US, NA")).toBeInTheDocument();
  });

  it("should display only region when city and country are not provided", () => {
    const eventNoLocation: ApiEventSummary = {
      ...mockEvent,
      city: null,
      country: null,
    };

    render(<EventCard event={eventNoLocation} />);

    expect(screen.getByText("NA")).toBeInTheDocument();
  });

  it("should display participant count when available", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("2048")).toBeInTheDocument();
  });

  it("should not display participant count when not provided", () => {
    const eventNoParticipants: ApiEventSummary = {
      ...mockEvent,
      participant_count: null,
    };

    render(<EventCard event={eventNoParticipants} />);

    expect(screen.queryByText("2048")).not.toBeInTheDocument();
  });

  it("should display the tier badge", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("major")).toBeInTheDocument();
  });

  it("should not display tier badge when tier is null", () => {
    const noTierEvent: ApiEventSummary = {
      ...mockEvent,
      tier: null,
    };

    render(<EventCard event={noTierEvent} />);

    expect(screen.queryByText("major")).not.toBeInTheDocument();
  });

  it("should display registration status badge", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("Registration Open")).toBeInTheDocument();
  });

  it("should display announced status", () => {
    const announcedEvent: ApiEventSummary = {
      ...mockEvent,
      status: "announced",
    };

    render(<EventCard event={announcedEvent} />);

    expect(screen.getByText("Announced")).toBeInTheDocument();
  });

  it("should display register badge when registration is open", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("Register")).toBeInTheDocument();
  });

  it("should not display register badge when registration is closed", () => {
    const closedEvent: ApiEventSummary = {
      ...mockEvent,
      status: "registration_closed",
    };

    render(<EventCard event={closedEvent} />);

    expect(screen.queryByText("Register")).not.toBeInTheDocument();
  });

  it("should display format name", () => {
    render(<EventCard event={mockEvent} />);

    expect(screen.getByText("Standard")).toBeInTheDocument();
  });
});
