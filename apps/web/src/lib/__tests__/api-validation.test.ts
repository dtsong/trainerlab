import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { z } from "zod";

import {
  validateApiResponse,
  ValidationError,
  PaginationFieldsSchema,
  CardSummarySchema,
  PaginatedCardSummarySchema,
  ArchetypeSchema,
  MetaSnapshotSchema,
  LabNoteSchema,
} from "../api-validation";

describe("ValidationError", () => {
  it("should create error with message and issues", () => {
    const issues = [
      {
        code: "invalid_type",
        expected: "string",
        received: "number",
        path: ["name"],
        message: "Expected string, received number",
      },
    ] as unknown as z.ZodIssue[];

    const error = new ValidationError("Validation failed", issues);

    expect(error.message).toBe("Validation failed");
    expect(error.issues).toEqual(issues);
    expect(error.name).toBe("ValidationError");
  });

  it("should be an instance of Error", () => {
    const error = new ValidationError("Test", []);

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ValidationError);
  });
});

describe("validateApiResponse", () => {
  const testSchema = z.object({
    id: z.string(),
    name: z.string(),
    count: z.number(),
  });

  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return parsed data on valid input", () => {
    const validData = { id: "1", name: "Test", count: 5 };

    const result = validateApiResponse(testSchema, validData, "/test/endpoint");

    expect(result).toEqual(validData);
  });

  it("should strip extra fields on valid input", () => {
    const dataWithExtra = { id: "1", name: "Test", count: 5, extra: "field" };

    const result = validateApiResponse(
      testSchema,
      dataWithExtra,
      "/test/endpoint"
    );

    expect(result).toEqual({ id: "1", name: "Test", count: 5 });
  });

  describe("in development mode", () => {
    const originalNodeEnv = process.env.NODE_ENV;

    beforeEach(() => {
      // @ts-expect-error - NODE_ENV reassignment for testing
      process.env.NODE_ENV = "development";
    });

    afterEach(() => {
      // @ts-expect-error - NODE_ENV reassignment for testing
      process.env.NODE_ENV = originalNodeEnv;
    });

    it("should throw ValidationError on invalid data", () => {
      const invalidData = { id: 123, name: "Test", count: "not a number" };

      expect(() =>
        validateApiResponse(testSchema, invalidData, "/test/endpoint")
      ).toThrow(ValidationError);
    });

    it("should include endpoint name in error message", () => {
      const invalidData = { id: 123 };

      try {
        validateApiResponse(testSchema, invalidData, "/api/v1/cards");
      } catch (error) {
        expect(error).toBeInstanceOf(ValidationError);
        expect((error as ValidationError).message).toContain("/api/v1/cards");
      }
    });

    it("should include issues in thrown error", () => {
      const invalidData = { id: 123, name: "Test", count: "bad" };

      try {
        validateApiResponse(testSchema, invalidData, "/test");
      } catch (error) {
        expect((error as ValidationError).issues.length).toBeGreaterThan(0);
      }
    });

    it("should log error to console on invalid data", () => {
      const invalidData = { id: 123 };

      try {
        validateApiResponse(testSchema, invalidData, "/test/endpoint");
      } catch {
        // expected
      }

      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining("API validation failed for /test/endpoint"),
        expect.any(Array)
      );
    });
  });

  describe("in production mode", () => {
    const originalNodeEnv = process.env.NODE_ENV;

    beforeEach(() => {
      // @ts-expect-error - NODE_ENV reassignment for testing
      process.env.NODE_ENV = "production";
    });

    afterEach(() => {
      // @ts-expect-error - NODE_ENV reassignment for testing
      process.env.NODE_ENV = originalNodeEnv;
    });

    it("should not throw on invalid data, return data as-is", () => {
      const invalidData = { id: 123, name: "Test", count: "bad" };

      const result = validateApiResponse(
        testSchema,
        invalidData,
        "/test/endpoint"
      );

      // In production, invalid data is returned as-is with a warning
      expect(result).toEqual(invalidData);
    });

    it("should log error and warning on invalid data", () => {
      const invalidData = { id: 123 };

      validateApiResponse(testSchema, invalidData, "/test/endpoint");

      expect(console.error).toHaveBeenCalled();
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining("Validation warning for /test/endpoint")
      );
    });
  });
});

