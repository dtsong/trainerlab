import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MobileNav } from "../MobileNav";

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

describe("MobileNav", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue("/");
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      authError: null,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
      clearAuthError: vi.fn(),
    });
  });

  describe("basic rendering", () => {
    it("should render all main tabs", () => {
      render(<MobileNav />);
      expect(screen.getByText("Home")).toBeInTheDocument();
      expect(screen.getByText("Meta")).toBeInTheDocument();
      expect(screen.getByText("JP")).toBeInTheDocument();
      expect(screen.getByText("Events")).toBeInTheDocument();
      expect(screen.getByText("More")).toBeInTheDocument();
    });
  });

  describe("active states", () => {
    it("should highlight Home tab when on /", () => {
      mockUsePathname.mockReturnValue("/");
      render(<MobileNav />);

      const homeLink = screen.getByText("Home").closest("a");
      expect(homeLink).toHaveClass("text-teal-500");
    });

    it("should highlight Meta tab when on /meta", () => {
      mockUsePathname.mockReturnValue("/meta");
      render(<MobileNav />);

      const metaLink = screen.getByText("Meta").closest("a");
      expect(metaLink).toHaveClass("text-teal-500");
    });

    it("should highlight JP tab when on /meta/japan", () => {
      mockUsePathname.mockReturnValue("/meta/japan");
      render(<MobileNav />);

      const jpLink = screen.getByText("JP").closest("a");
      expect(jpLink).toHaveClass("text-teal-500");
    });

    it("should not highlight Meta tab when on /meta/japan", () => {
      mockUsePathname.mockReturnValue("/meta/japan");
      render(<MobileNav />);

      const metaLink = screen.getByText("Meta").closest("a");
      expect(metaLink).toHaveClass("text-slate-500");
    });
  });

  describe("more drawer", () => {
    it("should open drawer when More is clicked", async () => {
      render(<MobileNav />);

      const moreButton = screen.getByText("More").closest("button");
      fireEvent.click(moreButton!);

      // Drawer content should be visible
      expect(await screen.findByText("Lab Notes")).toBeInTheDocument();
      expect(await screen.findByText("Investigate")).toBeInTheDocument();
      expect(await screen.findByText("Settings")).toBeInTheDocument();
    });

    it("should show auth buttons when not logged in", async () => {
      render(<MobileNav />);

      const moreButton = screen.getByText("More").closest("button");
      fireEvent.click(moreButton!);

      expect(await screen.findByText("Sign In")).toBeInTheDocument();
      expect(await screen.findByText("Sign Up")).toBeInTheDocument();
    });

    it("should show user info when logged in", async () => {
      mockUseAuth.mockReturnValue({
        user: {
          displayName: "Test User",
          email: "test@example.com",
          uid: "123",
          photoURL: null,
        },
        loading: false,
        authError: null,
        signIn: vi.fn(),
        signUp: vi.fn(),
        signInWithGoogle: vi.fn(),
        signOut: vi.fn(),
        getIdToken: vi.fn(),
        clearAuthError: vi.fn(),
      });

      render(<MobileNav />);

      const moreButton = screen.getByText("More").closest("button");
      fireEvent.click(moreButton!);

      expect(await screen.findByText("Test User")).toBeInTheDocument();
      expect(await screen.findByText("test@example.com")).toBeInTheDocument();
      expect(await screen.findByText("Sign Out")).toBeInTheDocument();
    });
  });
});
