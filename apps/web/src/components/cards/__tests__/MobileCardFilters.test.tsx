import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MobileCardFilters } from "../MobileCardFilters";
import { DEFAULT_FILTERS } from "../CardFilters";
import type { CardFiltersValues } from "../CardFilters";
import type { ApiSet } from "@trainerlab/shared-types";

function createMockSet(overrides: Partial<ApiSet> = {}): ApiSet {
  return {
    id: "sv1",
    name: "Scarlet & Violet",
    series: "Scarlet & Violet",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("MobileCardFilters", () => {
  describe("basic rendering", () => {
    it("should render the Filters trigger button", () => {
      const onChange = vi.fn();
      render(
        <MobileCardFilters values={DEFAULT_FILTERS} onChange={onChange} />
      );

      expect(
        screen.getByRole("button", { name: /filters/i })
      ).toBeInTheDocument();
    });

    it("should render the Filters button text", () => {
      const onChange = vi.fn();
      render(
        <MobileCardFilters values={DEFAULT_FILTERS} onChange={onChange} />
      );

      expect(screen.getByText("Filters")).toBeInTheDocument();
    });
  });

  describe("active filter indicator", () => {
    it("should not show active indicator when no filters are active", () => {
      const onChange = vi.fn();
      const { container } = render(
        <MobileCardFilters values={DEFAULT_FILTERS} onChange={onChange} />
      );

      // The active indicator is a small rounded dot
      const dot = container.querySelector(".rounded-full.bg-primary");
      expect(dot).not.toBeInTheDocument();
    });

    it("should show active indicator when supertype filter is set", () => {
      const onChange = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        supertype: "Pokemon",
      };
      const { container } = render(
        <MobileCardFilters values={values} onChange={onChange} />
      );

      const dot = container.querySelector(".rounded-full.bg-primary");
      expect(dot).toBeInTheDocument();
    });

    it("should show active indicator when types filter is set", () => {
      const onChange = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        types: "Fire",
      };
      const { container } = render(
        <MobileCardFilters values={values} onChange={onChange} />
      );

      const dot = container.querySelector(".rounded-full.bg-primary");
      expect(dot).toBeInTheDocument();
    });

    it("should show active indicator when set_id filter is set", () => {
      const onChange = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        set_id: "sv1",
      };
      const { container } = render(
        <MobileCardFilters values={values} onChange={onChange} />
      );

      const dot = container.querySelector(".rounded-full.bg-primary");
      expect(dot).toBeInTheDocument();
    });

    it("should show active indicator when standard_legal filter is set", () => {
      const onChange = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        standard_legal: "standard",
      };
      const { container } = render(
        <MobileCardFilters values={values} onChange={onChange} />
      );

      const dot = container.querySelector(".rounded-full.bg-primary");
      expect(dot).toBeInTheDocument();
    });
  });

  describe("sheet content", () => {
    it("should open sheet with title and description when button is clicked", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(
        <MobileCardFilters values={DEFAULT_FILTERS} onChange={onChange} />
      );

      const button = screen.getByRole("button", { name: /filters/i });
      await user.click(button);

      expect(screen.getByText("Filter Cards")).toBeInTheDocument();
      expect(
        screen.getByText("Narrow down your card search")
      ).toBeInTheDocument();
    });
  });

  describe("props forwarding", () => {
    it("should render without crashing when sets are provided", () => {
      const onChange = vi.fn();
      const sets = [
        createMockSet({ id: "sv1", name: "Scarlet & Violet" }),
        createMockSet({ id: "sv2", name: "Paldea Evolved" }),
      ];
      render(
        <MobileCardFilters
          values={DEFAULT_FILTERS}
          onChange={onChange}
          sets={sets}
        />
      );

      expect(
        screen.getByRole("button", { name: /filters/i })
      ).toBeInTheDocument();
    });

    it("should render without crashing when onClear is provided", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      render(
        <MobileCardFilters
          values={DEFAULT_FILTERS}
          onChange={onChange}
          onClear={onClear}
        />
      );

      expect(
        screen.getByRole("button", { name: /filters/i })
      ).toBeInTheDocument();
    });
  });
});
