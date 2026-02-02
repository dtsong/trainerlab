import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SectionLabel } from "../section-label";

describe("SectionLabel", () => {
  describe("basic rendering", () => {
    it("should render label text", () => {
      render(<SectionLabel label="Meta Breakdown" />);
      expect(screen.getByText("META BREAKDOWN")).toBeInTheDocument();
    });

    it("should render label in uppercase", () => {
      render(<SectionLabel label="deck analysis" />);
      expect(screen.getByText("DECK ANALYSIS")).toBeInTheDocument();
    });

    it("should apply monospace font styling", () => {
      render(<SectionLabel label="Test" />);
      const label = screen.getByTestId("section-label");
      expect(label).toHaveClass("font-mono");
    });

    it("should have tracking-wide class", () => {
      render(<SectionLabel label="Test" />);
      const label = screen.getByTestId("section-label");
      expect(label).toHaveClass("tracking-wide");
    });
  });

  describe("icon rendering", () => {
    it("should render without icon when not provided", () => {
      render(<SectionLabel label="Test" />);
      expect(
        screen.queryByTestId("section-label-icon"),
      ).not.toBeInTheDocument();
    });

    it("should render with icon when provided", () => {
      const icon = <span data-testid="custom-icon">🎯</span>;
      render(<SectionLabel label="Test" icon={icon} />);
      expect(screen.getByTestId("section-label-icon")).toBeInTheDocument();
      expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
    });
  });

  describe("divider", () => {
    it("should render horizontal divider", () => {
      render(<SectionLabel label="Test" />);
      expect(screen.getByTestId("section-label-divider")).toBeInTheDocument();
    });

    it("should have flex-grow on divider to fill remaining space", () => {
      render(<SectionLabel label="Test" />);
      const divider = screen.getByTestId("section-label-divider");
      expect(divider).toHaveClass("flex-grow");
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      render(<SectionLabel label="Test" className="custom-class" />);
      const label = screen.getByTestId("section-label");
      expect(label).toHaveClass("custom-class");
    });
  });
});
