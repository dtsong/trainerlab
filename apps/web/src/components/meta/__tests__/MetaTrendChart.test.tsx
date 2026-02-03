import React from "react";
import {
  describe,
  it,
  expect,
  vi,
  beforeAll,
  beforeEach,
  afterEach,
} from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

  it("should render responsive recharts container", () => {
    // Suppress console.warn for safeFormatDate
    const originalWarn = console.warn;
    console.warn = vi.fn();

    render(<MetaTrendChart snapshots={mockSnapshots} />);

    const container = screen.getByTestId("meta-trend-chart");
    // Recharts should render the responsive container
    expect(
      container.querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();

    console.warn = originalWarn;
  });

  it("should handle many archetypes without error", () => {
    // Suppress console.warn for safeFormatDate
    const originalWarn = console.warn;
    console.warn = vi.fn();

    // Create snapshots with more than 5 archetypes
    const manyArchetypesSnapshots: MetaSnapshot[] = [
      {
        snapshotDate: "2025-01-01",
        region: null,
        format: "standard",
        bestOf: 3,
        archetypeBreakdown: [
          { name: "Archetype 1", share: 0.15 },
          { name: "Archetype 2", share: 0.14 },
          { name: "Archetype 3", share: 0.13 },
          { name: "Archetype 4", share: 0.12 },
          { name: "Archetype 5", share: 0.11 },
          { name: "Archetype 6", share: 0.1 },
          { name: "Archetype 7", share: 0.09 },
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
          { name: "Archetype 1", share: 0.16 },
          { name: "Archetype 2", share: 0.13 },
          { name: "Archetype 3", share: 0.12 },
          { name: "Archetype 4", share: 0.11 },
          { name: "Archetype 5", share: 0.1 },
          { name: "Archetype 6", share: 0.09 },
          { name: "Archetype 7", share: 0.08 },
        ],
        cardUsage: [],
        sampleSize: 120,
      },
    ];

    render(<MetaTrendChart snapshots={manyArchetypesSnapshots} />);

    // Chart should render without error
    expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();

    console.warn = originalWarn;
  });
});
