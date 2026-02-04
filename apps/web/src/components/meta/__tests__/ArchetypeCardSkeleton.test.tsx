import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  ArchetypeCardSkeleton,
  ArchetypeGridSkeleton,
} from "../ArchetypeCardSkeleton";

// Mock shadcn Card components
vi.mock("@/components/ui/card", () => ({
  Card: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="skeleton-card" className={className}>
      {children}
    </div>
  ),
  CardHeader: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="card-header" className={className}>
      {children}
    </div>
  ),
  CardContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="card-content">{children}</div>
  ),
}));

import { vi } from "vitest";

describe("ArchetypeCardSkeleton", () => {
  it("should render without errors", () => {
    const { container } = render(<ArchetypeCardSkeleton />);

    expect(container).toBeTruthy();
  });

  it("should render a card element", () => {
    render(<ArchetypeCardSkeleton />);

    expect(screen.getByTestId("skeleton-card")).toBeInTheDocument();
  });

  it("should have animate-pulse class for loading animation", () => {
    render(<ArchetypeCardSkeleton />);

    expect(screen.getByTestId("skeleton-card")).toHaveClass("animate-pulse");
  });

  it("should render three placeholder card images", () => {
    render(<ArchetypeCardSkeleton />);

    const content = screen.getByTestId("card-content");
    const placeholders = content.querySelectorAll(".bg-muted");
    expect(placeholders).toHaveLength(3);
  });

  it("should apply custom className", () => {
    render(<ArchetypeCardSkeleton className="custom-class" />);

    expect(screen.getByTestId("skeleton-card")).toHaveClass("custom-class");
  });
});

describe("ArchetypeGridSkeleton", () => {
  it("should render without errors", () => {
    const { container } = render(<ArchetypeGridSkeleton />);

    expect(container).toBeTruthy();
  });

  it("should render 6 skeleton cards by default", () => {
    render(<ArchetypeGridSkeleton />);

    const cards = screen.getAllByTestId("skeleton-card");
    expect(cards).toHaveLength(6);
  });

  it("should render a custom number of skeleton cards", () => {
    render(<ArchetypeGridSkeleton count={3} />);

    const cards = screen.getAllByTestId("skeleton-card");
    expect(cards).toHaveLength(3);
  });

  it("should apply custom className to grid container", () => {
    const { container } = render(
      <ArchetypeGridSkeleton className="custom-grid" />
    );

    expect(container.firstChild).toHaveClass("custom-grid");
  });

  it("should have grid layout classes", () => {
    const { container } = render(<ArchetypeGridSkeleton />);

    expect(container.firstChild).toHaveClass("grid");
  });
});
