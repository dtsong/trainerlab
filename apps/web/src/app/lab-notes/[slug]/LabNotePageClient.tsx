"use client";

import {
  AlertCircle,
  ArrowLeft,
  CalendarDays,
  Lock,
  RefreshCw,
  User,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLabNote } from "@/hooks/useLabNotes";

import type { LabNoteType } from "@trainerlab/shared-types";

const typeColors: Record<LabNoteType, string> = {
  weekly_report: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  jp_dispatch: "bg-red-500/20 text-red-400 border-red-500/30",
  set_analysis: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  rotation_preview: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  tournament_recap: "bg-green-500/20 text-green-400 border-green-500/30",
  tournament_preview: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  archetype_evolution: "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

const typeLabels: Record<LabNoteType, string> = {
  weekly_report: "Weekly Report",
  jp_dispatch: "JP Dispatch",
  set_analysis: "Set Analysis",
  rotation_preview: "Rotation Preview",
  tournament_recap: "Tournament Recap",
  tournament_preview: "Tournament Preview",
  archetype_evolution: "Archetype Evolution",
};

interface LabNotePageClientProps {
  slug: string;
}

export function LabNotePageClient({ slug }: LabNotePageClientProps) {
  const { data: note, isLoading, isError, refetch } = useLabNote(slug);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-3xl">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-24 bg-muted rounded" />
          <div className="h-10 w-full bg-muted rounded" />
          <div className="h-4 w-48 bg-muted rounded" />
          <div className="space-y-2 mt-8">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-4 w-full bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError || !note) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-3xl">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load article</p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const publishedDate = note.published_at
    ? new Date(note.published_at)
    : new Date(note.created_at);
  const formattedDate = publishedDate.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <article className="container mx-auto py-8 px-4 max-w-3xl">
      <Link
        href="/lab-notes"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Lab Notes
      </Link>

      <header className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Badge variant="outline" className={typeColors[note.note_type]}>
            {typeLabels[note.note_type]}
          </Badge>
          {note.is_premium && (
            <div className="flex items-center gap-1 text-yellow-500 text-sm">
              <Lock className="h-4 w-4" />
              <span>Premium</span>
            </div>
          )}
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold mb-4">{note.title}</h1>

        {note.summary && (
          <p className="text-lg text-muted-foreground mb-4">{note.summary}</p>
        )}

        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <CalendarDays className="h-4 w-4" />
            <span>{formattedDate}</span>
          </div>
          {note.author_name && (
            <div className="flex items-center gap-1.5">
              <User className="h-4 w-4" />
              <span>{note.author_name}</span>
            </div>
          )}
        </div>

        {note.tags && note.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {note.tags.map((tag) => (
              <span
                key={tag}
                className="text-xs bg-muted px-2 py-1 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </header>

      {note.featured_image_url && (
        <div className="rounded-lg overflow-hidden mb-8">
          <img src={note.featured_image_url} alt="" className="w-full h-auto" />
        </div>
      )}

      <div className="prose prose-invert prose-slate max-w-none">
        <div className="whitespace-pre-wrap">{note.content}</div>
      </div>

      <footer className="mt-12 pt-8 border-t border-border">
        <Link
          href="/lab-notes"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Lab Notes
        </Link>
      </footer>
    </article>
  );
}
