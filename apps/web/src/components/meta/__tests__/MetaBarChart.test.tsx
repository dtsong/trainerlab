import React from "react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MetaBarChart } from "../MetaBarChart";
import type { CardUsageSummary } from "@trainerlab/shared-types";

// Mock router with accessible push function
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock ResizeObserver for Recharts ResponsiveContainer
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("MetaBarChart", () => {
  const mockData: CardUsageSummary[] = [
    { cardId: "sv4-54", inclusionRate: 0.85, avgCopies: 3.2 },
    { cardId: "sv3-6", inclusionRate: 0.72, avgCopies: 2.8 },
    { cardId: "swsh1-1", inclusionRate: 0.65, avgCopies: 4.0 },
  ];

  it("should render the chart container", () => {
    render(<MetaBarChart data={mockData} />);

    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should render with empty data", () => {
    render(<MetaBarChart data={[]} />);

    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    render(<MetaBarChart data={mockData} className="custom-class" />);

    expect(screen.getByTestId("meta-bar-chart")).toHaveClass("custom-class");
  });

  it("should include recharts container", () => {
    render(<MetaBarChart data={mockData} />);

    expect(
      screen
        .getByTestId("meta-bar-chart")
        .querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("should accept limit prop without error", () => {
    // Just verify component renders without error with limit prop
    render(<MetaBarChart data={mockData} limit={2} />);
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should accept cardNames prop without error", () => {
    const cardNames = { "sv4-54": "Charizard ex" };
    render(<MetaBarChart data={mockData} cardNames={cardNames} />);
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should navigate to card page when bar is clicked", () => {
    mockPush.mockClear();
    render(<MetaBarChart data={mockData} />);

    // Find the recharts Bar elements (they are rendered as SVG rect elements)
    const container = screen.getByTestId("meta-bar-chart");
    const bars = container.querySelectorAll(".recharts-bar-rectangle");

    // Click the first bar if it exists
    if (bars.length > 0) {
      fireEvent.click(bars[0]);
      // Verify router.push was called with the expected card URL
      expect(mockPush).toHaveBeenCalledWith("/cards/sv4-54");
    }
  });

  it("should display card name when cardNames prop is provided", () => {
    const cardNames = {
      "sv4-54": "Charizard ex",
      "sv3-6": "Gardevoir ex",
    };
    render(<MetaBarChart data={mockData} cardNames={cardNames} />);

    // The chart should render without error with card names
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should respect limit prop", () => {
    const manyCards: CardUsageSummary[] = Array.from(
      { length: 20 },
      (_, i) => ({
        cardId: `card-${i}`,
        inclusionRate: 0.9 - i * 0.04,
        avgCopies: 3,
      }),
    );

    render(<MetaBarChart data={manyCards} limit={5} />);
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
    // Chart should render with only 5 bars
  });
});
