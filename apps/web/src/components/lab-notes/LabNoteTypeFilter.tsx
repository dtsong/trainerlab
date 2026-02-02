"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import type { LabNoteType } from "@trainerlab/shared-types";

interface LabNoteTypeFilterProps {
  value: LabNoteType | "all";
  onChange: (value: LabNoteType | "all") => void;
}

const noteTypes: { value: LabNoteType | "all"; label: string }[] = [
  { value: "all", label: "All Types" },
  { value: "weekly_report", label: "Weekly Report" },
  { value: "jp_dispatch", label: "JP Dispatch" },
  { value: "set_analysis", label: "Set Analysis" },
  { value: "rotation_preview", label: "Rotation Preview" },
  { value: "tournament_recap", label: "Tournament Recap" },
  { value: "tournament_preview", label: "Tournament Preview" },
  { value: "archetype_evolution", label: "Archetype Evolution" },
];

export function LabNoteTypeFilter({ value, onChange }: LabNoteTypeFilterProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Filter by type" />
      </SelectTrigger>
      <SelectContent>
        {noteTypes.map((type) => (
          <SelectItem key={type.value} value={type.value}>
            {type.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
