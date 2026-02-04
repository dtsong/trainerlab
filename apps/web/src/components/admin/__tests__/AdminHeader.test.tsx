import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminHeader } from "../AdminHeader";

const mockSignOut = vi.fn();

vi.mock("@/hooks", () => ({
  useAuth: vi.fn(() => ({
    user: null,
    loading: false,
    signOut: mockSignOut,
  })),
}));

const mockUseAuth = vi.mocked((await import("@/hooks")).useAuth);

describe("AdminHeader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: {
        id: "1",
        email: "admin@trainerlab.gg",
        displayName: "Admin",
        photoURL: null,
      },
      loading: false,
      signOut: mockSignOut,
    });
  });

  it("renders the title prop", () => {
    render(<AdminHeader title="Dashboard" />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders different title values", () => {
    render(<AdminHeader title="Tournaments" />);

    expect(screen.getByText("Tournaments")).toBeInTheDocument();
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("displays the user email", () => {
    render(<AdminHeader title="Admin" />);

    expect(screen.getByText("admin@trainerlab.gg")).toBeInTheDocument();
  });

  it("handles null user email gracefully", () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: "1",
        email: null,
        displayName: "Admin",
        photoURL: null,
      },
      loading: false,
      signOut: mockSignOut,
    });

    render(<AdminHeader title="Admin" />);

    // Should not crash when email is null
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("renders the sign out button", () => {
    render(<AdminHeader title="Admin" />);

    expect(
      screen.getByRole("button", { name: /sign out/i })
    ).toBeInTheDocument();
  });

  it("calls signOut when sign out button is clicked", async () => {
    const user = userEvent.setup();

    render(<AdminHeader title="Admin" />);

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });

  it("renders as a header element", () => {
    render(<AdminHeader title="Admin" />);

    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("does not display email when user is null", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signOut: mockSignOut,
    });

    render(<AdminHeader title="Admin" />);

    // Title should still render
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });
});
