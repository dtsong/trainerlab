import { describe, expect, it } from "vitest";

import {
  filterGrantsByEmail,
  filterRecentAccessEvents,
  filterUsersByEmail,
  parseEmailLines,
} from "../utils";

describe("admin access utils", () => {
  it("deduplicates and normalizes batch email input", () => {
    const parsed = parseEmailLines(
      " A@EXAMPLE.com\na@example.com\n\nB@example.com "
    );

    expect(parsed).toEqual(["a@example.com", "b@example.com"]);
  });

  it("filters users and grants by email query", () => {
    const users = [
      { id: "u1", email: "alice@example.com" },
      { id: "u2", email: "bob@example.com" },
    ] as never[];
    const grants = [
      { id: "g1", email: "alice@example.com" },
      { id: "g2", email: "carol@example.com" },
    ] as never[];

    expect(filterUsersByEmail(users, "ali")).toHaveLength(1);
    expect(filterGrantsByEmail(grants, "car")).toHaveLength(1);
  });

  it("keeps only access-related audit events", () => {
    const events = [
      {
        id: "a1",
        action: "beta.grant",
        actor_email: "admin@trainerlab.io",
        target_email: "alice@example.com",
      },
      {
        id: "a2",
        action: "cards.placeholder.create",
        actor_email: "admin@trainerlab.io",
        target_email: "-",
      },
    ] as never[];

    const filtered = filterRecentAccessEvents(events, "alice");
    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.id).toBe("a1");
  });
});
