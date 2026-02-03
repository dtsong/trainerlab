import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DataTable } from "../DataTable";
import type { Column, SortState } from "../DataTable";

interface TestRow {
  id: string;
  name: string;
  value: number;
}

const testData: TestRow[] = [
  { id: "1", name: "Alpha", value: 10 },
  { id: "2", name: "Beta", value: 20 },
];

const sortableColumns: Column<TestRow>[] = [
  { key: "name", header: "Name", render: (row) => row.name, sortable: true },
  {
    key: "value",
    header: "Value",
    render: (row) => String(row.value),
    sortable: true,
  },
];

const mixedColumns: Column<TestRow>[] = [
  { key: "name", header: "Name", render: (row) => row.name, sortable: true },
  { key: "value", header: "Value", render: (row) => String(row.value) },
];

const baseProps = {
  data: testData,
  page: 1,
  totalPages: 1,
  onPageChange: vi.fn(),
  rowKey: (row: TestRow) => row.id,
};

describe("DataTable sorting", () => {
  it("renders sort icons only on sortable columns", () => {
    const sort: SortState = { key: "name", direction: "asc" };

    render(
      <DataTable
        {...baseProps}
        columns={mixedColumns}
        sort={sort}
        onSortChange={vi.fn()}
      />
    );

    const headers = screen.getAllByRole("columnheader");
    // "Name" header (sortable, active asc) should have ArrowUp icon
    expect(headers[0].querySelector("svg")).toBeInTheDocument();
    // "Value" header (not sortable) should have no icon
    expect(headers[1].querySelector("svg")).toBeNull();
  });

  it("shows ArrowUp for active ascending sort", () => {
    const sort: SortState = { key: "name", direction: "asc" };

    const { container } = render(
      <DataTable
        {...baseProps}
        columns={sortableColumns}
        sort={sort}
        onSortChange={vi.fn()}
      />
    );

    // Active column (name) should have ArrowUp (lucide uses class names)
    const nameHeader = screen.getByText("Name").closest("th")!;
    const svg = nameHeader.querySelector("svg")!;
    expect(svg).toBeInTheDocument();

    // Inactive column (value) should have ArrowUpDown (opacity-40 on svg)
    const valueHeader = screen.getByText("Value").closest("th")!;
    const valueSvg = valueHeader.querySelector("svg")!;
    expect(valueSvg).toHaveClass("opacity-40");
  });

  it("shows ArrowDown for active descending sort", () => {
    const sort: SortState = { key: "name", direction: "desc" };

    render(
      <DataTable
        {...baseProps}
        columns={sortableColumns}
        sort={sort}
        onSortChange={vi.fn()}
      />
    );

    const nameHeader = screen.getByText("Name").closest("th")!;
    const svg = nameHeader.querySelector("svg")!;
    expect(svg).toBeInTheDocument();
  });

  it("calls onSortChange with ascending when clicking inactive column", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const sort: SortState = { key: "name", direction: "asc" };

    render(
      <DataTable
        {...baseProps}
        columns={sortableColumns}
        sort={sort}
        onSortChange={onSortChange}
      />
    );

    // Click inactive "Value" column
    await user.click(screen.getByText("Value").closest("th")!);

    expect(onSortChange).toHaveBeenCalledWith({
      key: "value",
      direction: "asc",
    });
  });

  it("toggles to descending when clicking active ascending column", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const sort: SortState = { key: "name", direction: "asc" };

    render(
      <DataTable
        {...baseProps}
        columns={sortableColumns}
        sort={sort}
        onSortChange={onSortChange}
      />
    );

    // Click active "Name" column (currently asc -> should become desc)
    await user.click(screen.getByText("Name").closest("th")!);

    expect(onSortChange).toHaveBeenCalledWith({
      key: "name",
      direction: "desc",
    });
  });

  it("toggles to ascending when clicking active descending column", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const sort: SortState = { key: "name", direction: "desc" };

    render(
      <DataTable
        {...baseProps}
        columns={sortableColumns}
        sort={sort}
        onSortChange={onSortChange}
      />
    );

    await user.click(screen.getByText("Name").closest("th")!);

    expect(onSortChange).toHaveBeenCalledWith({
      key: "name",
      direction: "asc",
    });
  });

  it("does not trigger sort on non-sortable column click", async () => {
    const user = userEvent.setup();
    const onSortChange = vi.fn();
    const sort: SortState = { key: "name", direction: "asc" };

    render(
      <DataTable
        {...baseProps}
        columns={mixedColumns}
        sort={sort}
        onSortChange={onSortChange}
      />
    );

    // Click non-sortable "Value" column
    await user.click(screen.getByText("Value").closest("th")!);

    expect(onSortChange).not.toHaveBeenCalled();
  });

  it("renders without sort props (backwards compatible)", () => {
    render(<DataTable {...baseProps} columns={sortableColumns} />);

    // Should render without errors, no sort icons since onSortChange is undefined
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();

    // Headers should not have sort icons (no onSortChange)
    const headers = screen.getAllByRole("columnheader");
    expect(headers[0].querySelector("svg")).toBeNull();
    expect(headers[1].querySelector("svg")).toBeNull();
  });
});
