"use client";

import { useCallback } from "react";
import { cn } from "@/lib/utils";

const SIZE_MAP = {
  sm: 24,
  md: 32,
} as const;

interface ArchetypeSpritesProps {
  spriteUrls: string[];
  archetypeName: string;
  size?: "sm" | "md";
  className?: string;
}

export function ArchetypeSprites({
  spriteUrls,
  archetypeName,
  size = "sm",
  className,
}: ArchetypeSpritesProps) {
  const px = SIZE_MAP[size];
  const visible = spriteUrls.slice(0, 3);

  const handleError = useCallback(
    (e: React.SyntheticEvent<HTMLImageElement>) => {
      e.currentTarget.style.display = "none";
    },
    []
  );

  if (visible.length === 0) {
    return null;
  }

  return (
    <span
      className={cn("inline-flex items-center gap-1", className)}
      data-testid="archetype-sprites"
    >
      {visible.map((url, i) => (
        <img
          key={`${url}-${i}`}
          src={url}
          alt={archetypeName}
          width={px}
          height={px}
          loading="lazy"
          onError={handleError}
          className="inline-block"
        />
      ))}
    </span>
  );
}
