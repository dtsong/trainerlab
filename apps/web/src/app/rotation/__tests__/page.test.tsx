import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import RotationPage from "../page";

import type {
  ApiRotationImpact,
  ApiRotationImpactList,
  ApiUpcomingFormat,
} from "@trainerlab/shared-types";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock the hooks
const mockUseCurrentFormat = vi.fn();
const mockUseUpcomingFormat = vi.fn();
const mockUseRotationImpacts = vi.fn();

vi.mock("@/hooks/useFormat", () => ({
  useCurrentFormat: () => mockUseCurrentFormat(),
  useUpcomingFormat: () => mockUseUpcomingFormat(),
  useRotationImpacts: (transition: string) =>
    mockUseRotationImpacts(transition),
}));

// Mock rotation components
vi.mock("@/components/rotation", () => ({
  ArchetypeSurvival: ({ impact }: { impact: ApiRotationImpact }) => (
    <div data-testid={`archetype-${impact.archetype_id}`}>
      {impact.archetype_name} - {impact.survival_rating}
    </div>
  ),
  CardRotationList: ({ impacts }: { impacts: ApiRotationImpact[] }) => (
    <div data-testid="card-rotation-list">{impacts.length} impacts</div>
  ),
}));

// Mock shadcn/ui Tabs to work without Radix
vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({
    children,
    value,
    onValueChange,
  }: {
    children: React.ReactNode;
    value: string;
    onValueChange: (v: string) => void;
  }) => (
    <div data-testid="tabs" data-value={value}>
      {children}
    </div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({
    children,
    value,
  }: {
    children: React.ReactNode;
    value: string;
  }) => <button data-testid={`tab-${value}`}>{children}</button>,
  TabsContent: ({
    children,
    value,
  }: {
    children: React.ReactNode;
    value: string;
  }) => <div data-testid={`tab-content-${value}`}>{children}</div>,
}));

