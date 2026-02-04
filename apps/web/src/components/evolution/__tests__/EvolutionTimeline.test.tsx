import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EvolutionTimeline } from "../EvolutionTimeline";
import { safeFormatDate } from "@/lib/date-utils";
import type { ApiEvolutionSnapshot } from "@trainerlab/shared-types";

const mockSnapshots: ApiEvolutionSnapshot[] = [
  {
    id: "snap-1",
    archetype: "Charizard ex",
    tournament_id: "t-1",
    meta_share: 0.15,
    top_cut_conversion: 0.25,
    best_placement: 1,
    deck_count: 42,
    meta_context: "Post-rotation meta settling",
    adaptations: [
      {
        id: "adapt-1",
        type: "tech",
        description: "Added Dusknoir tech",
      },
      {
        id: "adapt-2",
        type: "consistency",
        description: "Increased Rare Candy count",
      },
    ],
    created_at: "2024-06-01T00:00:00Z",
  },
  {
    id: "snap-2",
    archetype: "Charizard ex",
    tournament_id: "t-2",
    meta_share: 0.12,
    top_cut_conversion: 0.2,
    best_placement: 4,
    deck_count: 35,
    meta_context: null,
    adaptations: [],
    created_at: "2024-05-15T00:00:00Z",
  },
];

describe("EvolutionTimeline", () => {
  it("should render empty state when no snapshots", () => {
    render(<EvolutionTimeline snapshots={[]} />);

    expect(screen.getByText("No evolution data available")).toBeInTheDocument();
  });

  it("should render snapshot dates", () => {
    render(<EvolutionTimeline snapshots={mockSnapshots} />);

    const expectedDate1 = safeFormatDate(
      "2024-06-01T00:00:00Z",
      "MMM d, yyyy",
      "Unknown date"
    );
    const expectedDate2 = safeFormatDate(
      "2024-05-15T00:00:00Z",
      "MMM d, yyyy",
      "Unknown date"
    );
    expect(screen.getByText(expectedDate1)).toBeInTheDocument();
    expect(screen.getByText(expectedDate2)).toBeInTheDocument();
  });

  it("should display meta share percentages", () => {
    render(<EvolutionTimeline snapshots={mockSnapshots} />);

    expect(screen.getByText("15.0%")).toBeInTheDocument();
    expect(screen.getByText("12.0%")).toBeInTheDocument();
  });

  it("should display deck count for each snapshot", () => {
    render(<EvolutionTimeline snapshots={mockSnapshots} />);

    expect(screen.getByText("42 decks sampled")).toBeInTheDocument();
    expect(screen.getByText("35 decks sampled")).toBeInTheDocument();
  });

  it("should display best placement badge for top 8", () => {
    render(<EvolutionTimeline snapshots={mockSnapshots} />);

    expect(screen.getByText(/#1/)).toBeInTheDocument();
    expect(screen.getByText(/#4/)).toBeInTheDocument();
  });

  it("should not show placement badge when best_placement > 8", () => {
    const snapshotOutsideTop8: ApiEvolutionSnapshot[] = [
      {
        ...mockSnapshots[0],
        best_placement: 12,
      },
    ];

    render(<EvolutionTimeline snapshots={snapshotOutsideTop8} />);

    expect(screen.queryByText(/#12/)).not.toBeInTheDocument();
  });

  it("should not show placement badge when best_placement is null", () => {
    const snapshotNoPlacement: ApiEvolutionSnapshot[] = [
      {
        ...mockSnapshots[0],
        best_placement: null,
      },
    ];

    render(<EvolutionTimeline snapshots={snapshotNoPlacement} />);

    expect(screen.queryByText(/#/)).not.toBeInTheDocument();
  });

  it("should display meta context when available", () => {
    render(<EvolutionTimeline snapshots={mockSnapshots} />);

    expect(screen.getByText("Post-rotation meta settling")).toBeInTheDocument();
  });

  it("should render adaptation badges", () => {
    render(<EvolutionTimeline snapshots={mockSnapshots} />);

    expect(screen.getByText("tech")).toBeInTheDocument();
    expect(screen.getByText("consistency")).toBeInTheDocument();
  });

  it("should truncate adaptations at 3 and show overflow count", () => {
    const manyAdaptations: ApiEvolutionSnapshot[] = [
      {
        ...mockSnapshots[0],
        adaptations: [
          { id: "a1", type: "tech", description: "Tech 1" },
          { id: "a2", type: "consistency", description: "Con 1" },
          { id: "a3", type: "engine", description: "Eng 1" },
          { id: "a4", type: "removal", description: "Rem 1" },
          { id: "a5", type: "tech", description: "Tech 2" },
        ],
      },
    ];

    render(<EvolutionTimeline snapshots={manyAdaptations} />);

    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("should show dash when meta_share is null", () => {
    const nullShare: ApiEvolutionSnapshot[] = [
      {
        ...mockSnapshots[0],
        meta_share: null,
      },
    ];

    render(<EvolutionTimeline snapshots={nullShare} />);

    // The component renders the em dash character
    const metaShareEl = screen.getByText("\u2014");
    expect(metaShareEl).toBeInTheDocument();
  });

  it("should display 'Unknown date' for null created_at", () => {
    const nullDate: ApiEvolutionSnapshot[] = [
      {
        ...mockSnapshots[0],
        created_at: null,
      },
    ];

    render(<EvolutionTimeline snapshots={nullDate} />);

    expect(screen.getByText("Unknown date")).toBeInTheDocument();
  });

  it("should apply custom className", () => {
    const { container } = render(
      <EvolutionTimeline snapshots={mockSnapshots} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });

  it("should call onSnapshotClick when a snapshot is clicked", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(
      <EvolutionTimeline
        snapshots={mockSnapshots}
        onSnapshotClick={handleClick}
      />
    );

    await user.click(screen.getByText("15.0%"));

    expect(handleClick).toHaveBeenCalledWith(mockSnapshots[0]);
  });

  it("should add cursor-pointer class when onSnapshotClick is provided", () => {
    const { container } = render(
      <EvolutionTimeline snapshots={mockSnapshots} onSnapshotClick={vi.fn()} />
    );

    const clickableElements = container.querySelectorAll(".cursor-pointer");
    expect(clickableElements.length).toBeGreaterThan(0);
  });

  it("should not add cursor-pointer class without onSnapshotClick", () => {
    const { container } = render(
      <EvolutionTimeline snapshots={mockSnapshots} />
    );

    const clickableElements = container.querySelectorAll(".cursor-pointer");
    expect(clickableElements.length).toBe(0);
  });

  it("should render the timeline line", () => {
    const { container } = render(
      <EvolutionTimeline snapshots={mockSnapshots} />
    );

    const timelineLine = container.querySelector(".bg-border");
    expect(timelineLine).toBeInTheDocument();
  });

  it("should render chevron icon when onSnapshotClick is provided", () => {
    render(
      <EvolutionTimeline snapshots={mockSnapshots} onSnapshotClick={vi.fn()} />
    );

    // ChevronRight icons are rendered but hidden on mobile
    const { container } = render(
      <EvolutionTimeline snapshots={mockSnapshots} onSnapshotClick={vi.fn()} />
    );

    const chevrons = container.querySelectorAll(".sm\\:block");
    expect(chevrons.length).toBeGreaterThan(0);
  });
});
