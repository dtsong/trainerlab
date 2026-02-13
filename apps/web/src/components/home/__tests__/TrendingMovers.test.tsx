import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { TrendingMovers } from "../TrendingMovers";

const mockUseHomeMetaData = vi.fn();

vi.mock("@/hooks/useMeta", () => ({
  useHomeMetaData: () => mockUseHomeMetaData(),
}));

describe("TrendingMovers", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseHomeMetaData.mockReturnValue({
      isLoading: false,
      globalMeta: {
        archetype_breakdown: [
          { name: "Dragapult ex", share: 0.1 },
          { name: "Charizard ex", share: 0.08 },
        ],
      },
      history: {
        snapshots: [
          {
            archetype_breakdown: [
              { name: "Dragapult ex", share: 0.04 },
              { name: "Charizard ex", share: 0.07 },
            ],
          },
        ],
      },
    });
  });

  it("renders movers when data is available", () => {
    render(<TrendingMovers />);

    expect(screen.getByText("TRENDING MOVERS")).toBeInTheDocument();
    expect(screen.getByText("Dragapult ex")).toBeInTheDocument();
  });

  it("renders nothing while loading", () => {
    mockUseHomeMetaData.mockReturnValue({ isLoading: true });
    const { container } = render(<TrendingMovers />);
    expect(container.textContent).toBe("");
  });
});
