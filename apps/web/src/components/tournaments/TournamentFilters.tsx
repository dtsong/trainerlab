"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface TournamentFiltersProps {
  format: "standard" | "expanded" | "all";
  onFormatChange: (format: "standard" | "expanded" | "all") => void;
}

const formats = [
  { value: "all", label: "All Formats" },
  { value: "standard", label: "Standard" },
  { value: "expanded", label: "Expanded" },
];

export function TournamentFilters({
  format,
  onFormatChange,
}: TournamentFiltersProps) {
  return (
    <Select value={format} onValueChange={onFormatChange}>
      <SelectTrigger className="w-[140px]">
        <SelectValue placeholder="Format" />
      </SelectTrigger>
      <SelectContent>
        {formats.map((f) => (
          <SelectItem key={f.value} value={f.value}>
            {f.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
