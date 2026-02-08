import { useQuery } from "@tanstack/react-query";
import { cardsApi } from "@/lib/api";

/**
 * Batch lookup card names and images by IDs.
 * Returns a map of cardId -> { name, imageSmall }.
 */
export function useCardBatchLookup(cardIds: string[]) {
  return useQuery({
    queryKey: ["cards", "batch", cardIds.sort().join(",")],
    queryFn: () => cardsApi.getBatch(cardIds),
    enabled: cardIds.length > 0,
    staleTime: 1000 * 60 * 15,
    select: (data) =>
      Object.fromEntries(
        data.map((c) => [
          c.id,
          { name: c.name, imageSmall: c.image_small ?? null },
        ])
      ),
  });
}
