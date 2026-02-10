"use client";

import { Badge } from "@/components/ui/badge";

interface CountdownBadgeProps {
  date: string;
}

function getCountdown(dateStr: string): {
  label: string;
  className: string;
} {
  const eventDate = new Date(dateStr);
  const now = new Date();
  const diffMs = eventDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return {
      label: "Past",
      className: "bg-slate-500/20 text-slate-500 border-slate-500/30",
    };
  }
  if (diffDays === 0) {
    return {
      label: "Today",
      className: "bg-red-500/20 text-red-500 border-red-500/30",
    };
  }
  if (diffDays === 1) {
    return {
      label: "Tomorrow",
      className: "bg-orange-500/20 text-orange-500 border-orange-500/30",
    };
  }
  if (diffDays <= 7) {
    return {
      label: `${diffDays}d`,
      className: "bg-amber-500/20 text-amber-500 border-amber-500/30",
    };
  }
  if (diffDays <= 30) {
    return {
      label: `${Math.ceil(diffDays / 7)}w`,
      className: "bg-teal-500/20 text-teal-500 border-teal-500/30",
    };
  }
  return {
    label: `${Math.ceil(diffDays / 30)}mo`,
    className: "bg-blue-500/20 text-blue-500 border-blue-500/30",
  };
}

export function CountdownBadge({ date }: CountdownBadgeProps) {
  const { label, className } = getCountdown(date);

  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  );
}
