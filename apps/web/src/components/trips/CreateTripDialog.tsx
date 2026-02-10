"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateTrip } from "@/hooks/useTrips";

interface CreateTripDialogProps {
  trigger: React.ReactNode;
}

export function CreateTripDialog({ trigger }: CreateTripDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const createTrip = useCreateTrip();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    createTrip.mutate(
      { name: name.trim(), notes: notes.trim() || null },
      {
        onSuccess: () => {
          setName("");
          setNotes("");
          setOpen(false);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create Trip</DialogTitle>
            <DialogDescription>
              Plan a trip around upcoming Pokemon TCG events.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="trip-name">Trip Name</Label>
              <Input
                id="trip-name"
                placeholder="e.g., Spring 2026 Regionals"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="trip-notes">
                Notes <span className="text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="trip-notes"
                placeholder="Goals, travel details, etc."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!name.trim() || createTrip.isPending}
            >
              {createTrip.isPending ? "Creating..." : "Create Trip"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
