import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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
  (await import("next/navigation")).usePathname,
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
      signIn: vi.fn(),
      signUp: vi.fn(),
    });
  });

  describe("basic rendering", () => {
    it("should render logo with TrainerLab text", () => {
      render(<TopNav />);
      expect(screen.getByText("TrainerLab")).toBeInTheDocument();
    });

    it("should render all navigation links", () => {
      render(<TopNav />);
      expect(screen.getByText("Meta")).toBeInTheDocument();
      expect(screen.getByText("From Japan")).toBeInTheDocument();
      expect(screen.getByText("Tournaments")).toBeInTheDocument();
      expect(screen.getByText("Lab Notes")).toBeInTheDocument();
    });

    it("should render Investigate button", () => {
      render(<TopNav />);
      expect(screen.getByText("Investigate")).toBeInTheDocument();
    });
  });

  describe("active states", () => {
    it("should show active state for Meta when on /meta", () => {
      mockUsePathname.mockReturnValue("/meta");
      render(<TopNav />);

      const metaLink = screen.getByText("Meta").closest("a");
      expect(metaLink).toHaveClass("text-slate-900");
    });

    it("should show active state for From Japan when on /meta/japan", () => {
      mockUsePathname.mockReturnValue("/meta/japan");
      render(<TopNav />);

      const jpLink = screen.getByText("From Japan").closest("a");
      expect(jpLink).toHaveClass("text-slate-900");
    });

    it("should not show active state for Meta when on /meta/japan", () => {
      mockUsePathname.mockReturnValue("/meta/japan");
      render(<TopNav />);

      const metaLink = screen.getByText("Meta").closest("a");
      expect(metaLink).toHaveClass("text-slate-600");
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
        signIn: vi.fn(),
        signUp: vi.fn(),
      });
      render(<TopNav />);

      // Should have a loading placeholder
      const loadingEl = document.querySelector(".animate-pulse");
      expect(loadingEl).toBeInTheDocument();
    });
  });

  describe("scroll shadow", () => {
    it("should not have shadow initially", () => {
      render(<TopNav />);
      const header = document.querySelector("header");
      expect(header).not.toHaveClass("shadow-md");
    });

    it("should add shadow on scroll", () => {
      render(<TopNav />);

      // Simulate scroll
      Object.defineProperty(window, "scrollY", { value: 10, writable: true });
      fireEvent.scroll(window);

      const header = document.querySelector("header");
      expect(header).toHaveClass("shadow-md");
    });
  });
});
