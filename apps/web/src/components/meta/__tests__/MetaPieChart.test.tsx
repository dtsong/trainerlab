import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetaPieChart } from "../MetaPieChart";
import type { Archetype } from "@trainerlab/shared-types";

// Mock ResizeObserver for Recharts ResponsiveContainer
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("MetaPieChart", () => {
  const mockData: Archetype[] = [
    { name: "Charizard ex", share: 0.15 },
    { name: "Gardevoir ex", share: 0.12 },
    { name: "Miraidon ex", share: 0.1 },
    { name: "Lost Zone", share: 0.08 },
  ];

  it("should render the chart container", () => {
    render(<MetaPieChart data={mockData} />);

    expect(screen.getByTestId("meta-pie-chart")).toBeInTheDocument();
  });

  it("should render with empty data", () => {
    render(<MetaPieChart data={[]} />);

    expect(screen.getByTestId("meta-pie-chart")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    render(<MetaPieChart data={mockData} className="custom-class" />);

    expect(screen.getByTestId("meta-pie-chart")).toHaveClass("custom-class");
  });

  it("should include recharts container", () => {
    render(<MetaPieChart data={mockData} />);

    // Recharts renders a responsive-container
    expect(
      screen
        .getByTestId("meta-pie-chart")
        .querySelector(".recharts-responsive-container"),
    ).toBeInTheDocument();
  });
});
