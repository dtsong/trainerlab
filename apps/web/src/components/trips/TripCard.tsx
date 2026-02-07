"use client";

import { CalendarDays, MapPin } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CountdownBadge } from "@/components/events";

import type { ApiTripSummary } from "@trainerlab/shared-types";

interface TripCardProps {
  trip: ApiTripSummary;
}

const statusConfig: Record<string, { label: string; className: string }> = {
  planning: {
    label: "Planning",
    className: "bg-blue-500/20 text-blue-600 border-blue-500/30",
  },
  confirmed: {
    label: "Confirmed",
    className: "bg-green-500/20 text-green-600 border-green-500/30",
  },
  completed: {
    label: "Completed",
    className: "bg-slate-500/20 text-slate-500 border-slate-500/30",
  },
  cancelled: {
    label: "Cancelled",
    className: "bg-red-500/20 text-red-500 border-red-500/30",
  },
};

export function TripCard({ trip }: TripCardProps) {
  const config = statusConfig[trip.status] ?? statusConfig.planning;

  return (
    <Link href={`/trips/${trip.id}`}>
      <Card className="h-full transition-colors hover:border-primary/50">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg line-clamp-2">{trip.name}</CardTitle>
            <Badge variant="outline" className={config.className}>
              {config.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
            <span>
              {trip.event_count} {trip.event_count === 1 ? "event" : "events"}
            </span>
          </div>

          {trip.next_event && (
            <div className="border-t pt-3 mt-3">
              <div className="text-xs font-medium text-muted-foreground mb-2">
                Next Event
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="text-sm font-medium line-clamp-1">
                    {trip.next_event.name}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <CalendarDays className="h-3 w-3" />
                      {new Date(trip.next_event.date).toLocaleDateString(
                        "en-US",
                        {
                          month: "short",
                          day: "numeric",
                        }
                      )}
                    </span>
                    {trip.next_event.region && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {trip.next_event.region}
                      </span>
                    )}
                  </div>
                </div>
                <CountdownBadge date={trip.next_event.date} />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
