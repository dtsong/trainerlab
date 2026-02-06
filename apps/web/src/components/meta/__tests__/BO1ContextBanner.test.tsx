import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BO1ContextBanner } from "../BO1ContextBanner";

const STORAGE_KEY = "trainerlab-bo1-banner-dismissed";

describe("BO1ContextBanner", () => {
  beforeEach(() => {
    localStorage.removeItem(STORAGE_KEY);
  });

  it("should render the banner with correct content", () => {
    render(<BO1ContextBanner />);

    expect(screen.getByTestId("bo1-context-banner")).toBeInTheDocument();
    expect(screen.getByText("Japan Best-of-1 Format")).toBeInTheDocument();
    expect(
      screen.getByText(/tie counts as a loss for both players/i)
    ).toBeInTheDocument();
  });

  it("should have role alert for accessibility", () => {
    render(<BO1ContextBanner />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("should dismiss when close button is clicked", async () => {
    const user = userEvent.setup();
    render(<BO1ContextBanner />);

    expect(screen.getByTestId("bo1-context-banner")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /dismiss/i }));

    expect(screen.queryByTestId("bo1-context-banner")).not.toBeInTheDocument();
  });

  it("should persist dismissal to localStorage", async () => {
    const user = userEvent.setup();
    render(<BO1ContextBanner />);

    await user.click(screen.getByRole("button", { name: /dismiss/i }));

    expect(localStorage.getItem(STORAGE_KEY)).toBe("true");
  });

  it("should not render when previously dismissed via localStorage", () => {
    localStorage.setItem(STORAGE_KEY, "true");

    render(<BO1ContextBanner />);

    expect(screen.queryByTestId("bo1-context-banner")).not.toBeInTheDocument();
  });

  it("should render when localStorage value is not 'true'", () => {
    localStorage.setItem(STORAGE_KEY, "false");

    render(<BO1ContextBanner />);

    expect(screen.getByTestId("bo1-context-banner")).toBeInTheDocument();
  });

  it("should explain tie = double loss rule", () => {
    render(<BO1ContextBanner />);

    expect(
      screen.getByText(/tie counts as a loss for both players/i)
    ).toBeInTheDocument();
  });

  it("should mention impact on deck building", () => {
    render(<BO1ContextBanner />);

    expect(
      screen.getByText(/faster, more aggressive decks are favored/i)
    ).toBeInTheDocument();
  });
});
