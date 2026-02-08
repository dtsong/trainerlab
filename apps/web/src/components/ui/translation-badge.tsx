import { Languages } from "lucide-react";

interface TranslationBadgeProps {
  sourceUrl?: string;
  sourceName?: string;
}

export function TranslationBadge({
  sourceUrl,
  sourceName,
}: TranslationBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-400">
      <Languages className="h-3 w-3" />
      Machine-translated
      {sourceUrl && (
        <>
          {" · "}
          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-amber-900 dark:hover:text-amber-200"
          >
            {sourceName || "Original"}
          </a>
        </>
      )}
    </span>
  );
}
