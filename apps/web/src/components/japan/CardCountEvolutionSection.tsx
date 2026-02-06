"use client";

import { AlertCircle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChartErrorBoundary } from "@/components/meta/ChartErrorBoundary";
import { useCardCountEvolution } from "@/hooks/useJapan";
import { CardCountEvolutionChart } from "./CardCountEvolutionChart";

interface CardCountEvolutionSectionProps {
  archetypes: string[];
  selectedArchetype: string;
  onArchetypeChange: (archetype: string) => void;
  className?: string;
}

export function CardCountEvolutionSection({
  archetypes,
  selectedArchetype,
  onArchetypeChange,
  className,
}: CardCountEvolutionSectionProps) {
  const { data, isLoading, error } = useCardCountEvolution(
    selectedArchetype ? { archetype: selectedArchetype } : null
  );

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Card Count Evolution (BO1)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load card count data
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={className} data-testid="card-count-section">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Card Count Evolution (BO1)</h2>
          <p className="text-sm text-muted-foreground">
            How average card copies change over time within an archetype
          </p>
        </div>
        {archetypes.length > 0 && (
          <Select value={selectedArchetype} onValueChange={onArchetypeChange}>
            <SelectTrigger
              className="w-[220px]"
              data-testid="archetype-selector"
            >
              <SelectValue placeholder="Select archetype" />
            </SelectTrigger>
            <SelectContent>
              {archetypes.map((a) => (
                <SelectItem key={a} value={a}>
                  {a}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {isLoading ? (
        <Card>
          <CardContent className="pt-6">
            <div className="h-[350px] animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <ChartErrorBoundary chartName="Card Count Evolution (BO1)">
              <CardCountEvolutionChart cards={data?.cards ?? []} />
            </ChartErrorBoundary>
            {data && data.tournaments_analyzed > 0 && (
              <p className="mt-2 text-xs text-muted-foreground text-center">
                Based on {data.tournaments_analyzed} tournament
                {data.tournaments_analyzed !== 1 ? "s" : ""}
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
