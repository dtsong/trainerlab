"use client";

import { memo, useCallback, useMemo, useRef } from "react";
import { TierBadge } from "@/components/ui/tier-badge";
import { TrendArrow } from "@/components/ui/trend-arrow";
import { JPSignalBadge } from "@/components/ui/jp-signal-badge";
import { cn } from "@/lib/utils";

export type Tier = "S" | "A" | "B" | "C" | "Rogue";

export interface ArchetypeData {
  id: string;
  name: string;
  tier: Tier;
  share: number;
  trend: "up" | "down" | "stable";
  trendValue?: number;
  jpShare?: number;
  signatureCardUrl?: string;
}

interface ArchetypeRowProps {
  archetype: ArchetypeData;
  onClick: (archetype: ArchetypeData) => void;
  isSelected: boolean;
  index: number;
  onKeyDown: (e: React.KeyboardEvent, index: number) => void;
}

const ArchetypeRow = memo(function ArchetypeRow({
  archetype,
  onClick,
  isSelected,
  index,
  onKeyDown,
}: ArchetypeRowProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(archetype)}
      onKeyDown={(e) => onKeyDown(e, index)}
      className={cn(
        "flex w-full items-center gap-4 px-4 py-3 text-left transition-colors",
        "hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-teal-500",
        isSelected && "bg-teal-50",
        index % 2 === 0 ? "bg-white" : "bg-slate-50/50"
      )}
      aria-pressed={isSelected}
      style={{ contentVisibility: "auto", containIntrinsicSize: "auto 56px" }}
    >
      {/* Signature card placeholder */}
      <div className="h-12 w-8 flex-shrink-0 rounded bg-gradient-to-br from-slate-200 to-slate-300" />

      {/* Name and share */}
      <div className="flex-1 min-w-0">
        <span className="font-medium text-slate-900 truncate block">
          {archetype.name}
        </span>
      </div>

      {/* Share percentage */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm text-slate-600">
          {archetype.share.toFixed(1)}%
        </span>
        <TrendArrow
          direction={archetype.trend}
          value={archetype.trendValue}
          size="sm"
        />
      </div>

      {/* JP Signal badge */}
      {archetype.jpShare !== undefined &&
        Math.abs(archetype.jpShare - archetype.share) > 5 && (
          <JPSignalBadge
            jpShare={archetype.jpShare}
            enShare={archetype.share}
            threshold={5}
          />
        )}
    </button>
  );
});

interface TierSectionProps {
  tier: Tier;
  archetypes: ArchetypeData[];
  onArchetypeClick: (archetype: ArchetypeData) => void;
  selectedId?: string;
  startIndex: number;
  onKeyDown: (e: React.KeyboardEvent, index: number) => void;
}

const TierSection = memo(function TierSection({
  tier,
  archetypes,
  onArchetypeClick,
  selectedId,
  startIndex,
  onKeyDown,
}: TierSectionProps) {
  if (archetypes.length === 0) return null;

  return (
    <div className="border-b border-slate-200 last:border-b-0">
      {/* Tier header */}
      <div className="flex items-center gap-2 bg-slate-100 px-4 py-2">
        <TierBadge tier={tier} size="md" />
        <span className="text-sm font-medium text-slate-600">
          {archetypes.length} {archetypes.length === 1 ? "deck" : "decks"}
        </span>
      </div>

      {/* Archetype rows */}
      {archetypes.map((archetype, idx) => (
        <ArchetypeRow
          key={archetype.id}
          archetype={archetype}
          onClick={onArchetypeClick}
          isSelected={archetype.id === selectedId}
          index={startIndex + idx}
          onKeyDown={onKeyDown}
        />
      ))}
    </div>
  );
});

export interface TierListProps {
  archetypes: ArchetypeData[];
  onArchetypeSelect: (archetype: ArchetypeData) => void;
  selectedArchetypeId?: string;
  className?: string;
}

export function TierList({
  archetypes,
  onArchetypeSelect,
  selectedArchetypeId,
  className,
}: TierListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Memoize tier grouping to avoid recalculation
  const { tierGroups, flatList, tierStartIndices } = useMemo(() => {
    const groups: Record<Tier, ArchetypeData[]> = {
      S: [],
      A: [],
      B: [],
      C: [],
      Rogue: [],
    };

    archetypes.forEach((archetype) => {
      groups[archetype.tier].push(archetype);
    });

    // Flatten for keyboard navigation
    const flat = [
      ...groups.S,
      ...groups.A,
      ...groups.B,
      ...groups.C,
      ...groups.Rogue,
    ];

    // Calculate start indices for each tier
    let idx = 0;
    const startIndices: Record<Tier, number> = {
      S: 0,
      A: 0,
      B: 0,
      C: 0,
      Rogue: 0,
    };

    (["S", "A", "B", "C", "Rogue"] as Tier[]).forEach((tier) => {
      startIndices[tier] = idx;
      idx += groups[tier].length;
    });

    return {
      tierGroups: groups,
      flatList: flat,
      tierStartIndices: startIndices,
    };
  }, [archetypes]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, currentIndex: number) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const nextIndex = Math.min(currentIndex + 1, flatList.length - 1);
        const buttons = listRef.current?.querySelectorAll("button");
        (buttons?.[nextIndex] as HTMLButtonElement)?.focus();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prevIndex = Math.max(currentIndex - 1, 0);
        const buttons = listRef.current?.querySelectorAll("button");
        (buttons?.[prevIndex] as HTMLButtonElement)?.focus();
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onArchetypeSelect(flatList[currentIndex]);
      }
    },
    [flatList, onArchetypeSelect]
  );

  return (
    <div
      ref={listRef}
      className={cn(
        "overflow-hidden rounded-lg border border-slate-200",
        className
      )}
      role="listbox"
      aria-label="Meta tier list"
    >
      <TierSection
        tier="S"
        archetypes={tierGroups.S}
        onArchetypeClick={onArchetypeSelect}
        selectedId={selectedArchetypeId}
        startIndex={tierStartIndices.S}
        onKeyDown={handleKeyDown}
      />
      <TierSection
        tier="A"
        archetypes={tierGroups.A}
        onArchetypeClick={onArchetypeSelect}
        selectedId={selectedArchetypeId}
        startIndex={tierStartIndices.A}
        onKeyDown={handleKeyDown}
      />
      <TierSection
        tier="B"
        archetypes={tierGroups.B}
        onArchetypeClick={onArchetypeSelect}
        selectedId={selectedArchetypeId}
        startIndex={tierStartIndices.B}
        onKeyDown={handleKeyDown}
      />
      <TierSection
        tier="C"
        archetypes={tierGroups.C}
        onArchetypeClick={onArchetypeSelect}
        selectedId={selectedArchetypeId}
        startIndex={tierStartIndices.C}
        onKeyDown={handleKeyDown}
      />
      <TierSection
        tier="Rogue"
        archetypes={tierGroups.Rogue}
        onArchetypeClick={onArchetypeSelect}
        selectedId={selectedArchetypeId}
        startIndex={tierStartIndices.Rogue}
        onKeyDown={handleKeyDown}
      />
    </div>
  );
}
