import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock api-validation before importing api module
vi.mock("./api-validation", () => ({
  validateApiResponse: vi.fn((_, data) => data),
  PaginatedCardSummarySchema: {},
  MetaSnapshotSchema: {},
  MetaHistoryResponseSchema: {},
  ArchetypeSchema: { array: () => ({}) },
  LabNoteListResponseSchema: {},
  LabNoteSchema: {},
  TournamentListResponseSchema: {},
}));

// Store the original fetch
const originalFetch = globalThis.fetch;

// Mock global fetch
const mockFetch = vi.fn();

beforeEach(() => {
  globalThis.fetch = mockFetch;
  vi.clearAllMocks();
});

afterEach(() => {
  globalThis.fetch = originalFetch;
});

// Import after mocks are set up
import {
  cardsApi,
  setsApi,
  metaApi,
  tournamentsApi,
  labNotesApi,
  japanApi,
  translationsApi,
  formatApi,
  rotationApi,
  evolutionApi,
  labNotesAdminApi,
  translationsAdminApi,
  ApiError,
  getAuthToken,
  fetchApiAuth,
} from "../api";

import type {
  TournamentTier,
  LabNoteType,
  LabNoteStatus,
  ApiLabNoteCreateRequest,
  ApiLabNoteUpdateRequest,
  ApiLabNoteStatusUpdate,
  ApiSubmitTranslationRequest,
  ApiUpdateTranslationRequest,
  ApiGlossaryTermCreateRequest,
} from "@trainerlab/shared-types";

function createMockResponse(data: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    statusText: ok ? "OK" : "Error",
    json: vi.fn().mockResolvedValue(data),
  } as unknown as Response;
}

describe("ApiError", () => {
  it("should create an error with message, status, and body", () => {
    const error = new ApiError("Not found", 404, {
      detail: "Resource missing",
    });

    expect(error.message).toBe("Not found");
    expect(error.status).toBe(404);
    expect(error.body).toEqual({ detail: "Resource missing" });
    expect(error.name).toBe("ApiError");
  });

  it("should create an error without body", () => {
    const error = new ApiError("Server error", 500);

    expect(error.message).toBe("Server error");
    expect(error.status).toBe(500);
    expect(error.body).toBeUndefined();
  });

  it("should be an instance of Error", () => {
    const error = new ApiError("Test error", 400);

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ApiError);
  });
});

describe("cardsApi", () => {
  it("should search cards with no params", async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_next: false,
      has_prev: false,
    };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await cardsApi.search();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/cards"),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
    expect(result).toEqual(mockData);
  });

  it("should search cards with query params", async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_next: false,
      has_prev: false,
    };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await cardsApi.search({
      q: "Charizard",
      supertype: "Pokemon",
      page: 2,
      limit: 50,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("q=Charizard");
    expect(calledUrl).toContain("supertype=Pokemon");
    expect(calledUrl).toContain("page=2");
    expect(calledUrl).toContain("limit=50");
  });

  it("should include standard and expanded params when defined", async () => {
    const mockData = {
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_next: false,
      has_prev: false,
    };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await cardsApi.search({ standard: true, expanded: false });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("standard=true");
    expect(calledUrl).toContain("expanded=false");
  });

  it("should get card by ID", async () => {
    const mockCard = { id: "sv3-125", name: "Charizard ex" };
    mockFetch.mockResolvedValue(createMockResponse(mockCard));

    const result = await cardsApi.getById("sv3-125");

    expect(result).toEqual(mockCard);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/cards/sv3-125");
  });

  it("should encode card ID in URL", async () => {
    const mockCard = { id: "sv3/125", name: "Test Card" };
    mockFetch.mockResolvedValue(createMockResponse(mockCard));

    await cardsApi.getById("sv3/125");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/cards/sv3%2F125");
  });
});

