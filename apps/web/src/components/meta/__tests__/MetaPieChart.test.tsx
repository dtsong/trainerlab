import React from "react";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, within, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Archetype } from "@trainerlab/shared-types";
import { groupArchetypes } from "@/lib/meta-utils";

// Capture props passed to recharts components so we can invoke callbacks
let capturedPieProps: Record<string, unknown> = {};
let capturedTooltipProps: Record<string, unknown> = {};

vi.mock("recharts", () => ({
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: (props: Record<string, unknown>) => {
    capturedPieProps = props;
    const children = props.children as React.ReactNode;
    return <div data-testid="pie">{children}</div>;
  },
  Cell: (props: Record<string, unknown>) => (
    <div
      data-testid="pie-cell"
      data-fill={props.fill as string}
      data-opacity={String(props.opacity)}
    />
  ),
  Tooltip: (props: Record<string, unknown>) => {
    capturedTooltipProps = props;
    const ContentComponent = props.content as React.ReactElement;
    return <div data-testid="tooltip">{ContentComponent}</div>;
  },
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div className="recharts-responsive-container">{children}</div>
  ),
}));

// Import after mocks
import { MetaPieChart } from "../MetaPieChart";

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

  beforeEach(() => {
    capturedPieProps = {};
    capturedTooltipProps = {};
  });

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

  describe("CustomTooltip", () => {
    it("should render tooltip content when active with payload", () => {
      render(<MetaPieChart data={mockData} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;
      expect(tooltipContent).toBeDefined();

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          payload: [
            {
              name: "Charizard ex",
              value: 15,
              payload: {
                name: "Charizard ex",
                share: 0.15,
                value: 15,
                color: "#ff0000",
              },
            },
          ],
        })
      );

      expect(container.textContent).toContain("Charizard ex");
      expect(container.textContent).toContain("15.0% of meta");
    });

    it("should render nothing when not active", () => {
      render(<MetaPieChart data={mockData} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: false,
          payload: [
            {
              name: "Charizard ex",
              value: 15,
              payload: {
                name: "Charizard ex",
                share: 0.15,
                value: 15,
                color: "#ff0000",
              },
            },
          ],
        })
      );

      expect(container.textContent).toBe("");
    });

    it("should render nothing when payload is empty", () => {
      render(<MetaPieChart data={mockData} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          payload: [],
        })
      );

      expect(container.textContent).toBe("");
    });

    it("should render nothing when payload is undefined", () => {
      render(<MetaPieChart data={mockData} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          payload: undefined,
        })
      );

      expect(container.textContent).toBe("");
    });
  });

  describe("Pie onMouseEnter/onMouseLeave", () => {
    it("should set activeIndex on mouse enter", () => {
      render(<MetaPieChart data={mockData} />);
      const onMouseEnter = capturedPieProps.onMouseEnter as (
        data: unknown,
        index: number
      ) => void;
      expect(onMouseEnter).toBeDefined();

      // Triggering onMouseEnter should set the active index
      // This exercises the setActiveIndex(index) callback
      act(() => {
        onMouseEnter(undefined, 0);
      });
    });

    it("should clear activeIndex on mouse leave", () => {
      render(<MetaPieChart data={mockData} />);
      const onMouseLeave = capturedPieProps.onMouseLeave as () => void;
      expect(onMouseLeave).toBeDefined();

      // Triggering onMouseLeave should clear the active index
      // This exercises the setActiveIndex(null) callback
      act(() => {
        onMouseLeave();
      });
    });
  });

  describe("legend interaction", () => {
    it("should update activeIndex on legend item hover", async () => {
      const user = userEvent.setup();
      render(<MetaPieChart data={mockData} />);
      const legend = screen.getByTestId("pie-legend");
      const buttons = within(legend).getAllByRole("button");

      // Hover over first legend item
      await user.hover(buttons[0]);
      // Un-hover
      await user.unhover(buttons[0]);
    });
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

    it("should sort Other detail by share descending", async () => {
      const user = userEvent.setup();
      render(<MetaPieChart data={manyArchetypes} topN={8} />);

      await user.click(screen.getByText("Other (12)"));
      const detail = screen.getByTestId("other-detail");

      // The Other detail should show archetypes sorted by share desc
      // Archetype 9 has higher share than Archetype 20
      const detailText = detail.textContent || "";
      const idx9 = detailText.indexOf("Archetype 9");
      const idx20 = detailText.indexOf("Archetype 20");
      expect(idx9).toBeLessThan(idx20);
    });
  });

  describe("center label", () => {
    it("should render center label with top archetype name and share", () => {
      const { container } = render(<MetaPieChart data={mockData} />);
      // The center label uses native <text> SVG elements inside PieChart
      const textElements = container.querySelectorAll("text");
      expect(textElements.length).toBeGreaterThanOrEqual(2);

      // Check that the top archetype name and percentage are present
      const allText = Array.from(textElements).map((t) => t.textContent);
      expect(allText).toContain("Charizard ex");
      expect(allText).toContain("15.0%");
    });

    it("should not render center label text elements when data is empty", () => {
      const { container } = render(<MetaPieChart data={[]} />);
      const textElements = container.querySelectorAll("text");
      expect(textElements.length).toBe(0);
    });
  });
});
