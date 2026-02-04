"use client";

import { CheckCircle2, XCircle, MinusCircle } from "lucide-react";
import { TierBadge } from "@/components/ui/tier-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { safeFormatDate } from "@/lib/date-utils";
import type { ApiArchetypePrediction, PredictionTier } from "@trainerlab/shared-types";

interface PredictionAccuracyTableProps {
  predictions: ApiArchetypePrediction[];
  className?: string;
}

function isValidTier(tier: string | null | undefined): tier is PredictionTier {
  return (
    tier === "S" ||
    tier === "A" ||
    tier === "B" ||
    tier === "C" ||
    tier === "Rogue"
  );
}

function getAccuracyIcon(score: number | null | undefined) {
  if (score === null || score === undefined) {
    return <MinusCircle className="h-4 w-4 text-muted-foreground" />;
  }
  if (score >= 0.8) {
    return <CheckCircle2 className="h-4 w-4 text-green-500" />;
  }
  if (score >= 0.5) {
    return <MinusCircle className="h-4 w-4 text-amber-500" />;
  }
  return <XCircle className="h-4 w-4 text-red-500" />;
}

function getAccuracyClass(score: number | null | undefined): string {
  if (score === null || score === undefined) return "text-muted-foreground";
  if (score >= 0.8) return "text-green-500";
  if (score >= 0.5) return "text-amber-500";
  return "text-red-500";
}

export function PredictionAccuracyTable({
  predictions,
  className,
}: PredictionAccuracyTableProps) {
  if (!predictions.length) {
    return (
      <div className={cn("text-center text-muted-foreground py-8", className)}>
        No scored predictions yet
      </div>
    );
  }

  return (
    <div className={cn("rounded-lg border overflow-hidden", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Archetype</TableHead>
            <TableHead>Tier</TableHead>
            <TableHead className="text-right">Predicted</TableHead>
            <TableHead className="text-right">Actual</TableHead>
            <TableHead className="text-right">Accuracy</TableHead>
            <TableHead>Date</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {predictions.map((prediction) => {
            const predictedMid = prediction.predicted_meta_share?.mid;
            const date = safeFormatDate(prediction.created_at, "MMM d");

            return (
              <TableRow key={prediction.id}>
                <TableCell className="font-medium">
                  {prediction.archetype_id}
                </TableCell>
                <TableCell>
                  {isValidTier(prediction.predicted_tier) ? (
                    <TierBadge tier={prediction.predicted_tier} />
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell className="text-right font-mono">
                  {predictedMid !== null && predictedMid !== undefined
                    ? `${(predictedMid * 100).toFixed(1)}%`
                    : "—"}
                </TableCell>
                <TableCell className="text-right font-mono">
                  {prediction.actual_meta_share !== null &&
                  prediction.actual_meta_share !== undefined
                    ? `${(prediction.actual_meta_share * 100).toFixed(1)}%`
                    : "—"}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {getAccuracyIcon(prediction.accuracy_score)}
                    <span
                      className={cn(
                        "font-mono",
                        getAccuracyClass(prediction.accuracy_score)
                      )}
                    >
                      {prediction.accuracy_score !== null &&
                      prediction.accuracy_score !== undefined
                        ? `${(prediction.accuracy_score * 100).toFixed(0)}%`
                        : "—"}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">{date}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
