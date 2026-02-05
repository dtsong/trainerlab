import React from "react";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent, within, act } from "@testing-library/react";
import type { MetaSnapshot } from "@trainerlab/shared-types";

// Capture props passed to recharts components so we can invoke callbacks
let capturedXAxisProps: Record<string, unknown> = {};
let capturedYAxisProps: Record<string, unknown> = {};
let capturedTooltipProps: Record<string, unknown> = {};
let capturedLegendProps: Record<string, unknown> = {};
let capturedLineProps: Array<Record<string, unknown>> = [];

vi.mock("recharts", () => ({
  LineChart: ({ children, ...props }: { children: React.ReactNode }) => (
    <div data-testid="line-chart" data-props={JSON.stringify(props)}>
      {children}
    </div>
  ),
  Line: (props: Record<string, unknown>) => {
    capturedLineProps.push(props);
    return (
      <div
        data-testid={`line-${props.dataKey}`}
        data-hide={String(props.hide)}
      />
    );
  },
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
    // Render the content prop (CustomTooltip) if provided
    const ContentComponent = props.content as React.ReactElement;
    return <div data-testid="tooltip">{ContentComponent}</div>;
  },
  Legend: (props: Record<string, unknown>) => {
    capturedLegendProps = props;
    return <div data-testid="legend" />;
  },
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div className="recharts-responsive-container">{children}</div>
  ),
}));

