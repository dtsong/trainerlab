import React from "react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LabNoteTypeFilter } from "../LabNoteTypeFilter";

// Mock pointer capture and scroll APIs for Radix UI compatibility in jsdom
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn().mockReturnValue(false);
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
  HTMLElement.prototype.scrollIntoView = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});

describe("LabNoteTypeFilter", () => {
  it("should render with 'All Types' when value is 'all'", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="all" onChange={onChange} />);

    expect(screen.getByText("All Types")).toBeInTheDocument();
  });

  it("should display 'Weekly Report' when selected", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="weekly_report" onChange={onChange} />);

    expect(screen.getByText("Weekly Report")).toBeInTheDocument();
  });

  it("should display 'JP Dispatch' when selected", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="jp_dispatch" onChange={onChange} />);

    expect(screen.getByText("JP Dispatch")).toBeInTheDocument();
  });

  it("should display 'Set Analysis' when selected", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="set_analysis" onChange={onChange} />);

    expect(screen.getByText("Set Analysis")).toBeInTheDocument();
  });

  it("should display 'Rotation Preview' when selected", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="rotation_preview" onChange={onChange} />);

    expect(screen.getByText("Rotation Preview")).toBeInTheDocument();
  });

  it("should display 'Tournament Recap' when selected", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="tournament_recap" onChange={onChange} />);

    expect(screen.getByText("Tournament Recap")).toBeInTheDocument();
  });

  it("should display 'Tournament Preview' when selected", () => {
    const onChange = vi.fn();
    render(
      <LabNoteTypeFilter value="tournament_preview" onChange={onChange} />
    );

    expect(screen.getByText("Tournament Preview")).toBeInTheDocument();
  });

  it("should display 'Archetype Evolution' when selected", () => {
    const onChange = vi.fn();
    render(
      <LabNoteTypeFilter value="archetype_evolution" onChange={onChange} />
    );

    expect(screen.getByText("Archetype Evolution")).toBeInTheDocument();
  });

  it("should call onChange when a type is selected", async () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="all" onChange={onChange} />);

    // Open the dropdown
    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Select JP Dispatch
    const option = await screen.findByText("JP Dispatch");
    fireEvent.click(option);

    expect(onChange).toHaveBeenCalledWith("jp_dispatch");
  });

  it("should update displayed value when props change", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <LabNoteTypeFilter value="all" onChange={onChange} />
    );

    expect(screen.getByText("All Types")).toBeInTheDocument();

    rerender(<LabNoteTypeFilter value="set_analysis" onChange={onChange} />);

    expect(screen.getByText("Set Analysis")).toBeInTheDocument();
  });

  it("should render the select trigger as a combobox", () => {
    const onChange = vi.fn();
    render(<LabNoteTypeFilter value="all" onChange={onChange} />);

    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });
});
