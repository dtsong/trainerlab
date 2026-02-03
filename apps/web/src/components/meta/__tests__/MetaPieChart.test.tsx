import React from "react";
import { describe, it, expect, beforeAll } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MetaPieChart } from "../MetaPieChart";
import type { Archetype } from "@trainerlab/shared-types";
import { groupArchetypes } from "@/lib/meta-utils";

// Mock ResizeObserver for Recharts ResponsiveContainer
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("groupArchetypes", () => {
  it("should return all archetypes when count <= topN", () => {
    const data: Archetype[] = [
      { name: "A", share: 0.5 },
      { name: "B", share: 0.3 },
    ];
    const result = groupArchetypes(data, { topN: 8 });
    expect(result.displayed).toEqual(data);
    expect(result.other).toBeNull();
  });

  it("should group archetypes beyond topN into Other", () => {
    const data: Archetype[] = Array.from({ length: 12 }, (_, i) => ({
      name: `Archetype ${i}`,
      share: 0.1 - i * 0.005,
    }));
    const result = groupArchetypes(data, { topN: 8 });
    expect(result.displayed).toHaveLength(8);
    expect(result.other).not.toBeNull();
    expect(result.other!.count).toBe(4);
    expect(result.other!.archetypes).toHaveLength(4);
  });

  it("should sort by share descending", () => {
    const data: Archetype[] = [
      { name: "Low", share: 0.01 },
      { name: "High", share: 0.5 },
      { name: "Mid", share: 0.1 },
    ];
    const result = groupArchetypes(data, { topN: 2 });
    expect(result.displayed[0].name).toBe("High");
    expect(result.displayed[1].name).toBe("Mid");
    expect(result.other!.archetypes[0].name).toBe("Low");
  });

  it("should sum Other share correctly", () => {
    const data: Archetype[] = [
      { name: "A", share: 0.5 },
      { name: "B", share: 0.3 },
      { name: "C", share: 0.1 },
      { name: "D", share: 0.1 },
    ];
    const result = groupArchetypes(data, { topN: 2 });
    expect(result.other!.share).toBeCloseTo(0.2);
  });

  it("should default topN to 8", () => {
    const data: Archetype[] = Array.from({ length: 10 }, (_, i) => ({
      name: `Arch ${i}`,
      share: 0.1,
    }));
    const result = groupArchetypes(data);
    expect(result.displayed).toHaveLength(8);
    expect(result.other!.count).toBe(2);
  });

  it("should handle empty array", () => {
    const result = groupArchetypes([]);
    expect(result.displayed).toEqual([]);
    expect(result.other).toBeNull();
  });
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
    expect(
      screen
        .getByTestId("meta-pie-chart")
        .querySelector(".recharts-responsive-container")
    ).toBeInTheDocument();
  });

  it("should render a custom legend", () => {
    render(<MetaPieChart data={mockData} />);
    const legend = screen.getByTestId("pie-legend");
    expect(legend).toBeInTheDocument();
    expect(within(legend).getByText("Charizard ex")).toBeInTheDocument();
    expect(within(legend).getByText("Gardevoir ex")).toBeInTheDocument();
  });

  it("should not show Other when data fits within topN", () => {
    render(<MetaPieChart data={mockData} />);
    expect(screen.queryByText(/Other/)).not.toBeInTheDocument();
  });

  describe("with many archetypes", () => {
    const manyArchetypes: Archetype[] = Array.from({ length: 20 }, (_, i) => ({
      name: `Archetype ${i + 1}`,
      share: 0.15 - i * 0.005,
    }));

    it("should show Other bucket with count", () => {
      render(<MetaPieChart data={manyArchetypes} topN={8} />);
      expect(screen.getByText("Other (12)")).toBeInTheDocument();
    });

    it("should render only topN + 1 legend entries", () => {
      render(<MetaPieChart data={manyArchetypes} topN={8} />);
      const legend = screen.getByTestId("pie-legend");
      const buttons = within(legend).getAllByRole("button");
      expect(buttons).toHaveLength(9); // 8 + Other
    });

    it("should expand Other detail on click", async () => {
      const user = userEvent.setup();
      render(<MetaPieChart data={manyArchetypes} topN={8} />);

      expect(screen.queryByTestId("other-detail")).not.toBeInTheDocument();

      await user.click(screen.getByText("Other (12)"));

      const detail = screen.getByTestId("other-detail");
      expect(detail).toBeInTheDocument();
      // Should contain one of the grouped archetypes
      expect(within(detail).getByText("Archetype 9")).toBeInTheDocument();
    });

    it("should collapse Other detail on second click", async () => {
      const user = userEvent.setup();
      render(<MetaPieChart data={manyArchetypes} topN={8} />);

      await user.click(screen.getByText("Other (12)"));
      expect(screen.getByTestId("other-detail")).toBeInTheDocument();

      await user.click(screen.getByText("Other (12)"));
      expect(screen.queryByTestId("other-detail")).not.toBeInTheDocument();
    });
  });
});
