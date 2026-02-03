import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JPSignalBadge } from "../jp-signal-badge";

describe("JPSignalBadge", () => {
  describe("threshold logic", () => {
    it("should render when jpShare > enShare by more than threshold", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={0.05} />);
      expect(screen.getByTestId("jp-signal-badge")).toBeInTheDocument();
    });

    it("should render when jpShare < enShare by more than threshold", () => {
      render(<JPSignalBadge jpShare={0.05} enShare={0.15} />);
      expect(screen.getByTestId("jp-signal-badge")).toBeInTheDocument();
    });

    it("should not render when difference is below threshold", () => {
      render(<JPSignalBadge jpShare={0.1} enShare={0.08} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should not render when difference equals threshold", () => {
      render(<JPSignalBadge jpShare={0.1} enShare={0.05} threshold={0.05} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should render with custom threshold", () => {
      render(<JPSignalBadge jpShare={0.12} enShare={0.1} threshold={0.01} />);
      expect(screen.getByTestId("jp-signal-badge")).toBeInTheDocument();
    });

    it("should use default threshold of 0.05", () => {
      render(<JPSignalBadge jpShare={0.1} enShare={0.04} />);
      expect(screen.getByTestId("jp-signal-badge")).toBeInTheDocument();
    });
  });

  describe("direction display", () => {
    it("should show positive percentage when JP is higher", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={0.05} />);
      expect(screen.getByText("JP +10%")).toBeInTheDocument();
    });

    it("should show negative percentage when JP is lower", () => {
      render(<JPSignalBadge jpShare={0.05} enShare={0.15} />);
      expect(screen.getByText("JP -10%")).toBeInTheDocument();
    });

    it("should round to nearest integer", () => {
      render(<JPSignalBadge jpShare={0.156} enShare={0.05} />);
      expect(screen.getByText("JP +11%")).toBeInTheDocument();
    });

    it("should handle small differences correctly", () => {
      render(<JPSignalBadge jpShare={0.12} enShare={0.05} />);
      expect(screen.getByText("JP +7%")).toBeInTheDocument();
    });
  });

  describe("styling", () => {
    it("should have rose background color", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={0.05} />);
      const badge = screen.getByTestId("jp-signal-badge");
      expect(badge).toHaveClass("bg-signal-jp");
    });

    it("should have white text", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={0.05} />);
      const badge = screen.getByTestId("jp-signal-badge");
      expect(badge).toHaveClass("text-white");
    });
  });

  describe("className handling", () => {
    it("should accept custom className", () => {
      render(
        <JPSignalBadge jpShare={0.15} enShare={0.05} className="custom-class" />
      );
      const badge = screen.getByTestId("jp-signal-badge");
      expect(badge).toHaveClass("custom-class");
    });
  });

  describe("input validation", () => {
    it("should not render when jpShare is NaN", () => {
      render(<JPSignalBadge jpShare={NaN} enShare={0.05} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should not render when enShare is NaN", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={NaN} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should not render when jpShare is Infinity", () => {
      render(<JPSignalBadge jpShare={Infinity} enShare={0.05} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should not render when enShare is negative Infinity", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={-Infinity} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should not render when threshold is negative", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={0.05} threshold={-0.01} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });

    it("should not render when threshold is NaN", () => {
      render(<JPSignalBadge jpShare={0.15} enShare={0.05} threshold={NaN} />);
      expect(screen.queryByTestId("jp-signal-badge")).not.toBeInTheDocument();
    });
  });
});
