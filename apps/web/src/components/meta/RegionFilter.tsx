"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Region } from "@trainerlab/shared-types";

interface RegionFilterProps {
  value: Region;
  onChange: (value: Region) => void;
  className?: string;
}

const REGIONS: { value: Region; label: string; flag: string }[] = [
  { value: "global", label: "Global", flag: "🌍" },
  { value: "NA", label: "North America", flag: "🇺🇸" },
  { value: "EU", label: "Europe", flag: "🇪🇺" },
  { value: "JP", label: "Japan", flag: "🇯🇵" },
  { value: "LATAM", label: "Latin America", flag: "🌎" },
  { value: "OCE", label: "Oceania", flag: "🇦🇺" },
];

export function RegionFilter({
  value,
  onChange,
  className,
}: RegionFilterProps) {
  const selectedRegion = REGIONS.find((r) => r.value === value);

  return (
    <Select value={value} onValueChange={(v) => onChange(v as Region)}>
      <SelectTrigger className={className} data-testid="region-filter">
        <SelectValue>
          {selectedRegion && (
            <span className="flex items-center gap-2">
              <span>{selectedRegion.flag}</span>
              <span>{selectedRegion.label}</span>
            </span>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {REGIONS.map((region) => (
          <SelectItem key={region.value} value={region.value}>
            <span className="flex items-center gap-2">
              <span>{region.flag}</span>
              <span>{region.label}</span>
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
