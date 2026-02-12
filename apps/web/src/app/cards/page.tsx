"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCards } from "@/hooks/useCards";
import { useSets } from "@/hooks/useSets";
import {
  CardGrid,
  CardGridSkeleton,
  CardFiltersSkeleton,
  CardSearchInput,
  CardFilters,
  MobileCardFilters,
  DEFAULT_FILTERS,
  type CardFiltersValues,
} from "@/components/cards";
import { Button } from "@/components/ui/button";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
  parseIntParam,
  parseStringParam,
} from "@/lib/url-state";

const DEFAULT_PAGE_SIZE = 20;
const LEGALITY_VALUES = ["all", "standard", "expanded"] as const;

function isSameFilters(a: CardFiltersValues, b: CardFiltersValues): boolean {
  return (
    a.supertype === b.supertype &&
    a.types === b.types &&
    a.set_id === b.set_id &&
    a.standard_legal === b.standard_legal
  );
}

export default function CardsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const urlSearch = parseStringParam(searchParams.get("q"), {
    defaultValue: "",
  });
  const urlPage = parseIntParam(searchParams.get("page"), {
    defaultValue: 1,
    min: 1,
  });
  const urlFilters: CardFiltersValues = {
    supertype: parseStringParam(searchParams.get("supertype"), {
      defaultValue: DEFAULT_FILTERS.supertype,
    }),
    types: parseStringParam(searchParams.get("types"), {
      defaultValue: DEFAULT_FILTERS.types,
    }),
    set_id: parseStringParam(searchParams.get("set_id"), {
      defaultValue: DEFAULT_FILTERS.set_id,
    }),
    standard_legal: parseEnumParam(
      searchParams.get("standard_legal"),
      LEGALITY_VALUES,
      DEFAULT_FILTERS.standard_legal
    ),
  };

  const [search, setSearch] = useState(urlSearch);
  const [page, setPage] = useState(urlPage);
  const [filters, setFilters] = useState<CardFiltersValues>(urlFilters);

  useEffect(() => {
    if (search !== urlSearch) {
      setSearch(urlSearch);
    }
  }, [search, urlSearch]);

  useEffect(() => {
    if (page !== urlPage) {
      setPage(urlPage);
    }
  }, [page, urlPage]);

  useEffect(() => {
    if (!isSameFilters(filters, urlFilters)) {
      setFilters(urlFilters);
    }
  }, [filters, urlFilters]);

  const { data: setsData, isLoading: setsLoading } = useSets();

  const updateUrl = useCallback(
    (
      updates: Partial<
        CardFiltersValues & {
          q: string;
          page: number;
        }
      >,
      navigationMode: "replace" | "push" = "replace"
    ) => {
      const query = mergeSearchParams(searchParams, updates, {
        q: "",
        page: 1,
        supertype: DEFAULT_FILTERS.supertype,
        types: DEFAULT_FILTERS.types,
        set_id: DEFAULT_FILTERS.set_id,
        standard_legal: DEFAULT_FILTERS.standard_legal,
      });
      const href = buildPathWithQuery("/cards", query);
      if (navigationMode === "push") {
        router.push(href, { scroll: false });
        return;
      }
      router.replace(href, { scroll: false });
    },
    [router, searchParams]
  );

  const cardSearchParams = {
    q: search || undefined,
    supertype: filters.supertype !== "all" ? filters.supertype : undefined,
    types: filters.types !== "all" ? filters.types : undefined,
    set_id: filters.set_id !== "all" ? filters.set_id : undefined,
    standard: filters.standard_legal === "standard" ? true : undefined,
    expanded: filters.standard_legal === "expanded" ? true : undefined,
    page,
    limit: DEFAULT_PAGE_SIZE,
  };

  const { data, isLoading, isError, error } = useCards(cardSearchParams);

  const handleSearchChange = useCallback(
    (value: string) => {
      setSearch(value);
      setPage(1); // Reset to first page on search change
      updateUrl({ q: value, page: 1 }, "replace");
    },
    [updateUrl]
  );

  const handleFilterChange = useCallback(
    (key: keyof CardFiltersValues, value: string) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
      setPage(1); // Reset to first page on filter change
      updateUrl({ [key]: value, page: 1 }, "replace");
    },
    [updateUrl]
  );

  const handleClearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
    updateUrl({ ...DEFAULT_FILTERS, page: 1 }, "replace");
  }, [updateUrl]);

  const handlePrevPage = () => {
    const nextPage = Math.max(1, page - 1);
    setPage(nextPage);
    updateUrl({ page: nextPage }, "push");
  };
  const handleNextPage = () => {
    if (data && page < data.total_pages) {
      const nextPage = page + 1;
      setPage(nextPage);
      updateUrl({ page: nextPage }, "push");
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
        <div className="flex gap-2 items-center">
          <CardSearchInput
            value={search}
            onChange={handleSearchChange}
            placeholder="Search by card name..."
            className="max-w-md flex-1"
          />
          {/* Mobile filter button */}
          {!setsLoading && (
            <MobileCardFilters
              values={filters}
              onChange={handleFilterChange}
              onClear={handleClearFilters}
              sets={setsData}
            />
          )}
        </div>
        {/* Desktop filters */}
        <div className="hidden md:block">
          {setsLoading ? (
            <CardFiltersSkeleton />
          ) : (
            <CardFilters
              values={filters}
              onChange={handleFilterChange}
              onClear={handleClearFilters}
              sets={setsData}
            />
          )}
        </div>
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
