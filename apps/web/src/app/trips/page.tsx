"use client";

import { AlertCircle, Luggage, Plus, RefreshCw } from "lucide-react";

import {
  AddEventToTripDialog,
  TripCard,
  CreateTripDialog,
} from "@/components/trips";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTrips } from "@/hooks/useTrips";
import { useAuth } from "@/hooks";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function TripsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const { data: trips, isLoading, isError, refetch } = useTrips();

  const addEventId = searchParams.get("add_event");
  const [addDialogOpen, setAddDialogOpen] = useState(Boolean(addEventId));

  useEffect(() => {
    setAddDialogOpen(Boolean(addEventId));
  }, [addEventId]);

  const handleAddDialogChange = (open: boolean) => {
    setAddDialogOpen(open);
    if (!open && addEventId) {
      router.replace("/trips", { scroll: false });
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">My Trips</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-10 w-48 bg-muted rounded" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-48 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">My Trips</h1>
        <Card>
          <CardContent className="py-12 text-center">
            <Luggage className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">
              Sign in to plan your trips
            </p>
            <p className="text-muted-foreground mb-6">
              Create trip plans around upcoming Pokemon TCG events.
            </p>
            <Button asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">My Trips</h1>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load trips</p>
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
    <div className="container mx-auto py-8 px-4">
      {addEventId && trips && (
        <AddEventToTripDialog
          open={addDialogOpen}
          onOpenChange={handleAddDialogChange}
          eventId={addEventId}
          trips={trips}
        />
      )}

      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">My Trips</h1>
        <CreateTripDialog
          trigger={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Trip
            </Button>
          }
        />
      </div>

      {!trips || trips.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Luggage className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No trips yet</p>
            <p className="text-muted-foreground mb-6">
              Plan your season by creating a trip around upcoming events.
            </p>
            <CreateTripDialog
              trigger={
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Trip
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {trips.map((trip) => (
            <TripCard key={trip.id} trip={trip} />
          ))}
        </div>
      )}
    </div>
  );
}
