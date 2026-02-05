import React from "react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CardFilters, DEFAULT_FILTERS } from "../CardFilters";
import type { CardFiltersValues } from "../CardFilters";
import type { ApiSet } from "@trainerlab/shared-types";

// Mock pointer capture and scroll APIs for Radix UI compatibility in jsdom
beforeAll(() => {
  HTMLElement.prototype.hasPointerCapture = vi.fn().mockReturnValue(false);
  HTMLElement.prototype.setPointerCapture = vi.fn();
  HTMLElement.prototype.releasePointerCapture = vi.fn();
  HTMLElement.prototype.scrollIntoView = vi.fn();
  Element.prototype.scrollIntoView = vi.fn();
});

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

describe("CardFilters", () => {
  describe("basic rendering", () => {
    it("should render all four filter dropdowns", () => {
      const onChange = vi.fn();
      render(<CardFilters values={DEFAULT_FILTERS} onChange={onChange} />);

      expect(
        screen.getByRole("combobox", { name: /filter by card type/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("combobox", { name: /filter by energy type/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("combobox", { name: /filter by set/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("combobox", { name: /filter by format/i })
      ).toBeInTheDocument();
    });

    it("should accept custom className", () => {
      const onChange = vi.fn();
      const { container } = render(
        <CardFilters
          values={DEFAULT_FILTERS}
          onChange={onChange}
          className="custom-filters"
        />
      );

      expect(container.firstChild).toHaveClass("custom-filters");
    });
  });

  describe("clear filters button", () => {
    it("should not show clear button when all filters are default", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      render(
        <CardFilters
          values={DEFAULT_FILTERS}
          onChange={onChange}
          onClear={onClear}
        />
      );

      expect(
        screen.queryByRole("button", { name: /clear filters/i })
      ).not.toBeInTheDocument();
    });

    it("should show clear button when a filter is active", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        supertype: "Pokemon",
      };
      render(
        <CardFilters values={values} onChange={onChange} onClear={onClear} />
      );

      expect(
        screen.getByRole("button", { name: /clear filters/i })
      ).toBeInTheDocument();
    });

    it("should not show clear button when onClear is not provided even with active filters", () => {
      const onChange = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        supertype: "Pokemon",
      };
      render(<CardFilters values={values} onChange={onChange} />);

      expect(
        screen.queryByRole("button", { name: /clear filters/i })
      ).not.toBeInTheDocument();
    });

    it("should call onClear when clear button is clicked", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      const onClear = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        types: "Fire",
      };
      render(
        <CardFilters values={values} onChange={onChange} onClear={onClear} />
      );

      const clearButton = screen.getByRole("button", {
        name: /clear filters/i,
      });
      await user.click(clearButton);

      expect(onClear).toHaveBeenCalledTimes(1);
    });
  });

  describe("active filter detection", () => {
    it("should detect active supertype filter", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        supertype: "Pokemon",
      };
      render(
        <CardFilters values={values} onChange={onChange} onClear={onClear} />
      );

      expect(
        screen.getByRole("button", { name: /clear filters/i })
      ).toBeInTheDocument();
    });

    it("should detect active types filter", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        types: "Lightning",
      };
      render(
        <CardFilters values={values} onChange={onChange} onClear={onClear} />
      );

      expect(
        screen.getByRole("button", { name: /clear filters/i })
      ).toBeInTheDocument();
    });

    it("should detect active set_id filter", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        set_id: "sv1",
      };
      render(
        <CardFilters values={values} onChange={onChange} onClear={onClear} />
      );

      expect(
        screen.getByRole("button", { name: /clear filters/i })
      ).toBeInTheDocument();
    });

    it("should detect active standard_legal filter", () => {
      const onChange = vi.fn();
      const onClear = vi.fn();
      const values: CardFiltersValues = {
        ...DEFAULT_FILTERS,
        standard_legal: "standard",
      };
      render(
        <CardFilters values={values} onChange={onChange} onClear={onClear} />
      );

      expect(
        screen.getByRole("button", { name: /clear filters/i })
      ).toBeInTheDocument();
    });
  });

  describe("filter selection callbacks", () => {
    it("should call onChange with supertype when supertype filter is changed", async () => {
      const onChange = vi.fn();
      render(<CardFilters values={DEFAULT_FILTERS} onChange={onChange} />);

      const supertypeTrigger = screen.getByRole("combobox", {
        name: /filter by card type/i,
      });
      fireEvent.click(supertypeTrigger);

      const option = await screen.findByText("Pokemon");
      fireEvent.click(option);

      expect(onChange).toHaveBeenCalledWith("supertype", "Pokemon");
    });

    it("should call onChange with types when energy type filter is changed", async () => {
      const onChange = vi.fn();
      render(<CardFilters values={DEFAULT_FILTERS} onChange={onChange} />);

      const energyTrigger = screen.getByRole("combobox", {
        name: /filter by energy type/i,
      });
      fireEvent.click(energyTrigger);

      const option = await screen.findByText("Fire");
      fireEvent.click(option);

      expect(onChange).toHaveBeenCalledWith("types", "Fire");
    });

    it("should call onChange with set_id when set filter is changed", async () => {
      const onChange = vi.fn();
      const sets: ApiSet[] = [
        createMockSet({ id: "sv1", name: "Scarlet & Violet" }),
      ];
      render(
        <CardFilters values={DEFAULT_FILTERS} onChange={onChange} sets={sets} />
      );

      const setTrigger = screen.getByRole("combobox", {
        name: /filter by set/i,
      });
      fireEvent.click(setTrigger);

      const option = await screen.findByText("Scarlet & Violet");
      fireEvent.click(option);

      expect(onChange).toHaveBeenCalledWith("set_id", "sv1");
    });

    it("should call onChange with standard_legal when format filter is changed", async () => {
      const onChange = vi.fn();
      render(<CardFilters values={DEFAULT_FILTERS} onChange={onChange} />);

      const formatTrigger = screen.getByRole("combobox", {
        name: /filter by format/i,
      });
      fireEvent.click(formatTrigger);

      const option = await screen.findByText("Standard Legal");
      fireEvent.click(option);

      expect(onChange).toHaveBeenCalledWith("standard_legal", "standard");
    });
  });

  describe("DEFAULT_FILTERS export", () => {
    it("should have all values set to 'all'", () => {
      expect(DEFAULT_FILTERS).toEqual({
        supertype: "all",
        types: "all",
        set_id: "all",
        standard_legal: "all",
      });
    });
  });
});
