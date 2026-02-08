"use client";

import { memo } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardTrigger,
  HoverCardContent,
} from "@/components/ui/hover-card";
import { CardImage } from "./CardImage";

interface CardReferenceProps {
  cardId: string;
  cardName?: string | null;
  imageSmall?: string | null;
  variant?: "inline" | "badge";
  showThumbnail?: boolean;
  className?: string;
}

export const CardReference = memo(function CardReference({
  cardId,
  cardName,
  imageSmall,
  variant = "inline",
  showThumbnail = false,
  className,
}: CardReferenceProps) {
  const displayName = cardName || cardId;
  const hasImage = !!imageSmall;

  const content = (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      {showThumbnail && (
        <span className="inline-block shrink-0">
          <CardImage src={imageSmall} alt={displayName} size="thumbnail" />
        </span>
      )}
      <span className="inline-flex flex-col justify-center">
        <span
          className={cn(
            "leading-tight",
            cardName
              ? "font-sans text-sm font-medium"
              : "font-mono text-xs text-muted-foreground"
          )}
        >
          {displayName}
        </span>
        {cardName && (
          <span className="font-mono text-[10px] leading-none text-muted-foreground/60">
            {cardId}
          </span>
        )}
      </span>
    </span>
  );

  const trigger =
    variant === "badge" ? (
      <Badge
        variant="outline"
        className="cursor-default gap-1.5 py-1 pr-2.5 pl-1.5"
      >
        {content}
      </Badge>
    ) : (
      <span className="inline-flex cursor-default rounded-sm px-0.5 transition-colors hover:bg-muted/50">
        {content}
      </span>
    );

  if (!hasImage) {
    return trigger;
  }

  return (
    <HoverCard openDelay={300} closeDelay={100}>
      <HoverCardTrigger asChild>{trigger}</HoverCardTrigger>
      <HoverCardContent
        side="top"
        align="center"
        className="w-auto border-zinc-700/50 bg-zinc-900/95 p-2 shadow-xl backdrop-blur-sm"
      >
        <div
          className="overflow-hidden rounded-md"
          style={{ width: 288, height: 403 }}
        >
          <Image
            src={imageSmall}
            alt={displayName}
            width={288}
            height={403}
            className="h-full w-full object-cover"
            unoptimized={imageSmall.startsWith("http")}
          />
        </div>
        <p className="mt-1.5 text-center font-sans text-xs font-medium text-zinc-300">
          {displayName}
        </p>
      </HoverCardContent>
    </HoverCard>
  );
});
