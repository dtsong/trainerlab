"use client";

import Image from "next/image";
import { memo, useState } from "react";
import { ImageOff } from "lucide-react";
import { cn } from "@/lib/utils";

type CardImageSize = "thumbnail" | "small" | "large";

interface CardImageProps {
  src: string | null | undefined;
  alt: string;
  size?: CardImageSize;
  className?: string;
  priority?: boolean;
}

// Card aspect ratio is roughly 2.5:3.5 (poker card)
const SIZES = {
  thumbnail: { width: 80, height: 112 },
  small: { width: 160, height: 224 },
  large: { width: 320, height: 448 },
} as const;

function Placeholder({ size }: { size: CardImageSize }) {
  const iconSize = size === "large" ? 48 : size === "small" ? 24 : 16;
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-muted">
      <ImageOff className="text-muted-foreground" size={iconSize} />
    </div>
  );
}

export const CardImage = memo(function CardImage({
  src,
  alt,
  size = "small",
  className,
  priority = false,
}: CardImageProps) {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const { width, height } = SIZES[size];

  const showPlaceholder = error || !src;

  return (
    <div
      className={cn("relative overflow-hidden rounded-lg bg-muted", className)}
      style={{ width, height }}
    >
      {showPlaceholder ? (
        <Placeholder size={size} />
      ) : (
        <>
          {!loaded && <Placeholder size={size} />}
          <Image
            src={src}
            alt={alt}
            width={width}
            height={height}
            className={cn("object-cover", !loaded && "opacity-0")}
            onError={() => setError(true)}
            onLoad={() => setLoaded(true)}
            priority={priority}
            unoptimized={src.startsWith("http")}
          />
        </>
      )}
    </div>
  );
});
