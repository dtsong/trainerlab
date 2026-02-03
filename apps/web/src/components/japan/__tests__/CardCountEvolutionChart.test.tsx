import React from "react";
import { describe, it, expect, beforeAll } from "vitest";
import { render, screen } from "@testing-library/react";
import { CardCountEvolutionChart } from "../CardCountEvolutionChart";
import type { ApiCardCountEvolution } from "@trainerlab/shared-types";

// Mock ResizeObserver for Recharts
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockCards: ApiCardCountEvolution[] = [
  {
    card_id: "sv4-6",
    card_name: "Charizard ex",
    data_points: [
      {
        snapshot_date: "2024-01-08",
        avg_copies: 2.5,
        inclusion_rate: 0.8,
        sample_size: 10,
      },
      {
        snapshot_date: "2024-01-15",
        avg_copies: 3.0,
        inclusion_rate: 0.85,
        sample_size: 12,
      },
      {
        snapshot_date: "2024-01-22",
        avg_copies: 3.5,
        inclusion_rate: 0.9,
        sample_size: 15,
      },
    ],
    total_change: 1.0,
    current_avg: 3.5,
  },
  {
    card_id: "sv3-12",
    card_name: "Rare Candy",
    data_points: [
      {
        snapshot_date: "2024-01-08",
        avg_copies: 4.0,
        inclusion_rate: 1.0,
        sample_size: 10,
      },
      {
        snapshot_date: "2024-01-15",
        avg_copies: 3.5,
        inclusion_rate: 0.95,
        sample_size: 12,
      },
    ],
    total_change: -0.5,
    current_avg: 3.5,
  },
];

describe("CardCountEvolutionChart", () => {
  it("should render the chart container", () => {
    render(<CardCountEvolutionChart cards={mockCards} />);
    expect(screen.getByTestId("card-count-chart")).toBeInTheDocument();
  });

  it("should render empty state when no cards", () => {
    render(<CardCountEvolutionChart cards={[]} />);
    expect(
      screen.getByText("Not enough data to display chart")
    ).toBeInTheDocument();
  });

  it("should render with custom className", () => {
    render(<CardCountEvolutionChart cards={mockCards} className="my-chart" />);
    const container = screen.getByTestId("card-count-chart");
    expect(container).toHaveClass("my-chart");
  });

  it("should render a Recharts ResponsiveContainer when data exists", () => {
    const { container } = render(<CardCountEvolutionChart cards={mockCards} />);
    // Recharts renders a responsive container div
    const responsiveContainer = container.querySelector(
      ".recharts-responsive-container"
    );
    expect(responsiveContainer).toBeInTheDocument();
  });

  it("should handle single data point gracefully", () => {
    const singlePoint: ApiCardCountEvolution[] = [
      {
        card_id: "x1",
        card_name: "Single Card",
        data_points: [
          {
            snapshot_date: "2024-01-08",
            avg_copies: 2.0,
            inclusion_rate: 0.5,
            sample_size: 4,
          },
        ],
        total_change: 0,
        current_avg: 2.0,
      },
    ];
    render(<CardCountEvolutionChart cards={singlePoint} />);
    expect(screen.getByTestId("card-count-chart")).toBeInTheDocument();
  });
});
