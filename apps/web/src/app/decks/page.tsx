"use client";

import { Suspense, useState, useMemo, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus, FolderOpen, SortAsc } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DeckCard } from "@/components/deck";
import { useDecks } from "@/hooks/useDecks";
import type { DeckFormat } from "@/types/deck";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseEnumParam,
} from "@/lib/url-state";

type SortOption = "updated" | "created" | "name";
type FilterFormat = "all" | DeckFormat;

function DecksPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const SORT_VALUES = ["updated", "created", "name"] as const;
  const FORMAT_VALUES = ["all", "standard", "expanded"] as const;
  const urlSortBy = parseEnumParam(
    searchParams.get("sort"),
    SORT_VALUES,
    "updated"
  );
  const urlFilterFormat = parseEnumParam(
    searchParams.get("format"),
    FORMAT_VALUES,
    "all"
  );

  const [sortBy, setSortBy] = useState<SortOption>(urlSortBy);
  const [filterFormat, setFilterFormat] =
    useState<FilterFormat>(urlFilterFormat);

  useEffect(() => {
    if (sortBy !== urlSortBy) {
      setSortBy(urlSortBy);
    }
  }, [sortBy, urlSortBy]);

  useEffect(() => {
    if (filterFormat !== urlFilterFormat) {
      setFilterFormat(urlFilterFormat);
    }
  }, [filterFormat, urlFilterFormat]);

  const updateUrl = (updates: { sort?: SortOption; format?: FilterFormat }) => {
    const query = mergeSearchParams(searchParams, updates, {
      sort: "updated",
      format: "all",
    });
    const href = buildPathWithQuery("/decks", query);
    router.replace(href, { scroll: false });
  };

  const { decks, isLoading, loadError } = useDecks();

  const filteredAndSortedDecks = useMemo(() => {
    let result = [...decks];

    // Filter by format
    if (filterFormat !== "all") {
      result = result.filter((deck) => deck.format === filterFormat);
    }

    // Sort
    result.sort((a, b) => {
      switch (sortBy) {
        case "updated":
          return (
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
          );
        case "created":
          return (
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          );
        case "name":
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    return result;
  }, [decks, sortBy, filterFormat]);

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">My Decks</h1>
          <p className="text-muted-foreground">
            Manage your Pokemon TCG deck collection
          </p>
        </div>
        <Button asChild>
          <Link href="/decks/new">
            <Plus className="h-4 w-4 mr-2" />
            New Deck
          </Link>
        </Button>
      </div>

      {/* Filters and Sort */}
      {decks.length > 0 && (
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <SortAsc className="h-4 w-4 text-muted-foreground" />
            <Select
              value={sortBy}
              onValueChange={(value) => {
                const nextSort = value as SortOption;
                setSortBy(nextSort);
                updateUrl({ sort: nextSort });
              }}
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="updated">Last Updated</SelectItem>
                <SelectItem value="created">Date Created</SelectItem>
                <SelectItem value="name">Name</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Select
            value={filterFormat}
            onValueChange={(value) => {
              const nextFormat = value as FilterFormat;
              setFilterFormat(nextFormat);
              updateUrl({ format: nextFormat });
            }}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Formats</SelectItem>
              <SelectItem value="standard">Standard</SelectItem>
              <SelectItem value="expanded">Expanded</SelectItem>
            </SelectContent>
          </Select>

          {filterFormat !== "all" && (
            <span className="text-sm text-muted-foreground">
              {filteredAndSortedDecks.length} deck
              {filteredAndSortedDecks.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-[220px] rounded-lg border bg-muted animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {!isLoading && loadError && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-destructive font-medium mb-2">
            Failed to load decks
          </p>
          <p className="text-muted-foreground mb-4 max-w-md">{loadError}</p>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !loadError && decks.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <FolderOpen className="h-16 w-16 text-muted-foreground mb-4" />
          <h2 className="text-xl font-semibold mb-2">No decks yet</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            Create your first deck to start building your collection. You can
            search for cards, add them to your deck, and export for Pokemon TCG
            Online or Live.
          </p>
          <Button asChild size="lg">
            <Link href="/decks/new">
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Deck
            </Link>
          </Button>
        </div>
      )}

      {/* Filtered Empty State */}
      {!isLoading &&
        decks.length > 0 &&
        filteredAndSortedDecks.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-muted-foreground mb-4">
              No decks match your current filters.
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setFilterFormat("all");
                updateUrl({ format: "all" });
              }}
            >
              Clear Filters
            </Button>
          </div>
        )}

      {/* Deck Grid */}
      {!isLoading && filteredAndSortedDecks.length > 0 && (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredAndSortedDecks.map((deck) => (
            <DeckCard key={deck.id} deck={deck} />
          ))}
        </div>
      )}
    </div>
  );
}

function DecksPageFallback() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">My Decks</h1>
          <p className="text-muted-foreground">
            Manage your Pokemon TCG deck collection
          </p>
        </div>
      </div>
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-[220px] rounded-lg border bg-muted animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}

export default function DecksPage() {
  return (
    <Suspense fallback={<DecksPageFallback />}>
      <DecksPageContent />
    </Suspense>
  );
}
