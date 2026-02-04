import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FilterBar, type FilterBarProps } from "../FilterBar";

// Mock PillToggle to make it testable without internal implementation details
vi.mock("@/components/ui/pill-toggle", () => ({
  PillToggle: ({
    options,
    value,
    onChange,
  }: {
    options: { value: string; label: string }[];
    value: string;
    onChange: (value: string) => void;
  }) => (
    <div data-testid="pill-toggle">
      {options.map((opt) => (
        <button
          key={opt.value}
          aria-pressed={opt.value === value}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  ),
}));

describe("FilterBar", () => {
  const defaultProps: FilterBarProps = {
    format: "standard",
    region: "global",
    period: "week",
    onFormatChange: vi.fn(),
    onRegionChange: vi.fn(),
    onPeriodChange: vi.fn(),
  };

  it("should render all three filter labels", () => {
    render(<FilterBar {...defaultProps} />);

    expect(screen.getByText("Format")).toBeInTheDocument();
    expect(screen.getByText("Region")).toBeInTheDocument();
    expect(screen.getByText("Period")).toBeInTheDocument();
  });

  it("should render format options", () => {
    render(<FilterBar {...defaultProps} />);

    expect(screen.getByText("Standard")).toBeInTheDocument();
    expect(screen.getByText("Expanded")).toBeInTheDocument();
  });

  it("should render region options", () => {
    render(<FilterBar {...defaultProps} />);

    expect(screen.getByText("Global")).toBeInTheDocument();
    expect(screen.getByText("NA")).toBeInTheDocument();
    expect(screen.getByText("EU")).toBeInTheDocument();
    expect(screen.getByText("JP")).toBeInTheDocument();
    expect(screen.getByText("LATAM")).toBeInTheDocument();
    expect(screen.getByText("APAC")).toBeInTheDocument();
  });

  it("should render period options", () => {
    render(<FilterBar {...defaultProps} />);

    expect(screen.getByText("Week")).toBeInTheDocument();
    expect(screen.getByText("Month")).toBeInTheDocument();
    expect(screen.getByText("Season")).toBeInTheDocument();
  });

  it("should call onFormatChange when format is clicked", async () => {
    const onFormatChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar {...defaultProps} onFormatChange={onFormatChange} />);

    await user.click(screen.getByText("Expanded"));

    expect(onFormatChange).toHaveBeenCalledWith("expanded");
  });

  it("should call onRegionChange when region is clicked", async () => {
    const onRegionChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar {...defaultProps} onRegionChange={onRegionChange} />);

    await user.click(screen.getByText("EU"));

    expect(onRegionChange).toHaveBeenCalledWith("EU");
  });

  it("should call onPeriodChange when period is clicked", async () => {
    const onPeriodChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar {...defaultProps} onPeriodChange={onPeriodChange} />);

    await user.click(screen.getByText("Month"));

    expect(onPeriodChange).toHaveBeenCalledWith("month");
  });

  it("should show the current format as selected", () => {
    render(<FilterBar {...defaultProps} format="standard" />);

    const standardBtn = screen.getByText("Standard");
    expect(standardBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("should show the current region as selected", () => {
    render(<FilterBar {...defaultProps} region="JP" />);

    const jpBtn = screen.getByText("JP");
    expect(jpBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("should show the current period as selected", () => {
    render(<FilterBar {...defaultProps} period="season" />);

    const seasonBtn = screen.getByText("Season");
    expect(seasonBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("should apply custom className", () => {
    const { container } = render(
      <FilterBar {...defaultProps} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass("custom-class");
  });
});
