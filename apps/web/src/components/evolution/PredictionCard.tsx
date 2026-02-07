"use client";

import { TrendingUp, AlertCircle, Flag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TierBadge } from "@/components/ui/tier-badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type {
  ApiArchetypePrediction,
  PredictionTier,
} from "@trainerlab/shared-types";

interface PredictionCardProps {
  prediction: ApiArchetypePrediction;
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

export function PredictionCard({ prediction, className }: PredictionCardProps) {
  const metaShare = prediction.predicted_meta_share;
  const day2Rate = prediction.predicted_day2_rate;
  const confidencePercent = prediction.confidence
    ? prediction.confidence * 100
    : null;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-teal-500" />
            Prediction
          </CardTitle>
          {isValidTier(prediction.predicted_tier) && (
            <TierBadge tier={prediction.predicted_tier} size="md" />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {metaShare && (
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground">Expected Meta Share</span>
              <span className="font-mono font-medium">
                {(metaShare.low * 100).toFixed(1)}% -{" "}
                {(metaShare.high * 100).toFixed(1)}%
              </span>
            </div>
            <div className="relative h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="absolute h-full bg-teal-500/30"
                style={{
                  left: `${metaShare.low * 100 * 2}%`,
                  width: `${(metaShare.high - metaShare.low) * 100 * 2}%`,
                }}
              />
              <div
                className="absolute w-1 h-full bg-teal-500"
                style={{ left: `${metaShare.mid * 100 * 2}%` }}
              />
            </div>
            <div className="text-xs text-muted-foreground text-center mt-1">
              Most likely: {(metaShare.mid * 100).toFixed(1)}%
            </div>
          </div>
        )}

        {day2Rate && (
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground">Expected Day 2 Rate</span>
              <span className="font-mono font-medium">
                {(day2Rate.low * 100).toFixed(1)}% -{" "}
                {(day2Rate.high * 100).toFixed(1)}%
              </span>
            </div>
            <div className="relative h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="absolute h-full bg-amber-500/30"
                style={{
                  left: `${day2Rate.low * 100 * 2}%`,
                  width: `${(day2Rate.high - day2Rate.low) * 100 * 2}%`,
                }}
              />
              <div
                className="absolute w-1 h-full bg-amber-500"
                style={{ left: `${day2Rate.mid * 100 * 2}%` }}
              />
            </div>
          </div>
        )}

        {confidencePercent !== null && (
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground">Confidence</span>
              <span className="font-mono font-medium">
                {confidencePercent.toFixed(0)}%
              </span>
            </div>
            <Progress value={confidencePercent} className="h-1.5" />
          </div>
        )}

        {prediction.likely_adaptations &&
          prediction.likely_adaptations.length > 0 && (
            <div className="pt-2 border-t">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                <Flag className="h-3.5 w-3.5 text-blue-500" />
                <span>Expected Adaptations</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {prediction.likely_adaptations.map((adaptation, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {adaptation.description || adaptation.type || "Unknown"}
                  </Badge>
                ))}
              </div>
            </div>
          )}

        {prediction.actual_meta_share != null && (
          <div className="pt-2 border-t bg-muted/50 -mx-6 -mb-6 px-6 py-3 mt-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <span className="text-sm">
                Actual result:{" "}
                <span className="font-mono font-medium">
                  {(prediction.actual_meta_share * 100).toFixed(1)}%
                </span>
                {prediction.accuracy_score != null && (
                  <span className="text-muted-foreground ml-2">
                    ({(prediction.accuracy_score * 100).toFixed(0)}% accurate)
                  </span>
                )}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
