"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { TournamentType } from "@trainerlab/shared-types";

interface TournamentTypeFilterProps {
  value: TournamentType;
  onChange: (value: TournamentType) => void;
  className?: string;
}

const TOURNAMENT_TYPES: { value: TournamentType; label: string }[] = [
  { value: "all", label: "All Tournaments" },
  { value: "official", label: "Official (Regionals/ICs)" },
  { value: "grassroots", label: "Grassroots (Leagues)" },
];

const VALID_TYPES: TournamentType[] = ["all", "official", "grassroots"];

function isValidTournamentType(value: string): value is TournamentType {
  return VALID_TYPES.includes(value as TournamentType);
}

export function TournamentTypeFilter({
  value,
  onChange,
  className,
}: TournamentTypeFilterProps) {
  const handleChange = (newValue: string) => {
    if (isValidTournamentType(newValue)) {
      onChange(newValue);
    }
  };

  const selected = TOURNAMENT_TYPES.find((t) => t.value === value);

  return (
    <Select value={value} onValueChange={handleChange}>
      <SelectTrigger
        className={className}
        data-testid="tournament-type-filter"
        aria-label="Filter by tournament type"
      >
        <SelectValue>{selected?.label}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {TOURNAMENT_TYPES.map((type) => (
          <SelectItem key={type.value} value={type.value}>
            {type.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
