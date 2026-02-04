import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ContentGrid } from "../ContentGrid";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock section-label
vi.mock("@/components/ui/section-label", () => ({
  SectionLabel: ({ label }: { label: string }) => <span>{label}</span>,
}));

// Mock skeletons
vi.mock("../skeletons", () => ({
  IndexCardSkeleton: () => <div data-testid="index-card-skeleton" />,
}));

// Mock hooks
const mockUseLabNotes = vi.fn();
const mockUseTournaments = vi.fn();

vi.mock("@/hooks/useLabNotes", () => ({
  useLabNotes: (...args: unknown[]) => mockUseLabNotes(...args),
}));

vi.mock("@/hooks/useTournaments", () => ({
  useTournaments: (...args: unknown[]) => mockUseTournaments(...args),
}));

describe("ContentGrid", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseLabNotes.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });
  });

  it("should render the 'Latest Updates' section label", () => {
    render(<ContentGrid />);

    expect(screen.getByText("Latest Updates")).toBeInTheDocument();
  });

  it("should render the annotation subtitle", () => {
    render(<ContentGrid />);

    expect(
      screen.getByText(
        "Research notes, tournament results, and upcoming events"
      )
    ).toBeInTheDocument();
  });

  it("should render three index card columns", () => {
    render(<ContentGrid />);

    expect(screen.getByText("Lab Notes")).toBeInTheDocument();
    expect(screen.getByText("Recent Tournaments")).toBeInTheDocument();
    expect(screen.getByText("Upcoming Events")).toBeInTheDocument();
  });

  it("should render view-all links for each column", () => {
    render(<ContentGrid />);

    const articlesLink = screen.getByRole("link", { name: /All articles/i });
    expect(articlesLink).toHaveAttribute("href", "/lab-notes");

    const tournamentsLink = screen.getByRole("link", {
      name: /All tournaments/i,
    });
    expect(tournamentsLink).toHaveAttribute("href", "/tournaments");

    const calendarLink = screen.getByRole("link", {
      name: /Full calendar/i,
    });
    expect(calendarLink).toHaveAttribute(
      "href",
      "/tournaments?filter=upcoming"
    );
  });

  it("should show skeleton cards while loading", () => {
    mockUseLabNotes.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<ContentGrid />);

    const skeletons = screen.getAllByTestId("index-card-skeleton");
    expect(skeletons).toHaveLength(3);
  });

  it("should show empty messages when no data", () => {
    render(<ContentGrid />);

    expect(screen.getByText("No articles yet")).toBeInTheDocument();
    expect(screen.getByText("No tournaments yet")).toBeInTheDocument();
    expect(screen.getByText("No upcoming events")).toBeInTheDocument();
  });

  it("should show error messages when requests fail", () => {
    mockUseLabNotes.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });
    mockUseTournaments.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<ContentGrid />);

    expect(screen.getByText("Could not load articles")).toBeInTheDocument();
    expect(screen.getByText("Could not load tournaments")).toBeInTheDocument();
    expect(screen.getByText("Could not load events")).toBeInTheDocument();
  });

  it("should render lab notes when data is available", () => {
    mockUseLabNotes.mockReturnValue({
      data: {
        items: [
          {
            title: "Meta Report Week 1",
            summary: "A summary of the current meta",
            slug: "meta-report-week-1",
            published_at: "2025-01-15",
            created_at: "2025-01-14",
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    render(<ContentGrid />);

    expect(screen.getByText("Meta Report Week 1")).toBeInTheDocument();
    expect(
      screen.getByText("A summary of the current meta")
    ).toBeInTheDocument();
  });

  it("should render tournaments when data is available", () => {
    mockUseTournaments.mockReturnValue({
      data: {
        items: [
          {
            id: "t1",
            name: "Regional Championship",
            date: "2025-01-20",
            region: "NA",
            participant_count: 256,
            top_placements: [{ archetype: "Charizard ex" }],
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    render(<ContentGrid />);

    // Tournament name should appear at least once (in recent or upcoming column)
    expect(
      screen.getAllByText("Regional Championship").length
    ).toBeGreaterThanOrEqual(1);
  });

  it("should link lab notes to their slug-based URLs", () => {
    mockUseLabNotes.mockReturnValue({
      data: {
        items: [
          {
            title: "Test Article",
            summary: "Test summary",
            slug: "test-article",
            published_at: "2025-01-15",
            created_at: "2025-01-14",
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    render(<ContentGrid />);

    const link = screen.getByRole("link", { name: /Test Article/i });
    expect(link).toHaveAttribute("href", "/lab-notes/test-article");
  });
});
