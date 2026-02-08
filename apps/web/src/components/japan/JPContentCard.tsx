"use client";

import { format } from "date-fns";
import { ExternalLink, FileText, ListOrdered } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TranslationBadge } from "@/components/ui/translation-badge";

interface JPContentCardProps {
  title: string | null;
  excerpt: string | null;
  sourceUrl: string;
  sourceName: string | null;
  contentType: string;
  publishedDate: string | null;
  archetypeRefs: string[] | null;
}

export function JPContentCard({
  title,
  excerpt,
  sourceUrl,
  sourceName,
  contentType,
  publishedDate,
  archetypeRefs,
}: JPContentCardProps) {
  const icon =
    contentType === "tier_list" ? (
      <ListOrdered className="h-4 w-4 text-teal-600 dark:text-teal-400" />
    ) : (
      <FileText className="h-4 w-4 text-teal-600 dark:text-teal-400" />
    );

  const typeLabel = contentType === "tier_list" ? "Tier List" : "Article";

  return (
    <Card className="transition-colors hover:border-teal-500/30">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            {/* Header row */}
            <div className="flex flex-wrap items-center gap-2">
              {icon}
              <Badge variant="outline" className="text-[10px]">
                {typeLabel}
              </Badge>
              {sourceName && (
                <Badge variant="secondary" className="text-[10px]">
                  {sourceName}
                </Badge>
              )}
              {publishedDate && (
                <span className="text-[10px] text-muted-foreground">
                  {format(new Date(publishedDate), "MMM d, yyyy")}
                </span>
              )}
            </div>

            {/* Title */}
            {title && (
              <h3 className="text-sm font-medium leading-snug">{title}</h3>
            )}

            {/* Excerpt */}
            {excerpt && (
              <p className="line-clamp-3 text-xs leading-relaxed text-muted-foreground">
                {excerpt}
              </p>
            )}

            {/* Archetype tags */}
            {archetypeRefs && archetypeRefs.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {archetypeRefs.slice(0, 5).map((ref) => (
                  <span
                    key={ref}
                    className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                  >
                    {ref}
                  </span>
                ))}
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center gap-2">
              <TranslationBadge
                sourceUrl={sourceUrl}
                sourceName={sourceName || undefined}
              />
            </div>
          </div>

          {/* External link */}
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            title="View original"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
