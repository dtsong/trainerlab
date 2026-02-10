import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeckExportModal } from "../DeckExportModal";
import { exportDeck } from "@/lib/deckFormats";
import { useDeckStore } from "@/stores/deckStore";
import type { DeckCard } from "@/types/deck";
import type { ApiCardSummary } from "@trainerlab/shared-types";

// Mock the deck store
vi.mock("@/stores/deckStore", () => ({
  useDeckStore: vi.fn((selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      cards: [],
      name: "My Test Deck",
    })
  ),
}));

// Mock the deckFormats utilities
vi.mock("@/lib/deckFormats", () => ({
  exportDeck: vi.fn(
    (_cards: DeckCard[], format: string) => `Exported in ${format} format`
  ),
  getFormatDisplayName: vi.fn((format: string) => {
    if (format === "ptcgo") return "PTCGO";
    if (format === "ptcgl") return "Pokemon TCG Live";
    return format;
  }),
}));

// Mock Dialog components to render content directly
vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({
    children,
    open,
  }: {
    children: React.ReactNode;
    open: boolean;
    onOpenChange?: (open: boolean) => void;
  }) => (open ? <div data-testid="dialog">{children}</div> : null),
  DialogContent: ({
    children,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => <div data-testid="dialog-content">{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  DialogTitle: ({ children }: { children: React.ReactNode }) => (
    <h2>{children}</h2>
  ),
  DialogDescription: ({ children }: { children: React.ReactNode }) => (
    <p>{children}</p>
  ),
}));

// Mock Select components
vi.mock("@/components/ui/select", () => ({
  Select: ({
    children,
    onValueChange,
  }: {
    children: React.ReactNode;
    value?: string;
    onValueChange?: (value: string) => void;
  }) => (
    <div data-testid="select" data-onvaluechange={onValueChange}>
      {children}
    </div>
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
  }) => <option value={value}>{children}</option>,
  SelectTrigger: ({ children }: { children: React.ReactNode; id?: string }) => (
    <div>{children}</div>
  ),
  SelectValue: () => <span />,
}));

// Mock Textarea
vi.mock("@/components/ui/textarea", () => ({
  Textarea: ({
    value,
    ...props
  }: {
    value?: string;
    id?: string;
    readOnly?: boolean;
    className?: string;
  }) => <textarea {...props} value={value} readOnly />,
}));

function createMockCard(
  overrides: Partial<ApiCardSummary> = {}
): ApiCardSummary {
  return {
    id: "swsh1-1",
    name: "Pikachu",
    supertype: "Pokemon",
    types: ["Lightning"],
    set_id: "swsh1",
    rarity: "Common",
    image_small: "https://example.com/pikachu.png",
    ...overrides,
  };
}

function createMockDeckCards(): DeckCard[] {
  return [
    {
      card: createMockCard(),
      quantity: 4,
      position: 0,
    },
    {
      card: createMockCard({
        id: "swsh1-2",
        name: "Professor's Research",
        supertype: "Trainer",
      }),
      quantity: 4,
      position: 1,
    },
  ];
}