describe("Zod schemas", () => {
  describe("PaginationFieldsSchema", () => {
    it("should validate valid pagination data", () => {
      const data = {
        total: 100,
        page: 1,
        limit: 20,
        has_next: true,
        has_prev: false,
        total_pages: 5,
      };

      expect(PaginationFieldsSchema.safeParse(data).success).toBe(true);
    });

    it("should accept optional next_cursor", () => {
      const data = {
        total: 100,
        page: 1,
        limit: 20,
        has_next: true,
        has_prev: false,
        total_pages: 5,
        next_cursor: "abc123",
      };

      expect(PaginationFieldsSchema.safeParse(data).success).toBe(true);
    });

    it("should accept null next_cursor", () => {
      const data = {
        total: 100,
        page: 1,
        limit: 20,
        has_next: true,
        has_prev: false,
        total_pages: 5,
        next_cursor: null,
      };

      expect(PaginationFieldsSchema.safeParse(data).success).toBe(true);
    });

    it("should reject invalid pagination data", () => {
      const data = { total: "not a number", page: 1 };

      expect(PaginationFieldsSchema.safeParse(data).success).toBe(false);
    });
  });

  describe("CardSummarySchema", () => {
    it("should validate valid card summary", () => {
      const data = {
        id: "sv3-125",
        name: "Charizard ex",
        supertype: "Pokemon",
        types: ["Fire"],
        set_id: "sv3",
        set_name: "Obsidian Flames",
        number: "125",
        rarity: "Double Rare",
        image_small: "https://example.com/small.jpg",
        image_large: "https://example.com/large.jpg",
      };

      expect(CardSummarySchema.safeParse(data).success).toBe(true);
    });

    it("should accept null/optional fields", () => {
      const data = {
        id: "sv3-125",
        name: "Charizard ex",
        supertype: "Pokemon",
        types: null,
        set_id: "sv3",
        set_name: "Obsidian Flames",
        number: "125",
        rarity: null,
        image_small: null,
      };

      expect(CardSummarySchema.safeParse(data).success).toBe(true);
    });
  });

  describe("PaginatedCardSummarySchema", () => {
    it("should validate paginated card response", () => {
      const data = {
        total: 1,
        page: 1,
        limit: 20,
        has_next: false,
        has_prev: false,
        total_pages: 1,
        items: [
          {
            id: "sv3-125",
            name: "Charizard ex",
            supertype: "Pokemon",
            set_id: "sv3",
            set_name: "Obsidian Flames",
            number: "125",
          },
        ],
      };

      expect(PaginatedCardSummarySchema.safeParse(data).success).toBe(true);
    });
  });

  describe("ArchetypeSchema", () => {
    it("should validate archetype data", () => {
      const data = { name: "Dragapult ex", share: 15.3 };

      expect(ArchetypeSchema.safeParse(data).success).toBe(true);
    });

    it("should reject missing fields", () => {
      expect(ArchetypeSchema.safeParse({ name: "Test" }).success).toBe(false);
      expect(ArchetypeSchema.safeParse({ share: 10 }).success).toBe(false);
    });
  });

  describe("MetaSnapshotSchema", () => {
    it("should validate meta snapshot", () => {
      const data = {
        snapshot_date: "2024-01-01",
        format: "standard",
        best_of: 3,
        archetype_breakdown: [{ name: "Dragapult ex", share: 15.3 }],
        sample_size: 500,
      };

      expect(MetaSnapshotSchema.safeParse(data).success).toBe(true);
    });

    it("should accept optional fields", () => {
      const data = {
        snapshot_date: "2024-01-01",
        region: "JP",
        format: "standard",
        best_of: 1,
        archetype_breakdown: [],
        sample_size: 100,
        diversity_index: 0.85,
        jp_signals: {
          leading_indicators: ["card-1"],
          deck_innovations: ["innovation-1"],
          format_specific_notes: "BO1 format",
        },
      };

      expect(MetaSnapshotSchema.safeParse(data).success).toBe(true);
    });
  });

  describe("LabNoteSchema", () => {
    it("should validate lab note with passthrough", () => {
      const data = {
        id: "note-1",
        title: "Meta Analysis",
        slug: "meta-analysis",
        note_type: "analysis",
        status: "published",
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-02T00:00:00Z",
        content: "Some extra content field",
      };

      const result = LabNoteSchema.safeParse(data);
      expect(result.success).toBe(true);
      // passthrough allows extra fields
      if (result.success) {
        expect(result.data).toHaveProperty("content");
      }
    });
  });
});
