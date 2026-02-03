import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatBlock } from "../stat-block";

describe("StatBlock", () => {
  describe("basic rendering", () => {
    it("should render value as string", () => {
      render(<StatBlock value="42.5%" label="Win Rate" />);
      expect(screen.getByText("42.5%")).toBeInTheDocument();
    });

    it("should render value as number", () => {
      render(<StatBlock value={1234} label="Total Games" />);
      expect(screen.getByText("1234")).toBeInTheDocument();
    });

    it("should render label text", () => {
      render(<StatBlock value="100" label="Sample Size" />);
      expect(screen.getByText("Sample Size")).toBeInTheDocument();
    });

    it("should apply monospace font to value", () => {
      render(<StatBlock value="42%" label="Rate" />);
      const valueElement = screen.getByText("42%");
      expect(valueElement).toHaveClass("font-mono");
    });

    it("should apply large font size to value", () => {
      render(<StatBlock value="42%" label="Rate" />);
      const valueElement = screen.getByText("42%");
      expect(valueElement).toHaveClass("text-4xl");
    });

    it("should apply muted color to label", () => {
      render(<StatBlock value="42%" label="Rate" />);
      const labelElement = screen.getByText("Rate");
      expect(labelElement).toHaveClass("text-muted-foreground");
    });
  });

  describe("optional subtext", () => {
    it("should not render subtext when not provided", () => {
      render(<StatBlock value="42%" label="Rate" />);
      expect(
        screen.queryByTestId("stat-block-subtext")
      ).not.toBeInTheDocument();
    });

    it("should render subtext when provided", () => {
      render(<StatBlock value="42%" label="Rate" subtext="vs last week" />);
      expect(screen.getByText("vs last week")).toBeInTheDocument();
    });

    it("should apply small styling to subtext", () => {
      render(<StatBlock value="42%" label="Rate" subtext="vs last week" />);
      const subtextElement = screen.getByTestId("stat-block-subtext");
      expect(subtextElement).toHaveClass("text-sm");
    });
  });

  describe("trend integration", () => {
    it("should not render TrendArrow when trend not provided", () => {
      render(<StatBlock value="42%" label="Rate" />);
      expect(screen.queryByTestId("trend-arrow")).not.toBeInTheDocument();
    });

    it("should render TrendArrow when trend is 'up'", () => {
      render(<StatBlock value="42%" label="Rate" trend="up" />);
      expect(screen.getByTestId("trend-arrow")).toBeInTheDocument();
      expect(screen.getByTestId("trend-arrow-up")).toBeInTheDocument();
    });

    it("should render TrendArrow when trend is 'down'", () => {
      render(<StatBlock value="42%" label="Rate" trend="down" />);
      expect(screen.getByTestId("trend-arrow")).toBeInTheDocument();
      expect(screen.getByTestId("trend-arrow-down")).toBeInTheDocument();
    });

    it("should render TrendArrow when trend is 'stable'", () => {
      render(<StatBlock value="42%" label="Rate" trend="stable" />);
      expect(screen.getByTestId("trend-arrow")).toBeInTheDocument();
      expect(screen.getByTestId("trend-arrow-stable")).toBeInTheDocument();
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      render(<StatBlock value="42%" label="Rate" className="custom-class" />);
      const statBlock = screen.getByTestId("stat-block");
      expect(statBlock).toHaveClass("custom-class");
    });
  });
});
