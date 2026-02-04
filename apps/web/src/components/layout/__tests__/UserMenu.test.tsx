import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserMenu } from "../UserMenu";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  })),
}));

// Mock sonner
vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

// Mock Radix Avatar so that AvatarImage renders a real img tag immediately
vi.mock("@/components/ui/avatar", () => ({
  Avatar: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => <span className={className}>{children}</span>,
  AvatarImage: ({ src, alt }: { src?: string; alt?: string }) =>
    src ? <img src={src} alt={alt} /> : null,
  AvatarFallback: ({ children }: { children: React.ReactNode }) => (
    <span>{children}</span>
  ),
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
const mockUseRouter = vi.mocked((await import("next/navigation")).useRouter);
const mockUseAuth = vi.mocked((await import("@/hooks")).useAuth);

function createMockUser(overrides = {}) {
  return {
    id: "user-1",
    email: "ash@pokemon.com",
    displayName: "Ash Ketchum",
    photoURL: "https://example.com/ash.png",
    ...overrides,
  };
}

describe("UserMenu", () => {
  const mockPush = vi.fn();
  const mockSignOut = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockReset();
    mockSignOut.mockReset();

    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: vi.fn(),
      prefetch: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
    });

    mockUseAuth.mockReturnValue({
      user: createMockUser(),
      loading: false,
      signOut: mockSignOut,
    });
  });

  it("should render nothing when user is null", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signOut: mockSignOut,
    });

    const { container } = render(<UserMenu />);
    expect(container.innerHTML).toBe("");
  });

  it("should render avatar button when user is logged in", () => {
    render(<UserMenu />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("should display user initials in avatar fallback", () => {
    render(<UserMenu />);
    expect(screen.getByText("AK")).toBeInTheDocument();
  });

  it("should display single-word name initials correctly", () => {
    mockUseAuth.mockReturnValue({
      user: createMockUser({ displayName: "Pikachu" }),
      loading: false,
      signOut: mockSignOut,
    });

    render(<UserMenu />);
    expect(screen.getByText("PI")).toBeInTheDocument();
  });

  it("should display 'U' when displayName is null", () => {
    mockUseAuth.mockReturnValue({
      user: createMockUser({ displayName: null }),
      loading: false,
      signOut: mockSignOut,
    });

    render(<UserMenu />);
    expect(screen.getByText("U")).toBeInTheDocument();
  });

  it("should show user name and email in dropdown when opened", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button"));

    expect(screen.getByText("Ash Ketchum")).toBeInTheDocument();
    expect(screen.getByText("ash@pokemon.com")).toBeInTheDocument();
  });

  it("should show 'User' as display name fallback in dropdown", async () => {
    const user = userEvent.setup();
    mockUseAuth.mockReturnValue({
      user: createMockUser({ displayName: null }),
      loading: false,
      signOut: mockSignOut,
    });

    render(<UserMenu />);
    await user.click(screen.getByRole("button"));

    expect(screen.getByText("User")).toBeInTheDocument();
  });

  it("should show My Decks menu item", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button"));

    expect(screen.getByText("My Decks")).toBeInTheDocument();
  });

  it("should show Settings menu item", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button"));

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("should show Sign out menu item", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button"));

    expect(screen.getByText("Sign out")).toBeInTheDocument();
  });

  it("should navigate to /decks when My Decks is clicked", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("My Decks"));

    expect(mockPush).toHaveBeenCalledWith("/decks");
  });

  it("should navigate to /settings when Settings is clicked", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Settings"));

    expect(mockPush).toHaveBeenCalledWith("/settings");
  });

  it("should call signOut and navigate to / on sign out", async () => {
    const user = userEvent.setup();
    mockSignOut.mockResolvedValue(undefined);

    render(<UserMenu />);

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Sign out"));

    expect(mockSignOut).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("should show error toast when sign out fails", async () => {
    const user = userEvent.setup();
    const { toast } = await import("sonner");
    mockSignOut.mockRejectedValue(new Error("Sign out failed"));

    render(<UserMenu />);

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByText("Sign out"));

    expect(toast.error).toHaveBeenCalledWith(
      "Failed to sign out. Please try again."
    );
  });

  it("should render avatar image when photoURL is provided", () => {
    render(<UserMenu />);
    const img = document.querySelector("img");
    expect(img).toHaveAttribute("src", "https://example.com/ash.png");
  });
});
