import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TopNav } from "../TopNav";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/"),
}));

// Mock useAuth hook
vi.mock("@/hooks", () => ({
  useAuth: vi.fn(() => ({
    user: null,
    loading: false,
    signOut: vi.fn(),
  })),
}));

// Get mocked functions
const mockUsePathname = vi.mocked(
  (await import("next/navigation")).usePathname
);
const mockUseAuth = vi.mocked((await import("@/hooks")).useAuth);

describe("TopNav", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue("/");
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signOut: vi.fn(),
    });
  });

  describe("basic rendering", () => {
    it("should render logo with TrainerLab text", () => {
      render(<TopNav />);
      expect(screen.getByText(/Trainer/)).toBeInTheDocument();
    });

    it("should render Research Floor label", () => {
      render(<TopNav />);
      expect(screen.getByText("Research Floor")).toBeInTheDocument();
    });

    it("should render all navigation links", () => {
      render(<TopNav />);
      expect(screen.getByText("Meta Overview")).toBeInTheDocument();
      expect(screen.getByText("JP Intelligence")).toBeInTheDocument();
      expect(screen.getByText("Tournaments")).toBeInTheDocument();
      expect(screen.getByText("Lab Notes")).toBeInTheDocument();
      expect(screen.getByText("Deck Profiles")).toBeInTheDocument();
    });

    it("should render search bar with placeholder", () => {
      render(<TopNav />);
      expect(screen.getByText("Investigate...")).toBeInTheDocument();
    });

    it("should render keyboard shortcut badge", () => {
      render(<TopNav />);
      expect(screen.getByText("⌘K")).toBeInTheDocument();
    });

    it("should render format label and clock", () => {
      render(<TopNav />);
      expect(screen.getByText("SVI–ASC")).toBeInTheDocument();
    });
  });

  describe("active states", () => {
    it("should show active state for Meta Overview on /meta", () => {
      mockUsePathname.mockReturnValue("/meta");
      render(<TopNav />);

      const metaLink = screen.getByText("Meta Overview").closest("a");
      expect(metaLink).toHaveClass("border-flame");
      expect(metaLink).toHaveClass("text-lab-text");
    });

    it("should show active state for JP Intelligence on /meta/japan", () => {
      mockUsePathname.mockReturnValue("/meta/japan");
      render(<TopNav />);

      const jpLink = screen.getByText("JP Intelligence").closest("a");
      expect(jpLink).toHaveClass("border-flame");
    });

    it("should not show active Meta Overview on /meta/japan", () => {
      mockUsePathname.mockReturnValue("/meta/japan");
      render(<TopNav />);

      const metaLink = screen.getByText("Meta Overview").closest("a");
      expect(metaLink).toHaveClass("border-transparent");
      expect(metaLink).toHaveClass("text-lab-text-muted");
    });
  });

  describe("JP Intelligence pulse dot", () => {
    it("should render a pulsing dot on JP Intelligence tab", () => {
      render(<TopNav />);

      const jpLink = screen.getByText("JP Intelligence").closest("a");
      const dot = jpLink?.querySelector(".animate-lab-pulse");
      expect(dot).toBeInTheDocument();
    });
  });

  describe("auth states", () => {
    it("should show Sign In button when not logged in", () => {
      render(<TopNav />);
      expect(screen.getByText("Sign In")).toBeInTheDocument();
    });

    it("should show loading state when auth is loading", () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
        signOut: vi.fn(),
      });
      render(<TopNav />);

      const loadingEl = document.querySelector(".animate-pulse");
      expect(loadingEl).toBeInTheDocument();
    });
  });
});
