import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DeckCardSkeleton, DeckGridSkeleton } from "../DeckCardSkeleton";

// Mock the UI components
vi.mock("@/components/ui/card", () => ({
  Card: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="card" className={className}>
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
  CardContent: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="card-content" className={className}>
      {children}
    </div>
  ),
  CardFooter: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => (
    <div data-testid="card-footer" className={className}>
      {children}
    </div>
  ),
}));

// Mock cn utility
vi.mock("@/lib/utils", () => ({
  cn: (...args: (string | undefined | false | null)[]) =>
    args.filter(Boolean).join(" "),
}));

describe("DeckCardSkeleton", () => {
  it("should render with animate-pulse class", () => {
    render(<DeckCardSkeleton />);
    const card = screen.getByTestId("card");
    expect(card.className).toContain("animate-pulse");
  });

  it("should render card header section", () => {
    render(<DeckCardSkeleton />);
    expect(screen.getByTestId("card-header")).toBeInTheDocument();
  });

  it("should render card content section", () => {
    render(<DeckCardSkeleton />);
    expect(screen.getByTestId("card-content")).toBeInTheDocument();
  });

  it("should render card footer section", () => {
    render(<DeckCardSkeleton />);
    expect(screen.getByTestId("card-footer")).toBeInTheDocument();
  });

  it("should render title placeholder in header", () => {
    render(<DeckCardSkeleton />);
    const header = screen.getByTestId("card-header");
    const titlePlaceholder = header.querySelector(".h-5.w-32");
    expect(titlePlaceholder).toBeInTheDocument();
  });

  it("should render badge placeholder in header", () => {
    render(<DeckCardSkeleton />);
    const header = screen.getByTestId("card-header");
    const badgePlaceholder = header.querySelector(".h-5.w-16");
    expect(badgePlaceholder).toBeInTheDocument();
  });

  it("should render 3 featured card image placeholders", () => {
    render(<DeckCardSkeleton />);
    const content = screen.getByTestId("card-content");
    const imagePlaceholders = content.querySelectorAll("[style]");
    expect(imagePlaceholders.length).toBe(3);
  });

  it("should render featured card placeholders with correct dimensions", () => {
    render(<DeckCardSkeleton />);
    const content = screen.getByTestId("card-content");
    const imagePlaceholders = content.querySelectorAll("[style]");
    const firstPlaceholder = imagePlaceholders[0] as HTMLElement;
    expect(firstPlaceholder.style.width).toBe("48px");
    expect(firstPlaceholder.style.height).toBe("67px");
  });

  it("should render 2 button placeholders in footer", () => {
    render(<DeckCardSkeleton />);
    const footer = screen.getByTestId("card-footer");
    const buttonPlaceholders = footer.querySelectorAll(".h-8.flex-1");
    expect(buttonPlaceholders.length).toBe(2);
  });

  it("should accept and apply custom className", () => {
    render(<DeckCardSkeleton className="custom-class" />);
    const card = screen.getByTestId("card");
    expect(card.className).toContain("custom-class");
  });
});

describe("DeckGridSkeleton", () => {
  it("should render 6 skeleton cards by default", () => {
    render(<DeckGridSkeleton />);
    const cards = screen.getAllByTestId("card");
    expect(cards.length).toBe(6);
  });

  it("should render custom number of skeleton cards", () => {
    render(<DeckGridSkeleton count={3} />);
    const cards = screen.getAllByTestId("card");
    expect(cards.length).toBe(3);
  });

  it("should render with grid layout classes", () => {
    const { container } = render(<DeckGridSkeleton />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.className).toContain("grid");
  });

  it("should accept and apply custom className", () => {
    const { container } = render(<DeckGridSkeleton className="custom-grid" />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.className).toContain("custom-grid");
  });

  it("should render 1 skeleton card when count is 1", () => {
    render(<DeckGridSkeleton count={1} />);
    const cards = screen.getAllByTestId("card");
    expect(cards.length).toBe(1);
  });

  it("should render 12 skeleton cards when count is 12", () => {
    render(<DeckGridSkeleton count={12} />);
    const cards = screen.getAllByTestId("card");
    expect(cards.length).toBe(12);
  });
});
