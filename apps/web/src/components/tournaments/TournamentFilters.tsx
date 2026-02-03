"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface TournamentFiltersProps {
  region: string;
  format: "standard" | "expanded" | "all";
  tier: "major" | "grassroots";
  onRegionChange: (region: string) => void;
  onFormatChange: (format: "standard" | "expanded" | "all") => void;
  onTierChange: (tier: "major" | "grassroots") => void;
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

const tierOptions = [
  { value: "major" as const, label: "Major" },
  { value: "grassroots" as const, label: "Grassroots" },
];

export function TournamentFilters({
  region,
  format,
  tier,
  onRegionChange,
  onFormatChange,
  onTierChange,
}: TournamentFiltersProps) {
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
          {tierOptions.map((t) => (
            <SelectItem key={t.value} value={t.value}>
              {t.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
