"use client";

import type { ApiSet } from "@trainerlab/shared-types";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Pokemon TCG supertypes
const SUPERTYPES = ["Pokemon", "Trainer", "Energy"] as const;

// Pokemon TCG energy types
const ENERGY_TYPES = [
  "Colorless",
  "Darkness",
  "Dragon",
  "Fairy",
  "Fighting",
  "Fire",
  "Grass",
  "Lightning",
  "Metal",
  "Psychic",
  "Water",
] as const;

export interface CardFiltersValues {
  supertype: string;
  types: string;
  set_id: string;
  standard_legal: string;
}

interface CardFiltersProps {
  values: CardFiltersValues;
  onChange: (key: keyof CardFiltersValues, value: string) => void;
  sets?: ApiSet[];
  className?: string;
}

export function CardFilters({
  values,
  onChange,
  sets = [],
  className,
}: CardFiltersProps) {
  return (
    <div className={cn("flex flex-wrap gap-3", className)}>
      {/* Supertype filter */}
      <Select
        value={values.supertype}
        onValueChange={(v) => onChange("supertype", v)}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          {SUPERTYPES.map((type) => (
            <SelectItem key={type} value={type}>
              {type}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Energy type filter */}
      <Select value={values.types} onValueChange={(v) => onChange("types", v)}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Energy" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Energy</SelectItem>
          {ENERGY_TYPES.map((type) => (
            <SelectItem key={type} value={type}>
              {type}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Set filter */}
      <Select
        value={values.set_id}
        onValueChange={(v) => onChange("set_id", v)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Set" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Sets</SelectItem>
          {sets.map((set) => (
            <SelectItem key={set.id} value={set.id}>
              {set.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Legality filter */}
      <Select
        value={values.standard_legal}
        onValueChange={(v) => onChange("standard_legal", v)}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Format" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Formats</SelectItem>
          <SelectItem value="standard">Standard Legal</SelectItem>
          <SelectItem value="expanded">Expanded Legal</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
