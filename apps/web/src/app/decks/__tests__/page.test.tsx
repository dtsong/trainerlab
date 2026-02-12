import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import DecksPage from "../page";

const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();
const mockUseDecks = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
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

vi.mock("@/hooks/useDecks", () => ({
  useDecks: () => mockUseDecks(),
}));

vi.mock("@/components/deck", () => ({
  DeckCard: ({ deck }: { deck: { name: string; format: string } }) => (
    <div data-testid="deck-card">
      {deck.name} ({deck.format})
    </div>
  ),
}));

vi.mock("@/components/ui/select", async () => {
  const ReactLib = await import("react");
  const SelectContext = ReactLib.createContext<
    ((value: string) => void) | null
  >(null);

  return {
    Select: ({
      children,
      onValueChange,
    }: {
      children: React.ReactNode;
      onValueChange?: (value: string) => void;
    }) => (
      <SelectContext.Provider value={onValueChange ?? null}>
        <div>{children}</div>
      </SelectContext.Provider>
    ),
    SelectContent: ({ children }: { children: React.ReactNode }) => (
      <div>{children}</div>
    ),
    SelectItem: ({
      children,
      value,
    }: {
      children: React.ReactNode;
      value: string;
    }) => {
      const onValueChange = ReactLib.useContext(SelectContext);
      return <button onClick={() => onValueChange?.(value)}>{children}</button>;
    },
    SelectTrigger: ({ children }: { children: React.ReactNode }) => (
      <div>{children}</div>
    ),
    SelectValue: () => <span />,
  };
});

describe("DecksPage URL behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();

    mockUseDecks.mockReturnValue({
      decks: [
        {
          id: "1",
          name: "Alpha Deck",
          description: "",
          format: "expanded",
          cards: [],
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-03T00:00:00.000Z",
        },
        {
          id: "2",
          name: "Beta Deck",
          description: "",
          format: "standard",
          cards: [],
          createdAt: "2026-01-02T00:00:00.000Z",
          updatedAt: "2026-01-04T00:00:00.000Z",
        },
      ],
      isLoading: false,
      loadError: null,
    });
  });

  it("hydrates filter format from URL", () => {
    mockSearchParams = new URLSearchParams("format=expanded");

    render(<DecksPage />);

    expect(screen.getByText("Alpha Deck (expanded)")).toBeInTheDocument();
    expect(screen.queryByText("Beta Deck (standard)")).not.toBeInTheDocument();
  });

  it("uses replace when sort changes", () => {
    mockSearchParams = new URLSearchParams("format=expanded");

    render(<DecksPage />);

    fireEvent.click(screen.getByText("Name"));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("sort=name"),
      { scroll: false }
    );
    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("format=expanded"),
      { scroll: false }
    );
  });
});
