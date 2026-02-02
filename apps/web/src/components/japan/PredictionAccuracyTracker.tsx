"use client";

import { format, parseISO } from "date-fns";
import {
  CheckCircle2,
  XCircle,
  CircleDot,
  AlertCircle,
  Target,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { usePredictions } from "@/hooks/useJapan";
import type { ApiPrediction } from "@trainerlab/shared-types";

function OutcomeIcon({ outcome }: { outcome: string | null | undefined }) {
  if (outcome === "correct") {
    return <CheckCircle2 className="h-4 w-4 text-green-500" />;
  }
  if (outcome === "incorrect") {
    return <XCircle className="h-4 w-4 text-red-500" />;
  }
  if (outcome === "partial") {
    return <CircleDot className="h-4 w-4 text-yellow-500" />;
  }
  return <Target className="h-4 w-4 text-muted-foreground" />;
}

function ConfidenceBadge({
  confidence,
}: {
  confidence: string | null | undefined;
}) {
  if (confidence === "high") {
    return <Badge variant="default">High</Badge>;
  }
  if (confidence === "medium") {
    return <Badge variant="secondary">Medium</Badge>;
  }
  if (confidence === "low") {
    return <Badge variant="outline">Low</Badge>;
  }
  return null;
}

function PredictionRow({ prediction }: { prediction: ApiPrediction }) {
  const createdDate = format(parseISO(prediction.created_at), "MMM d, yyyy");
  const resolvedDate = prediction.resolved_at
    ? format(parseISO(prediction.resolved_at), "MMM d, yyyy")
    : null;
  const isResolved = !!prediction.resolved_at;

  return (
    <div className="border-b last:border-0 py-3">
      <div className="flex items-start gap-3">
        <OutcomeIcon outcome={prediction.outcome} />
        <div className="flex-1 min-w-0">
          <p className="font-medium">{prediction.prediction_text}</p>
          <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-muted-foreground">
            <span>{prediction.target_event}</span>
            {prediction.category && (
              <Badge variant="outline" className="text-xs">
                {prediction.category}
              </Badge>
            )}
            <ConfidenceBadge confidence={prediction.confidence} />
          </div>
          {prediction.reasoning && (
            <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
              {prediction.reasoning}
            </p>
          )}
          {isResolved && prediction.outcome_notes && (
            <p className="mt-2 text-sm italic">
              Outcome: {prediction.outcome_notes}
            </p>
          )}
        </div>
        <div className="text-right text-sm text-muted-foreground shrink-0">
          <div>{createdDate}</div>
          {resolvedDate && (
            <div className="text-xs">Resolved: {resolvedDate}</div>
          )}
        </div>
      </div>
    </div>
  );
}

interface PredictionAccuracyTrackerProps {
  className?: string;
  limit?: number;
}

export function PredictionAccuracyTracker({
  className,
  limit = 10,
}: PredictionAccuracyTrackerProps) {
  const { data, isLoading, error } = usePredictions({ limit });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Prediction Accuracy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load predictions
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Prediction Accuracy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-16 animate-pulse rounded bg-muted" />
            <div className="h-24 animate-pulse rounded bg-muted" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const predictions = data?.items ?? [];
  const stats = {
    total: data?.total ?? 0,
    resolved: data?.resolved ?? 0,
    correct: data?.correct ?? 0,
    partial: data?.partial ?? 0,
    incorrect: data?.incorrect ?? 0,
    accuracyRate: data?.accuracy_rate,
  };

  const accuracyPercent = stats.accuracyRate
    ? (stats.accuracyRate * 100).toFixed(0)
    : null;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Prediction Accuracy Tracker</CardTitle>
        <p className="text-sm text-muted-foreground">
          Our track record: JP meta predictions vs actual EN outcomes
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Stats summary */}
        <div className="grid gap-4 sm:grid-cols-4">
          <div className="text-center p-3 bg-muted rounded-lg">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg dark:bg-green-950">
            <div className="text-2xl font-bold text-green-600">
              {stats.correct}
            </div>
            <div className="text-xs text-muted-foreground">Correct</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg dark:bg-yellow-950">
            <div className="text-2xl font-bold text-yellow-600">
              {stats.partial}
            </div>
            <div className="text-xs text-muted-foreground">Partial</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg dark:bg-red-950">
            <div className="text-2xl font-bold text-red-600">
              {stats.incorrect}
            </div>
            <div className="text-xs text-muted-foreground">Incorrect</div>
          </div>
        </div>

        {/* Accuracy bar */}
        {accuracyPercent && stats.resolved > 0 && (
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted-foreground">
                Overall Accuracy ({stats.resolved} resolved)
              </span>
              <span className="font-medium">{accuracyPercent}%</span>
            </div>
            <Progress value={Number(accuracyPercent)} className="h-2" />
          </div>
        )}

        {/* Prediction list */}
        {predictions.length === 0 ? (
          <p className="py-4 text-center text-muted-foreground">
            No predictions tracked yet
          </p>
        ) : (
          <div className="border-t pt-4">
            {predictions.map((prediction) => (
              <PredictionRow key={prediction.id} prediction={prediction} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
