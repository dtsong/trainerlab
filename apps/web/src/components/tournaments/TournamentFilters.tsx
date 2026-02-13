"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  MAJOR_FORMAT_FILTER_OPTIONS,
  SEASON_FILTER_OPTIONS,
  type MajorFormatFilterValue,
  type SeasonFilterValue,
} from "@/lib/official-majors";

interface TournamentFiltersProps {
  format: "standard" | "expanded" | "all";
  majorFormatKey: MajorFormatFilterValue;
  season: SeasonFilterValue;
  onFormatChange: (format: "standard" | "expanded" | "all") => void;
  onMajorFormatChange: (majorFormatKey: MajorFormatFilterValue) => void;
  onSeasonChange: (season: SeasonFilterValue) => void;
  showMajorFilters?: boolean;
}

const formats = [
  { value: "all", label: "All Formats" },
  { value: "standard", label: "Standard" },
  { value: "expanded", label: "Expanded" },
];

export function TournamentFilters({
  format,
  majorFormatKey,
  season,
  onFormatChange,
  onMajorFormatChange,
  onSeasonChange,
  showMajorFilters = false,
}: TournamentFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
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

      {showMajorFilters && (
        <>
          <Select
            value={majorFormatKey}
            onValueChange={(value) =>
              onMajorFormatChange(value as MajorFormatFilterValue)
            }
          >
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Major Window" />
            </SelectTrigger>
            <SelectContent>
              {MAJOR_FORMAT_FILTER_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={season}
            onValueChange={(value) =>
              onSeasonChange(value as SeasonFilterValue)
            }
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Season" />
            </SelectTrigger>
            <SelectContent>
              {SEASON_FILTER_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </>
      )}
    </div>
  );
}
