import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Header } from "../Header";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    onClick,
  }: {
    children: React.ReactNode;
    href: string;
    onClick?: () => void;
  }) => (
    <a href={href} onClick={onClick}>
      {children}
    </a>
  ),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/"),
}));

// Mock sonner
vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

// Mock useAuth hook
vi.mock("@/hooks", () => ({
  useAuth: vi.fn(() => ({
    user: null,
    loading: false,
    signOut: vi.fn(),
  })),
}));

// Mock UserMenu to isolate Header tests
vi.mock("../UserMenu", () => ({
  UserMenu: () => <div data-testid="user-menu">UserMenu</div>,
}));

// Mock Sheet components (radix primitives)
vi.mock("@/components/ui/sheet", () => ({
  Sheet: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetContent: ({
    children,
  }: {
    children: React.ReactNode;
    side?: string;
    className?: string;
  }) => <div data-testid="sheet-content">{children}</div>,
  SheetTrigger: ({
    children,
  }: {
    children: React.ReactNode;
    asChild?: boolean;
    className?: string;
  }) => <div>{children}</div>,
}));

// Get mocked functions
const mockUsePathname = vi.mocked(
  (await import("next/navigation")).usePathname
);
const mockUseAuth = vi.mocked((await import("@/hooks")).useAuth);

function createMockUser(overrides = {}) {
  return {
    id: "user-1",
    email: "ash@pokemon.com",
    displayName: "Ash Ketchum",
    photoURL: null,
    ...overrides,
  };
}

describe("Header", () => {
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
    it("should render the TrainerLab brand", () => {
      render(<Header />);
      expect(screen.getByText("TrainerLab")).toBeInTheDocument();
    });

    it("should render the brand link pointing to home", () => {
      render(<Header />);
      const brandLink = screen.getByText("TrainerLab").closest("a");
      expect(brandLink).toHaveAttribute("href", "/");
    });

    it("should render within a header element", () => {
      render(<Header />);
      const header = document.querySelector("header");
      expect(header).toBeInTheDocument();
    });

    it("should have sticky positioning", () => {
      render(<Header />);
      const header = document.querySelector("header");
      expect(header).toHaveClass("sticky", "top-0");
    });
  });

  describe("navigation links", () => {
    it("should render Cards link", () => {
      render(<Header />);
      const cardsLinks = screen.getAllByText("Cards");
      expect(cardsLinks.length).toBeGreaterThan(0);
      const link = cardsLinks[0].closest("a");
      expect(link).toHaveAttribute("href", "/cards");
    });

    it("should render Decks link", () => {
      render(<Header />);
      const decksLinks = screen.getAllByText("Decks");
      expect(decksLinks.length).toBeGreaterThan(0);
    });

    it("should render Meta link", () => {
      render(<Header />);
      const metaLinks = screen.getAllByText("Meta");
      expect(metaLinks.length).toBeGreaterThan(0);
    });
  });

  describe("auth states - logged out", () => {
    it("should show Sign In button when not logged in", () => {
      render(<Header />);
      const signInLinks = screen.getAllByText("Sign In");
      expect(signInLinks.length).toBeGreaterThan(0);
    });

    it("should link Sign In to /auth/login", () => {
      render(<Header />);
      const signInLinks = screen.getAllByText("Sign In");
      const link = signInLinks[0].closest("a");
      expect(link).toHaveAttribute("href", "/auth/login");
    });
  });

  describe("auth states - loading", () => {
    it("should show loading skeleton when auth is loading", () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
        signOut: vi.fn(),
      });

      render(<Header />);
      const loadingElements = document.querySelectorAll(".animate-pulse");
      expect(loadingElements.length).toBeGreaterThan(0);
    });

    it("should not show Sign In when loading", () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.queryByText("Sign In")).not.toBeInTheDocument();
    });
  });

  describe("auth states - logged in", () => {
    it("should render UserMenu when user is logged in", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByTestId("user-menu")).toBeInTheDocument();
    });

    it("should not show Sign In button when logged in", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      // The desktop Sign In should not appear; mobile may show user info instead
      const signInLinks = screen.queryAllByText("Sign In");
      // With a logged-in user, no Sign In should be shown
      expect(signInLinks.length).toBe(0);
    });

    it("should display user name in mobile menu when logged in", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByText("Ash Ketchum")).toBeInTheDocument();
    });

    it("should display user email in mobile menu when logged in", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByText("ash@pokemon.com")).toBeInTheDocument();
    });

    it("should show My Decks link in mobile menu", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByText("My Decks")).toBeInTheDocument();
    });

    it("should show Settings link in mobile menu", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByText("Settings")).toBeInTheDocument();
    });

    it("should show Sign Out button in mobile menu", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser(),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByText("Sign Out")).toBeInTheDocument();
    });

    it("should show 'User' fallback when displayName is null", () => {
      mockUseAuth.mockReturnValue({
        user: createMockUser({ displayName: null }),
        loading: false,
        signOut: vi.fn(),
      });

      render(<Header />);
      expect(screen.getByText("User")).toBeInTheDocument();
    });
  });

  describe("mobile menu toggle button", () => {
    it("should render toggle menu button with sr-only label", () => {
      render(<Header />);
      expect(screen.getByText("Toggle menu")).toBeInTheDocument();
    });
  });
});
