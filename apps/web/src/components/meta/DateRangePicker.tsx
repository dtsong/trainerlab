"use client";

import { useState } from "react";
import { format, subDays, startOfDay, endOfDay } from "date-fns";
import { Calendar, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface DateRange {
  start: Date;
  end: Date;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  className?: string;
}

const PRESETS = [
  { label: "Last 7 days", days: 7 },
  { label: "Last 30 days", days: 30 },
  { label: "Last 90 days", days: 90 },
] as const;

export function DateRangePicker({
  value,
  onChange,
  className,
}: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [startDate, setStartDate] = useState(format(value.start, "yyyy-MM-dd"));
  const [endDate, setEndDate] = useState(format(value.end, "yyyy-MM-dd"));
  const [error, setError] = useState<string | null>(null);

  const handlePreset = (days: number) => {
    const end = endOfDay(new Date());
    const start = startOfDay(subDays(end, days));
    onChange({ start, end });
    setStartDate(format(start, "yyyy-MM-dd"));
    setEndDate(format(end, "yyyy-MM-dd"));
    setError(null);
    setIsOpen(false);
  };

  const handleApply = () => {
    const start = startOfDay(new Date(startDate));
    const end = endOfDay(new Date(endDate));

    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      setError("Please enter valid dates");
      return;
    }

    if (start > end) {
      setError("Start date must be before end date");
      return;
    }

    setError(null);
    onChange({ start, end });
    setIsOpen(false);
  };

  const formatDisplay = () => {
    return `${format(value.start, "MMM d")} - ${format(value.end, "MMM d, yyyy")}`;
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-[240px] justify-start text-left font-normal",
            className,
          )}
          data-testid="date-range-picker"
        >
          <Calendar className="mr-2 h-4 w-4" />
          {formatDisplay()}
          <ChevronDown className="ml-auto h-4 w-4 opacity-50" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Select Date Range</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((preset) => (
              <Button
                key={preset.days}
                variant="outline"
                size="sm"
                onClick={() => handlePreset(preset.days)}
              >
                {preset.label}
              </Button>
            ))}
          </div>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <label htmlFor="date-range-start" className="text-sm font-medium">
                Start Date
              </label>
              <Input
                id="date-range-start"
                type="date"
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  setError(null);
                }}
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="date-range-end" className="text-sm font-medium">
                End Date
              </label>
              <Input
                id="date-range-end"
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  setError(null);
                }}
              />
            </div>
          </div>
          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApply}>Apply</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
