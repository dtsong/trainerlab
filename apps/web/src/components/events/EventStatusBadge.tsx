"use client";

import { Badge } from "@/components/ui/badge";

import type { EventStatus } from "@trainerlab/shared-types";

interface EventStatusBadgeProps {
  status: EventStatus;
}

const statusConfig: Record<EventStatus, { label: string; className: string }> =
  {
    announced: {
      label: "Announced",
      className: "bg-blue-500/20 text-blue-500 border-blue-500/30",
    },
    registration_open: {
      label: "Registration Open",
      className: "bg-green-500/20 text-green-500 border-green-500/30",
    },
    registration_closed: {
      label: "Reg. Closed",
      className: "bg-amber-500/20 text-amber-500 border-amber-500/30",
    },
    active: {
      label: "Live",
      className: "bg-red-500/20 text-red-500 border-red-500/30",
    },
    completed: {
      label: "Completed",
      className: "bg-slate-500/20 text-slate-500 border-slate-500/30",
    },
  };

export function EventStatusBadge({ status }: EventStatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.announced;

  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
}
