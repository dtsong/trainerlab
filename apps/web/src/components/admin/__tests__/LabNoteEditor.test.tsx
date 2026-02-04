import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LabNoteEditor } from "../LabNoteEditor";
import type { ApiLabNote } from "@trainerlab/shared-types";

const mockPush = vi.fn();
const mockMutate = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
}));

vi.mock("next/dynamic", () => ({
  __esModule: true,
  default: (loader: () => Promise<unknown>, _opts?: unknown) => {
    // Return a simple component that renders a placeholder
    const DynamicComponent = ({ content }: { content: string }) => (
      <div data-testid="markdown-preview">{content}</div>
    );
    DynamicComponent.displayName = "DynamicMarkdownPreview";
    return DynamicComponent;
  },
}));

vi.mock("@/hooks/useLabNotesAdmin", () => ({
  useCreateLabNote: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
  useUpdateLabNote: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
  useDeleteLabNote: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
}));

vi.mock("@trainerlab/shared-types", () => ({
  labNoteTypeLabels: {
    weekly_report: "Weekly Report",
    jp_dispatch: "JP Dispatch",
    set_analysis: "Set Analysis",
    rotation_preview: "Rotation Preview",
    tournament_recap: "Tournament Recap",
    tournament_preview: "Tournament Preview",
    archetype_evolution: "Archetype Evolution",
  },
}));

const mockCreateLabNote = vi.mocked(
  (await import("@/hooks/useLabNotesAdmin")).useCreateLabNote
);
const mockUpdateLabNote = vi.mocked(
  (await import("@/hooks/useLabNotesAdmin")).useUpdateLabNote
);
const mockDeleteLabNote = vi.mocked(
  (await import("@/hooks/useLabNotesAdmin")).useDeleteLabNote
);

const sampleNote: ApiLabNote = {
  id: "note-1",
  slug: "sample-note",
  note_type: "weekly_report",
  title: "Sample Note Title",
  summary: "A short summary",
  content: "# Hello World\n\nSome content here.",
  author_name: "Daniel",
  status: "draft",
  version: 3,
  is_published: false,
  published_at: null,
  meta_description: "SEO description",
  featured_image_url: null,
  tags: ["meta", "analysis"],
  related_content: null,
  is_premium: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-15T00:00:00Z",
};

