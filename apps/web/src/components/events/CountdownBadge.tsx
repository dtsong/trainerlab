"use client";

import { Badge } from "@/components/ui/badge";

interface CountdownBadgeProps {
  date: string;
}

function getCountdown(dateStr: string): {
  label: string;
  className: string;
} {
  const now = new Date();
  const hasTime = dateStr.includes("T");
  // If the API provides a date-only string, treat it as an all-day event ending
  // at local end-of-day so "Today" doesn't immediately become "Past".
  const eventDate = hasTime
    ? new Date(dateStr)
    : new Date(`${dateStr}T23:59:59`);
  const diffMs = eventDate.getTime() - now.getTime();
  const msHour = 1000 * 60 * 60;
  const msDay = msHour * 24;

  const startOfToday = new Date(now);
  startOfToday.setHours(0, 0, 0, 0);
  const endOfToday = new Date(now);
  endOfToday.setHours(23, 59, 59, 999);

  const startOfTomorrow = new Date(startOfToday);
  startOfTomorrow.setDate(startOfTomorrow.getDate() + 1);
  const endOfTomorrow = new Date(endOfToday);
  endOfTomorrow.setDate(endOfTomorrow.getDate() + 1);

  const diffDays = Math.ceil(diffMs / msDay);

  if (eventDate < startOfToday) {
    return {
      label: "Past",
      className: "bg-slate-500/20 text-slate-500 border-slate-500/30",
    };
  }
  if (eventDate >= startOfToday && eventDate <= endOfToday) {
    return {
      label: "Today",
      className:
        "bg-red-500/20 text-red-500 border-red-500/30 motion-safe:animate-pulse",
    };
  }
  if (eventDate >= startOfTomorrow && eventDate <= endOfTomorrow) {
    return {
      label: "Tomorrow",
      className: "bg-orange-500/20 text-orange-500 border-orange-500/30",
    };
  }
  if (diffDays <= 7) {
    const days = Math.max(0, Math.floor(diffMs / msDay));
    const hours = Math.max(0, Math.floor((diffMs - days * msDay) / msHour));
    const timeLabel = days > 0 ? `${days}d ${hours}h` : `${hours}h`;
    return {
      label: `Starts in ${timeLabel}`,
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
