export type OgImageType =
  | "widget"
  | "lab-note"
  | "evolution"
  | "archetype"
  | "meta";

export interface OgImageDescriptor {
  type: OgImageType;
  id?: string;
  slug?: string;
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function stripPngSuffix(value: string): string {
  return value.replace(/\.png$/i, "");
}

export function humanizeSlug(value: string): string {
  const normalized = value.replace(/[-_]+/g, " ").trim();
  if (!normalized) return "Untitled";
  return normalized.replace(/\b\w/g, (char) => char.toUpperCase());
}

export function parseOgPath(slugSegments: string[]): OgImageDescriptor | null {
  if (slugSegments.length === 0) return null;

  const [head, second] = slugSegments.map(safeDecode);

  if (slugSegments.length === 1) {
    if (head.toLowerCase() === "meta.png") {
      return { type: "meta" };
    }

    const widgetMatch = stripPngSuffix(head).match(/^w_(.+)$/i);
    if (widgetMatch?.[1]) {
      return { type: "widget", id: widgetMatch[1] };
    }

    return null;
  }

  if (!second) return null;

  const cleanSecond = stripPngSuffix(second);

  if (head === "lab-notes" && cleanSecond) {
    return { type: "lab-note", slug: cleanSecond };
  }

  if (head === "evolution" && cleanSecond) {
    return { type: "evolution", slug: cleanSecond };
  }

  if (head === "archetypes" && cleanSecond) {
    return { type: "archetype", id: cleanSecond };
  }

  return null;
}
