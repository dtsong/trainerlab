"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  CalendarDays,
  Eye,
  Lock,
  RefreshCw,
  Share2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  EvolutionTimeline,
  EvolutionChart,
  AdaptationLog,
  PredictionCard,
} from "@/components/evolution";
import {
  useEvolutionArticle,
  useArchetypePrediction,
} from "@/hooks/useEvolution";

interface EvolutionArticlePageClientProps {
  slug: string;
}

export function EvolutionArticlePageClient({
  slug,
}: EvolutionArticlePageClientProps) {
  const {
    data: article,
    isLoading,
    isError,
    refetch,
  } = useEvolutionArticle(slug);
  const {
    data: prediction,
    isError: isPredictionError,
    refetch: refetchPrediction,
  } = useArchetypePrediction(article?.archetype_id ?? null);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-5xl">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-24 bg-muted rounded" />
          <div className="h-10 w-full bg-muted rounded" />
          <div className="h-4 w-48 bg-muted rounded" />
          <div className="h-64 w-full bg-muted rounded mt-8" />
        </div>
      </div>
    );
  }

  if (isError || !article) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-5xl">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">Failed to load article</p>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const publishedDate = article.published_at
    ? new Date(article.published_at)
    : null;
  const formattedDate = publishedDate
    ? publishedDate.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    : null;

  const allAdaptations = article.snapshots.flatMap((s) => s.adaptations);

  return (
    <article className="container mx-auto py-8 px-4 max-w-5xl">
      <Link
        href="/evolution"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Evolution
      </Link>

      <header className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Badge
            variant="outline"
            className="bg-teal-500/10 text-teal-600 border-teal-500/30"
          >
            {article.archetype_id}
          </Badge>
          {article.is_premium && (
            <div className="flex items-center gap-1 text-amber-500 text-sm">
              <Lock className="h-4 w-4" />
              <span>Premium</span>
            </div>
          )}
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold mb-4">{article.title}</h1>

        {article.excerpt && (
          <p className="text-lg text-muted-foreground mb-4">
            {article.excerpt}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          {formattedDate && (
            <div className="flex items-center gap-1.5">
              <CalendarDays className="h-4 w-4" />
              <span>{formattedDate}</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <Eye className="h-4 w-4" />
            <span>{article.view_count.toLocaleString()} views</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Share2 className="h-4 w-4" />
            <span>{article.share_count} shares</span>
          </div>
        </div>
      </header>

      {article.introduction && (
        <div className="prose prose-slate dark:prose-invert max-w-none mb-8">
          <p className="text-lg leading-relaxed">{article.introduction}</p>
        </div>
      )}

      <Tabs defaultValue="timeline" className="mb-8">
        <TabsList>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="chart">Chart</TabsTrigger>
          <TabsTrigger value="adaptations">
            Adaptations ({allAdaptations.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Evolution Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <EvolutionTimeline snapshots={article.snapshots} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chart" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <EvolutionChart snapshots={article.snapshots} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="adaptations" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>All Adaptations</CardTitle>
            </CardHeader>
            <CardContent>
              <AdaptationLog adaptations={allAdaptations} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {isPredictionError ? (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Current Prediction</h2>
          <Card className="border-amber-500/50">
            <CardContent className="py-6 text-center">
              <AlertCircle className="h-8 w-8 mx-auto text-amber-500 mb-3" />
              <p className="text-amber-600 dark:text-amber-400 mb-3">
                Unable to load prediction data
              </p>
              <Button
                onClick={() => refetchPrediction()}
                variant="outline"
                size="sm"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : prediction ? (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Current Prediction</h2>
          <PredictionCard prediction={prediction} />
        </div>
      ) : null}

      {article.conclusion && (
        <div className="prose prose-slate dark:prose-invert max-w-none mb-8">
          <h2 className="text-xl font-semibold mb-4">Conclusion</h2>
          <p className="leading-relaxed">{article.conclusion}</p>
        </div>
      )}

      <footer className="mt-12 pt-8 border-t border-border">
        <Link
          href="/evolution"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Evolution
        </Link>
      </footer>
    </article>
  );
}
