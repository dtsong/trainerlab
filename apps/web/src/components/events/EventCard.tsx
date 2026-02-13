"use client";

import { CalendarDays, MapPin, Plus, Users } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks";
import {
  getMajorFormatBadgeText,
  isOfficialMajorTier,
} from "@/lib/official-majors";
import { CountdownBadge } from "./CountdownBadge";
import { EventStatusBadge } from "./EventStatusBadge";

import type { ApiEventSummary } from "@trainerlab/shared-types";

interface EventCardProps {
  event: ApiEventSummary;
}

const tierColors: Record<string, string> = {
  major: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  premier: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  league: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

function formatLocation(event: ApiEventSummary): string {
  return (
    [event.city, event.country, event.region].filter(Boolean).join(", ") ||
    event.region
  );
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function EventCard({ event }: EventCardProps) {
  const { user } = useAuth();
  const date = new Date(event.date);
  const formattedDate = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const majorFormatBadgeText = getMajorFormatBadgeText(
    event.major_format_key,
    event.major_format_label
  );
  const shouldShowMajorFormatBadge = Boolean(
    isOfficialMajorTier(event.tier) && majorFormatBadgeText
  );

  return (
    <Card className="h-full transition-colors hover:border-primary/50">
      <Link href={`/events/${event.id}`} className="block">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg line-clamp-2">{event.name}</CardTitle>
            <CountdownBadge date={event.date} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <EventStatusBadge status={event.status} />
            {event.status === "registration_open" && event.registration_url && (
              <Badge className="bg-teal-500/20 text-teal-500 border-teal-500/30">
                Register
              </Badge>
            )}
            {event.tier && (
              <Badge
                variant="outline"
                className={tierColors[event.tier] ?? tierColors.league}
              >
                {event.tier}
              </Badge>
            )}
            {event.format && (
              <Badge variant="outline">{capitalize(event.format)}</Badge>
            )}
            {shouldShowMajorFormatBadge && (
              <Badge
                variant="outline"
                title={event.major_format_label ?? undefined}
                aria-label={`Major format window ${majorFormatBadgeText ?? ""}`}
              >
                {majorFormatBadgeText ?? ""}
              </Badge>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <CalendarDays className="h-4 w-4" />
              <span>{formattedDate}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              <span>{formatLocation(event)}</span>
            </div>
            {event.participant_count != null && (
              <div className="flex items-center gap-1.5">
                <Users className="h-4 w-4" />
                <span>{event.participant_count}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Link>

      {user && (
        <CardFooter>
          <Button asChild size="sm" className="w-full">
            <Link href={`/trips?add_event=${event.id}`}>
              <Plus className="h-4 w-4 mr-2" />
              Add to Trip
            </Link>
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
