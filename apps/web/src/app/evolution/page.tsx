"use client";

import { Suspense, useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  FileText,
  RefreshCw,
  TrendingUp,
  Clock,
  Lock,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useEvolutionArticles } from "@/hooks/useEvolution";
import {
  buildPathWithQuery,
  mergeSearchParams,
  parseIntParam,
} from "@/lib/url-state";

function EvolutionPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlPage = parseIntParam(searchParams.get("page"), {
    defaultValue: 1,
    min: 1,
  });

  const [page, setPage] = useState(urlPage);
  const limit = 12;

  useEffect(() => {
    if (page !== urlPage) {
      setPage(urlPage);
    }
  }, [page, urlPage]);

  const updateUrl = (nextPage: number, navigationMode: "replace" | "push") => {
    const normalizedPage = Math.max(1, nextPage);
    const query = mergeSearchParams(
      searchParams,
      { page: normalizedPage },
      { page: 1 }
    );
    const href = buildPathWithQuery("/evolution", query);
    if (navigationMode === "replace") {
      router.replace(href, { scroll: false });
      return;
    }
    router.push(href, { scroll: false });
  };

  const { data, isLoading, isError, refetch } = useEvolutionArticles({
    limit,
    offset: (page - 1) * limit,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Deck Evolution</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 bg-muted rounded" />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-64 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Deck Evolution</h1>
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">
              Failed to load evolution articles
            </p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const articles = data || [];

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-teal-500" />
            Deck Evolution
          </h1>
          <p className="text-muted-foreground">
            Track how top archetypes adapt and evolve through the competitive
            season
          </p>
        </div>
        <Link href="/evolution/accuracy">
          <Button variant="outline">View Prediction Accuracy</Button>
        </Link>
      </div>

      {articles.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No evolution articles available yet.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {articles.map((article) => (
              <Link key={article.id} href={`/evolution/${article.slug}`}>
                <Card className="h-full hover:border-teal-500/50 transition-colors cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-2 mb-3">
                      <Badge
                        variant="outline"
                        className="bg-teal-500/10 text-teal-600 border-teal-500/30"
                      >
                        {article.archetype_id}
                      </Badge>
                      {article.is_premium && (
                        <div className="flex items-center gap-1 text-amber-500">
                          <Lock className="h-3.5 w-3.5" />
                        </div>
                      )}
                    </div>

                    <h2 className="font-semibold text-lg mb-2 line-clamp-2">
                      {article.title}
                    </h2>

                    {article.excerpt && (
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-3">
                        {article.excerpt}
                      </p>
                    )}

                    {article.published_at && (
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-auto">
                        <Clock className="h-3.5 w-3.5" />
                        {new Date(article.published_at).toLocaleDateString(
                          "en-US",
                          {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          }
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {articles.length >= limit && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <Button
                variant="outline"
                disabled={page === 1}
                onClick={() => {
                  const nextPage = page - 1;
                  setPage(nextPage);
                  updateUrl(nextPage, "push");
                }}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">Page {page}</span>
              <Button
                variant="outline"
                disabled={articles.length < limit}
                onClick={() => {
                  const nextPage = page + 1;
                  setPage(nextPage);
                  updateUrl(nextPage, "push");
                }}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EvolutionPageFallback() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Deck Evolution</h1>
      <div className="animate-pulse space-y-4">
        <div className="h-6 w-48 bg-muted rounded" />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-muted rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function EvolutionPage() {
  return (
    <Suspense fallback={<EvolutionPageFallback />}>
      <EvolutionPageContent />
    </Suspense>
  );
}
