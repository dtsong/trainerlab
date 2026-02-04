import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SurvivalBadge } from "../SurvivalBadge";

import type { SurvivalRating } from "@trainerlab/shared-types";

describe("SurvivalBadge", () => {
  describe("rating labels", () => {
    const cases: { rating: SurvivalRating; label: string }[] = [
      { rating: "dies", label: "Dies" },
      { rating: "crippled", label: "Crippled" },
      { rating: "adapts", label: "Adapts" },
      { rating: "thrives", label: "Thrives" },
      { rating: "unknown", label: "Unknown" },
    ];

    it.each(cases)(
      "should render '$label' text for '$rating' rating",
      ({ rating, label }) => {
        render(<SurvivalBadge rating={rating} />);
        expect(screen.getByText(label)).toBeInTheDocument();
      }
    );
  });

  describe("variant styles", () => {
    it("should apply red styles for 'dies' rating", () => {
      render(<SurvivalBadge rating="dies" />);
      const badge = screen.getByText("Dies");
      expect(badge).toHaveClass("bg-red-500/20", "text-red-400");
    });

    it("should apply orange styles for 'crippled' rating", () => {
      render(<SurvivalBadge rating="crippled" />);
      const badge = screen.getByText("Crippled");
      expect(badge).toHaveClass("bg-orange-500/20", "text-orange-400");
    });

    it("should apply yellow styles for 'adapts' rating", () => {
      render(<SurvivalBadge rating="adapts" />);
      const badge = screen.getByText("Adapts");
      expect(badge).toHaveClass("bg-yellow-500/20", "text-yellow-400");
    });

    it("should apply green styles for 'thrives' rating", () => {
      render(<SurvivalBadge rating="thrives" />);
      const badge = screen.getByText("Thrives");
      expect(badge).toHaveClass("bg-green-500/20", "text-green-400");
    });

    it("should apply slate styles for 'unknown' rating", () => {
      render(<SurvivalBadge rating="unknown" />);
      const badge = screen.getByText("Unknown");
      expect(badge).toHaveClass("bg-slate-500/20", "text-slate-400");
    });
  });

  describe("base styles", () => {
    it("should include base badge classes", () => {
      render(<SurvivalBadge rating="thrives" />);
      const badge = screen.getByText("Thrives");
      expect(badge).toHaveClass(
        "inline-flex",
        "items-center",
        "rounded-md",
        "text-xs",
        "font-semibold"
      );
    });
  });

  describe("className handling", () => {
    it("should accept and merge custom className", () => {
      render(<SurvivalBadge rating="adapts" className="custom-class" />);
      const badge = screen.getByText("Adapts");
      expect(badge).toHaveClass("custom-class");
      // Should still have base classes
      expect(badge).toHaveClass("inline-flex");
    });
  });

  describe("ref forwarding", () => {
    it("should forward ref to the span element", () => {
      const ref = React.createRef<HTMLSpanElement>();
      render(<SurvivalBadge rating="dies" ref={ref} />);
      expect(ref.current).toBeInstanceOf(HTMLSpanElement);
      expect(ref.current?.textContent).toBe("Dies");
    });
  });

  describe("HTML attributes", () => {
    it("should pass through additional HTML attributes", () => {
      render(
        <SurvivalBadge rating="thrives" data-testid="survival" title="info" />
      );
      const badge = screen.getByTestId("survival");
      expect(badge).toHaveAttribute("title", "info");
    });
  });
});
