import type {
  AdminAccessGrant,
  AdminAccessUser,
  AdminAuditEvent,
} from "@/lib/api";

export const ACCESS_AUDIT_ACTIONS = new Set([
  "beta.grant",
  "beta.revoke",
  "subscriber.grant",
  "subscriber.revoke",
  "beta.invite_grant",
  "beta.invite_revoke",
  "subscriber.invite_grant",
  "subscriber.invite_revoke",
]);

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function parseEmailLines(input: string): string[] {
  const lines = input
    .split(/\r?\n/)
    .map((line) => normalizeEmail(line))
    .filter((line) => line.length > 0);
  return Array.from(new Set(lines));
}

export function filterUsersByEmail(
  users: AdminAccessUser[] | undefined,
  query: string
): AdminAccessUser[] {
  if (!users) {
    return [];
  }

  const normalizedQuery = normalizeEmail(query);
  if (!normalizedQuery) {
    return users;
  }

  return users.filter((user) => user.email.includes(normalizedQuery));
}

export function filterGrantsByEmail(
  grants: AdminAccessGrant[] | undefined,
  query: string
): AdminAccessGrant[] {
  if (!grants) {
    return [];
  }

  const normalizedQuery = normalizeEmail(query);
  if (!normalizedQuery) {
    return grants;
  }

  return grants.filter((grant) => grant.email.includes(normalizedQuery));
}

export function filterRecentAccessEvents(
  events: AdminAuditEvent[] | undefined,
  query: string
): AdminAuditEvent[] {
  if (!events) {
    return [];
  }

  const normalizedQuery = normalizeEmail(query);
  return events
    .filter((event) => ACCESS_AUDIT_ACTIONS.has(event.action))
    .filter((event) => {
      if (!normalizedQuery) {
        return true;
      }

      return (
        event.target_email.includes(normalizedQuery) ||
        event.actor_email.includes(normalizedQuery)
      );
    });
}

export function formatWhen(value: string): string {
  return value.replace(".000", "");
}