describe("RotationPage", () => {
  const mockCurrentFormat = {
    id: "f-current",
    name: "F-2025",
    display_name: "Regulation F",
    legal_sets: ["sv1"],
    is_current: true,
    is_upcoming: false,
  };

  const mockUpcomingFormat: ApiUpcomingFormat = {
    format: {
      id: "f-next",
      name: "G-2026",
      display_name: "Regulation G",
      legal_sets: ["sv1", "sv2"],
      is_current: false,
      is_upcoming: true,
    },
    days_until_rotation: 30,
    rotation_date: "2026-04-01T00:00:00Z",
  };

  const mockImpacts: ApiRotationImpactList = {
    format_transition: "F-2025-to-G-2026",
    total_archetypes: 3,
    impacts: [
      {
        id: "impact-1",
        format_transition: "F-2025-to-G-2026",
        archetype_id: "arch-1",
        archetype_name: "Charizard ex",
        survival_rating: "adapts",
        rotating_cards: [{ card_name: "Arven", count: 2 }],
      },
      {
        id: "impact-2",
        format_transition: "F-2025-to-G-2026",
        archetype_id: "arch-2",
        archetype_name: "Lugia VSTAR",
        survival_rating: "dies",
        rotating_cards: [{ card_name: "Archeops", count: 2 }],
      },
      {
        id: "impact-3",
        format_transition: "F-2025-to-G-2026",
        archetype_id: "arch-3",
        archetype_name: "Gardevoir ex",
        survival_rating: "thrives",
        rotating_cards: [],
      },
    ],
  };

  const mockRefetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  function setupLoadedState() {
    mockUseCurrentFormat.mockReturnValue({ data: mockCurrentFormat });
    mockUseUpcomingFormat.mockReturnValue({
      data: mockUpcomingFormat,
      isLoading: false,
    });
    mockUseRotationImpacts.mockReturnValue({
      data: mockImpacts,
      isLoading: false,
      isError: false,
      refetch: mockRefetch,
    });
  }

  describe("loading state", () => {
    it("should show loading skeleton when upcoming format is loading", () => {
      mockUseCurrentFormat.mockReturnValue({ data: undefined });
      mockUseUpcomingFormat.mockReturnValue({
        data: undefined,
        isLoading: true,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
        refetch: mockRefetch,
      });

      const { container } = render(<RotationPage />);
      expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
    });

    it("should show loading skeleton when impacts are loading", () => {
      mockUseCurrentFormat.mockReturnValue({ data: mockCurrentFormat });
      mockUseUpcomingFormat.mockReturnValue({
        data: mockUpcomingFormat,
        isLoading: false,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        refetch: mockRefetch,
      });

      const { container } = render(<RotationPage />);
      expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
    });
  });

  describe("no upcoming rotation", () => {
    it("should show empty state when no upcoming format exists", () => {
      mockUseCurrentFormat.mockReturnValue({ data: mockCurrentFormat });
      mockUseUpcomingFormat.mockReturnValue({
        data: undefined,
        isLoading: false,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
        refetch: mockRefetch,
      });

      render(<RotationPage />);

      expect(screen.getByText("Rotation Impact")).toBeInTheDocument();
      expect(
        screen.getByText("No upcoming rotation announced yet.")
      ).toBeInTheDocument();
    });
  });

  describe("error state", () => {
    it("should show error message when impacts fail to load", () => {
      mockUseCurrentFormat.mockReturnValue({ data: mockCurrentFormat });
      mockUseUpcomingFormat.mockReturnValue({
        data: mockUpcomingFormat,
        isLoading: false,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        refetch: mockRefetch,
      });

      render(<RotationPage />);

      expect(
        screen.getByText("Failed to load rotation data")
      ).toBeInTheDocument();
    });

    it("should show Try Again button on error", () => {
      mockUseCurrentFormat.mockReturnValue({ data: mockCurrentFormat });
      mockUseUpcomingFormat.mockReturnValue({
        data: mockUpcomingFormat,
        isLoading: false,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        refetch: mockRefetch,
      });

      render(<RotationPage />);

      const retryButton = screen.getByText("Try Again");
      expect(retryButton).toBeInTheDocument();
    });

    it("should call refetch when Try Again is clicked", () => {
      mockUseCurrentFormat.mockReturnValue({ data: mockCurrentFormat });
      mockUseUpcomingFormat.mockReturnValue({
        data: mockUpcomingFormat,
        isLoading: false,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        refetch: mockRefetch,
      });

      render(<RotationPage />);

      fireEvent.click(screen.getByText("Try Again"));
      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe("loaded state", () => {
    it("should display the format name in the header", () => {
      setupLoadedState();
      render(<RotationPage />);

      expect(
        screen.getByText("Regulation G Rotation Impact")
      ).toBeInTheDocument();
    });

    it("should display the rotation date and days remaining", () => {
      setupLoadedState();
      render(<RotationPage />);

      const expectedDate = new Date("2026-04-01T00:00:00Z").toLocaleDateString(
        "en-US",
        {
          month: "long",
          day: "numeric",
          year: "numeric",
        }
      );
      expect(screen.getByText(new RegExp(expectedDate))).toBeInTheDocument();
      expect(screen.getByText(/30 days remaining/)).toBeInTheDocument();
    });

    it("should display total archetypes count", () => {
      setupLoadedState();
      render(<RotationPage />);

      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("Total Archetypes")).toBeInTheDocument();
    });

    it("should display survival rating filter buttons", () => {
      setupLoadedState();
      render(<RotationPage />);

      expect(screen.getByText("Total Archetypes")).toBeInTheDocument();
      expect(screen.getByText("Thrives")).toBeInTheDocument();
      expect(screen.getByText("Adapts")).toBeInTheDocument();
      expect(screen.getByText("Crippled")).toBeInTheDocument();
      expect(screen.getByText("Dies")).toBeInTheDocument();
    });

    it("should display survival rating counts", () => {
      setupLoadedState();
      render(<RotationPage />);

      // thrives: 1 (Gardevoir ex), adapts: 1 (Charizard ex), dies: 1 (Lugia VSTAR)
      const thrivesButton = screen.getByText("Thrives").closest("button");
      expect(thrivesButton).toHaveTextContent("1");

      const adaptsButton = screen.getByText("Adapts").closest("button");
      expect(adaptsButton).toHaveTextContent("1");

      const diesButton = screen.getByText("Dies").closest("button");
      expect(diesButton).toHaveTextContent("1");
    });
  });

  describe("tab navigation", () => {
    it("should render overview and cards tabs", () => {
      setupLoadedState();
      render(<RotationPage />);

      expect(screen.getByText("Archetype Overview")).toBeInTheDocument();
      expect(screen.getByText("Rotating Cards")).toBeInTheDocument();
    });

    it("should render archetype survival components in overview tab", () => {
      setupLoadedState();
      render(<RotationPage />);

      expect(screen.getByTestId("archetype-arch-1")).toBeInTheDocument();
      expect(screen.getByTestId("archetype-arch-2")).toBeInTheDocument();
      expect(screen.getByTestId("archetype-arch-3")).toBeInTheDocument();
    });

    it("should render CardRotationList in cards tab", () => {
      setupLoadedState();
      render(<RotationPage />);

      expect(screen.getByTestId("card-rotation-list")).toBeInTheDocument();
    });
  });

  describe("rating filter", () => {
    it("should filter archetypes when a rating filter is clicked", () => {
      setupLoadedState();
      render(<RotationPage />);

      // Click "Dies" filter
      const diesButton = screen.getByText("Dies").closest("button");
      fireEvent.click(diesButton!);

      // Only Lugia VSTAR (dies) should remain
      expect(screen.getByTestId("archetype-arch-2")).toBeInTheDocument();
      expect(screen.queryByTestId("archetype-arch-1")).not.toBeInTheDocument();
      expect(screen.queryByTestId("archetype-arch-3")).not.toBeInTheDocument();
    });

    it("should show all archetypes when 'all' filter is selected", () => {
      setupLoadedState();
      render(<RotationPage />);

      // Click a specific filter first
      const diesButton = screen.getByText("Dies").closest("button");
      fireEvent.click(diesButton!);

      // Then click Total Archetypes (all)
      const allButton = screen.getByText("Total Archetypes").closest("button");
      fireEvent.click(allButton!);

      expect(screen.getByTestId("archetype-arch-1")).toBeInTheDocument();
      expect(screen.getByTestId("archetype-arch-2")).toBeInTheDocument();
      expect(screen.getByTestId("archetype-arch-3")).toBeInTheDocument();
    });

    it("should show empty message when no archetypes match the filter", () => {
      setupLoadedState();
      render(<RotationPage />);

      // Click "Crippled" filter - no archetypes have this rating
      const crippledButton = screen.getByText("Crippled").closest("button");
      fireEvent.click(crippledButton!);

      expect(
        screen.getByText("No archetypes match the selected filter.")
      ).toBeInTheDocument();
    });
  });

  describe("format transition", () => {
    it("should build transition string from current and upcoming format names", () => {
      setupLoadedState();
      render(<RotationPage />);

      // The hook should be called with the transition string
      expect(mockUseRotationImpacts).toHaveBeenCalledWith("F-2025-to-G-2026");
    });

    it("should pass empty transition when formats are not loaded", () => {
      mockUseCurrentFormat.mockReturnValue({ data: undefined });
      mockUseUpcomingFormat.mockReturnValue({
        data: undefined,
        isLoading: true,
      });
      mockUseRotationImpacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: false,
        refetch: mockRefetch,
      });

      render(<RotationPage />);

      expect(mockUseRotationImpacts).toHaveBeenCalledWith("");
    });
  });
});