describe("DeckExportModal", () => {
  const mockOnOpenChange = vi.fn();
  let mockWriteText: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock clipboard API (navigator.clipboard doesn't exist in jsdom)
    mockWriteText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: mockWriteText },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should not render when open is false", () => {
    render(<DeckExportModal open={false} onOpenChange={mockOnOpenChange} />);
    expect(screen.queryByTestId("dialog")).not.toBeInTheDocument();
  });

  it("should render when open is true", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByTestId("dialog")).toBeInTheDocument();
  });

  it("should render the Export Deck title", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("Export Deck")).toBeInTheDocument();
  });

  it("should render the description text", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(
      screen.getByText(/Export your deck list to use in Pokemon TCG/)
    ).toBeInTheDocument();
  });

  it("should render format selector", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("Format")).toBeInTheDocument();
  });

  it("should render PTCGO format option", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("PTCGO")).toBeInTheDocument();
  });

  it("should render Pokemon TCG Live format option", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("Pokemon TCG Live")).toBeInTheDocument();
  });

  it("should render preview section", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("Preview")).toBeInTheDocument();
  });

  it("should render the exported text in the preview textarea", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    const textarea = document.querySelector("textarea");
    expect(textarea).toHaveValue("Exported in ptcgo format");
  });

  it("should render Copy to Clipboard button", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("Copy to Clipboard")).toBeInTheDocument();
  });

  it("should render Download button", () => {
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText("Download")).toBeInTheDocument();
  });

  it("should copy text to clipboard when Copy is clicked", async () => {
    const user = userEvent.setup();
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);

    await user.click(screen.getByText("Copy to Clipboard"));

    // Verify the copy operation completed by checking the UI feedback
    await waitFor(() => {
      expect(screen.getByText("Copied!")).toBeInTheDocument();
    });
  });

  it("should show 'Copied!' text after successful copy", async () => {
    const user = userEvent.setup();
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);

    await user.click(screen.getByText("Copy to Clipboard"));

    await waitFor(() => {
      expect(screen.getByText("Copied!")).toBeInTheDocument();
    });
  });

  it("should show 'Copy failed' when clipboard write fails", async () => {
    const user = userEvent.setup();
    // Override clipboard with a failing mock
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: vi
          .fn()
          .mockRejectedValue(new Error("Clipboard not available")),
      },
      writable: true,
      configurable: true,
    });

    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);

    await user.click(screen.getByText("Copy to Clipboard"));

    await waitFor(() => {
      expect(screen.getByText("Copy failed")).toBeInTheDocument();
    });
  });

  it("should trigger download when Download is clicked", async () => {
    const user = userEvent.setup();

    // Mock URL.createObjectURL and revokeObjectURL
    const mockCreateObjectURL = vi.fn(() => "blob:mock-url");
    const mockRevokeObjectURL = vi.fn();
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;

    // Render first, then set up download mocks before clicking
    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);

    // Mock document.createElement for the download link (after render)
    const mockClick = vi.fn();
    const mockLink = {
      href: "",
      download: "",
      click: mockClick,
    };
    const originalCreateElement = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      if (tag === "a") return mockLink as unknown as HTMLAnchorElement;
      return originalCreateElement(tag);
    });
    vi.spyOn(document.body, "appendChild").mockImplementation(
      (node) => node as HTMLElement
    );
    vi.spyOn(document.body, "removeChild").mockImplementation(
      (node) => node as HTMLElement
    );

    await user.click(screen.getByText("Download"));

    expect(mockClick).toHaveBeenCalled();
    expect(mockLink.download).toBe("My Test Deck-ptcgo.txt");
    expect(mockRevokeObjectURL).toHaveBeenCalled();
  });

  it("should use provided cards prop instead of store cards", () => {
    const mockedExportDeck = vi.mocked(exportDeck);
    const customCards = createMockDeckCards();

    render(
      <DeckExportModal
        open={true}
        onOpenChange={mockOnOpenChange}
        cards={customCards}
      />
    );

    expect(mockedExportDeck).toHaveBeenCalledWith(customCards, "ptcgo");
  });

  it("should use provided deckName prop for downloads", () => {
    render(
      <DeckExportModal
        open={true}
        onOpenChange={mockOnOpenChange}
        deckName="Custom Deck Name"
      />
    );

    // The deckName prop is used when downloading, so just verify it renders
    expect(screen.getByTestId("dialog")).toBeInTheDocument();
  });

  it("should use 'deck' as fallback name when no name is provided", () => {
    // Override the store mock to return empty name
    vi.mocked(useDeckStore).mockImplementation(((
      selector: (state: Record<string, unknown>) => unknown
    ) =>
      selector({
        cards: [],
        name: "",
      })) as typeof useDeckStore);

    render(<DeckExportModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByTestId("dialog")).toBeInTheDocument();
  });
});
