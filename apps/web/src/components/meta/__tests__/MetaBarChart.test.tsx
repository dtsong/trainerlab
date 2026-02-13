import React from "react";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { CardUsageSummary } from "@trainerlab/shared-types";

// Mock router with accessible push function
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Capture props passed to recharts components so we can invoke callbacks
let capturedXAxisProps: Record<string, unknown> = {};
let capturedYAxisProps: Record<string, unknown> = {};
let capturedTooltipProps: Record<string, unknown> = {};
let capturedBarProps: Record<string, unknown> = {};

vi.mock("recharts", () => ({
  BarChart: ({ children, ...props }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart" data-props={JSON.stringify(props)}>
      {children}
    </div>
  ),
  Bar: (props: Record<string, unknown>) => {
    capturedBarProps = props;
    // Render children (Cell components) if present
    const children = props.children as React.ReactNode;
    return <div data-testid="bar">{children}</div>;
  },
  Cell: (props: Record<string, unknown>) => (
    <div data-testid="cell" data-fill={props.fill as string} />
  ),
  XAxis: (props: Record<string, unknown>) => {
    capturedXAxisProps = props;
    return <div data-testid="x-axis" />;
  },
  YAxis: (props: Record<string, unknown>) => {
    capturedYAxisProps = props;
    return <div data-testid="y-axis" />;
  },
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
import { MetaBarChart } from "../MetaBarChart";

// Mock ResizeObserver for Recharts ResponsiveContainer
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  // MatchMedia is used to decide whether to show Y-axis thumbnails.
  // Default to desktop in tests so thumbnail tick rendering can be exercised.
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation(() => ({
      matches: true,
      media: "(min-width: 640px)",
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

describe("MetaBarChart", () => {
  const mockData: CardUsageSummary[] = [
    {
      cardId: "sv4-54",
      inclusionRate: 0.85,
      avgCopies: 3.2,
      imageSmall: "https://img.test/sv4-54.png",
    },
    { cardId: "sv3-6", inclusionRate: 0.72, avgCopies: 2.8 },
    { cardId: "swsh1-1", inclusionRate: 0.65, avgCopies: 4.0 },
  ];

  beforeEach(() => {
    capturedXAxisProps = {};
    capturedYAxisProps = {};
    capturedTooltipProps = {};
    capturedBarProps = {};
    mockPush.mockClear();
  });

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
        .querySelector(".recharts-responsive-container")
    ).toBeInTheDocument();
  });

  it("should accept limit prop without error", () => {
    render(<MetaBarChart data={mockData} limit={2} />);
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should accept cardNames prop without error", () => {
    const cardNames = { "sv4-54": "Charizard ex" };
    render(<MetaBarChart data={mockData} cardNames={cardNames} />);
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  it("should respect limit prop", () => {
    const manyCards: CardUsageSummary[] = Array.from(
      { length: 20 },
      (_, i) => ({
        cardId: `card-${i}`,
        inclusionRate: 0.9 - i * 0.04,
        avgCopies: 3,
      })
    );

    render(<MetaBarChart data={manyCards} limit={5} />);
    expect(screen.getByTestId("meta-bar-chart")).toBeInTheDocument();
  });

  describe("XAxis tickFormatter", () => {
    it("should format values as percentages", () => {
      render(<MetaBarChart data={mockData} />);
      const tickFormatter = capturedXAxisProps.tickFormatter as (
        value: number
      ) => string;
      expect(tickFormatter).toBeDefined();
      expect(tickFormatter(85)).toBe("85%");
      expect(tickFormatter(0)).toBe("0%");
    });
  });

  describe("YAxis tick rendering", () => {
    it("should provide a custom tick renderer", () => {
      render(<MetaBarChart data={mockData} />);
      expect(capturedYAxisProps.tick).toBeDefined();
      expect(typeof capturedYAxisProps.tick).toBe("function");
    });

    it("should render a thumbnail when imageSmall is available", async () => {
      render(<MetaBarChart data={mockData} />);

      const tick = capturedYAxisProps.tick as (
        props: unknown
      ) => React.ReactNode;
      const el = tick({
        x: 100,
        y: 50,
        payload: { value: "sv4-54" },
      });

      const { container } = render(<svg>{el}</svg>);
      expect(container.querySelector("image")).toBeTruthy();
    });
  });

  describe("CustomTooltip", () => {
    it("should render tooltip content when active with payload", () => {
      render(<MetaBarChart data={mockData} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;
      expect(tooltipContent).toBeDefined();

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          payload: [
            {
              name: "value",
              value: 85,
              payload: {
                cardId: "sv4-54",
                name: "Charizard ex",
                inclusionRate: 0.85,
                avgCopies: 3.2,
              },
            },
          ],
        })
      );

      expect(container.textContent).toContain("Charizard ex");
      expect(container.textContent).toContain("85.0% inclusion rate");
      expect(container.textContent).toContain("3.2 avg copies");
    });

    it("should render nothing when not active", () => {
      render(<MetaBarChart data={mockData} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: false,
          payload: [
            {
              name: "value",
              value: 85,
              payload: {
                cardId: "sv4-54",
                name: "Charizard ex",
                inclusionRate: 0.85,
                avgCopies: 3.2,
              },
            },
          ],
        })
      );

      expect(container.textContent).toBe("");
    });

    it("should render nothing when payload is empty", () => {
      render(<MetaBarChart data={mockData} />);
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
      render(<MetaBarChart data={mockData} />);
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

  describe("Bar onClick (handleBarClick)", () => {
    it("should navigate to card page when bar is clicked", () => {
      render(<MetaBarChart data={mockData} />);
      const onClick = capturedBarProps.onClick as (
        data: unknown,
        index: number
      ) => void;
      expect(onClick).toBeDefined();

      // Click the first bar (index 0) - data is sorted by inclusionRate desc
      // mockData[0] has cardId "sv4-54" (highest inclusionRate at 0.85)
      onClick(undefined, 0);

      expect(mockPush).toHaveBeenCalledWith("/investigate/card/sv4-54");
    });

    it("should navigate to correct card for different bar indices", () => {
      render(<MetaBarChart data={mockData} />);
      const onClick = capturedBarProps.onClick as (
        data: unknown,
        index: number
      ) => void;

      onClick(undefined, 1);
      expect(mockPush).toHaveBeenCalledWith("/investigate/card/sv3-6");
    });

    it("should not navigate when bar index is out of range", () => {
      render(<MetaBarChart data={mockData} />);
      const onClick = capturedBarProps.onClick as (
        data: unknown,
        index: number
      ) => void;

      onClick(undefined, 999);
      expect(mockPush).not.toHaveBeenCalled();
    });

    it("should URL-encode card IDs with special characters", () => {
      const dataWithSpecialChars: CardUsageSummary[] = [
        { cardId: "card/special#1", inclusionRate: 0.9, avgCopies: 3 },
      ];

      render(<MetaBarChart data={dataWithSpecialChars} />);
      const onClick = capturedBarProps.onClick as (
        data: unknown,
        index: number
      ) => void;

      onClick(undefined, 0);
      expect(mockPush).toHaveBeenCalledWith(
        `/investigate/card/${encodeURIComponent("card/special#1")}`
      );
    });
  });

  describe("chart data transformation", () => {
    it("should use cardNames when provided", () => {
      const cardNames = {
        "sv4-54": "Charizard ex",
        "sv3-6": "Gardevoir ex",
      };

      render(<MetaBarChart data={mockData} cardNames={cardNames} />);
      const barChart = screen.getByTestId("bar-chart");
      const dataProps = JSON.parse(barChart.getAttribute("data-props") || "{}");

      // Chart data should use card names
      expect(dataProps.data).toBeDefined();
      const names = dataProps.data.map((d: Record<string, unknown>) => d.name);
      expect(names).toContain("Charizard ex");
      expect(names).toContain("Gardevoir ex");
    });

    it("should fall back to cardId when cardNames not provided", () => {
      render(<MetaBarChart data={mockData} />);
      const barChart = screen.getByTestId("bar-chart");
      const dataProps = JSON.parse(barChart.getAttribute("data-props") || "{}");

      const names = dataProps.data.map((d: Record<string, unknown>) => d.name);
      expect(names).toContain("sv4-54");
    });

    it("should sort data by inclusionRate descending", () => {
      const unsortedData: CardUsageSummary[] = [
        { cardId: "low", inclusionRate: 0.1, avgCopies: 1 },
        { cardId: "high", inclusionRate: 0.9, avgCopies: 4 },
        { cardId: "mid", inclusionRate: 0.5, avgCopies: 2 },
      ];

      render(<MetaBarChart data={unsortedData} />);
      const barChart = screen.getByTestId("bar-chart");
      const dataProps = JSON.parse(barChart.getAttribute("data-props") || "{}");

      expect(dataProps.data[0].name).toBe("high");
      expect(dataProps.data[1].name).toBe("mid");
      expect(dataProps.data[2].name).toBe("low");
    });

    it("should render Cell components with different colors", () => {
      render(<MetaBarChart data={mockData} />);
      const cells = screen.getAllByTestId("cell");
      expect(cells.length).toBe(3);
      // Each cell should have a fill attribute
      cells.forEach((cell) => {
        expect(cell.getAttribute("data-fill")).toBeTruthy();
      });
    });
  });
});
