"use client";

import {
  AlertCircle,
  ArrowLeft,
  CalendarDays,
  ExternalLink,
  MapPin,
  Plus,
  RefreshCw,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { CountdownBadge, EventStatusBadge } from "@/components/events";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useEvent } from "@/hooks/useEvents";
import { useAuth } from "@/hooks";
import {
  getMajorFormatBadgeText,
  isOfficialMajorTier,
} from "@/lib/official-majors";

const tierColors: Record<string, string> = {
  major: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  premier: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  league: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: event, isLoading, isError, refetch } = useEvent(params.id);
  const { user } = useAuth();

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-6">
          <div className="h-6 w-32 bg-muted rounded" />
          <div className="h-10 w-80 bg-muted rounded" />
          <div className="h-64 bg-muted rounded-lg" />
        </div>
      </div>
    );
  }

  if (isError || !event) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">
              Failed to load event details
            </p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const date = new Date(event.date);
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
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

  const mapsQuery = [
    event.venue_name,
    event.venue_address,
    event.city,
    event.country,
  ]
    .filter(Boolean)
    .join(", ");
  const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    mapsQuery || event.region
  )}`;

  return (
    <div className="container mx-auto py-8 px-4">
      <Link
        href="/events"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Events
      </Link>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <div className="flex items-start gap-3 mb-4">
              <h1 className="text-3xl font-bold">{event.name}</h1>
              <CountdownBadge date={event.date} />
            </div>

            <div className="flex flex-wrap items-center gap-3 mb-4">
              <EventStatusBadge status={event.status} />
              {event.tier && (
                <Badge
                  variant="outline"
                  className={tierColors[event.tier] ?? tierColors.league}
                >
                  {event.tier}
                </Badge>
              )}
              {event.format && (
                <Badge variant="outline">
                  {event.format.charAt(0).toUpperCase() + event.format.slice(1)}
                </Badge>
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
          </div>

          {/* Event details card */}
          <Card>
            <CardHeader>
              <CardTitle>Event Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <CalendarDays className="h-5 w-5 text-muted-foreground shrink-0" />
                <span>{formattedDate}</span>
              </div>

              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-muted-foreground shrink-0" />
                <span>
                  {[
                    event.venue_name,
                    event.venue_address,
                    event.city,
                    event.country,
                    event.region,
                  ]
                    .filter(Boolean)
                    .join(", ") || event.region}
                </span>
              </div>

              {mapsQuery && (
                <div className="pt-1">
                  <Button asChild variant="outline" size="sm">
                    <a
                      href={googleMapsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <MapPin className="h-4 w-4 mr-2" />
                      Open in Google Maps
                    </a>
                  </Button>
                </div>
              )}

              {event.participant_count != null && (
                <div className="flex items-center gap-3">
                  <Users className="h-5 w-5 text-muted-foreground shrink-0" />
                  <span>{event.participant_count} players</span>
                </div>
              )}

              {event.registration_url && (
                <div className="pt-2">
                  <Button asChild variant="outline">
                    <a
                      href={event.registration_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Registration Page
                    </a>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Registration timeline */}
          {(event.registration_opens_at || event.registration_closes_at) && (
            <Card>
              <CardHeader>
                <CardTitle>Registration Timeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {event.registration_opens_at && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Opens</span>
                    <span>
                      {new Date(event.registration_opens_at).toLocaleDateString(
                        "en-US",
                        {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                          hour: "numeric",
                          minute: "2-digit",
                        }
                      )}
                    </span>
                  </div>
                )}
                {event.registration_closes_at && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Closes</span>
                    <span>
                      {new Date(
                        event.registration_closes_at
                      ).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {user && (
            <Card>
              <CardContent className="py-6">
                <Button className="w-full" asChild>
                  <Link href={`/trips?add_event=${event.id}`}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add to Trip
                  </Link>
                </Button>
              </CardContent>
            </Card>
          )}

          {event.event_source && (
            <Card>
              <CardContent className="py-4">
                <div className="text-xs text-muted-foreground">
                  Source: {event.event_source}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
