import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }: { children: string }) => (
    <div data-testid="react-markdown">{children}</div>
  ),
}));

vi.mock("remark-gfm", () => ({
  __esModule: true,
  default: {},
}));

// Import after mocks are set up
import MarkdownPreview from "../MarkdownPreview";

describe("MarkdownPreview", () => {
  it("renders the content string", () => {
    render(<MarkdownPreview content="Hello, world!" />);

    expect(screen.getByText("Hello, world!")).toBeInTheDocument();
  });

  it("passes content to the Markdown component", () => {
    render(<MarkdownPreview content="# Heading" />);

    const markdownEl = screen.getByTestId("react-markdown");
    expect(markdownEl).toHaveTextContent("# Heading");
  });

  it("renders empty content without crashing", () => {
    render(<MarkdownPreview content="" />);

    const markdownEl = screen.getByTestId("react-markdown");
    expect(markdownEl).toBeInTheDocument();
    expect(markdownEl).toHaveTextContent("");
  });

  it("renders multiline markdown content", () => {
    const multiline = "Line one\n\nLine two\n\n- Item 1\n- Item 2";
    render(<MarkdownPreview content={multiline} />);

    expect(screen.getByTestId("react-markdown")).toHaveTextContent("Line one");
    expect(screen.getByTestId("react-markdown")).toHaveTextContent("Line two");
  });

  it("wraps content in a prose-styled container", () => {
    const { container } = render(<MarkdownPreview content="Some content" />);

    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain("prose");
    expect(wrapper.className).toContain("prose-invert");
    expect(wrapper.className).toContain("prose-zinc");
  });

  it("applies max-w-none to allow full width", () => {
    const { container } = render(<MarkdownPreview content="Some content" />);

    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain("max-w-none");
  });

  it("renders content with special characters", () => {
    render(<MarkdownPreview content="Code: `const x = 1;` and **bold**" />);

    expect(screen.getByTestId("react-markdown")).toHaveTextContent(
      "Code: `const x = 1;` and **bold**"
    );
  });
});
