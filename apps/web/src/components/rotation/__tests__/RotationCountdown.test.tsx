import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { RotationCountdown } from "../RotationCountdown";

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

// Mock the useFormat hook
const mockUseUpcomingFormat = vi.fn();
vi.mock("@/hooks/useFormat", () => ({
  useUpcomingFormat: () => mockUseUpcomingFormat(),
}));

describe("RotationCountdown", () => {
  const mockUpcomingFormat = {
    format: {
      id: "f-1",
      name: "G-2026",
      display_name: "Regulation G",
      legal_sets: ["sv1", "sv2"],
      is_current: false,
      is_upcoming: true,
    },
    days_until_rotation: 30,
    rotation_date: "2026-04-01T00:00:00Z",
  };

  it("should render nothing while loading", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    const { container } = render(<RotationCountdown />);
    expect(container.firstChild).toBeNull();
  });

  it("should render nothing on error", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    const { container } = render(<RotationCountdown />);
    expect(container.firstChild).toBeNull();
  });

  it("should render nothing when no data is returned", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    });

    const { container } = render(<RotationCountdown />);
    expect(container.firstChild).toBeNull();
  });

  it("should render nothing when rotation is more than 60 days away", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 90 },
      isLoading: false,
      isError: false,
    });

    const { container } = render(<RotationCountdown />);
    expect(container.firstChild).toBeNull();
  });

  it("should render countdown when rotation is within 60 days", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: mockUpcomingFormat,
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    expect(screen.getByText("Rotation Countdown")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
    expect(screen.getByText("days")).toBeInTheDocument();
  });

  it("should display singular 'day' when 1 day remaining", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 1 },
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("day")).toBeInTheDocument();
  });

  it("should display the formatted rotation date", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: mockUpcomingFormat,
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    // The date is formatted using toLocaleDateString which is timezone-dependent
    const expectedDate = new Date("2026-04-01T00:00:00Z").toLocaleDateString(
      "en-US",
      {
        month: "long",
        day: "numeric",
        year: "numeric",
      }
    );
    expect(
      screen.getByText(new RegExp(`Regulation G format begins ${expectedDate}`))
    ).toBeInTheDocument();
  });

  it("should render the 'View Rotation Impact' link", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: mockUpcomingFormat,
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    const link = screen.getByText("View Rotation Impact");
    expect(link.closest("a")).toHaveAttribute("href", "/rotation");
  });

  it("should apply red urgency class when 7 or fewer days remain", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 5 },
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    const card = screen.getByText("Rotation Countdown").closest(".border");
    expect(card).toHaveClass("text-red-400");
  });

  it("should apply orange urgency class when 8-14 days remain", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 10 },
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    const card = screen.getByText("Rotation Countdown").closest(".border");
    expect(card).toHaveClass("text-orange-400");
  });

  it("should apply yellow urgency class when 15-30 days remain", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 20 },
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    const card = screen.getByText("Rotation Countdown").closest(".border");
    expect(card).toHaveClass("text-yellow-400");
  });

  it("should apply blue urgency class when 31-60 days remain", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 45 },
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    const card = screen.getByText("Rotation Countdown").closest(".border");
    expect(card).toHaveClass("text-blue-400");
  });

  it("should render at exactly 60 days", () => {
    mockUseUpcomingFormat.mockReturnValue({
      data: { ...mockUpcomingFormat, days_until_rotation: 60 },
      isLoading: false,
      isError: false,
    });

    render(<RotationCountdown />);

    expect(screen.getByText("60")).toBeInTheDocument();
    expect(screen.getByText("Rotation Countdown")).toBeInTheDocument();
  });
});
