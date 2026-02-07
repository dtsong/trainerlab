import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ApiEvolutionSnapshot } from "@trainerlab/shared-types";
import { EvolutionChart } from "../EvolutionChart";

vi.mock("recharts", () => ({
  ComposedChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="composed-chart">{children}</div>
  ),
  Area: () => <div data-testid="area" />,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Legend: () => <div data-testid="legend" />,
}));

describe("EvolutionChart", () => {
  const mockSnapshots: ApiEvolutionSnapshot[] = [
    {
      id: "snapshot-1",
      archetype_id: "charizard-ex",
      created_at: "2024-06-01T00:00:00Z",
      meta_share: 0.15,
      top_cut_conversion: 0.25,
      sample_size: 100,
    },
    {
      id: "snapshot-2",
      archetype_id: "charizard-ex",
      created_at: "2024-06-15T00:00:00Z",
      meta_share: 0.18,
      top_cut_conversion: 0.3,
      sample_size: 150,
    },
  ];

  it("should render the chart when snapshots are provided", () => {
    render(<EvolutionChart snapshots={mockSnapshots} />);

    expect(screen.getByTestId("evolution-chart")).toBeInTheDocument();
    expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
    expect(screen.getByTestId("composed-chart")).toBeInTheDocument();
  });

  it("should render chart components", () => {
    render(<EvolutionChart snapshots={mockSnapshots} />);

    expect(screen.getByTestId("area")).toBeInTheDocument();
    expect(screen.getByTestId("line")).toBeInTheDocument();
    expect(screen.getAllByTestId("y-axis")).toHaveLength(2);
    expect(screen.getByTestId("x-axis")).toBeInTheDocument();
  });

  it("should show empty state when no snapshots", () => {
    render(<EvolutionChart snapshots={[]} />);

    expect(screen.getByText("No chart data available")).toBeInTheDocument();
  });

  it("should show empty state when all snapshots lack created_at", () => {
    const invalidSnapshots: ApiEvolutionSnapshot[] = [
      {
        id: "snapshot-1",
        archetype_id: "charizard-ex",
        created_at: null,
        meta_share: 0.15,
        top_cut_conversion: 0.25,
        sample_size: 100,
      },
    ];

    render(<EvolutionChart snapshots={invalidSnapshots} />);

    expect(screen.getByText("No chart data available")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    render(
      <EvolutionChart snapshots={mockSnapshots} className="custom-class" />
    );

    expect(screen.getByTestId("evolution-chart")).toHaveClass("custom-class");
  });

  it("should filter out snapshots without created_at", () => {
    const mixedSnapshots: ApiEvolutionSnapshot[] = [
      {
        id: "valid",
        archetype_id: "charizard-ex",
        created_at: "2024-06-01T00:00:00Z",
        meta_share: 0.15,
        top_cut_conversion: 0.25,
        sample_size: 100,
      },
      {
        id: "invalid",
        archetype_id: "charizard-ex",
        created_at: null,
        meta_share: 0.2,
        top_cut_conversion: 0.3,
        sample_size: 100,
      },
    ];

    render(<EvolutionChart snapshots={mixedSnapshots} />);

    expect(screen.getByTestId("evolution-chart")).toBeInTheDocument();
    expect(
      screen.queryByText("No chart data available")
    ).not.toBeInTheDocument();
  });

  it("should handle snapshots with null meta_share", () => {
    const snapshotsWithNullShare: ApiEvolutionSnapshot[] = [
      {
        id: "snapshot-1",
        archetype_id: "charizard-ex",
        created_at: "2024-06-01T00:00:00Z",
        meta_share: null,
        top_cut_conversion: 0.25,
        sample_size: 100,
      },
    ];

    render(<EvolutionChart snapshots={snapshotsWithNullShare} />);

    expect(screen.getByTestId("evolution-chart")).toBeInTheDocument();
  });

  it("should handle snapshots with null top_cut_conversion", () => {
    const snapshotsWithNullConversion: ApiEvolutionSnapshot[] = [
      {
        id: "snapshot-1",
        archetype_id: "charizard-ex",
        created_at: "2024-06-01T00:00:00Z",
        meta_share: 0.15,
        top_cut_conversion: null,
        sample_size: 100,
      },
    ];

    render(<EvolutionChart snapshots={snapshotsWithNullConversion} />);

    expect(screen.getByTestId("evolution-chart")).toBeInTheDocument();
  });

  it("should sort snapshots by date ascending", () => {
    const unsortedSnapshots: ApiEvolutionSnapshot[] = [
      {
        id: "later",
        archetype_id: "charizard-ex",
        created_at: "2024-06-15T00:00:00Z",
        meta_share: 0.18,
        top_cut_conversion: 0.3,
        sample_size: 100,
      },
      {
        id: "earlier",
        archetype_id: "charizard-ex",
        created_at: "2024-06-01T00:00:00Z",
        meta_share: 0.15,
        top_cut_conversion: 0.25,
        sample_size: 100,
      },
    ];

    render(<EvolutionChart snapshots={unsortedSnapshots} />);

    expect(screen.getByTestId("evolution-chart")).toBeInTheDocument();
  });

  it("should include legend component", () => {
    render(<EvolutionChart snapshots={mockSnapshots} />);

    expect(screen.getByTestId("legend")).toBeInTheDocument();
  });

  it("should include tooltip component", () => {
    render(<EvolutionChart snapshots={mockSnapshots} />);

    expect(screen.getByTestId("tooltip")).toBeInTheDocument();
  });
});
