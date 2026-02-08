"use client";

import { useQuery } from "@tanstack/react-query";
import { japanApi } from "@/lib/api";
import { JPContentCard } from "./JPContentCard";
import { CardInnovationTracker, NewArchetypeWatch } from "@/components/japan";

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

  return (
    <div className="space-y-10">
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

      {/* Moved from Meta Overview tab */}
      <section>
        <NewArchetypeWatch limit={9} />
      </section>

      <section>
        <CardInnovationTracker limit={20} />
      </section>
    </div>
  );
}
