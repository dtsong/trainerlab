"use client";

import { SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  CardFilters,
  type CardFiltersValues,
  DEFAULT_FILTERS,
} from "./CardFilters";
import type { ApiSet } from "@trainerlab/shared-types";

interface MobileCardFiltersProps {
  values: CardFiltersValues;
  onChange: (key: keyof CardFiltersValues, value: string) => void;
  onClear?: () => void;
  sets?: ApiSet[];
}

export function MobileCardFilters({
  values,
  onChange,
  onClear,
  sets,
}: MobileCardFiltersProps) {
  const hasActiveFilters =
    values.supertype !== DEFAULT_FILTERS.supertype ||
    values.types !== DEFAULT_FILTERS.types ||
    values.set_id !== DEFAULT_FILTERS.set_id ||
    values.standard_legal !== DEFAULT_FILTERS.standard_legal;

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="md:hidden">
          <SlidersHorizontal className="h-4 w-4 mr-2" />
          Filters
          {hasActiveFilters && (
            <span className="ml-2 h-2 w-2 rounded-full bg-primary" />
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="h-auto max-h-[80vh]">
        <SheetHeader>
          <SheetTitle>Filter Cards</SheetTitle>
          <SheetDescription>Narrow down your card search</SheetDescription>
        </SheetHeader>
        <div className="py-4">
          <CardFilters
            values={values}
            onChange={onChange}
            onClear={onClear}
            sets={sets}
            className="flex-col items-stretch"
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
