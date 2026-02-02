"use client";

import { AlertCircle, FileText, RefreshCw, Rss } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { LabNoteCard, LabNoteTypeFilter } from "@/components/lab-notes";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLabNotes } from "@/hooks/useLabNotes";

import type { LabNoteType } from "@trainerlab/shared-types";

export default function LabNotesPage() {
  const [noteType, setNoteType] = useState<LabNoteType | "all">("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useLabNotes({
    note_type: noteType === "all" ? undefined : noteType,
    page,
    limit: 12,
  });

  const handleTypeChange = (newType: LabNoteType | "all") => {
    setNoteType(newType);
    setPage(1);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Lab Notes</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-10 w-48 bg-muted rounded" />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-64 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Lab Notes</h1>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load lab notes</p>
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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Lab Notes</h1>
          <p className="text-muted-foreground">
            Analysis, reports, and insights from the TrainerLab team
          </p>
        </div>
        <div className="flex items-center gap-4">
          <LabNoteTypeFilter value={noteType} onChange={handleTypeChange} />
          <Link
            href="/feed.xml"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <Rss className="h-4 w-4" />
            RSS
          </Link>
        </div>
      </div>

      {data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No lab notes found matching your filter.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((note) => (
              <LabNoteCard key={note.id} note={note} />
            ))}
          </div>

          {data && (data.has_prev || data.has_next) && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <Button
                variant="outline"
                disabled={!data.has_prev}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {data.page} of {Math.ceil(data.total / data.limit)}
              </span>
              <Button
                variant="outline"
                disabled={!data.has_next}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
