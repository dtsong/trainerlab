import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TierBadge } from "../tier-badge";

describe("TierBadge", () => {
  describe("tier rendering", () => {
    it("should render S tier with correct color", () => {
      render(<TierBadge tier="S" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveTextContent("S");
      expect(badge).toHaveClass("bg-tier-s");
    });

    it("should render A tier with correct color", () => {
      render(<TierBadge tier="A" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveTextContent("A");
      expect(badge).toHaveClass("bg-tier-a");
    });

    it("should render B tier with correct color", () => {
      render(<TierBadge tier="B" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveTextContent("B");
      expect(badge).toHaveClass("bg-tier-b");
    });

    it("should render C tier with correct color", () => {
      render(<TierBadge tier="C" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveTextContent("C");
      expect(badge).toHaveClass("bg-tier-c");
    });

    it("should render Rogue tier with correct color", () => {
      render(<TierBadge tier="Rogue" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveTextContent("Rogue");
      expect(badge).toHaveClass("bg-tier-rogue");
    });
  });

  describe("size variants", () => {
    it("should render small size by default", () => {
      render(<TierBadge tier="S" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveClass("h-4", "min-w-4", "text-xs");
    });

    it("should render small size when size='sm'", () => {
      render(<TierBadge tier="S" size="sm" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveClass("h-4", "min-w-4", "text-xs");
    });

    it("should render medium size when size='md'", () => {
      render(<TierBadge tier="S" size="md" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveClass("h-6", "min-w-6", "text-sm");
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      render(<TierBadge tier="S" className="custom-class" />);
      const badge = screen.getByTestId("tier-badge");
      expect(badge).toHaveClass("custom-class");
    });
  });
});
