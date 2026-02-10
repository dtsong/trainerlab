"use client";

import { useQuery } from "@tanstack/react-query";
import { Languages } from "lucide-react";
import { japanApi } from "@/lib/api";
import { JPContentCard } from "./JPContentCard";
import { CardInnovationTracker, NewArchetypeWatch } from "@/components/japan";
import { Badge } from "@/components/ui/badge";

interface JPAnalysisTabProps {
  era?: string;
}

export function JPAnalysisTab({ era }: JPAnalysisTabProps) {
  const { data: tierLists, isLoading: isLoadingTierLists } = useQuery({
    queryKey: ["japan", "content", "tier_list", era],
    queryFn: () =>
      japanApi.getContent({
        content_type: "tier_list",
        era,
        limit: 10,
      }),
    staleTime: 1000 * 60 * 15,
  });

  const { data: articles, isLoading: isLoadingArticles } = useQuery({
    queryKey: ["japan", "content", "article", era],
    queryFn: () =>
      japanApi.getContent({
        content_type: "article",
        era,
        limit: 10,
      }),
    staleTime: 1000 * 60 * 15,
  });

  const totalItems =
    (tierLists?.items.length ?? 0) + (articles?.items.length ?? 0);

  return (
    <div className="space-y-10">
      {/* Era context banner */}
      {era && (
        <div
          className="flex items-center gap-2 rounded-md border border-teal-500/20 bg-teal-500/5 px-3 py-2"
          data-testid="era-context-banner"
        >
          <Languages className="h-3.5 w-3.5 shrink-0 text-teal-600 dark:text-teal-400" />
          <span className="text-xs text-muted-foreground">
            Showing translated content for the{" "}
            <Badge variant="outline" className="mx-0.5 text-[10px]">
              {era}
            </Badge>{" "}
            era
            {totalItems > 0 && (
              <span className="ml-1 text-foreground/70">
                ({totalItems} {totalItems === 1 ? "item" : "items"})
              </span>
            )}
          </span>
        </div>
      )}

      {/* Translated Tier Lists */}
      <section>
        <h2 className="mb-4 text-xl font-semibold">Translated Tier Lists</h2>
        {isLoadingTierLists && (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        )}
        {!isLoadingTierLists && tierLists?.items.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No translated tier lists available yet
          </p>
        )}
        {!isLoadingTierLists && tierLists && tierLists.items.length > 0 && (
          <div className="space-y-3">
            {tierLists.items.map((item) => (
              <JPContentCard
                key={item.id}
                title={item.title_en}
                excerpt={item.translated_text}
                sourceUrl={item.source_url}
                sourceName={item.source_name}
                contentType={item.content_type}
                publishedDate={item.published_date}
                archetypeRefs={item.archetype_refs}
              />
            ))}
          </div>
        )}
      </section>

      {/* Translated Articles */}
      <section>
        <h2 className="mb-4 text-xl font-semibold">Translated Articles</h2>
        {isLoadingArticles && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        )}
        {!isLoadingArticles && articles?.items.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No translated articles available yet
          </p>
        )}
        {!isLoadingArticles && articles && articles.items.length > 0 && (
          <div className="space-y-3">
            {articles.items.map((item) => (
              <JPContentCard
                key={item.id}
                title={item.title_en}
                excerpt={item.translated_text}
                sourceUrl={item.source_url}
                sourceName={item.source_name}
                contentType={item.content_type}
                publishedDate={item.published_date}
                archetypeRefs={item.archetype_refs}
              />
            ))}
          </div>
        )}
      </section>

      {/* New Archetypes + Innovation */}
      <section>
        <NewArchetypeWatch limit={9} />
      </section>

      <section>
        <CardInnovationTracker limit={20} />
      </section>
    </div>
  );
}
