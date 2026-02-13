"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArchetypeSprites } from "./ArchetypeSprites";
import { cn } from "@/lib/utils";
import type { Archetype } from "@trainerlab/shared-types";

interface ArchetypeCardProps {
  archetype: Archetype;
  className?: string;
}

export function ArchetypeCard({ archetype, className }: ArchetypeCardProps) {
  const sharePercent = (archetype.share * 100).toFixed(1);
  const spriteUrls = archetype.spriteUrls ?? [];

  return (
    <Link href={`/meta/archetype/${encodeURIComponent(archetype.name)}`}>
      <Card
        className={cn(
          "cursor-pointer transition-all hover:shadow-lg hover:border-primary/50",
          className
        )}
        data-testid="archetype-card"
      >
        <CardHeader className="p-4 pb-2">
          <CardTitle className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              {spriteUrls.length > 0 && (
                <ArchetypeSprites
                  spriteUrls={spriteUrls}
                  archetypeName={archetype.name}
                  size="sm"
                />
              )}
              <span className="truncate text-base">{archetype.name}</span>
            </div>
            <span className="shrink-0 text-xl font-bold text-primary">
              {sharePercent}%
            </span>
          </CardTitle>
        </CardHeader>
      </Card>
    </Link>
  );
}
