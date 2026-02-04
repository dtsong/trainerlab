"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  RefreshCw,
  Target,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { PredictionAccuracyTable } from "@/components/evolution";
import { usePredictionAccuracy } from "@/hooks/useEvolution";

export default function PredictionAccuracyPage() {
  const { data, isLoading, isError, refetch } = usePredictionAccuracy(50);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-24 bg-muted rounded" />
          <div className="h-10 w-64 bg-muted rounded" />
          <div className="grid gap-6 sm:grid-cols-3 mt-8">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-muted rounded-lg" />
            ))}
          </div>
          <div className="h-96 bg-muted rounded-lg mt-8" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="border-destructive">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <p className="text-destructive mb-4">
              Failed to load prediction accuracy
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

  const accuracyPercent = data?.average_accuracy
    ? data.average_accuracy * 100
    : null;

  return (
    <div className="container mx-auto py-8 px-4">
      <Link
        href="/evolution"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Evolution
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
          <Target className="h-8 w-8 text-teal-500" />
          Prediction Accuracy
        </h1>
        <p className="text-muted-foreground">
          Tracking how well our meta predictions perform against actual
          tournament results
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Predictions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data?.total_predictions ?? 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Scored Predictions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data?.scored_predictions ?? 0}
            </div>
            <div className="text-sm text-muted-foreground">
              {data?.total_predictions && data.total_predictions > 0
                ? `${(((data.scored_predictions ?? 0) / data.total_predictions) * 100).toFixed(0)}% resolved`
                : ""}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Average Accuracy
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div
                className={`text-3xl font-bold ${
                  accuracyPercent !== null
                    ? accuracyPercent >= 70
                      ? "text-green-500"
                      : accuracyPercent >= 50
                        ? "text-amber-500"
                        : "text-red-500"
                    : ""
                }`}
              >
                {accuracyPercent !== null
                  ? `${accuracyPercent.toFixed(0)}%`
                  : "—"}
              </div>
              <TrendingUp className="h-5 w-5 text-muted-foreground" />
            </div>
            {accuracyPercent !== null && (
              <Progress value={accuracyPercent} className="h-2 mt-2" />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Predictions</CardTitle>
        </CardHeader>
        <CardContent>
          <PredictionAccuracyTable predictions={data?.predictions ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}