describe("LabNoteEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateLabNote.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    } as ReturnType<typeof mockCreateLabNote>);
    mockUpdateLabNote.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    } as ReturnType<typeof mockUpdateLabNote>);
    mockDeleteLabNote.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as ReturnType<typeof mockDeleteLabNote>);
  });

  describe("New note mode (no note prop)", () => {
    it("renders empty title input", () => {
      render(<LabNoteEditor />);

      const titleInput = screen.getByPlaceholderText("Note title...");
      expect(titleInput).toBeInTheDocument();
      expect(titleInput).toHaveValue("");
    });

    it("renders the Write and Preview tabs", () => {
      render(<LabNoteEditor />);

      expect(screen.getByText("Write")).toBeInTheDocument();
      expect(screen.getByText("Preview")).toBeInTheDocument();
    });

    it("renders the content textarea in write mode", () => {
      render(<LabNoteEditor />);

      expect(
        screen.getByPlaceholderText("Write your content in markdown...")
      ).toBeInTheDocument();
    });

    it("renders status selector defaulting to draft", () => {
      render(<LabNoteEditor />);

      const statusSelect = screen.getByDisplayValue("Draft");
      expect(statusSelect).toBeInTheDocument();
    });

    it("renders note type selector defaulting to Weekly Report", () => {
      render(<LabNoteEditor />);

      const typeSelect = screen.getByDisplayValue("Weekly Report");
      expect(typeSelect).toBeInTheDocument();
    });

    it("renders the Save button", () => {
      render(<LabNoteEditor />);

      expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    });

    it("disables Save when title is empty", () => {
      render(<LabNoteEditor />);

      expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
    });

    it("does not render the Delete button for new notes", () => {
      render(<LabNoteEditor />);

      expect(screen.queryByText("Delete note")).not.toBeInTheDocument();
    });

    it("does not render version info for new notes", () => {
      render(<LabNoteEditor />);

      expect(screen.queryByText("Version")).not.toBeInTheDocument();
    });

    it("allows typing a title", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor />);

      const titleInput = screen.getByPlaceholderText("Note title...");
      await user.type(titleInput, "My New Note");

      expect(titleInput).toHaveValue("My New Note");
    });

    it("renders note type options", () => {
      render(<LabNoteEditor />);

      expect(screen.getByText("Weekly Report")).toBeInTheDocument();
      expect(screen.getByText("JP Dispatch")).toBeInTheDocument();
      expect(screen.getByText("Set Analysis")).toBeInTheDocument();
      expect(screen.getByText("Rotation Preview")).toBeInTheDocument();
      expect(screen.getByText("Tournament Recap")).toBeInTheDocument();
    });

    it("renders status options", () => {
      render(<LabNoteEditor />);

      expect(screen.getByText("Draft")).toBeInTheDocument();
      // The status dropdown should contain all status options
      const statusSelect = screen.getByDisplayValue("Draft");
      expect(statusSelect).toBeInTheDocument();
    });

    it("renders the summary textarea", () => {
      render(<LabNoteEditor />);

      expect(
        screen.getByPlaceholderText("Short summary for cards...")
      ).toBeInTheDocument();
    });

    it("renders the meta description textarea", () => {
      render(<LabNoteEditor />);

      expect(
        screen.getByPlaceholderText("SEO description...")
      ).toBeInTheDocument();
    });

    it("renders the tag input", () => {
      render(<LabNoteEditor />);

      expect(
        screen.getByPlaceholderText("Add tag + Enter")
      ).toBeInTheDocument();
    });

    it("shows meta description character count", () => {
      render(<LabNoteEditor />);

      expect(screen.getByText("0/300")).toBeInTheDocument();
    });

    it("note type selector is enabled for new notes", () => {
      render(<LabNoteEditor />);

      const typeSelect = screen.getByDisplayValue("Weekly Report");
      expect(typeSelect).not.toBeDisabled();
    });
  });

  describe("Edit mode (note prop provided)", () => {
    it("populates the title from the note", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByDisplayValue("Sample Note Title")).toBeInTheDocument();
    });

    it("populates the content textarea from the note", () => {
      render(<LabNoteEditor note={sampleNote} />);

      const textarea = screen.getByPlaceholderText(
        "Write your content in markdown..."
      ) as HTMLTextAreaElement;
      expect(textarea.value).toBe("# Hello World\n\nSome content here.");
    });

    it("populates the summary from the note", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByDisplayValue("A short summary")).toBeInTheDocument();
    });

    it("populates the meta description from the note", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByDisplayValue("SEO description")).toBeInTheDocument();
    });

    it("displays existing tags", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByText("meta")).toBeInTheDocument();
      expect(screen.getByText("analysis")).toBeInTheDocument();
    });

    it("shows the version number", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByText("v3")).toBeInTheDocument();
    });

    it("renders the Delete button", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByText("Delete note")).toBeInTheDocument();
    });

    it("disables the note type selector for existing notes", () => {
      render(<LabNoteEditor note={sampleNote} />);

      const typeSelect = screen.getByDisplayValue("Weekly Report");
      expect(typeSelect).toBeDisabled();
    });

    it("shows the meta description character count for existing content", () => {
      render(<LabNoteEditor note={sampleNote} />);

      // "SEO description" is 15 characters
      expect(screen.getByText("15/300")).toBeInTheDocument();
    });
  });

  describe("Tag management", () => {
    it("adds a tag on Enter key press", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor />);

      const tagInput = screen.getByPlaceholderText("Add tag + Enter");
      await user.type(tagInput, "pikachu{Enter}");

      expect(screen.getByText("pikachu")).toBeInTheDocument();
      expect(tagInput).toHaveValue("");
    });

    it("removes a tag when x is clicked", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor note={sampleNote} />);

      // There should be "x" buttons for each tag
      const removeButtons = screen.getAllByText("x");
      expect(removeButtons.length).toBe(2); // "meta" and "analysis"

      await user.click(removeButtons[0]);

      expect(screen.queryByText("meta")).not.toBeInTheDocument();
      expect(screen.getByText("analysis")).toBeInTheDocument();
    });

    it("does not add duplicate tags", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor note={sampleNote} />);

      const tagInput = screen.getByPlaceholderText("Add tag + Enter");
      await user.type(tagInput, "meta{Enter}");

      // Should still only have one "meta" tag
      const metaTags = screen.getAllByText("meta");
      expect(metaTags).toHaveLength(1);
    });

    it("converts tags to lowercase", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor />);

      const tagInput = screen.getByPlaceholderText("Add tag + Enter");
      await user.type(tagInput, "PIKACHU{Enter}");

      expect(screen.getByText("pikachu")).toBeInTheDocument();
    });
  });

  describe("Saving state", () => {
    it("shows Saving... text when create mutation is pending", () => {
      mockCreateLabNote.mockReturnValue({
        mutate: mockMutate,
        isPending: true,
      } as ReturnType<typeof mockCreateLabNote>);

      render(<LabNoteEditor />);

      expect(
        screen.getByRole("button", { name: "Saving..." })
      ).toBeInTheDocument();
    });

    it("shows Saving... text when update mutation is pending", () => {
      mockUpdateLabNote.mockReturnValue({
        mutate: mockMutate,
        isPending: true,
      } as ReturnType<typeof mockUpdateLabNote>);

      render(<LabNoteEditor note={sampleNote} />);

      expect(
        screen.getByRole("button", { name: "Saving..." })
      ).toBeInTheDocument();
    });

    it("shows Deleting... text when delete mutation is pending", () => {
      mockDeleteLabNote.mockReturnValue({
        mutate: vi.fn(),
        isPending: true,
      } as ReturnType<typeof mockDeleteLabNote>);

      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByText("Deleting...")).toBeInTheDocument();
    });
  });

  describe("Tabs", () => {
    it("starts on the Write tab", () => {
      render(<LabNoteEditor />);

      expect(
        screen.getByPlaceholderText("Write your content in markdown...")
      ).toBeInTheDocument();
    });

    it("switches to Preview tab on click", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor />);

      await user.click(screen.getByText("Preview"));

      // In preview mode with no content, shows "Nothing to preview"
      expect(screen.getByText("Nothing to preview")).toBeInTheDocument();
    });

    it("shows Nothing to preview when content is empty", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor />);

      await user.click(screen.getByText("Preview"));

      expect(screen.getByText("Nothing to preview")).toBeInTheDocument();
    });

    it("switches back to Write tab", async () => {
      const user = userEvent.setup();
      render(<LabNoteEditor />);

      await user.click(screen.getByText("Preview"));
      await user.click(screen.getByText("Write"));

      expect(
        screen.getByPlaceholderText("Write your content in markdown...")
      ).toBeInTheDocument();
    });
  });

  describe("Toolbar", () => {
    it("renders formatting toolbar buttons", () => {
      render(<LabNoteEditor />);

      expect(screen.getByTitle("Bold")).toBeInTheDocument();
      expect(screen.getByTitle("Italic")).toBeInTheDocument();
      expect(screen.getByTitle("Heading")).toBeInTheDocument();
      expect(screen.getByTitle("Link")).toBeInTheDocument();
      expect(screen.getByTitle("Code")).toBeInTheDocument();
      expect(screen.getByTitle("List")).toBeInTheDocument();
    });
  });

  describe("Slug", () => {
    it("displays the slug placeholder for new notes", () => {
      render(<LabNoteEditor />);

      expect(screen.getByText("/slug")).toBeInTheDocument();
    });

    it("displays the existing slug for edit mode", () => {
      render(<LabNoteEditor note={sampleNote} />);

      expect(screen.getByText("/sample-note")).toBeInTheDocument();
    });
  });
});