describe("setsApi", () => {
  it("should list all sets", async () => {
    const mockSets = [{ id: "sv3", name: "Obsidian Flames" }];
    mockFetch.mockResolvedValue(createMockResponse(mockSets));

    const result = await setsApi.list();

    expect(result).toEqual(mockSets);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/sets");
  });

  it("should get set by ID", async () => {
    const mockSet = { id: "sv3", name: "Obsidian Flames" };
    mockFetch.mockResolvedValue(createMockResponse(mockSet));

    const result = await setsApi.getById("sv3");

    expect(result).toEqual(mockSet);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/sets/sv3");
  });

  it("should get cards for a set with pagination", async () => {
    const mockData = { items: [], total: 0, page: 2, limit: 50 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await setsApi.getCards("sv3", 2, 50);

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/sets/sv3/cards");
    expect(calledUrl).toContain("page=2");
    expect(calledUrl).toContain("limit=50");
  });
});

describe("japanApi", () => {
  it("should list innovations with params", async () => {
    const mockData = { items: [], total: 0 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await japanApi.listInnovations({ set_code: "sv5", limit: 10 });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/japan/innovation");
    expect(calledUrl).toContain("set_code=sv5");
    expect(calledUrl).toContain("limit=10");
  });

  it("should list innovations with en_legal param", async () => {
    const mockData = { items: [], total: 0 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await japanApi.listInnovations({ en_legal: false });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("en_legal=false");
  });

  it("should get innovation detail", async () => {
    const mockData = { card_id: "sv5-101", card_name: "Test" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await japanApi.getInnovationDetail("sv5-101");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/japan/innovation/sv5-101");
  });

  it("should get card count evolution", async () => {
    const mockData = { archetype: "Dragapult ex", evolution: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await japanApi.getCardCountEvolution({
      archetype: "Dragapult ex",
      days: 30,
      top_cards: 5,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/japan/card-count-evolution");
    expect(calledUrl).toContain("archetype=Dragapult+ex");
    expect(calledUrl).toContain("days=30");
    expect(calledUrl).toContain("top_cards=5");
  });
});

describe("fetchApi error handling", () => {
  it("should throw ApiError on non-ok response", async () => {
    mockFetch.mockResolvedValue(
      createMockResponse({ detail: "Not found" }, false, 404)
    );

    await expect(cardsApi.getById("nonexistent")).rejects.toThrow(ApiError);

    try {
      await cardsApi.getById("nonexistent");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(404);
    }
  });

  it("should throw ApiError on network error", async () => {
    mockFetch.mockRejectedValue(new TypeError("Network request failed"));

    await expect(cardsApi.getById("sv3-125")).rejects.toThrow(ApiError);

    try {
      await cardsApi.getById("sv3-125");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(0);
      expect((error as ApiError).message).toContain("Network error");
    }
  });

  it("should throw ApiError on invalid JSON response", async () => {
    const mockResponse = {
      ok: true,
      status: 200,
      statusText: "OK",
      json: vi.fn().mockRejectedValue(new SyntaxError("Unexpected token")),
    } as unknown as Response;
    mockFetch.mockResolvedValue(mockResponse);

    await expect(cardsApi.getById("sv3-125")).rejects.toThrow(ApiError);

    try {
      await cardsApi.getById("sv3-125");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).message).toContain("invalid data format");
    }
  });

  it("should handle non-ok response with unparseable body", async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: vi.fn().mockRejectedValue(new SyntaxError("Unexpected token")),
    } as unknown as Response;
    mockFetch.mockResolvedValue(mockResponse);

    await expect(setsApi.list()).rejects.toThrow(ApiError);

    try {
      await setsApi.list();
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(500);
      expect((error as ApiError).body).toBeUndefined();
    }
  });
});

describe("translationsApi", () => {
  it("should get adoption rates with params", async () => {
    const mockData = { items: [], total: 0 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await translationsApi.getAdoptionRates({
      days: 30,
      archetype: "Dragapult ex",
      limit: 10,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/japan/adoption-rates");
    expect(calledUrl).toContain("days=30");
    expect(calledUrl).toContain("archetype=Dragapult+ex");
    expect(calledUrl).toContain("limit=10");
  });

  it("should get upcoming cards with params", async () => {
    const mockData = { items: [], total: 0 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await translationsApi.getUpcomingCards({
      include_released: true,
      min_impact: 5,
      limit: 20,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/japan/upcoming-cards");
    expect(calledUrl).toContain("include_released=true");
    expect(calledUrl).toContain("min_impact=5");
    expect(calledUrl).toContain("limit=20");
  });

  it("should get adoption rates with no params", async () => {
    const mockData = { items: [], total: 0 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await translationsApi.getAdoptionRates();

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/japan/adoption-rates");
    expect(calledUrl).not.toContain("?");
  });
});

describe("URL construction", () => {
  it("should use correct base URL from environment", async () => {
    const mockData = { items: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await setsApi.list();

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    // Default is http://localhost:8000 or whatever NEXT_PUBLIC_API_URL is
    expect(calledUrl).toMatch(/^https?:\/\/.+\/api\/v1\/sets$/);
  });

  it("should set Content-Type header to application/json", async () => {
    const mockData = { items: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await setsApi.list();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });
});

describe("metaApi", () => {
  it("should get current meta with no params", async () => {
    const mockData = { archetypes: [], snapshot_date: "2025-01-01" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await metaApi.getCurrent();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/meta/current");
    expect(calledUrl).not.toContain("?");
  });

  it("should get current meta with params", async () => {
    const mockData = { archetypes: [], snapshot_date: "2025-01-01" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await metaApi.getCurrent({
      region: "JP",
      format: "standard",
      best_of: 1,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/meta/current");
    expect(calledUrl).toContain("region=JP");
    expect(calledUrl).toContain("format=standard");
    expect(calledUrl).toContain("best_of=1");
  });

  it("should get meta history with params", async () => {
    const mockData = { snapshots: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await metaApi.getHistory({
      region: "NA",
      format: "expanded",
      best_of: 3,
      days: 30,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/meta/history");
    expect(calledUrl).toContain("region=NA");
    expect(calledUrl).toContain("format=expanded");
    expect(calledUrl).toContain("best_of=3");
    expect(calledUrl).toContain("days=30");
  });

  it("should get meta history with no params", async () => {
    const mockData = { snapshots: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await metaApi.getHistory();

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/meta/history");
    expect(calledUrl).not.toContain("?");
  });

  it("should get archetypes with params", async () => {
    const mockData = [{ id: "archetype-1", name: "Charizard ex" }];
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await metaApi.getArchetypes({ region: "EU", format: "standard" });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/meta/archetypes");
    expect(calledUrl).toContain("region=EU");
    expect(calledUrl).toContain("format=standard");
  });

  it("should get archetypes with no params", async () => {
    const mockData = [{ id: "archetype-1", name: "Charizard ex" }];
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await metaApi.getArchetypes();

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/meta/archetypes");
    expect(calledUrl).not.toContain("?");
  });
});

describe("tournamentsApi", () => {
  it("should list tournaments with no params", async () => {
    const mockData = { items: [], total: 0, page: 1, limit: 20 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await tournamentsApi.list();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/tournaments");
    expect(calledUrl).not.toContain("?");
  });

  it("should list tournaments with params", async () => {
    const mockData = { items: [], total: 0, page: 1, limit: 10 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await tournamentsApi.list({
      region: "NA",
      format: "standard",
      start_date: "2025-01-01",
      end_date: "2025-06-01",
      best_of: 3,
      tier: "regional" as TournamentTier,
      sort_by: "date",
      order: "desc",
      page: 2,
      limit: 10,
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/tournaments");
    expect(calledUrl).toContain("region=NA");
    expect(calledUrl).toContain("format=standard");
    expect(calledUrl).toContain("start_date=2025-01-01");
    expect(calledUrl).toContain("end_date=2025-06-01");
    expect(calledUrl).toContain("best_of=3");
    expect(calledUrl).toContain("tier=regional");
    expect(calledUrl).toContain("sort_by=date");
    expect(calledUrl).toContain("order=desc");
    expect(calledUrl).toContain("page=2");
    expect(calledUrl).toContain("limit=10");
  });

  it("should get tournament by ID", async () => {
    const mockData = { id: "t-123", name: "NAIC 2025" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await tournamentsApi.getById("t-123");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/tournaments/t-123");
  });

  it("should encode tournament ID in URL", async () => {
    const mockData = { id: "t/123", name: "Test Tournament" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await tournamentsApi.getById("t/123");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/tournaments/t%2F123");
  });

  it("should get placement decklist", async () => {
    const mockData = { cards: [], format: "standard" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await tournamentsApi.getPlacementDecklist("t-123", "p-456");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain(
      "/api/v1/tournaments/t-123/placements/p-456/decklist"
    );
  });

  it("should encode placement decklist IDs in URL", async () => {
    const mockData = { cards: [], format: "standard" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await tournamentsApi.getPlacementDecklist("t/1", "p/2");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain(
      "/api/v1/tournaments/t%2F1/placements/p%2F2/decklist"
    );
  });
});

describe("labNotesApi", () => {
  it("should list lab notes with no params", async () => {
    const mockData = { items: [], total: 0, page: 1, limit: 20 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await labNotesApi.list();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes");
    expect(calledUrl).not.toContain("?");
  });

  it("should list lab notes with params", async () => {
    const mockData = { items: [], total: 0, page: 2, limit: 10 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await labNotesApi.list({
      page: 2,
      limit: 10,
      note_type: "analysis" as LabNoteType,
      tag: "meta",
    });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes");
    expect(calledUrl).toContain("page=2");
    expect(calledUrl).toContain("limit=10");
    expect(calledUrl).toContain("note_type=analysis");
    expect(calledUrl).toContain("tag=meta");
  });

  it("should get lab note by slug", async () => {
    const mockData = { slug: "my-note", title: "Test Note" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await labNotesApi.getBySlug("my-note");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/my-note");
  });

  it("should encode slug in URL", async () => {
    const mockData = { slug: "my/note", title: "Test Note" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await labNotesApi.getBySlug("my/note");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/my%2Fnote");
  });
});

describe("formatApi", () => {
  it("should get current format", async () => {
    const mockData = { format: "standard", regulation: "G" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await formatApi.getCurrent();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/format/current");
  });

  it("should get upcoming format", async () => {
    const mockData = { format: "standard", regulation: "H" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await formatApi.getUpcoming();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/format/upcoming");
  });
});

describe("rotationApi", () => {
  it("should get rotation impacts for a transition", async () => {
    const mockData = { impacts: [], transition: "G-to-H" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await rotationApi.getImpacts("G-to-H");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/rotation/impact");
    expect(calledUrl).toContain("transition=G-to-H");
  });

  it("should encode transition parameter", async () => {
    const mockData = { impacts: [], transition: "G to H" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await rotationApi.getImpacts("G to H");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("transition=G%20to%20H");
  });

  it("should get archetype impact without transition", async () => {
    const mockData = { archetype_id: "arch-1", impact: "high" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await rotationApi.getArchetypeImpact("arch-1");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/rotation/impact/arch-1");
    expect(calledUrl).not.toContain("transition");
  });

  it("should get archetype impact with transition", async () => {
    const mockData = { archetype_id: "arch-1", impact: "high" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await rotationApi.getArchetypeImpact("arch-1", "G-to-H");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/rotation/impact/arch-1");
    expect(calledUrl).toContain("transition=G-to-H");
  });

  it("should encode archetype ID in URL", async () => {
    const mockData = { archetype_id: "arch/1", impact: "high" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await rotationApi.getArchetypeImpact("arch/1");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/rotation/impact/arch%2F1");
  });
});

describe("evolutionApi", () => {
  it("should list articles with no params", async () => {
    const mockData = [{ slug: "article-1", title: "Test Article" }];
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await evolutionApi.listArticles();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/evolution");
    expect(calledUrl).not.toContain("?");
  });

  it("should list articles with params", async () => {
    const mockData = [{ slug: "article-1", title: "Test Article" }];
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await evolutionApi.listArticles({ limit: 10, offset: 5 });

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/evolution");
    expect(calledUrl).toContain("limit=10");
    expect(calledUrl).toContain("offset=5");
  });

  it("should get article by slug", async () => {
    const mockData = { slug: "my-article", title: "Test Article" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await evolutionApi.getArticleBySlug("my-article");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/evolution/my-article");
  });

  it("should encode article slug in URL", async () => {
    const mockData = { slug: "my/article", title: "Test Article" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await evolutionApi.getArticleBySlug("my/article");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/evolution/my%2Farticle");
  });

  it("should get accuracy with no limit", async () => {
    const mockData = { accuracy: 0.85, total: 100 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await evolutionApi.getAccuracy();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/evolution/accuracy");
    expect(calledUrl).not.toContain("limit");
  });

  it("should get accuracy with limit", async () => {
    const mockData = { accuracy: 0.85, total: 50 };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await evolutionApi.getAccuracy(50);

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/evolution/accuracy");
    expect(calledUrl).toContain("limit=50");
  });

  it("should get archetype evolution without limit", async () => {
    const mockData = { archetype_id: "arch-1", timeline: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await evolutionApi.getArchetypeEvolution("arch-1");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/archetypes/arch-1/evolution");
    expect(calledUrl).not.toContain("limit");
  });

  it("should get archetype evolution with limit", async () => {
    const mockData = { archetype_id: "arch-1", timeline: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await evolutionApi.getArchetypeEvolution("arch-1", 20);

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/archetypes/arch-1/evolution");
    expect(calledUrl).toContain("limit=20");
  });

  it("should get archetype prediction", async () => {
    const mockData = { archetype_id: "arch-1", prediction: "rising" };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    const result = await evolutionApi.getArchetypePrediction("arch-1");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/archetypes/arch-1/prediction");
  });

  it("should encode archetype ID in evolution URL", async () => {
    const mockData = { archetype_id: "arch/1", timeline: [] };
    mockFetch.mockResolvedValue(createMockResponse(mockData));

    await evolutionApi.getArchetypeEvolution("arch/1");

    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/api/v1/archetypes/arch%2F1/evolution");
  });
});

describe("getAuthToken", () => {
  it("should return token when auth endpoint responds successfully", async () => {
    mockFetch.mockResolvedValue(createMockResponse({ token: "jwt-token-123" }));

    const token = await getAuthToken();

    expect(token).toBe("jwt-token-123");
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toBe("/api/auth/token");
  });

  it("should return null when auth endpoint returns non-ok", async () => {
    mockFetch.mockResolvedValue(
      createMockResponse({ error: "Unauthorized" }, false, 401)
    );

    const token = await getAuthToken();

    expect(token).toBeNull();
  });

  it("should return null when auth endpoint throws a network error", async () => {
    mockFetch.mockRejectedValue(new TypeError("Network error"));

    const token = await getAuthToken();

    expect(token).toBeNull();
  });

  it("should return null when token is missing from response", async () => {
    mockFetch.mockResolvedValue(createMockResponse({}));

    const token = await getAuthToken();

    expect(token).toBeNull();
  });
});

describe("fetchApiAuth", () => {
  it("should add Authorization header with Bearer token", async () => {
    // First call: getAuthToken fetches /api/auth/token
    // Second call: the actual API request
    mockFetch
      .mockResolvedValueOnce(createMockResponse({ token: "jwt-token-123" }))
      .mockResolvedValueOnce(createMockResponse({ data: "protected" }));

    const result = await fetchApiAuth<{ data: string }>("/api/v1/protected");

    expect(result).toEqual({ data: "protected" });
    // Second call should have Authorization header
    expect(mockFetch).toHaveBeenCalledTimes(2);
    const [url, options] = mockFetch.mock.calls[1];
    expect(url).toContain("/api/v1/protected");
    expect((options as RequestInit).headers).toEqual(
      expect.objectContaining({
        Authorization: "Bearer jwt-token-123",
        "Content-Type": "application/json",
      })
    );
  });

  it("should throw ApiError when not authenticated", async () => {
    mockFetch.mockResolvedValue(
      createMockResponse({ error: "Unauthorized" }, false, 401)
    );

    await expect(fetchApiAuth("/api/v1/protected")).rejects.toThrow(ApiError);

    try {
      // Reset mock for second attempt
      mockFetch.mockResolvedValue(
        createMockResponse({ error: "Unauthorized" }, false, 401)
      );
      await fetchApiAuth("/api/v1/protected");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(401);
      expect((error as ApiError).message).toBe("Not authenticated");
    }
  });
});

describe("labNotesAdminApi", () => {
  // Helper to mock auth token + API response
  function mockAuthAndResponse(data: unknown, ok = true, status = 200) {
    mockFetch
      .mockResolvedValueOnce(createMockResponse({ token: "admin-token" }))
      .mockResolvedValueOnce(createMockResponse(data, ok, status));
  }

  it("should list admin lab notes with no params", async () => {
    const mockData = { items: [], total: 0, page: 1, limit: 20 };
    mockAuthAndResponse(mockData);

    const result = await labNotesAdminApi.list();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/admin/all");
    expect(calledUrl).not.toContain("?");
  });

  it("should list admin lab notes with params", async () => {
    const mockData = { items: [], total: 0, page: 1, limit: 10 };
    mockAuthAndResponse(mockData);

    await labNotesAdminApi.list({
      page: 1,
      limit: 10,
      note_type: "analysis" as LabNoteType,
      tag: "meta",
      status: "draft" as LabNoteStatus,
    });

    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/admin/all");
    expect(calledUrl).toContain("page=1");
    expect(calledUrl).toContain("limit=10");
    expect(calledUrl).toContain("note_type=analysis");
    expect(calledUrl).toContain("tag=meta");
    expect(calledUrl).toContain("status=draft");
  });

  it("should get admin lab note by ID", async () => {
    const mockData = { id: "note-1", title: "Admin Note" };
    mockAuthAndResponse(mockData);

    const result = await labNotesAdminApi.getById("note-1");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/admin/note-1");
  });

  it("should create a lab note", async () => {
    const createData = { title: "New Note", content: "Content here" };
    const mockData = { id: "note-new", ...createData };
    mockAuthAndResponse(mockData);

    const result = await labNotesAdminApi.create(
      createData as ApiLabNoteCreateRequest
    );

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify(createData));
  });

  it("should update a lab note", async () => {
    const updateData = { title: "Updated Note" };
    const mockData = { id: "note-1", title: "Updated Note" };
    mockAuthAndResponse(mockData);

    const result = await labNotesAdminApi.update(
      "note-1",
      updateData as ApiLabNoteUpdateRequest
    );

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/note-1");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("PATCH");
    expect(options.body).toBe(JSON.stringify(updateData));
  });

  it("should update lab note status", async () => {
    const statusData = { status: "published" };
    const mockData = { id: "note-1", status: "published" };
    mockAuthAndResponse(mockData);

    const result = await labNotesAdminApi.updateStatus(
      "note-1",
      statusData as ApiLabNoteStatusUpdate
    );

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/note-1/status");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("PATCH");
    expect(options.body).toBe(JSON.stringify(statusData));
  });

  it("should delete a lab note", async () => {
    mockAuthAndResponse(undefined);

    await labNotesAdminApi.delete("note-1");

    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/note-1");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("DELETE");
  });

  it("should list revisions for a lab note", async () => {
    const mockData = [
      { revision: 1, created_at: "2025-01-01" },
      { revision: 2, created_at: "2025-01-02" },
    ];
    mockAuthAndResponse(mockData);

    const result = await labNotesAdminApi.listRevisions("note-1");

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/note-1/revisions");
  });

  it("should encode ID in admin lab note URLs", async () => {
    const mockData = { id: "note/1", title: "Admin Note" };
    mockAuthAndResponse(mockData);

    await labNotesAdminApi.getById("note/1");

    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/lab-notes/admin/note%2F1");
  });
});

describe("translationsAdminApi", () => {
  // Helper to mock auth token + API response
  function mockAuthAndResponse(data: unknown, ok = true, status = 200) {
    mockFetch
      .mockResolvedValueOnce(createMockResponse({ token: "admin-token" }))
      .mockResolvedValueOnce(createMockResponse(data, ok, status));
  }

  it("should list translations with no params", async () => {
    const mockData = { items: [], total: 0 };
    mockAuthAndResponse(mockData);

    const result = await translationsAdminApi.list();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations");
    expect(calledUrl).not.toContain("?");
  });

  it("should list translations with params", async () => {
    const mockData = { items: [], total: 0 };
    mockAuthAndResponse(mockData);

    await translationsAdminApi.list({
      status: "pending",
      content_type: "card",
      limit: 10,
      offset: 5,
    });

    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations");
    expect(calledUrl).toContain("status_filter=pending");
    expect(calledUrl).toContain("content_type=card");
    expect(calledUrl).toContain("limit=10");
    expect(calledUrl).toContain("offset=5");
  });

  it("should submit a translation", async () => {
    const submitData = {
      content_type: "card",
      source_text: "Japanese text",
    };
    const mockData = { id: "trans-1", ...submitData };
    mockAuthAndResponse(mockData);

    const result = await translationsAdminApi.submit(
      submitData as ApiSubmitTranslationRequest
    );

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify(submitData));
  });

  it("should update a translation", async () => {
    const updateData = { translated_text: "Updated translation" };
    const mockData = { id: "trans-1", translated_text: "Updated translation" };
    mockAuthAndResponse(mockData);

    const result = await translationsAdminApi.update(
      "trans-1",
      updateData as ApiUpdateTranslationRequest
    );

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations/trans-1");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("PATCH");
    expect(options.body).toBe(JSON.stringify(updateData));
  });

  it("should encode ID in translation update URL", async () => {
    const updateData = { translated_text: "Updated" };
    const mockData = { id: "trans/1", translated_text: "Updated" };
    mockAuthAndResponse(mockData);

    await translationsAdminApi.update(
      "trans/1",
      updateData as ApiUpdateTranslationRequest
    );

    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations/trans%2F1");
  });

  it("should list glossary with active only by default", async () => {
    const mockData = { items: [] };
    mockAuthAndResponse(mockData);

    const result = await translationsAdminApi.listGlossary();

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations/glossary");
    expect(calledUrl).toContain("active_only=true");
  });

  it("should list glossary including inactive terms", async () => {
    const mockData = { items: [] };
    mockAuthAndResponse(mockData);

    await translationsAdminApi.listGlossary(false);

    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations/glossary");
    expect(calledUrl).not.toContain("active_only");
  });

  it("should create a glossary term", async () => {
    const createData = {
      jp_term: "Japanese term",
      en_term: "English term",
    };
    const mockData = { id: "gloss-1", ...createData };
    mockAuthAndResponse(mockData);

    const result = await translationsAdminApi.createGlossaryTerm(
      createData as ApiGlossaryTermCreateRequest
    );

    expect(result).toEqual(mockData);
    const calledUrl = mockFetch.mock.calls[1][0] as string;
    expect(calledUrl).toContain("/api/v1/admin/translations/glossary");
    const options = mockFetch.mock.calls[1][1] as RequestInit;
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify(createData));
  });
});
