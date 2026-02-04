import { format, parseISO } from "date-fns";

export function safeFormatDate(
  dateStr: string | null | undefined,
  formatStr: string,
  fallback = "—"
): string {
  if (!dateStr) return fallback;
  try {
    return format(parseISO(dateStr), formatStr);
  } catch {
    console.error("Invalid date format:", dateStr);
    return fallback;
  }
}
