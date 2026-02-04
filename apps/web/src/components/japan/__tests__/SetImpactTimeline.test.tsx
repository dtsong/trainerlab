import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SetImpactTimeline } from "../SetImpactTimeline";
import * as api from "@/lib/api";
import type { ApiJPSetImpact } from "@trainerlab/shared-types";

vi.mock("@/lib/api", () => ({
  japanApi: {
    listSetImpacts: vi.fn(),
  },
}));

const mockJapanApi = vi.mocked(api.japanApi);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

const mockImpact: ApiJPSetImpact = {
  id: "impact-1",
  set_code: "SV6",
  set_name: "Twilight Masquerade",
  jp_release_date: "2024-04-26T00:00:00Z",
  en_release_date: "2024-05-24T00:00:00Z",
  key_innovations: ["Dragapult ex", "Teal Mask Ogerpon ex"],
  new_archetypes: ["Raging Bolt ex"],
  jp_meta_before: [
    { archetype: "Charizard ex", share: 0.15 },
    { archetype: "Lugia VSTAR", share: 0.12 },
  ],
  jp_meta_after: [
    { archetype: "Dragapult ex", share: 0.18 },
    { archetype: "Charizard ex", share: 0.1 },
    { archetype: "Raging Bolt ex", share: 0.08 },
  ],
  analysis: "Dragapult ex reshuffled the meta significantly.",
};

describe("SetImpactTimeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockJapanApi.listSetImpacts.mockReturnValue(new Promise(() => {}));

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(screen.getByText("Set Impact History")).toBeInTheDocument();
  });

  it("should render title and description when data loads", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    // Wait for the description which only appears after data loads
    expect(
      await screen.findByText(/How each set changed the JP meta/)
    ).toBeInTheDocument();
    expect(screen.getByText("Set Impact History")).toBeInTheDocument();
  });

  it("should display empty state when no impacts", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("No set impacts tracked yet")
    ).toBeInTheDocument();
  });

  it("should render set name and code", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(await screen.findByText("Twilight Masquerade")).toBeInTheDocument();
    expect(screen.getByText("SV6")).toBeInTheDocument();
  });

  it("should display formatted release dates", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    // date-fns format uses local timezone, so midnight UTC dates may
    // render as the previous day depending on the runner's timezone
    expect(await screen.findByText(/Apr 2[56], 2024/)).toBeInTheDocument();
    expect(screen.getByText(/May 2[34], 2024/)).toBeInTheDocument();
  });

  it("should display TBD when EN release date is null", async () => {
    const noEnDate: ApiJPSetImpact = {
      ...mockImpact,
      en_release_date: null,
    };

    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [noEnDate],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(await screen.findByText("TBD")).toBeInTheDocument();
  });

  it("should render key innovations badges", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(await screen.findByText("Key Innovations")).toBeInTheDocument();
    expect(screen.getByText("Dragapult ex")).toBeInTheDocument();
    expect(screen.getByText("Teal Mask Ogerpon ex")).toBeInTheDocument();
  });

  it("should render new archetypes badges", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(await screen.findByText("New Archetypes")).toBeInTheDocument();
    expect(screen.getByText("Raging Bolt ex")).toBeInTheDocument();
  });

  it("should not render key innovations when empty", async () => {
    const noInnovations: ApiJPSetImpact = {
      ...mockImpact,
      key_innovations: null,
    };

    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [noInnovations],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    await screen.findByText("Twilight Masquerade");
    expect(screen.queryByText("Key Innovations")).not.toBeInTheDocument();
  });

  it("should not render new archetypes when empty", async () => {
    const noArchetypes: ApiJPSetImpact = {
      ...mockImpact,
      new_archetypes: null,
    };

    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [noArchetypes],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    await screen.findByText("Twilight Masquerade");
    expect(screen.queryByText("New Archetypes")).not.toBeInTheDocument();
  });

  it("should expand to show meta comparison and analysis on click", async () => {
    const user = userEvent.setup();

    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    await screen.findByText("Twilight Masquerade");

    // Analysis should not be visible initially
    expect(screen.queryByText("Analysis")).not.toBeInTheDocument();

    // Click the expand button
    const expandButton = screen.getByRole("button");
    await user.click(expandButton);

    // Analysis and meta comparison should now be visible
    expect(screen.getByText("Analysis")).toBeInTheDocument();
    expect(
      screen.getByText("Dragapult ex reshuffled the meta significantly.")
    ).toBeInTheDocument();
    expect(screen.getByText(/Meta Shift/)).toBeInTheDocument();
  });

  it("should collapse expanded section on second click", async () => {
    const user = userEvent.setup();

    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact],
      total: 1,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    await screen.findByText("Twilight Masquerade");

    const expandButton = screen.getByRole("button");
    await user.click(expandButton);
    expect(screen.getByText("Analysis")).toBeInTheDocument();

    await user.click(expandButton);
    expect(screen.queryByText("Analysis")).not.toBeInTheDocument();
  });

  it("should show error state when data fails to load", async () => {
    mockJapanApi.listSetImpacts.mockRejectedValue(new Error("Network error"));

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Failed to load set impacts")
    ).toBeInTheDocument();
  });

  it("should pass custom limit to API", () => {
    mockJapanApi.listSetImpacts.mockReturnValue(new Promise(() => {}));

    render(<SetImpactTimeline limit={5} />, { wrapper: createWrapper() });

    expect(mockJapanApi.listSetImpacts).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 5 })
    );
  });

  it("should apply custom className", async () => {
    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [],
      total: 0,
    });

    const { container } = render(
      <SetImpactTimeline className="custom-class" />,
      { wrapper: createWrapper() }
    );

    await screen.findByText("Set Impact History");
    const wrapper = container.querySelector(".custom-class");
    expect(wrapper).toBeInTheDocument();
  });

  it("should render multiple set impact cards", async () => {
    const secondImpact: ApiJPSetImpact = {
      ...mockImpact,
      id: "impact-2",
      set_code: "SV5",
      set_name: "Temporal Forces",
      jp_release_date: "2024-01-26T00:00:00Z",
    };

    mockJapanApi.listSetImpacts.mockResolvedValue({
      items: [mockImpact, secondImpact],
      total: 2,
    });

    render(<SetImpactTimeline />, { wrapper: createWrapper() });

    expect(await screen.findByText("Twilight Masquerade")).toBeInTheDocument();
    expect(screen.getByText("Temporal Forces")).toBeInTheDocument();
  });
});
