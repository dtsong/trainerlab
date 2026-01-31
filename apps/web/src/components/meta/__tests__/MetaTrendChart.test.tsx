import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetaTrendChart } from "../MetaTrendChart";
import type { MetaSnapshot } from "@trainerlab/shared-types";

// Mock ResizeObserver for Recharts ResponsiveContainer
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("MetaTrendChart", () => {
  const mockSnapshots: MetaSnapshot[] = [
    {
      snapshotDate: "2025-01-01",
      region: null,
      format: "standard",
      bestOf: 3,
      archetypeBreakdown: [
        { name: "Charizard ex", share: 0.15 },
        { name: "Gardevoir ex", share: 0.12 },
      ],
      cardUsage: [],
      sampleSize: 100,
    },
    {
      snapshotDate: "2025-01-08",
      region: null,
      format: "standard",
      bestOf: 3,
      archetypeBreakdown: [
        { name: "Charizard ex", share: 0.18 },
        { name: "Gardevoir ex", share: 0.1 },
      ],
      cardUsage: [],
      sampleSize: 120,
    },
    {
      snapshotDate: "2025-01-15",
      region: null,
      format: "standard",
      bestOf: 3,
      archetypeBreakdown: [
        { name: "Charizard ex", share: 0.2 },
        { name: "Gardevoir ex", share: 0.09 },
      ],
      cardUsage: [],
      sampleSize: 150,
    },
  ];

  it("should render the chart container", () => {
    render(<MetaTrendChart snapshots={mockSnapshots} />);

    expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();
  });

  it("should render with empty data", () => {
    render(<MetaTrendChart snapshots={[]} />);

    expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    render(
      <MetaTrendChart snapshots={mockSnapshots} className="custom-class" />,
    );

    expect(screen.getByTestId("meta-trend-chart")).toHaveClass("custom-class");
  });

  it("should include recharts container", () => {
    render(<MetaTrendChart snapshots={mockSnapshots} />);

    expect(
      screen
        .getByTestId("meta-trend-chart")
        .querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });

  it("should handle single snapshot", () => {
    render(<MetaTrendChart snapshots={[mockSnapshots[0]]} />);

    expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();
  });
});
