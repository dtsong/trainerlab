import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import EvolutionPage from "../page";

const mockPush = vi.fn();
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();
const mockUseEvolutionArticles = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/hooks/useEvolution", () => ({
  useEvolutionArticles: (...args: unknown[]) =>
    mockUseEvolutionArticles(...args),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("EvolutionPage URL behavior", () => {
  const article = {
    id: "a1",
    slug: "charizard-evo",
    archetype_id: "charizard",
    title: "Charizard Evolution",
    excerpt: "Meta shifts",
    is_premium: false,
    published_at: "2026-01-10T00:00:00Z",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();

    mockUseEvolutionArticles.mockReturnValue({
      data: Array.from({ length: 12 }).map((_, i) => ({
        ...article,
        id: `${article.id}-${i}`,
        slug: `${article.slug}-${i}`,
      })),
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it("hydrates page from URL and passes correct offset", () => {
    mockSearchParams = new URLSearchParams("page=3");

    render(<EvolutionPage />);

    expect(mockUseEvolutionArticles).toHaveBeenCalledWith({
      limit: 12,
      offset: 24,
    });
  });

  it("uses push when moving to next page", () => {
    render(<EvolutionPage />);

    fireEvent.click(screen.getByText("Next"));

    expect(mockPush).toHaveBeenCalledWith("/evolution?page=2", {
      scroll: false,
    });
  });

  it("omits default page param when navigating back to page 1", () => {
    mockSearchParams = new URLSearchParams("page=2");

    render(<EvolutionPage />);

    fireEvent.click(screen.getByText("Previous"));

    expect(mockPush).toHaveBeenCalledWith("/evolution", { scroll: false });
  });
});
