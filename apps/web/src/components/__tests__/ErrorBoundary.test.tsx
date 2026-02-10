import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBoundary } from "../ErrorBoundary";

// Component that conditionally throws
function ThrowingComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Test error message");
  }
  return <div data-testid="child-content">Child content</div>;
}

describe("ErrorBoundary", () => {
  // Suppress console.error for expected errors during tests
  const originalError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalError;
  });

  it("should render children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("should render default error UI when child throws", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("should display the error message", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("should render description text in error state", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(
      screen.getByText(/An unexpected error occurred/)
    ).toBeInTheDocument();
  });

  it("should render Try Again button", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Try Again")).toBeInTheDocument();
  });

  it("should render Report Issue button", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Report Issue")).toBeInTheDocument();
  });

  it("should render custom fallback when provided", () => {
    const customFallback = (
      <div data-testid="custom-fallback">Custom error display</div>
    );

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId("custom-fallback")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("should not render children when error occurs", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.queryByTestId("child-content")).not.toBeInTheDocument();
  });

  it("should reset error state when Try Again is clicked", async () => {
    const user = userEvent.setup();

    let shouldThrow = true;
    function ControlledComponent() {
      if (shouldThrow) {
        throw new Error("Controlled error");
      }
      return <div data-testid="recovered-content">Recovered</div>;
    }

    const { rerender } = render(
      <ErrorBoundary>
        <ControlledComponent />
      </ErrorBoundary>
    );

    // Verify error state
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    // Stop throwing and click retry
    shouldThrow = false;
    await user.click(screen.getByText("Try Again"));

    rerender(
      <ErrorBoundary>
        <ControlledComponent />
      </ErrorBoundary>
    );

    expect(screen.getByTestId("recovered-content")).toBeInTheDocument();
  });

  it("should open mailto link when Report Issue is clicked", async () => {
    const user = userEvent.setup();
    const mockWindowOpen = vi.fn();
    const originalOpen = window.open;
    window.open = mockWindowOpen;

    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    await user.click(screen.getByText("Report Issue"));

    expect(mockWindowOpen).toHaveBeenCalledWith(
      expect.stringContaining("mailto:support@trainerlab.io")
    );
    expect(mockWindowOpen).toHaveBeenCalledWith(
      expect.stringContaining("subject=")
    );
    expect(mockWindowOpen).toHaveBeenCalledWith(
      expect.stringContaining("body=")
    );

    window.open = originalOpen;
  });

  it("should include error message in report email body", async () => {
    const user = userEvent.setup();
    const mockWindowOpen = vi.fn();
    const originalOpen = window.open;
    window.open = mockWindowOpen;

    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    await user.click(screen.getByText("Report Issue"));

    expect(mockWindowOpen).toHaveBeenCalledWith(
      expect.stringContaining("Test%20error%20message")
    );

    window.open = originalOpen;
  });

  it("should log error to console via componentDidCatch", () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(console.error).toHaveBeenCalled();
    const errorCall = (
      console.error as ReturnType<typeof vi.fn>
    ).mock.calls.find(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("ErrorBoundary caught an error:")
    );
    expect(errorCall).toBeDefined();
  });

  it("should not display error message in UI when error has no message", () => {
    function NoMessageError(): React.ReactNode {
      throw new Error("");
    }

    render(
      <ErrorBoundary>
        <NoMessageError />
      </ErrorBoundary>
    );

    // The error message paragraph should not appear for empty message
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    const errorMessageEl = document.querySelector(".font-mono");
    // Empty string is falsy, so the conditional block should not render
    expect(errorMessageEl).not.toBeInTheDocument();
  });
});
