export const ADMIN_EMAILS = ["daniel@appraisehq.ai"] as const;

export function isAdminEmail(email: string | null | undefined): boolean {
  if (!email) return false;
  return (ADMIN_EMAILS as readonly string[]).includes(email);
}
