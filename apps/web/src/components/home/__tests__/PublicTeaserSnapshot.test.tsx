import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { PublicTeaserSnapshot } from "../PublicTeaserSnapshot";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/components/ui/section-label", () => ({
  SectionLabel: ({ label }: { label: string }) => <span>{label}</span>,
}));

const mockUseHomeTeaser = vi.fn();

vi.mock("@/hooks", () => ({
  useHomeTeaser: () => mockUseHomeTeaser(),
}));

describe("PublicTeaserSnapshot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders delayed teaser rows with sample size", () => {
    mockUseHomeTeaser.mockReturnValue({
      data: {
        snapshot_date: "2026-01-20",
        delay_days: 14,
        sample_size: 1234,
        top_archetypes: [
          {
            name: "Charizard ex",
            global_share: 0.155,
            jp_share: 0.18,
            divergence_pp: 2.5,
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    render(<PublicTeaserSnapshot />);

    expect(screen.getByText("Delayed by 14 days")).toBeInTheDocument();
    expect(screen.getByText("Charizard ex")).toBeInTheDocument();
    expect(screen.getByText("15.5%")).toBeInTheDocument();
    expect(screen.getByText("JP 18.0%")).toBeInTheDocument();
    expect(
      screen.getByText(/Sample size: 1,234 decklists\./)
    ).toBeInTheDocument();
  });

  it("renders no-data state when teaser data is empty", () => {
    mockUseHomeTeaser.mockReturnValue({
      data: {
        snapshot_date: null,
        delay_days: 14,
        sample_size: 0,
        top_archetypes: [],
      },
      isLoading: false,
      isError: false,
    });

    render(<PublicTeaserSnapshot />);

    expect(
      screen.getByText("Not enough delayed sample data yet.")
    ).toBeInTheDocument();
  });
});
