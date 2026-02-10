"use client";

import { useState } from "react";
import { Check, Copy, Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useShareTrip } from "@/hooks/useTrips";

interface ShareTripDialogProps {
  tripId: string;
  existingShareUrl?: string | null;
  trigger: React.ReactNode;
}

export function ShareTripDialog({
  tripId,
  existingShareUrl,
  trigger,
}: ShareTripDialogProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const shareTrip = useShareTrip();

  const shareUrl =
    (shareTrip.data?.share_token
      ? `${window.location.origin}/trips/share/${shareTrip.data.share_token}`
      : null) ?? existingShareUrl;

  const handleGenerateLink = () => {
    shareTrip.mutate(tripId);
  };

  const handleCopy = async () => {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Share Trip</DialogTitle>
          <DialogDescription>
            Share a read-only link to this trip with friends.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {shareUrl ? (
            <div className="flex items-center gap-2">
              <Input value={shareUrl} readOnly className="flex-1" />
              <Button variant="outline" size="icon" onClick={handleCopy}>
                {copied ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          ) : (
            <div className="text-center py-4">
              <Link2 className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground mb-4">
                Generate a shareable link for this trip.
              </p>
              <Button
                onClick={handleGenerateLink}
                disabled={shareTrip.isPending}
              >
                {shareTrip.isPending ? "Generating..." : "Generate Link"}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
