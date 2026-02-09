import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock ResizeObserver for jsdom
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

vi.mock("@/hooks/useWidgets", () => ({
  useWidgetData: vi.fn(),
}));

import { useWidgetData } from "@/hooks/useWidgets";
import { EmbedWidgetClient } from "../EmbedWidgetClient";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

describe("EmbedWidgetClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.body.className = "";
  });

  it("should render loading spinner", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeTruthy();
  });

  it("should render error state", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Not found"),
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    expect(screen.getByText("Failed to load widget")).toBeTruthy();
  });

  it("should render error from widget data", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: {
        widget_id: "w-1",
        type: "meta_snapshot",
        theme: "dark",
        accent_color: null,
        show_attribution: true,
        data: {},
        error: "Widget not found",
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    expect(screen.getByText("Failed to load widget")).toBeTruthy();
  });

  it("should render widget with data", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: {
        widget_id: "w-1",
        type: "meta_snapshot",
        theme: "dark",
        accent_color: null,
        show_attribution: true,
        data: { archetypes: [] },
        error: null,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    expect(screen.getByText("meta_snapshot widget")).toBeTruthy();
  });

  it("should show attribution when enabled", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: {
        widget_id: "w-1",
        type: "meta_snapshot",
        theme: "dark",
        accent_color: null,
        show_attribution: true,
        data: { archetypes: [] },
        error: null,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    expect(screen.getByText("Powered by TrainerLab")).toBeTruthy();
  });

  it("should hide attribution when disabled", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: {
        widget_id: "w-1",
        type: "meta_snapshot",
        theme: "dark",
        accent_color: null,
        show_attribution: false,
        data: { archetypes: [] },
        error: null,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    expect(screen.queryByText("Powered by TrainerLab")).toBeNull();
  });

  it("should apply theme class to body", () => {
    vi.mocked(useWidgetData).mockReturnValue({
      data: {
        widget_id: "w-1",
        type: "meta_snapshot",
        theme: "light",
        accent_color: null,
        show_attribution: false,
        data: { archetypes: [] },
        error: null,
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetData>);

    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <EmbedWidgetClient widgetId="w-1" />
      </Wrapper>
    );

    expect(document.body.classList.contains("light")).toBe(true);
  });
});
