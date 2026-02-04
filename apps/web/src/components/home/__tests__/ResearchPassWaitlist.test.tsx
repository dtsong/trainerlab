import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ResearchPassWaitlist } from "../ResearchPassWaitlist";

describe("ResearchPassWaitlist", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should render the section heading", () => {
    render(<ResearchPassWaitlist />);

    expect(screen.getByText("Research Pass")).toBeInTheDocument();
  });

  it("should render the description text", () => {
    render(<ResearchPassWaitlist />);

    expect(
      screen.getByText(/Get early access to premium features/)
    ).toBeInTheDocument();
  });

  it("should render the email input with placeholder", () => {
    render(<ResearchPassWaitlist />);

    expect(screen.getByPlaceholderText("Enter your email")).toBeInTheDocument();
  });

  it("should render the 'Join Waitlist' submit button", () => {
    render(<ResearchPassWaitlist />);

    expect(
      screen.getByRole("button", { name: /Join Waitlist/i })
    ).toBeInTheDocument();
  });

  it("should render the beta disclaimer text", () => {
    render(<ResearchPassWaitlist />);

    expect(
      screen.getByText("Free during beta. No spam, just launch updates.")
    ).toBeInTheDocument();
  });

  it("should show validation error for empty email", async () => {
    const user = userEvent.setup();

    render(<ResearchPassWaitlist />);

    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));

    expect(
      screen.getByText("Please enter a valid email address")
    ).toBeInTheDocument();
  });

  it("should show validation error for email without @", async () => {
    const user = userEvent.setup();

    render(<ResearchPassWaitlist />);

    const input = screen.getByPlaceholderText("Enter your email");
    await user.type(input, "notanemail");
    // Use fireEvent.submit to bypass HTML5 email input validation
    // which would prevent form submission in userEvent
    const form = input.closest("form")!;
    fireEvent.submit(form);

    expect(
      screen.getByText("Please enter a valid email address")
    ).toBeInTheDocument();
  });

  it("should clear error state when user types after error", async () => {
    const user = userEvent.setup();

    render(<ResearchPassWaitlist />);

    // Trigger error
    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));
    expect(
      screen.getByText("Please enter a valid email address")
    ).toBeInTheDocument();

    // Start typing to clear error
    const input = screen.getByPlaceholderText("Enter your email");
    await user.type(input, "t");

    expect(
      screen.queryByText("Please enter a valid email address")
    ).not.toBeInTheDocument();
  });

  it("should submit the form and show success message", async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    render(<ResearchPassWaitlist />);

    const input = screen.getByPlaceholderText("Enter your email");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));

    expect(await screen.findByText(/on the list/)).toBeInTheDocument();

    expect(global.fetch).toHaveBeenCalledWith("/api/waitlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "test@example.com" }),
    });
  });

  it("should show error message when API request fails", async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
    });

    render(<ResearchPassWaitlist />);

    const input = screen.getByPlaceholderText("Enter your email");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));

    expect(
      await screen.findByText("Something went wrong. Please try again.")
    ).toBeInTheDocument();
  });

  it("should show error message when fetch throws", async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    render(<ResearchPassWaitlist />);

    const input = screen.getByPlaceholderText("Enter your email");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));

    expect(
      await screen.findByText("Something went wrong. Please try again.")
    ).toBeInTheDocument();
  });

  it("should hide the form and show success state after successful submit", async () => {
    const user = userEvent.setup();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    render(<ResearchPassWaitlist />);

    const input = screen.getByPlaceholderText("Enter your email");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));

    // Wait for success state
    await screen.findByText(/on the list/);

    // Form should be hidden
    expect(
      screen.queryByPlaceholderText("Enter your email")
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Join Waitlist/i })
    ).not.toBeInTheDocument();
  });

  it("should render error text with role='alert'", async () => {
    const user = userEvent.setup();

    render(<ResearchPassWaitlist />);

    await user.click(screen.getByRole("button", { name: /Join Waitlist/i }));

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Please enter a valid email address");
  });
});
