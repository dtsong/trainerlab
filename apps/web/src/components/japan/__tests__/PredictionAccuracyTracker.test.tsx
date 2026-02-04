import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PredictionAccuracyTracker } from "../PredictionAccuracyTracker";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  japanApi: {
    listPredictions: vi.fn(),
  },
}));

const mockJapanApi = vi.mocked(api.japanApi);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("PredictionAccuracyTracker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockJapanApi.listPredictions.mockReturnValue(new Promise(() => {}));

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(screen.getByText("Prediction Accuracy")).toBeInTheDocument();
  });

  it("should render the title and description when data loads", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [],
      total: 0,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Prediction Accuracy Tracker")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Our track record: JP meta predictions vs actual EN outcomes"
      )
    ).toBeInTheDocument();
  });

  it("should display stats summary when data is loaded", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [],
      total: 10,
      resolved: 7,
      correct: 5,
      partial: 1,
      incorrect: 1,
      accuracy_rate: 0.71,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("10")).toBeInTheDocument();
    expect(screen.getByText("Total")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("Correct")).toBeInTheDocument();
    expect(
      screen.getByText("1", { selector: ".text-yellow-600" })
    ).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByText("Incorrect")).toBeInTheDocument();
  });

  it("should display accuracy bar when resolved predictions exist", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [],
      total: 10,
      resolved: 7,
      correct: 5,
      partial: 1,
      incorrect: 1,
      accuracy_rate: 0.71,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("71%")).toBeInTheDocument();
    expect(
      screen.getByText("Overall Accuracy (7 resolved)")
    ).toBeInTheDocument();
  });

  it("should not display accuracy bar when no resolved predictions", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [],
      total: 3,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    await screen.findByText("Prediction Accuracy Tracker");
    expect(screen.queryByText(/Overall Accuracy/)).not.toBeInTheDocument();
  });

  it("should display empty state when no predictions", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [],
      total: 0,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("No predictions tracked yet")
    ).toBeInTheDocument();
  });

  it("should render prediction rows with text and event", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [
        {
          id: "pred-1",
          prediction_text: "Charizard ex will rise to Tier S",
          target_event: "NAIC 2024",
          created_at: "2024-03-15T00:00:00Z",
          resolved_at: null,
          outcome: null,
          confidence: "high",
          category: "meta-shift",
          reasoning: null,
          outcome_notes: null,
        },
      ],
      total: 1,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Charizard ex will rise to Tier S")
    ).toBeInTheDocument();
    expect(screen.getByText("NAIC 2024")).toBeInTheDocument();
    expect(screen.getByText("meta-shift")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("should render resolved prediction with outcome notes", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [
        {
          id: "pred-2",
          prediction_text: "Lugia will fall off",
          target_event: "Worlds 2024",
          created_at: "2024-05-01T00:00:00Z",
          resolved_at: "2024-08-20T00:00:00Z",
          outcome: "correct",
          confidence: "medium",
          category: null,
          reasoning: "JP meta already shifted away",
          outcome_notes: "Lugia dropped to 2% at Worlds",
        },
      ],
      total: 1,
      resolved: 1,
      correct: 1,
      partial: 0,
      incorrect: 0,
      accuracy_rate: 1.0,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("Lugia will fall off")).toBeInTheDocument();
    expect(
      screen.getByText("Outcome: Lugia dropped to 2% at Worlds")
    ).toBeInTheDocument();
    // date-fns format uses local timezone, so midnight UTC dates may
    // render as the previous day depending on the runner's timezone
    expect(screen.getByText(/Resolved: Aug (19|20), 2024/)).toBeInTheDocument();
  });

  it("should render reasoning text when provided", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [
        {
          id: "pred-3",
          prediction_text: "Test prediction",
          target_event: "Test Event",
          created_at: "2024-01-01T00:00:00Z",
          resolved_at: null,
          outcome: null,
          confidence: null,
          category: null,
          reasoning: "Based on JP tournament data",
          outcome_notes: null,
        },
      ],
      total: 1,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Based on JP tournament data")
    ).toBeInTheDocument();
  });

  it("should show error state when data fails to load", async () => {
    mockJapanApi.listPredictions.mockRejectedValue(new Error("Network error"));

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(
      await screen.findByText("Failed to load predictions")
    ).toBeInTheDocument();
  });

  it("should pass custom limit to the hook", () => {
    mockJapanApi.listPredictions.mockReturnValue(new Promise(() => {}));

    render(<PredictionAccuracyTracker limit={5} />, {
      wrapper: createWrapper(),
    });

    expect(mockJapanApi.listPredictions).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 5 })
    );
  });

  it("should apply custom className", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [],
      total: 0,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    const { container } = render(
      <PredictionAccuracyTracker className="custom-class" />,
      { wrapper: createWrapper() }
    );

    await screen.findByText("Prediction Accuracy Tracker");
    const card = container.querySelector(".custom-class");
    expect(card).toBeInTheDocument();
  });

  it("should render confidence badge variants correctly", async () => {
    mockJapanApi.listPredictions.mockResolvedValue({
      items: [
        {
          id: "pred-low",
          prediction_text: "Low confidence prediction",
          target_event: "Event A",
          created_at: "2024-01-01T00:00:00Z",
          resolved_at: null,
          outcome: null,
          confidence: "low",
          category: null,
          reasoning: null,
          outcome_notes: null,
        },
      ],
      total: 1,
      resolved: 0,
      correct: 0,
      partial: 0,
      incorrect: 0,
      accuracy_rate: null,
    });

    render(<PredictionAccuracyTracker />, { wrapper: createWrapper() });

    expect(await screen.findByText("Low")).toBeInTheDocument();
  });
});
