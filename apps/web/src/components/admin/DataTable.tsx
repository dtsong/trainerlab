"use client";

import { useState, ReactNode } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
  expandedRow?: (row: T) => ReactNode;
  rowKey: (row: T) => string;
}

export function DataTable<T>({
  columns,
  data,
  page,
  totalPages,
  onPageChange,
  isLoading,
  expandedRow,
  rowKey,
}: DataTableProps<T>) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  function toggleExpanded(key: string) {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <div>
      <div className="overflow-auto rounded border border-zinc-800">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              {expandedRow && <TableHead className="w-8 text-zinc-500" />}
              {columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={`font-mono text-xs uppercase tracking-wider text-zinc-500 ${col.className ?? ""}`}
                >
                  {col.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow className="border-zinc-800">
                <TableCell
                  colSpan={columns.length + (expandedRow ? 1 : 0)}
                  className="py-8 text-center font-mono text-sm text-zinc-500"
                >
                  Loading...
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow className="border-zinc-800">
                <TableCell
                  colSpan={columns.length + (expandedRow ? 1 : 0)}
                  className="py-8 text-center font-mono text-sm text-zinc-500"
                >
                  No data
                </TableCell>
              </TableRow>
            ) : (
              data.map((row) => {
                const key = rowKey(row);
                const isExpanded = expandedKeys.has(key);
                return (
                  <span key={key} className="contents">
                    <TableRow
                      className={`border-zinc-800 hover:bg-zinc-800/50 ${expandedRow ? "cursor-pointer" : ""}`}
                      onClick={
                        expandedRow ? () => toggleExpanded(key) : undefined
                      }
                    >
                      {expandedRow && (
                        <TableCell className="w-8 font-mono text-xs text-zinc-500">
                          {isExpanded ? "v" : ">"}
                        </TableCell>
                      )}
                      {columns.map((col) => (
                        <TableCell
                          key={col.key}
                          className={`font-mono text-sm text-zinc-300 ${col.className ?? ""}`}
                        >
                          {col.render(row)}
                        </TableCell>
                      ))}
                    </TableRow>
                    {expandedRow && isExpanded && (
                      <TableRow className="border-zinc-800">
                        <TableCell
                          colSpan={columns.length + 1}
                          className="bg-zinc-900/80 p-4"
                        >
                          {expandedRow(row)}
                        </TableCell>
                      </TableRow>
                    )}
                  </span>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between">
          <div className="font-mono text-xs text-zinc-500">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="border-zinc-700 bg-transparent font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
            >
              Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="border-zinc-700 bg-transparent font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
