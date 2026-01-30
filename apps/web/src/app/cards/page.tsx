"use client";

import { useState, useCallback } from "react";
import { useCards } from "@/hooks/useCards";
import { useSets } from "@/hooks/useSets";
import {
  CardGrid,
  CardGridSkeleton,
  CardSearchInput,
  CardFilters,
  type CardFiltersValues,
} from "@/components/cards";
import { Button } from "@/components/ui/button";

const DEFAULT_PAGE_SIZE = 20;

export default function CardsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<CardFiltersValues>({
    supertype: "all",
    types: "all",
    set_id: "all",
    standard_legal: "all",
  });

  const { data: setsData } = useSets();

  const searchParams = {
    q: search || undefined,
    supertype: filters.supertype !== "all" ? filters.supertype : undefined,
    types: filters.types !== "all" ? filters.types : undefined,
    set_id: filters.set_id !== "all" ? filters.set_id : undefined,
    standard: filters.standard_legal === "standard" ? true : undefined,
    expanded: filters.standard_legal === "expanded" ? true : undefined,
    page,
    limit: DEFAULT_PAGE_SIZE,
  };

  const { data, isLoading, isError, error } = useCards(searchParams);

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    setPage(1); // Reset to first page on search change
  }, []);

  const handleFilterChange = useCallback(
    (key: keyof CardFiltersValues, value: string) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
      setPage(1); // Reset to first page on filter change
    },
    [],
  );

  const handlePrevPage = () => setPage((p) => Math.max(1, p - 1));
  const handleNextPage = () => {
    if (data && page < data.total_pages) {
      setPage((p) => p + 1);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Card Database</h1>
        <p className="text-muted-foreground">
          Search and browse Pokemon TCG cards
        </p>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4 mb-8">
        <CardSearchInput
          value={search}
          onChange={handleSearchChange}
          placeholder="Search by card name..."
          className="max-w-md"
        />
        <CardFilters
          values={filters}
          onChange={handleFilterChange}
          sets={setsData}
        />
      </div>

      {/* Results Info */}
      {data && (
        <p className="text-sm text-muted-foreground mb-4">
          Showing {data.items.length} of {data.total} cards
          {data.total_pages > 1 &&
            ` (Page ${data.page} of ${data.total_pages})`}
        </p>
      )}

      {/* Error State */}
      {isError && (
        <div className="text-center py-12">
          <p className="text-destructive font-medium">Error loading cards</p>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && <CardGridSkeleton count={DEFAULT_PAGE_SIZE} />}

      {/* Card Grid */}
      {data && !isLoading && <CardGrid cards={data.items} />}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex justify-center gap-4 mt-8">
          <Button
            variant="outline"
            onClick={handlePrevPage}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="flex items-center text-sm text-muted-foreground">
            Page {page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            onClick={handleNextPage}
            disabled={page >= data.total_pages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
