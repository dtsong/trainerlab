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

interface EventFiltersProps {
  region: string;
  format: "standard" | "expanded" | "all";
  tier: string;
  majorFormatKey: MajorFormatFilterValue;
  season: SeasonFilterValue;
  onRegionChange: (region: string) => void;
  onFormatChange: (format: "standard" | "expanded" | "all") => void;
  onTierChange: (tier: string) => void;
  onMajorFormatChange: (majorFormatKey: MajorFormatFilterValue) => void;
  onSeasonChange: (season: SeasonFilterValue) => void;
}

const regions = [
  { value: "all", label: "All Regions" },
  { value: "NA", label: "North America" },
  { value: "EU", label: "Europe" },
  { value: "JP", label: "Japan" },
  { value: "LATAM", label: "Latin America" },
  { value: "OCE", label: "Oceania" },
];

const formats = [
  { value: "all", label: "All Formats" },
  { value: "standard", label: "Standard" },
  { value: "expanded", label: "Expanded" },
];

const tiers = [
  { value: "all", label: "All Tiers" },
  { value: "major", label: "Major" },
  { value: "premier", label: "Premier" },
  { value: "league", label: "League" },
];

export function EventFilters({
  region,
  format,
  tier,
  majorFormatKey,
  season,
  onRegionChange,
  onFormatChange,
  onTierChange,
  onMajorFormatChange,
  onSeasonChange,
}: EventFiltersProps) {
  return (
    <div className="flex flex-wrap gap-4">
      <Select value={region} onValueChange={onRegionChange}>
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Region" />
        </SelectTrigger>
        <SelectContent>
          {regions.map((r) => (
            <SelectItem key={r.value} value={r.value}>
              {r.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

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

      <Select value={tier} onValueChange={onTierChange}>
        <SelectTrigger className="w-[130px]">
          <SelectValue placeholder="Tier" />
        </SelectTrigger>
        <SelectContent>
          {tiers.map((t) => (
            <SelectItem key={t.value} value={t.value}>
              {t.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

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
        onValueChange={(value) => onSeasonChange(value as SeasonFilterValue)}
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
    </div>
  );
}
