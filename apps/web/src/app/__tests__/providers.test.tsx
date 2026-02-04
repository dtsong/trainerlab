import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Providers } from "../providers";

// Mock next-auth/react SessionProvider
vi.mock("next-auth/react", () => ({
  SessionProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="session-provider">{children}</div>
  ),
}));

// Mock @tanstack/react-query
const mockQueryClientProvider = vi.fn(
  ({ children }: { children: React.ReactNode; client: unknown }) => (
    <div data-testid="query-client-provider">{children}</div>
  )
);

vi.mock("@tanstack/react-query", () => ({
  QueryClient: vi.fn().mockImplementation(() => ({
    defaultOptions: {},
  })),
  QueryClientProvider: (props: {
    children: React.ReactNode;
    client: unknown;
  }) => mockQueryClientProvider(props),
}));

// Mock Toaster
vi.mock("@/components/ui/sonner", () => ({
  Toaster: () => <div data-testid="toaster" />,
}));

describe("Providers", () => {
  it("should render children", () => {
    render(
      <Providers>
        <div data-testid="child-content">Hello World</div>
      </Providers>
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("should wrap children with SessionProvider", () => {
    render(
      <Providers>
        <div data-testid="child-content">Test</div>
      </Providers>
    );

    const sessionProvider = screen.getByTestId("session-provider");
    expect(sessionProvider).toBeInTheDocument();

    // Child should be inside the session provider
    const child = screen.getByTestId("child-content");
    expect(sessionProvider).toContainElement(child);
  });

  it("should wrap children with QueryClientProvider", () => {
    render(
      <Providers>
        <div data-testid="child-content">Test</div>
      </Providers>
    );

    const queryProvider = screen.getByTestId("query-client-provider");
    expect(queryProvider).toBeInTheDocument();

    // Child should be inside the query client provider
    const child = screen.getByTestId("child-content");
    expect(queryProvider).toContainElement(child);
  });

  it("should render QueryClientProvider inside SessionProvider", () => {
    render(
      <Providers>
        <div>Test</div>
      </Providers>
    );

    const sessionProvider = screen.getByTestId("session-provider");
    const queryProvider = screen.getByTestId("query-client-provider");

    // QueryClientProvider should be nested inside SessionProvider
    expect(sessionProvider).toContainElement(queryProvider);
  });

  it("should render the Toaster component", () => {
    render(
      <Providers>
        <div>Test</div>
      </Providers>
    );

    expect(screen.getByTestId("toaster")).toBeInTheDocument();
  });

  it("should render the Toaster inside QueryClientProvider", () => {
    render(
      <Providers>
        <div>Test</div>
      </Providers>
    );

    const queryProvider = screen.getByTestId("query-client-provider");
    const toaster = screen.getByTestId("toaster");
    expect(queryProvider).toContainElement(toaster);
  });

  it("should pass a QueryClient instance to QueryClientProvider", () => {
    render(
      <Providers>
        <div>Test</div>
      </Providers>
    );

    expect(mockQueryClientProvider).toHaveBeenCalled();
    const callArgs = mockQueryClientProvider.mock.calls[0][0];
    expect(callArgs).toHaveProperty("client");
  });

  it("should render multiple children", () => {
    render(
      <Providers>
        <div data-testid="child-1">First</div>
        <div data-testid="child-2">Second</div>
      </Providers>
    );

    expect(screen.getByTestId("child-1")).toBeInTheDocument();
    expect(screen.getByTestId("child-2")).toBeInTheDocument();
  });
});