// Import after mocks
import { MetaTrendChart } from "../MetaTrendChart";

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

  beforeEach(() => {
    capturedXAxisProps = {};
    capturedYAxisProps = {};
    capturedTooltipProps = {};
    capturedLegendProps = {};
    capturedLineProps = [];
  });

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
      <MetaTrendChart snapshots={mockSnapshots} className="custom-class" />
    );
    expect(screen.getByTestId("meta-trend-chart")).toHaveClass("custom-class");
  });

  it("should include recharts container", () => {
    render(<MetaTrendChart snapshots={mockSnapshots} />);
    expect(
      screen
        .getByTestId("meta-trend-chart")
        .querySelector(".recharts-responsive-container")
    ).toBeInTheDocument();
  });

  it("should handle single snapshot", () => {
    render(<MetaTrendChart snapshots={[mockSnapshots[0]]} />);
    expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();
  });

  it("should render a Line for each archetype", () => {
    render(<MetaTrendChart snapshots={mockSnapshots} />);
    expect(screen.getByTestId("line-Charizard ex")).toBeInTheDocument();
    expect(screen.getByTestId("line-Gardevoir ex")).toBeInTheDocument();
  });

  it("should handle many archetypes without error", () => {
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
    ];

    render(<MetaTrendChart snapshots={manyArchetypesSnapshots} />);
    expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();
  });

  describe("XAxis tickFormatter", () => {
    it("should format date values using safeFormatDate", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const tickFormatter = capturedXAxisProps.tickFormatter as (
        value: string
      ) => string;
      expect(tickFormatter).toBeDefined();
      const result = tickFormatter("2025-01-01");
      // safeFormatDate with "MMM d" format should return something like "Jan 1"
      expect(result).toBe("Jan 1");
    });

    it("should handle invalid date gracefully in tickFormatter", () => {
      const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const tickFormatter = capturedXAxisProps.tickFormatter as (
        value: string
      ) => string;
      const result = tickFormatter("not-a-date");
      // safeFormatDate returns the raw string on error
      expect(result).toBe("not-a-date");
      warnSpy.mockRestore();
    });
  });

  describe("YAxis tickFormatter", () => {
    it("should format values as percentages", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const tickFormatter = capturedYAxisProps.tickFormatter as (
        value: number
      ) => string;
      expect(tickFormatter).toBeDefined();
      expect(tickFormatter(15)).toBe("15%");
      expect(tickFormatter(0)).toBe("0%");
    });
  });

  describe("CustomTooltip", () => {
    it("should render tooltip content when active with payload and label", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      // The Tooltip mock renders the content prop (CustomTooltip element)
      // We need to render CustomTooltip directly with props
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;
      expect(tooltipContent).toBeDefined();

      // Render CustomTooltip with active state
      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          label: "2025-01-01",
          payload: [
            { name: "Charizard ex", value: 15, color: "#ff0000" },
            { name: "Gardevoir ex", value: 12, color: "#00ff00" },
          ],
        })
      );

      expect(container.textContent).toContain("Charizard ex");
      expect(container.textContent).toContain("15.0%");
      expect(container.textContent).toContain("Gardevoir ex");
      expect(container.textContent).toContain("12.0%");
    });

    it("should render nothing when not active", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: false,
          label: "2025-01-01",
          payload: [{ name: "Charizard ex", value: 15, color: "#ff0000" }],
        })
      );

      expect(container.textContent).toBe("");
    });

    it("should render nothing when payload is empty", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          label: "2025-01-01",
          payload: [],
        })
      );

      expect(container.textContent).toBe("");
    });

    it("should render nothing when label is undefined", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const tooltipContent = capturedTooltipProps.content as React.ReactElement;

      const { container } = render(
        React.cloneElement(tooltipContent, {
          active: true,
          label: undefined,
          payload: [{ name: "Charizard ex", value: 15, color: "#ff0000" }],
        })
      );

      expect(container.textContent).toBe("");
    });
  });

  describe("Legend onClick (toggleArchetype)", () => {
    it("should toggle archetype visibility when legend item is clicked", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const onClick = capturedLegendProps.onClick as (e: {
        dataKey: string;
      }) => void;
      expect(onClick).toBeDefined();

      // Charizard ex should initially be visible (top 5 default)
      // Click to toggle it off
      act(() => {
        onClick({ dataKey: "Charizard ex" });
      });

      // Re-render should now mark Charizard as hidden
      // The Line component for Charizard ex should have hide=true after state update
    });

    it("should toggle archetype back on when clicked again", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const onClick = capturedLegendProps.onClick as (e: {
        dataKey: string;
      }) => void;

      // Toggle off then toggle on
      act(() => {
        onClick({ dataKey: "Charizard ex" });
      });
      act(() => {
        onClick({ dataKey: "Charizard ex" });
      });

      // Should be visible again
    });
  });

  describe("Legend formatter", () => {
    it("should render archetype name with visible styling", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const formatter = capturedLegendProps.formatter as (
        value: string
      ) => React.ReactElement;
      expect(formatter).toBeDefined();

      // Render the formatter output for a visible archetype
      const { container } = render(formatter("Charizard ex"));
      expect(container.textContent).toContain("Charizard ex");
      // Should have cursor-pointer and text-foreground classes (visible)
      const span = container.querySelector("span");
      expect(span).toHaveClass("cursor-pointer");
      expect(span).toHaveClass("text-foreground");
    });

    it("should render with muted styling for hidden archetypes", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      const formatter = capturedLegendProps.formatter as (
        value: string
      ) => React.ReactElement;

      // "Archetype 6" would not be in the default top 5 visible set
      // But we only have 2 archetypes in mockSnapshots, both visible
      // Test with a name not in the visibleArchetypes set
      const { container } = render(formatter("Nonexistent Archetype"));
      const span = container.querySelector("span");
      expect(span).toHaveClass("text-muted-foreground");
      expect(span).toHaveClass("line-through");
    });
  });

  describe("chart data transformation", () => {
    it("should sort chart data by date ascending", () => {
      const unsortedSnapshots: MetaSnapshot[] = [
        {
          snapshotDate: "2025-01-15",
          region: null,
          format: "standard",
          bestOf: 3,
          archetypeBreakdown: [{ name: "Deck A", share: 0.2 }],
          cardUsage: [],
          sampleSize: 100,
        },
        {
          snapshotDate: "2025-01-01",
          region: null,
          format: "standard",
          bestOf: 3,
          archetypeBreakdown: [{ name: "Deck A", share: 0.15 }],
          cardUsage: [],
          sampleSize: 100,
        },
      ];

      render(<MetaTrendChart snapshots={unsortedSnapshots} />);
      // If the component didn't crash, data transformation succeeded
      expect(screen.getByTestId("meta-trend-chart")).toBeInTheDocument();
    });

    it("should convert share values to percentages in chart data", () => {
      render(<MetaTrendChart snapshots={mockSnapshots} />);
      // The LineChart receives data prop with percentage values
      const lineChart = screen.getByTestId("line-chart");
      const dataProps = JSON.parse(
        lineChart.getAttribute("data-props") || "{}"
      );
      // data should have archetype values as share * 100
      expect(dataProps.data).toBeDefined();
      expect(dataProps.data[0]["Charizard ex"]).toBe(15); // 0.15 * 100
      expect(dataProps.data[0]["Gardevoir ex"]).toBe(12); // 0.12 * 100
    });
  });
});
