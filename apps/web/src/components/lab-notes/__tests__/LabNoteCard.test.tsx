import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LabNoteCard } from "../LabNoteCard";

import type { ApiLabNoteSummary } from "@trainerlab/shared-types";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("LabNoteCard", () => {
  const mockNote: ApiLabNoteSummary = {
    id: "note-1",
    slug: "weekly-meta-report-2026-w5",
    note_type: "weekly_report",
    title: "Weekly Meta Report - Week 5",
    summary: "Charizard ex continues to dominate the meta.",
    author_name: "Daniel Song",
    status: "published",
    is_published: true,
    published_at: "2026-02-01T12:00:00Z",
    featured_image_url: "https://example.com/image.jpg",
    tags: ["meta", "charizard", "weekly"],
    is_premium: false,
    created_at: "2026-01-31T10:00:00Z",
  };

  it("should render the note title", () => {
    render(<LabNoteCard note={mockNote} />);

    expect(screen.getByText("Weekly Meta Report - Week 5")).toBeInTheDocument();
  });

  it("should link to the note detail page via slug", () => {
    render(<LabNoteCard note={mockNote} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/lab-notes/weekly-meta-report-2026-w5"
    );
  });

  it("should display the note type badge", () => {
    render(<LabNoteCard note={mockNote} />);

    expect(screen.getByText("Weekly Report")).toBeInTheDocument();
  });

  it("should display different type badges correctly", () => {
    const jpNote: ApiLabNoteSummary = {
      ...mockNote,
      note_type: "jp_dispatch",
    };

    render(<LabNoteCard note={jpNote} />);

    expect(screen.getByText("JP Dispatch")).toBeInTheDocument();
  });

  it("should display the summary when provided", () => {
    render(<LabNoteCard note={mockNote} />);

    expect(
      screen.getByText("Charizard ex continues to dominate the meta.")
    ).toBeInTheDocument();
  });

  it("should not render summary paragraph when summary is null", () => {
    const noteWithoutSummary: ApiLabNoteSummary = {
      ...mockNote,
      summary: null,
    };

    render(<LabNoteCard note={noteWithoutSummary} />);

    expect(
      screen.queryByText("Charizard ex continues to dominate the meta.")
    ).not.toBeInTheDocument();
  });

  it("should display the published date when available", () => {
    render(<LabNoteCard note={mockNote} />);

    expect(screen.getByText("Feb 1, 2026")).toBeInTheDocument();
  });

  it("should fall back to created_at when published_at is not available", () => {
    const unpublishedNote: ApiLabNoteSummary = {
      ...mockNote,
      published_at: null,
    };

    render(<LabNoteCard note={unpublishedNote} />);

    expect(screen.getByText("Jan 31, 2026")).toBeInTheDocument();
  });

  it("should display the author name when provided", () => {
    render(<LabNoteCard note={mockNote} />);

    expect(screen.getByText("Daniel Song")).toBeInTheDocument();
  });

  it("should not display author when author_name is null", () => {
    const noteWithoutAuthor: ApiLabNoteSummary = {
      ...mockNote,
      author_name: null,
    };

    render(<LabNoteCard note={noteWithoutAuthor} />);

    expect(screen.queryByText("Daniel Song")).not.toBeInTheDocument();
  });

  it("should display the featured image when provided", () => {
    const { container } = render(<LabNoteCard note={mockNote} />);

    // The img has alt="" (decorative) so it won't have the img role
    const img = container.querySelector("img");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "https://example.com/image.jpg");
  });

  it("should not render image section when featured_image_url is null", () => {
    const noteWithoutImage: ApiLabNoteSummary = {
      ...mockNote,
      featured_image_url: null,
    };

    const { container } = render(<LabNoteCard note={noteWithoutImage} />);

    expect(container.querySelector("img")).not.toBeInTheDocument();
  });

  it("should display the premium lock icon for premium notes", () => {
    const premiumNote: ApiLabNoteSummary = {
      ...mockNote,
      is_premium: true,
    };

    const { container } = render(<LabNoteCard note={premiumNote} />);

    // Lock icon from lucide-react renders as an SVG
    const lockIcon = container.querySelector(".text-yellow-500");
    expect(lockIcon).toBeInTheDocument();
  });

  it("should not display the lock icon for free notes", () => {
    const { container } = render(<LabNoteCard note={mockNote} />);

    const lockIcon = container.querySelector(".text-yellow-500");
    expect(lockIcon).not.toBeInTheDocument();
  });

  it("should display tags when available", () => {
    render(<LabNoteCard note={mockNote} />);

    expect(screen.getByText("meta")).toBeInTheDocument();
    expect(screen.getByText("charizard")).toBeInTheDocument();
    expect(screen.getByText("weekly")).toBeInTheDocument();
  });

  it("should only display the first 3 tags", () => {
    const noteWithManyTags: ApiLabNoteSummary = {
      ...mockNote,
      tags: ["tag1", "tag2", "tag3", "tag4", "tag5"],
    };

    render(<LabNoteCard note={noteWithManyTags} />);

    expect(screen.getByText("tag1")).toBeInTheDocument();
    expect(screen.getByText("tag2")).toBeInTheDocument();
    expect(screen.getByText("tag3")).toBeInTheDocument();
    expect(screen.queryByText("tag4")).not.toBeInTheDocument();
    expect(screen.queryByText("tag5")).not.toBeInTheDocument();
  });

  it("should not render tags section when tags are null", () => {
    const noteWithoutTags: ApiLabNoteSummary = {
      ...mockNote,
      tags: null,
    };

    render(<LabNoteCard note={noteWithoutTags} />);

    expect(screen.queryByText("meta")).not.toBeInTheDocument();
  });

  it("should not render tags section when tags array is empty", () => {
    const noteWithEmptyTags: ApiLabNoteSummary = {
      ...mockNote,
      tags: [],
    };

    const { container } = render(<LabNoteCard note={noteWithEmptyTags} />);

    const tagContainer = container.querySelector(".flex.flex-wrap.gap-1.mt-3");
    expect(tagContainer).not.toBeInTheDocument();
  });

  it("should render all note type labels correctly", () => {
    const noteTypes = [
      { type: "set_analysis" as const, label: "Set Analysis" },
      { type: "rotation_preview" as const, label: "Rotation Preview" },
      { type: "tournament_recap" as const, label: "Tournament Recap" },
      { type: "tournament_preview" as const, label: "Tournament Preview" },
      { type: "archetype_evolution" as const, label: "Archetype Evolution" },
    ];

    noteTypes.forEach(({ type, label }) => {
      const note: ApiLabNoteSummary = { ...mockNote, note_type: type };
      const { unmount } = render(<LabNoteCard note={note} />);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    });
  });
});
