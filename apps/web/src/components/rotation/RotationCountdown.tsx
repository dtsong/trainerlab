"use client";

import { CalendarDays, Clock } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUpcomingFormat } from "@/hooks/useFormat";

export function RotationCountdown() {
  const { data, isLoading, isError } = useUpcomingFormat();

  // Only show if rotation is within 60 days
  if (isLoading || isError || !data || data.days_until_rotation > 60) {
    return null;
  }

  const daysRemaining = data.days_until_rotation;
  const rotationDate = new Date(data.rotation_date);
  const formattedDate = rotationDate.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  // Calculate urgency color
  const urgencyClass =
    daysRemaining <= 7
      ? "text-red-400 border-red-500/30 bg-red-500/10"
      : daysRemaining <= 14
        ? "text-orange-400 border-orange-500/30 bg-orange-500/10"
        : daysRemaining <= 30
          ? "text-yellow-400 border-yellow-500/30 bg-yellow-500/10"
          : "text-blue-400 border-blue-500/30 bg-blue-500/10";

  return (
    <Card className={`border ${urgencyClass}`}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Clock className="h-5 w-5" />
          Rotation Countdown
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-4xl font-bold tabular-nums">
              {daysRemaining}
              <span className="text-lg font-normal text-muted-foreground ml-2">
                {daysRemaining === 1 ? "day" : "days"}
              </span>
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              <span>
                {data.format.display_name} format begins {formattedDate}
              </span>
            </div>
          </div>
          <Link
            href="/rotation"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            View Rotation Impact
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
