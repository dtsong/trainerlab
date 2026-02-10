"use client";

import { AlertCircle, Luggage, RefreshCw } from "lucide-react";
import { useParams } from "next/navigation";

import { TripEventList } from "@/components/trips";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useSharedTrip } from "@/hooks/useTrips";

export default function SharedTripPage() {
  const params = useParams<{ token: string }>();
  const {
    data: trip,
    isLoading,
    isError,
    refetch,
  } = useSharedTrip(params.token);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-6">
          <div className="h-10 w-80 bg-muted rounded" />
          <div className="h-64 bg-muted rounded-lg" />
        </div>
      </div>
    );
  }

  if (isError || !trip) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">
              This trip could not be found or is no longer shared.
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

  return (
    <div className="container mx-auto py-8 px-4 max-w-3xl">
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
        <Luggage className="h-4 w-4" />
        <span>Shared Trip</span>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-3">{trip.name}</h1>
      </div>

      <h2 className="text-xl font-semibold mb-4">Events</h2>
      <TripEventList events={trip.events} readOnly />
    </div>
  );
}
