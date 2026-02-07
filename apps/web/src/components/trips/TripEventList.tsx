"use client";

import { CalendarDays, MapPin, Trash2, Users } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CountdownBadge, EventStatusBadge } from "@/components/events";

import type { ApiTripEventDetail } from "@trainerlab/shared-types";

interface TripEventListProps {
  events: ApiTripEventDetail[];
  onRemove?: (eventId: string) => void;
  readOnly?: boolean;
}

const roleLabels: Record<string, string> = {
  player: "Player",
  spectator: "Spectator",
  judge: "Judge",
  coach: "Coach",
};

export function TripEventList({
  events,
  onRemove,
  readOnly = false,
}: TripEventListProps) {
  if (events.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <CalendarDays className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
          <p className="text-muted-foreground">
            No events added to this trip yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {events.map((tripEvent) => {
        const ev = tripEvent.event;
        const date = new Date(ev.date);
        const formattedDate = date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        });

        return (
          <Card key={tripEvent.id}>
            <CardContent className="py-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Link
                      href={`/events/${ev.id}`}
                      className="text-base font-medium hover:underline line-clamp-1"
                    >
                      {ev.name}
                    </Link>
                    <CountdownBadge date={ev.date} />
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground mb-2">
                    <span className="flex items-center gap-1">
                      <CalendarDays className="h-3.5 w-3.5" />
                      {formattedDate}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" />
                      {[ev.city, ev.region].filter(Boolean).join(", ") ||
                        ev.region}
                    </span>
                    {ev.participant_count != null && (
                      <span className="flex items-center gap-1">
                        <Users className="h-3.5 w-3.5" />
                        {ev.participant_count}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <EventStatusBadge status={ev.status} />
                    <Badge variant="outline">
                      {roleLabels[tripEvent.role] ?? tripEvent.role}
                    </Badge>
                  </div>

                  {tripEvent.notes && (
                    <p className="mt-2 text-sm text-muted-foreground">
                      {tripEvent.notes}
                    </p>
                  )}
                </div>

                {!readOnly && onRemove && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => onRemove(tripEvent.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
