import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import GrassrootsPage from "../page";

const mockPush = vi.fn();
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();
const mockTournamentList = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/components/tournaments", () => ({
  TournamentList: (props: Record<string, unknown>) => {
    mockTournamentList(props);
    return <div>Tournament List</div>;
  },
}));

describe("GrassrootsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams(
      "region=EU&format=standard&best_of=1"
    );
  });

  it("uses grassroots-only data contract and renders navigation", () => {
    render(<GrassrootsPage />);

    expect(mockTournamentList).toHaveBeenCalledWith(
      expect.objectContaining({
        apiParams: expect.objectContaining({
          tier: "grassroots",
          region: "EU",
          format: "standard",
          best_of: 1,
        }),
      })
    );

    const backLink = screen.getByRole("link", {
      name: "Back to Official Tournaments",
    });
    expect(backLink).toHaveAttribute("href", "/tournaments");
  });
});
