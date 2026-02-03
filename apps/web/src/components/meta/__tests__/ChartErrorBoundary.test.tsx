import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChartErrorBoundary } from "../ChartErrorBoundary";

// Component that throws an error
function ThrowingComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div data-testid="child-content">Child content</div>;
}

describe("ChartErrorBoundary", () => {
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
      <ChartErrorBoundary>
        <ThrowingComponent shouldThrow={false} />
      </ChartErrorBoundary>
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  it("should render default fallback UI when child throws", () => {
    render(
      <ChartErrorBoundary chartName="TestChart">
        <ThrowingComponent shouldThrow={true} />
      </ChartErrorBoundary>
    );

    expect(screen.getByText("TestChart failed to load")).toBeInTheDocument();
    expect(
      screen.getByText("Please try refreshing the page")
    ).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("should use 'Chart' as default name when chartName is not provided", () => {
    render(
      <ChartErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ChartErrorBoundary>
    );

    expect(screen.getByText("Chart failed to load")).toBeInTheDocument();
  });

  it("should render custom fallback when provided", () => {
    const customFallback = (
      <div data-testid="custom-fallback">Custom error</div>
    );
    render(
      <ChartErrorBoundary fallback={customFallback}>
        <ThrowingComponent shouldThrow={true} />
      </ChartErrorBoundary>
    );

    expect(screen.getByTestId("custom-fallback")).toBeInTheDocument();
    expect(screen.queryByText("Chart failed to load")).not.toBeInTheDocument();
  });

  it("should reset error state when Try again is clicked", async () => {
    const user = userEvent.setup();

    // Use a stateful wrapper to control throwing
    let shouldThrow = true;
    function ControlledComponent() {
      if (shouldThrow) {
        throw new Error("Test error");
      }
      return <div data-testid="recovered-content">Recovered</div>;
    }

    const { rerender } = render(
      <ChartErrorBoundary chartName="TestChart">
        <ControlledComponent />
      </ChartErrorBoundary>
    );

    // Verify error state
    expect(screen.getByText("TestChart failed to load")).toBeInTheDocument();

    // Stop throwing and click retry
    shouldThrow = false;
    await user.click(screen.getByText("Try again"));

    // Re-render to trigger the recovered state
    rerender(
      <ChartErrorBoundary chartName="TestChart">
        <ControlledComponent />
      </ChartErrorBoundary>
    );

    expect(screen.getByTestId("recovered-content")).toBeInTheDocument();
  });

  it("should log error to console when error occurs", () => {
    render(
      <ChartErrorBoundary chartName="TestChart">
        <ThrowingComponent shouldThrow={true} />
      </ChartErrorBoundary>
    );

    expect(console.error).toHaveBeenCalled();
    const errorCall = (
      console.error as ReturnType<typeof vi.fn>
    ).mock.calls.find(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes('[ChartErrorBoundary] Chart "TestChart" crashed:')
    );
    expect(errorCall).toBeDefined();
  });

  it("should have correct styling on error fallback", () => {
    render(
      <ChartErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ChartErrorBoundary>
    );

    const container = screen.getByText("Chart failed to load").closest("div");
    expect(container).toHaveClass("text-center");
  });
});
