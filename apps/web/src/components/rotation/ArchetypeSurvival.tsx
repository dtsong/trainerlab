"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { ApiRotationImpact } from "@trainerlab/shared-types";

import { SurvivalBadge } from "./SurvivalBadge";

interface ArchetypeSurvivalProps {
  impact: ApiRotationImpact;
}

export function ArchetypeSurvival({ impact }: ArchetypeSurvivalProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasDetails =
    (impact.rotating_cards && impact.rotating_cards.length > 0) ||
    impact.analysis ||
    impact.jp_evidence;

  return (
    <Card className="transition-colors hover:border-primary/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium">
            {impact.archetype_name}
          </CardTitle>
          <SurvivalBadge rating={impact.survival_rating} />
        </div>
        {impact.jp_survival_share !== null &&
          impact.jp_survival_share !== undefined && (
            <div className="text-sm text-muted-foreground">
              JP Post-Rotation Share:{" "}
              {(impact.jp_survival_share * 100).toFixed(1)}%
            </div>
          )}
      </CardHeader>

      {hasDetails && (
        <CardContent className="pt-0">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4" />
                Hide details
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" />
                Show details
              </>
            )}
          </button>

          {isExpanded && (
            <div className="mt-4 space-y-4">
              {impact.rotating_cards && impact.rotating_cards.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Rotating Cards</h4>
                  <div className="space-y-2">
                    {impact.rotating_cards.map((card, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-sm"
                      >
                        <div className="flex items-center gap-2">
                          <span>{card.card_name}</span>
                          <span className="text-muted-foreground">
                            ×{card.count}
                          </span>
                          {card.role && (
                            <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                              {card.role}
                            </span>
                          )}
                        </div>
                        {card.replacement && (
                          <span className="text-green-400 text-xs">
                            → {card.replacement}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {impact.jp_evidence && (
                <div>
                  <h4 className="text-sm font-medium mb-2">JP Evidence</h4>
                  <p className="text-sm text-muted-foreground">
                    {impact.jp_evidence}
                  </p>
                </div>
              )}

              {impact.analysis && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Analysis</h4>
                  <p className="text-sm text-muted-foreground">
                    {impact.analysis}
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
