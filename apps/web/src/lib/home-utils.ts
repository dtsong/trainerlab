import type {
  ApiMetaSnapshot,
  ApiMetaHistoryResponse,
} from "@trainerlab/shared-types";

// --- Types ---

export interface ArchetypeWithTrend {
  rank: number;
  name: string;
  metaShare: number;
  trend: "up" | "down" | "stable";
  trendValue?: number;
  jpSignal?: number;
}

export interface JPDivergenceResult {
  hasSignificantDivergence: boolean;
  message: string;
}

export interface JPComparison {
  rank: number;
  jpName: string;
  jpShare: number;
  enName: string;
  enShare: number;
  divergence: number;
}

export interface HeroStats {
  tournamentCount: string;
  decklistCount: string;
  upcomingEvents: string;
}

export interface MetaMover {
  name: string;
  changeDirection: "up" | "down";
  changeValue: number;
  currentShare: number;
}

// --- Thresholds (percentage points) ---

const TREND_THRESHOLD_PP = 0.5;
const JP_SIGNAL_THRESHOLD_PP = 2;
const JP_DIVERGENCE_THRESHOLD_PP = 5;

const EXCLUDED_ARCHETYPES = new Set(["Unknown", "unknown", ""]);
const MIN_DIVERGENCE_SHARE = 0.01; // 1% minimum share to surface in banner

/**
 * Capitalize lowercase archetype names as a cosmetic safety net.
 * Only capitalizes if the entire name is lowercase (preserves proper names like "Charizard ex").
 */
function formatArchetypeName(name: string): string {
  if (name === name.toLowerCase()) {
    return name
      .split(" ")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }
  return name;
}

// --- Functions ---

/**
 * Compare current archetype shares vs previous snapshot from history.
 * Diff strictly >0.5pp = up/down, <=0.5pp = stable.
 * JP signal = JP share minus global share (only when abs difference strictly >2pp).
 */
export function computeTrends(
  globalMeta: ApiMetaSnapshot | undefined,
  history: ApiMetaHistoryResponse | undefined,
  jpMeta: ApiMetaSnapshot | undefined,
  limit: number = 5
): ArchetypeWithTrend[] {
  if (!globalMeta?.archetype_breakdown?.length) return [];

  const previousSnapshot =
    history?.snapshots && history.snapshots.length > 1
      ? history.snapshots[history.snapshots.length - 2]
      : undefined;

  const previousMap = new Map<string, number>();
  if (previousSnapshot?.archetype_breakdown) {
    for (const arch of previousSnapshot.archetype_breakdown) {
      previousMap.set(arch.name, arch.share * 100);
    }
  }

  const jpMap = new Map<string, number>();
  if (jpMeta?.archetype_breakdown) {
    for (const arch of jpMeta.archetype_breakdown) {
      jpMap.set(arch.name, arch.share * 100);
    }
  }

  return globalMeta.archetype_breakdown.slice(0, limit).map((arch, index) => {
    const share = arch.share * 100;
    const previousShare = previousMap.get(arch.name);
    let trend: "up" | "down" | "stable" = "stable";
    let trendValue: number | undefined;

    if (previousShare !== undefined) {
      const diff = share - previousShare;
      trendValue = Math.round(diff * 10) / 10;
      if (diff > TREND_THRESHOLD_PP) trend = "up";
      else if (diff < -TREND_THRESHOLD_PP) trend = "down";
    }

    const jpShare = jpMap.get(arch.name);
    let jpSignal: number | undefined;
    if (jpShare !== undefined) {
      const divergence = jpShare - share;
      if (Math.abs(divergence) > JP_SIGNAL_THRESHOLD_PP) {
        jpSignal = Math.round(divergence * 10) / 10;
      }
    }

    return {
      rank: index + 1,
      name: arch.name,
      metaShare: share,
      trend,
      trendValue,
      jpSignal,
    };
  });
}

/**
 * Detect significant JP vs global meta divergence.
 * Significant = any archetype in JP top 5 not in global top 10, or with strictly >5pp share difference.
 */
