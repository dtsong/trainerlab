import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BO1ContextBanner } from "../BO1ContextBanner";

describe("BO1ContextBanner", () => {
  it("should render the banner with correct content", () => {
    render(<BO1ContextBanner />);

    expect(screen.getByTestId("bo1-context-banner")).toBeInTheDocument();
    expect(screen.getByText("Japan Best-of-1 Format")).toBeInTheDocument();
    expect(
      screen.getByText(/tie counts as a loss for both players/i),
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

  it("should explain tie = double loss rule", () => {
    render(<BO1ContextBanner />);

    expect(
      screen.getByText(/tie counts as a loss for both players/i),
    ).toBeInTheDocument();
  });

  it("should mention impact on deck building", () => {
    render(<BO1ContextBanner />);

    expect(
      screen.getByText(/faster, more aggressive decks are favored/i),
    ).toBeInTheDocument();
  });
});
