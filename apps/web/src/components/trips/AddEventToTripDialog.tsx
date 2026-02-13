"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import type { ApiTripSummary } from "@trainerlab/shared-types";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAddTripEvent, useCreateTrip } from "@/hooks/useTrips";

interface AddEventToTripDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  eventId: string;
  trips: ApiTripSummary[];
}

export function AddEventToTripDialog({
  open,
  onOpenChange,
  eventId,
  trips,
}: AddEventToTripDialogProps) {
  const router = useRouter();
  const addTripEvent = useAddTripEvent();
  const createTrip = useCreateTrip();

  const [selectedTripId, setSelectedTripId] = useState<string>("");

  // Inline create-trip mode (only used when the user has no trips yet).
  const [newTripName, setNewTripName] = useState("");
  const [newTripNotes, setNewTripNotes] = useState("");

  const hasTrips = trips.length > 0;

  const dialogDescription = useMemo(() => {
    if (hasTrips) {
      return "Choose which trip to add this event to.";
    }
    return "You don't have any trips yet. Create one, then we'll add this event.";
  }, [hasTrips]);

  const handleClose = () => {
    onOpenChange(false);
    setSelectedTripId("");
  };

  const handleAddToTrip = async () => {
    if (!selectedTripId) return;

    try {
      await addTripEvent.mutateAsync({
        tripId: selectedTripId,
        data: { tournament_id: eventId },
      });
      // Replace the /trips?add_event=... history entry to avoid re-triggering.
      router.replace(`/trips/${selectedTripId}`);
    } finally {
      handleClose();
    }
  };

  const handleCreateAndAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTripName.trim()) return;

    try {
      const created = await createTrip.mutateAsync({
        name: newTripName.trim(),
        notes: newTripNotes.trim() || null,
      });
      await addTripEvent.mutateAsync({
        tripId: created.id,
        data: { tournament_id: eventId },
      });
      router.replace(`/trips/${created.id}`);
    } finally {
      setNewTripName("");
      setNewTripNotes("");
      handleClose();
    }
  };

  const isBusy = addTripEvent.isPending || createTrip.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Event to Trip</DialogTitle>
          <DialogDescription>{dialogDescription}</DialogDescription>
        </DialogHeader>

        {hasTrips ? (
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="trip-select">Trip</Label>
              <Select value={selectedTripId} onValueChange={setSelectedTripId}>
                <SelectTrigger id="trip-select">
                  <SelectValue placeholder="Select a trip" />
                </SelectTrigger>
                <SelectContent>
                  {trips.map((trip) => (
                    <SelectItem key={trip.id} value={trip.id}>
                      {trip.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        ) : (
          <form onSubmit={handleCreateAndAdd} className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="new-trip-name">Trip Name</Label>
              <Input
                id="new-trip-name"
                placeholder="e.g., Spring 2026 Regionals"
                value={newTripName}
                onChange={(e) => setNewTripName(e.target.value)}
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-trip-notes">
                Notes <span className="text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="new-trip-notes"
                placeholder="Goals, travel details, etc."
                value={newTripNotes}
                onChange={(e) => setNewTripNotes(e.target.value)}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={!newTripName.trim() || isBusy}>
                {isBusy ? "Working..." : "Create Trip & Add"}
              </Button>
            </DialogFooter>
          </form>
        )}

        {hasTrips ? (
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleAddToTrip}
              disabled={!selectedTripId || isBusy}
            >
              {isBusy ? "Adding..." : "Add to Trip"}
            </Button>
          </DialogFooter>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
