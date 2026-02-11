import React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/hooks", () => ({
  useWidget: vi.fn(),
  useWidgetEmbedCode: vi.fn(),
  useCreateWidget: vi.fn(),
  useUpdateWidget: vi.fn(),
  useDeleteWidget: vi.fn(),
}));

import {
  useCreateWidget,
  useDeleteWidget,
  useUpdateWidget,
  useWidget,
  useWidgetEmbedCode,
} from "@/hooks";
import { WidgetBuilder } from "../WidgetBuilder";

function renderWithClient(node: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={client}>{node}</QueryClientProvider>
  );
}

describe("WidgetBuilder", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useWidget).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidget>);

    vi.mocked(useWidgetEmbedCode).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetEmbedCode>);

    vi.mocked(useCreateWidget).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useCreateWidget>);

    vi.mocked(useUpdateWidget).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpdateWidget>);

    vi.mocked(useDeleteWidget).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeleteWidget>);
  });

  it("shows live preview and updates config values", () => {
    renderWithClient(<WidgetBuilder mode="create" />);

    const regionInput = screen.getByPlaceholderText("Region (global/JP/NA/EU)");
    fireEvent.change(regionInput, { target: { value: "JP" } });

    expect(screen.getByTestId("widget-live-preview")).toBeInTheDocument();
    expect(screen.getByText("region:")).toBeInTheDocument();
    expect(screen.getByText("JP")).toBeInTheDocument();
  });

  it("shows embed tabs in edit mode", () => {
    vi.mocked(useWidget).mockReturnValue({
      data: {
        id: "widget-1",
        user_id: "user-1",
        type: "meta_snapshot",
        config: { region: "global" },
        theme: "light",
        accent_color: "#14b8a6",
        show_attribution: true,
        embed_count: 0,
        view_count: 0,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidget>);

    vi.mocked(useWidgetEmbedCode).mockReturnValue({
      data: {
        widget_id: "widget-1",
        iframe_code: "<iframe />",
        script_code: "<script></script>",
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWidgetEmbedCode>);

    renderWithClient(<WidgetBuilder mode="edit" widgetId="widget-1" />);

    expect(screen.getByText("iFrame")).toBeInTheDocument();
    expect(screen.getByText("JS")).toBeInTheDocument();
    expect(screen.getByText("OG")).toBeInTheDocument();
  });
});
