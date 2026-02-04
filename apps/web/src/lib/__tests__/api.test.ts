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
  ApiError,
} from "../api";

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
