import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrendArrow } from "../trend-arrow";

describe("TrendArrow", () => {
  describe("direction rendering", () => {
    it("should render up arrow for 'up' direction", () => {
      render(<TrendArrow direction="up" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("text-signal-up");
      expect(screen.getByTestId("trend-arrow-up")).toBeInTheDocument();
    });

    it("should render down arrow for 'down' direction", () => {
      render(<TrendArrow direction="down" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("text-signal-down");
      expect(screen.getByTestId("trend-arrow-down")).toBeInTheDocument();
    });

    it("should render stable indicator for 'stable' direction", () => {
      render(<TrendArrow direction="stable" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("text-signal-stable");
      expect(screen.getByTestId("trend-arrow-stable")).toBeInTheDocument();
    });
  });

  describe("value display", () => {
    it("should display positive percentage value with plus sign", () => {
      render(<TrendArrow direction="up" value={5} />);
      expect(screen.getByText("+5%")).toBeInTheDocument();
    });

    it("should display negative percentage value with minus sign", () => {
      render(<TrendArrow direction="down" value={-3} />);
      expect(screen.getByText("-3%")).toBeInTheDocument();
    });

    it("should display negative value even when direction is down", () => {
      render(<TrendArrow direction="down" value={7} />);
      expect(screen.getByText("-7%")).toBeInTheDocument();
    });

    it("should display positive value even when direction is up", () => {
      render(<TrendArrow direction="up" value={-2} />);
      expect(screen.getByText("+2%")).toBeInTheDocument();
    });

    it("should format decimal values", () => {
      render(<TrendArrow direction="up" value={2.5} />);
      expect(screen.getByText("+2.5%")).toBeInTheDocument();
    });

    it("should not display value when not provided", () => {
      render(<TrendArrow direction="up" />);
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });
  });

  describe("size variants", () => {
    it("should render small size by default", () => {
      render(<TrendArrow direction="up" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("gap-0.5");
    });

    it("should render small size when size='sm'", () => {
      render(<TrendArrow direction="up" size="sm" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("gap-0.5");
    });

    it("should render medium size when size='md'", () => {
      render(<TrendArrow direction="up" size="md" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("gap-1");
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      render(<TrendArrow direction="up" className="custom-class" />);
      const arrow = screen.getByTestId("trend-arrow");
      expect(arrow).toHaveClass("custom-class");
    });
  });

  describe("input validation", () => {
    it("should not display value when value is NaN", () => {
      render(<TrendArrow direction="up" value={NaN} />);
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    it("should not display value when value is Infinity", () => {
      render(<TrendArrow direction="up" value={Infinity} />);
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    it("should not display value when value is negative Infinity", () => {
      render(<TrendArrow direction="down" value={-Infinity} />);
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    it("should still render arrow when value is invalid", () => {
      render(<TrendArrow direction="up" value={NaN} />);
      expect(screen.getByTestId("trend-arrow-up")).toBeInTheDocument();
    });
  });
});
