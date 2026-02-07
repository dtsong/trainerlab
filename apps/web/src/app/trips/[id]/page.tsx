"use client";

import {
  AlertCircle,
  ArrowLeft,
  Pencil,
  RefreshCw,
  Share2,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { TripEventList, ShareTripDialog } from "@/components/trips";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useTrip,
  useUpdateTrip,
  useDeleteTrip,
  useRemoveTripEvent,
} from "@/hooks/useTrips";

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

export default function TripDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { data: trip, isLoading, isError, refetch } = useTrip(params.id);
  const updateTrip = useUpdateTrip();
  const deleteTrip = useDeleteTrip();
  const removeTripEvent = useRemoveTripEvent();

  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editNotes, setEditNotes] = useState("");

  const handleStartEdit = () => {
    if (!trip) return;
    setEditName(trip.name);
    setEditNotes(trip.notes ?? "");
    setEditing(true);
  };

  const handleSaveEdit = () => {
    if (!trip) return;
    updateTrip.mutate(
      {
        id: trip.id,
        data: {
          name: editName.trim() || null,
          notes: editNotes.trim() || null,
        },
      },
      { onSuccess: () => setEditing(false) }
    );
  };

  const handleDelete = () => {
    if (!trip) return;
    if (!window.confirm("Delete this trip? This cannot be undone.")) return;
    deleteTrip.mutate(trip.id, {
      onSuccess: () => router.push("/trips"),
    });
  };

  const handleRemoveEvent = (eventId: string) => {
    if (!trip) return;
    removeTripEvent.mutate({ tripId: trip.id, eventId });
  };

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

  if (isError || !trip) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load trip</p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const config = statusConfig[trip.status] ?? statusConfig.planning;

  return (
    <div className="container mx-auto py-8 px-4">
      <Link
        href="/trips"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Trips
      </Link>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Trip header */}
          <div>
            {editing ? (
              <div className="space-y-3">
                <Input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Trip name"
                  className="text-xl font-bold"
                />
                <Input
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Notes (optional)"
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleSaveEdit}
                    disabled={updateTrip.isPending}
                  >
                    {updateTrip.isPending ? "Saving..." : "Save"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditing(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-start gap-3 mb-3">
                  <h1 className="text-3xl font-bold">{trip.name}</h1>
                  <Badge variant="outline" className={config.className}>
                    {config.label}
                  </Badge>
                </div>
                {trip.notes && (
                  <p className="text-muted-foreground mb-4">{trip.notes}</p>
                )}
              </>
            )}
          </div>

          {/* Events */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Events</h2>
              <Button variant="outline" size="sm" asChild>
                <Link href="/events">Browse Events</Link>
              </Button>
            </div>
            <TripEventList events={trip.events} onRemove={handleRemoveEvent} />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {!editing && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleStartEdit}
                >
                  <Pencil className="h-4 w-4 mr-2" />
                  Edit Trip
                </Button>
              )}

              <ShareTripDialog
                tripId={trip.id}
                existingShareUrl={trip.share_url}
                trigger={
                  <Button variant="outline" className="w-full justify-start">
                    <Share2 className="h-4 w-4 mr-2" />
                    Share Trip
                  </Button>
                }
              />

              <Button
                variant="outline"
                className="w-full justify-start text-destructive hover:text-destructive"
                onClick={handleDelete}
                disabled={deleteTrip.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                {deleteTrip.isPending ? "Deleting..." : "Delete Trip"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-4 text-xs text-muted-foreground space-y-1">
              <div>
                Created: {new Date(trip.created_at).toLocaleDateString()}
              </div>
              <div>
                Updated: {new Date(trip.updated_at).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
