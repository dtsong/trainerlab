import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetaBarChart } from "../MetaBarChart";
import type { CardUsageSummary } from "@trainerlab/shared-types";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
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
});