export function computeJPDivergence(
  globalMeta: ApiMetaSnapshot | undefined,
  jpMeta: ApiMetaSnapshot | undefined
): JPDivergenceResult {
  const defaultResult: JPDivergenceResult = {
    hasSignificantDivergence: false,
    message: "",
  };

  if (
    !globalMeta?.archetype_breakdown?.length ||
    !jpMeta?.archetype_breakdown?.length
  ) {
    return defaultResult;
  }

  const filteredGlobal = globalMeta.archetype_breakdown.filter(
    (a) => !EXCLUDED_ARCHETYPES.has(a.name) && a.name.trim() !== ""
  );
  const filteredJP = jpMeta.archetype_breakdown.filter(
    (a) =>
      !EXCLUDED_ARCHETYPES.has(a.name) &&
      a.name.trim() !== "" &&
      a.share >= MIN_DIVERGENCE_SHARE
  );

  const globalNames = new Set(filteredGlobal.slice(0, 10).map((a) => a.name));
  const globalMap = new Map<string, number>();
  for (const arch of filteredGlobal) {
    globalMap.set(arch.name, arch.share * 100);
  }

  const divergentArchetypes: string[] = [];
  let maxDivergence = 0;

  for (const jpArch of filteredJP.slice(0, 5)) {
    const jpShare = jpArch.share * 100;
    const globalShare = globalMap.get(jpArch.name);

    if (!globalNames.has(jpArch.name)) {
      divergentArchetypes.push(jpArch.name);
      maxDivergence = Math.max(maxDivergence, jpShare);
    } else if (
      globalShare !== undefined &&
      Math.abs(jpShare - globalShare) > JP_DIVERGENCE_THRESHOLD_PP
    ) {
      divergentArchetypes.push(jpArch.name);
      maxDivergence = Math.max(maxDivergence, Math.abs(jpShare - globalShare));
    }
  }

  if (divergentArchetypes.length === 0) {
    return defaultResult;
  }

  const formattedNames = divergentArchetypes.map(formatArchetypeName);
  const archNames =
    formattedNames.length === 1
      ? formattedNames[0]
      : `${formattedNames.slice(0, -1).join(", ")} and ${formattedNames[formattedNames.length - 1]}`;

  return {
    hasSignificantDivergence: true,
    message: `Japan's meta is diverging: ${archNames} showing significant differences from the global meta.`,
  };
}

/**
 * Build side-by-side JP vs Global comparison rows.
 */
export function buildJPComparisons(
  globalMeta: ApiMetaSnapshot | undefined,
  jpMeta: ApiMetaSnapshot | undefined,
  limit: number = 3
): JPComparison[] {
  if (
    !globalMeta?.archetype_breakdown?.length ||
    !jpMeta?.archetype_breakdown?.length
  ) {
    return [];
  }

  const globalTop = globalMeta.archetype_breakdown.slice(0, limit);
  const jpTop = jpMeta.archetype_breakdown.slice(0, limit);

  const globalMap = new Map<string, number>();
  for (const arch of globalMeta.archetype_breakdown) {
    globalMap.set(arch.name, arch.share * 100);
  }

  return jpTop.map((jpArch, index) => {
    const globalArch = globalTop[index];
    const jpShare = jpArch.share * 100;
    const globalShareForJpArch = globalMap.get(jpArch.name) ?? 0;
    const divergence =
      globalShareForJpArch > 0
        ? Math.round(
            ((jpShare - globalShareForJpArch) / globalShareForJpArch) * 100
          )
        : 100;

    return {
      rank: index + 1,
      jpName: jpArch.name,
      jpShare,
      enName: globalArch?.name ?? "—",
      enShare: (globalArch?.share ?? 0) * 100,
      divergence: Math.abs(divergence),
    };
  });
}

/**
 * Format hero stat values.
 */
export function computeHeroStats(
  tournamentCount: number | undefined,
  sampleSize: number | undefined,
  upcomingCount: number | undefined
): HeroStats {
  return {
    tournamentCount:
      tournamentCount !== undefined ? String(tournamentCount) : "--",
    decklistCount: formatCount(sampleSize),
    upcomingEvents: upcomingCount !== undefined ? String(upcomingCount) : "--",
  };
}

/**
 * Compute top movers from meta history (biggest share changes between current and oldest snapshot).
 */
export function computeMetaMovers(
  currentMeta: ApiMetaSnapshot | undefined,
  history: ApiMetaHistoryResponse | undefined,
  limit: number = 3
): MetaMover[] {
  if (
    !currentMeta?.archetype_breakdown?.length ||
    !history?.snapshots?.length
  ) {
    return [];
  }

  const oldestSnapshot = history.snapshots[0];
  if (!oldestSnapshot?.archetype_breakdown?.length) return [];

  const oldMap = new Map<string, number>();
  for (const arch of oldestSnapshot.archetype_breakdown) {
    oldMap.set(arch.name, arch.share * 100);
  }

  const movers: MetaMover[] = [];
  for (const arch of currentMeta.archetype_breakdown) {
    const share = arch.share * 100;
    const oldShare = oldMap.get(arch.name) ?? 0;
    const change = share - oldShare;
    if (Math.abs(change) > TREND_THRESHOLD_PP) {
      movers.push({
        name: arch.name,
        changeDirection: change > 0 ? "up" : "down",
        changeValue: Math.round(Math.abs(change) * 10) / 10,
        currentShare: share,
      });
    }
  }

  movers.sort((a, b) => b.changeValue - a.changeValue);
  return movers.slice(0, limit);
}

function formatCount(n: number | undefined): string {
  if (n === undefined) return "--";
  if (n >= 1000) {
    const k = Math.floor(n / 1000);
    return `${k}k+`;
  }
  return String(n);
}
