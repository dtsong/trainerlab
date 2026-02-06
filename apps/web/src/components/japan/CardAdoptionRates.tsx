"use client";

import { AlertCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useJPAdoptionRates } from "@/hooks/useTranslations";
import type { ApiJPAdoptionRate } from "@trainerlab/shared-types";

function RateBar({ rate }: { rate: number }) {
  const percent = Math.round(rate * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 overflow-hidden rounded-full bg-muted">
        <div className="h-full bg-teal-500" style={{ width: `${percent}%` }} />
      </div>
      <span className="font-mono text-sm">{percent}%</span>
    </div>
  );
}

function RateRow({ rate }: { rate: ApiJPAdoptionRate }) {
  return (
    <TableRow>
      <TableCell className="font-medium">
        <div className="flex flex-col">
          <span>{rate.card_name_en || rate.card_name_jp || rate.card_id}</span>
          {rate.card_name_en && rate.card_name_jp && (
            <span className="text-xs text-muted-foreground">
              {rate.card_name_jp}
            </span>
          )}
        </div>
      </TableCell>
      <TableCell>
        <RateBar rate={rate.inclusion_rate} />
      </TableCell>
      <TableCell className="font-mono">
        {rate.avg_copies?.toFixed(1) ?? "-"}
      </TableCell>
      <TableCell>
        {rate.archetype_context ? (
          <Badge variant="secondary" className="text-xs">
            {rate.archetype_context}
          </Badge>
        ) : (
          <span className="text-muted-foreground">All</span>
        )}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {rate.period_start} - {rate.period_end}
      </TableCell>
    </TableRow>
  );
}

interface CardAdoptionRatesProps {
  className?: string;
  limit?: number;
  days?: number;
  archetype?: string;
}

export function CardAdoptionRates({
  className,
  limit = 20,
  days = 30,
  archetype,
}: CardAdoptionRatesProps) {
  const { data, isLoading, error } = useJPAdoptionRates({
    limit,
    days,
    archetype,
  });

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Card Adoption Rates (BO1)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to load adoption rates
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Card Adoption Rates (BO1)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const rates = data?.rates ?? [];

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Card Adoption Rates (BO1)</CardTitle>
        <p className="text-sm text-muted-foreground">
          Most-used cards in JP meta (last {days} days)
        </p>
      </CardHeader>
      <CardContent>
        {rates.length === 0 ? (
          <p className="py-8 text-center text-muted-foreground">
            No adoption rate data available
          </p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Card</TableHead>
                  <TableHead>Inclusion Rate</TableHead>
                  <TableHead>Avg Copies</TableHead>
                  <TableHead>Archetype</TableHead>
                  <TableHead>Period</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rates.map((rate) => (
                  <RateRow key={rate.id} rate={rate} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
