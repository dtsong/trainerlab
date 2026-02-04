import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatCard } from "../StatCard";

describe("StatCard", () => {
  it("renders the label", () => {
    render(<StatCard label="Total Users" value={100} />);

    expect(screen.getByText("Total Users")).toBeInTheDocument();
  });

  it("renders a string value as-is", () => {
    render(<StatCard label="Status" value="Active" />);

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders a numeric value with locale formatting", () => {
    render(<StatCard label="Total Cards" value={12345} />);

    // toLocaleString() formats 12345 -> "12,345" in en-US
    expect(screen.getByText("12,345")).toBeInTheDocument();
  });

  it("renders zero as a valid numeric value", () => {
    render(<StatCard label="Errors" value={0} />);

    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders the detail text when provided", () => {
    render(<StatCard label="Active Decks" value={42} detail="Last 30 days" />);

    expect(screen.getByText("Last 30 days")).toBeInTheDocument();
  });

  it("does not render detail text when not provided", () => {
    render(<StatCard label="Active Decks" value={42} />);

    expect(screen.getByText("Active Decks")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    // Ensure no extra child beyond label and value
    expect(screen.queryByText("Last 30 days")).not.toBeInTheDocument();
  });

  it("handles large numbers with locale formatting", () => {
    render(<StatCard label="Page Views" value={1000000} />);

    expect(screen.getByText("1,000,000")).toBeInTheDocument();
  });

  it("renders an empty string value", () => {
    render(<StatCard label="Status" value="" />);

    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("renders label, value, and detail together", () => {
    render(<StatCard label="Tournaments" value={256} detail="+12 this week" />);

    expect(screen.getByText("Tournaments")).toBeInTheDocument();
    expect(screen.getByText("256")).toBeInTheDocument();
    expect(screen.getByText("+12 this week")).toBeInTheDocument();
  });
});
