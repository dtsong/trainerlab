import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { JPAnalysisTab } from "../JPAnalysisTab";

// Mock the API module
vi.mock("@/lib/api", () => ({
  japanApi: {
    getContent: vi.fn().mockResolvedValue({ items: [] }),
  },
}));

// Mock sub-components to keep tests focused
vi.mock("@/components/japan", () => ({
  CardInnovationTracker: () => (
    <div data-testid="card-innovation-tracker">CardInnovationTracker</div>
  ),
  NewArchetypeWatch: () => (
    <div data-testid="new-archetype-watch">NewArchetypeWatch</div>
  ),
}));

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("JPAnalysisTab", () => {
  it("should render the era context banner when era is provided", () => {
    renderWithQueryClient(<JPAnalysisTab era="post-nihil-zero" />);

    const banner = screen.getByTestId("era-context-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent("post-nihil-zero");
  });

  it("should not render the era context banner when era is undefined", () => {
    renderWithQueryClient(<JPAnalysisTab />);

    expect(screen.queryByTestId("era-context-banner")).not.toBeInTheDocument();
  });

  it("should render section headings", () => {
    renderWithQueryClient(<JPAnalysisTab era="post-nihil-zero" />);

    expect(screen.getByText("Translated Tier Lists")).toBeInTheDocument();
    expect(screen.getByText("Translated Articles")).toBeInTheDocument();
  });

  it("should render sub-components", () => {
    renderWithQueryClient(<JPAnalysisTab era="post-nihil-zero" />);

    expect(screen.getByTestId("new-archetype-watch")).toBeInTheDocument();
    expect(screen.getByTestId("card-innovation-tracker")).toBeInTheDocument();
  });
});
