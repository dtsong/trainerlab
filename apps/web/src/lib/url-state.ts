export function parseEnumParam<T extends string>(
  value: string | null,
  validValues: readonly T[],
  defaultValue: T
): T {
  if (!value) return defaultValue;
  return validValues.includes(value as T) ? (value as T) : defaultValue;
}

interface ParseIntOptions {
  defaultValue: number;
  min?: number;
  max?: number;
}

export function parseIntParam(
  value: string | null,
  { defaultValue, min, max }: ParseIntOptions
): number {
  if (!value) return defaultValue;
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) return defaultValue;
  if (min !== undefined && parsed < min) return defaultValue;
  if (max !== undefined && parsed > max) return defaultValue;
  return parsed;
}

interface ParseStringOptions {
  defaultValue?: string;
  trim?: boolean;
}

export function parseStringParam(
  value: string | null,
  { defaultValue = "", trim = true }: ParseStringOptions = {}
): string {
  if (value === null) return defaultValue;
  const next = trim ? value.trim() : value;
  return next === "" ? defaultValue : next;
}

type ParamValue = string | number | null | undefined;
type SearchParamSource = { toString: () => string };

export function mergeSearchParams(
  currentParams: SearchParamSource,
  updates: Record<string, ParamValue>,
  defaults: Partial<Record<string, string | number>> = {}
): string {
  const params = new URLSearchParams(currentParams.toString());

  for (const [key, value] of Object.entries(updates)) {
    const defaultValue = defaults[key];
    if (
      value === null ||
      value === undefined ||
      value === "" ||
      (defaultValue !== undefined && String(value) === String(defaultValue))
    ) {
      params.delete(key);
      continue;
    }

    params.set(key, String(value));
  }

  return params.toString();
}

export function buildPathWithQuery(path: string, query: string): string {
  return query ? `${path}?${query}` : path;
}
