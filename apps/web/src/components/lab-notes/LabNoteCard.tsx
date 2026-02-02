"use client";

import { CalendarDays, Lock, User } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { ApiLabNoteSummary, LabNoteType } from "@trainerlab/shared-types";

interface LabNoteCardProps {
  note: ApiLabNoteSummary;
}

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

export function LabNoteCard({ note }: LabNoteCardProps) {
  const publishedDate = note.published_at
    ? new Date(note.published_at)
    : new Date(note.created_at);
  const formattedDate = publishedDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Link href={`/lab-notes/${note.slug}`}>
      <Card className="h-full transition-colors hover:border-primary/50 group">
        {note.featured_image_url && (
          <div className="aspect-video overflow-hidden rounded-t-lg">
            <img
              src={note.featured_image_url}
              alt=""
              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
            />
          </div>
        )}
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-2 mb-2">
            <Badge variant="outline" className={typeColors[note.note_type]}>
              {typeLabels[note.note_type]}
            </Badge>
            {note.is_premium && <Lock className="h-4 w-4 text-yellow-500" />}
          </div>
          <CardTitle className="text-lg line-clamp-2 group-hover:text-primary transition-colors">
            {note.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {note.summary && (
            <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
              {note.summary}
            </p>
          )}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <CalendarDays className="h-3.5 w-3.5" />
              <span>{formattedDate}</span>
            </div>
            {note.author_name && (
              <div className="flex items-center gap-1">
                <User className="h-3.5 w-3.5" />
                <span>{note.author_name}</span>
              </div>
            )}
          </div>
          {note.tags && note.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {note.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-xs bg-muted px-2 py-0.5 rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
