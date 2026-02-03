"use client";

import {
  useState,
  useCallback,
  useEffect,
  startTransition,
  type KeyboardEvent,
} from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import {
  Bold,
  Italic,
  Heading1,
  Link as LinkIcon,
  Code,
  List,
  Pencil,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useCreateLabNote,
  useUpdateLabNote,
  useDeleteLabNote,
} from "@/hooks/useLabNotesAdmin";
import { labNoteTypeLabels } from "@trainerlab/shared-types";
import type {
  ApiLabNote,
  ApiLabNoteCreateRequest,
  LabNoteType,
  LabNoteStatus,
} from "@trainerlab/shared-types";

const MarkdownPreview = dynamic(
  () => import("@/components/admin/MarkdownPreview"),
  {
    ssr: false,
    loading: () => <PreviewSkeleton />,
  }
);

const preloadPreview = () => void import("@/components/admin/MarkdownPreview");

// Hoisted statics
const SLUG_STRIP = /[^a-z0-9\s-]/g;
const SLUG_SPACES = /\s+/g;

function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .replace(SLUG_STRIP, "")
    .replace(SLUG_SPACES, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 255);
}

function PreviewSkeleton() {
  return (
    <div className="animate-pulse space-y-3 p-4">
      <div className="h-6 w-3/4 rounded bg-zinc-800" />
      <div className="h-4 w-full rounded bg-zinc-800" />
      <div className="h-4 w-5/6 rounded bg-zinc-800" />
      <div className="h-4 w-2/3 rounded bg-zinc-800" />
    </div>
  );
}

const STATUS_OPTIONS: { value: LabNoteStatus; label: string; color: string }[] =
  [
    { value: "draft", label: "Draft", color: "bg-zinc-500" },
    { value: "review", label: "Review", color: "bg-amber-500" },
    { value: "published", label: "Published", color: "bg-teal-500" },
    { value: "archived", label: "Archived", color: "bg-red-500" },
  ];

const NOTE_TYPE_OPTIONS = Object.entries(labNoteTypeLabels) as [
  LabNoteType,
  string,
][];

const TOOLBAR_BUTTONS = [
  { icon: Bold, label: "Bold", prefix: "**", suffix: "**" },
  { icon: Italic, label: "Italic", prefix: "_", suffix: "_" },
  { icon: Heading1, label: "Heading", prefix: "## ", suffix: "" },
  null, // divider
  { icon: LinkIcon, label: "Link", prefix: "[", suffix: "](url)" },
  { icon: Code, label: "Code", prefix: "`", suffix: "`" },
  { icon: List, label: "List", prefix: "- ", suffix: "" },
] as const;

interface LabNoteEditorProps {
  note?: ApiLabNote;
}

export function LabNoteEditor({ note }: LabNoteEditorProps) {
  const router = useRouter();
  const isNew = !note;

  const [title, setTitle] = useState(note?.title ?? "");
  const [slug, setSlug] = useState(note?.slug ?? "");
  const [slugEditable, setSlugEditable] = useState(false);
  const [content, setContent] = useState(note?.content ?? "");
  const [summary, setSummary] = useState(note?.summary ?? "");
  const [noteType, setNoteType] = useState<LabNoteType>(
    note?.note_type ?? "weekly_report"
  );
  const [status, setStatus] = useState<LabNoteStatus>(note?.status ?? "draft");
  const [tags, setTags] = useState<string[]>(note?.tags ?? []);
  const [tagInput, setTagInput] = useState("");
  const [metaDescription, setMetaDescription] = useState(
    note?.meta_description ?? ""
  );
  const [activeTab, setActiveTab] = useState<"write" | "preview">("write");

  const createMutation = useCreateLabNote();
  const updateMutation = useUpdateLabNote();
  const deleteMutation = useDeleteLabNote();

  const isSaving = createMutation.isPending || updateMutation.isPending;

  // Auto-generate slug from title (only for new notes without manual slug edit)
  useEffect(() => {
    if (isNew && !slugEditable) {
      setSlug(generateSlug(title));
    }
  }, [title, isNew, slugEditable]);

  const handleAddTag = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && tagInput.trim()) {
        e.preventDefault();
        const newTag = tagInput.trim().toLowerCase();
        setTags((curr) => (curr.includes(newTag) ? curr : [...curr, newTag]));
        setTagInput("");
      }
    },
    [tagInput]
  );

  const handleRemoveTag = useCallback((tag: string) => {
    setTags((curr) => curr.filter((t) => t !== tag));
  }, []);

  const handleSave = useCallback(() => {
    if (isNew) {
      const payload: ApiLabNoteCreateRequest = {
        title,
        slug: slug || undefined,
        content,
        summary: summary || undefined,
        note_type: noteType,
        status,
        tags: tags.length > 0 ? tags : undefined,
        meta_description: metaDescription || undefined,
      };
      createMutation.mutate(payload, {
        onSuccess: (created: ApiLabNote) => {
          router.push(`/admin/lab-notes/${created.id}`);
        },
      });
    } else {
      updateMutation.mutate({
        id: note.id,
        data: {
          title,
          content,
          summary: summary || undefined,
          status,
          tags: tags.length > 0 ? tags : undefined,
          meta_description: metaDescription || undefined,
        },
      });
    }
  }, [
    isNew,
    title,
    slug,
    content,
    summary,
    noteType,
    status,
    tags,
    metaDescription,
    createMutation,
    updateMutation,
    note,
    router,
  ]);

  const handleDelete = useCallback(() => {
    if (note && window.confirm("Delete this lab note permanently?")) {
      deleteMutation.mutate(note.id);
    }
  }, [note, deleteMutation]);

  const handleTabChange = useCallback((tab: "write" | "preview") => {
    startTransition(() => {
      setActiveTab(tab);
    });
  }, []);

  const handleToolbarAction = useCallback(
    (prefix: string, suffix: string) => {
      const textarea = document.getElementById(
        "editor-content"
      ) as HTMLTextAreaElement;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const selected = content.substring(start, end);
      const newContent =
        content.substring(0, start) +
        prefix +
        (selected || "text") +
        suffix +
        content.substring(end);

      setContent(newContent);
      // Restore focus after a tick
      requestAnimationFrame(() => {
        textarea.focus();
        textarea.setSelectionRange(
          start + prefix.length,
          start + prefix.length + (selected || "text").length
        );
      });
    },
    [content]
  );

  const currentStatusOption = STATUS_OPTIONS.find(
    (opt) => opt.value === status
  );

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left panel — Writing Surface */}
      <div className="flex flex-1 flex-col overflow-auto p-6">
        {/* Title */}
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note title..."
          className="mb-1 w-full border-b border-zinc-800 bg-transparent font-mono text-xl font-semibold text-zinc-100 placeholder-zinc-600 outline-none transition-colors focus:border-teal-500"
        />

        {/* Slug */}
        <div className="mb-6 flex items-center gap-1.5">
          {slugEditable ? (
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              onBlur={() => setSlugEditable(false)}
              autoFocus
              className="w-full bg-transparent font-mono text-xs text-zinc-500 outline-none"
            />
          ) : (
            <button
              onClick={() => setSlugEditable(true)}
              className="flex items-center gap-1 font-mono text-xs text-zinc-500 hover:text-zinc-300"
            >
              <span>/{slug || "slug"}</span>
              <Pencil className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Tab toggle */}
        <div className="mb-3 flex gap-4 border-b border-zinc-800">
          <button
            onClick={() => handleTabChange("write")}
            className={`pb-2 font-mono text-sm transition-all ${
              activeTab === "write"
                ? "border-b-2 border-teal-500 text-zinc-100"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Write
          </button>
          <button
            onClick={() => handleTabChange("preview")}
            onMouseEnter={preloadPreview}
            onFocus={preloadPreview}
            className={`pb-2 font-mono text-sm transition-all ${
              activeTab === "preview"
                ? "border-b-2 border-teal-500 text-zinc-100"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Preview
          </button>
        </div>

        {/* Editor / Preview */}
        {activeTab === "write" ? (
          <div className="flex flex-1 flex-col">
            {/* Toolbar */}
            <div className="mb-2 flex items-center gap-0.5">
              {TOOLBAR_BUTTONS.map((btn, i) =>
                btn === null ? (
                  <div
                    key={`divider-${i}`}
                    className="mx-1 h-5 w-px bg-zinc-700"
                  />
                ) : (
                  <button
                    key={btn.label}
                    onClick={() => handleToolbarAction(btn.prefix, btn.suffix)}
                    title={btn.label}
                    className="flex h-8 w-8 items-center justify-center rounded text-zinc-400 transition-colors hover:bg-zinc-700/50 hover:text-zinc-200"
                  >
                    <btn.icon className="h-4 w-4" />
                  </button>
                )
              )}
            </div>

            <textarea
              id="editor-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your content in markdown..."
              className="min-h-[400px] flex-1 resize-none rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 font-mono text-sm text-zinc-200 placeholder-zinc-600 outline-none transition-colors focus:border-zinc-700"
            />
          </div>
        ) : (
          <div className="flex-1 rounded-lg bg-zinc-900/30 p-6">
            {content ? (
              <MarkdownPreview content={content} />
            ) : (
              <p className="font-mono text-sm text-zinc-500">
                Nothing to preview
              </p>
            )}
          </div>
        )}
      </div>

      {/* Right panel — Metadata Sidebar */}
      <div className="flex w-72 shrink-0 flex-col gap-5 overflow-auto border-l border-zinc-800 bg-zinc-950/50 p-5">
        {/* Status */}
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[2px] text-zinc-600">
            Status
          </label>
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${currentStatusOption?.color ?? "bg-zinc-500"}`}
            />
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as LabNoteStatus)}
              className="w-full rounded border border-zinc-800 bg-zinc-900 px-2 py-1.5 font-mono text-sm text-zinc-300 outline-none focus:border-zinc-700"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Note Type */}
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[2px] text-zinc-600">
            Type
          </label>
          <select
            value={noteType}
            onChange={(e) => setNoteType(e.target.value as LabNoteType)}
            disabled={!isNew}
            className="w-full rounded border border-zinc-800 bg-zinc-900 px-2 py-1.5 font-mono text-sm text-zinc-300 outline-none focus:border-zinc-700 disabled:opacity-50"
          >
            {NOTE_TYPE_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Summary */}
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[2px] text-zinc-600">
            Summary
          </label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Short summary for cards..."
            rows={3}
            className="w-full resize-none rounded border border-zinc-800 bg-zinc-900 px-2 py-1.5 font-mono text-sm text-zinc-300 placeholder-zinc-600 outline-none focus:border-zinc-700"
          />
        </div>

        {/* Meta Description */}
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[2px] text-zinc-600">
            Meta Description
          </label>
          <textarea
            value={metaDescription}
            onChange={(e) => setMetaDescription(e.target.value)}
            placeholder="SEO description..."
            rows={2}
            maxLength={300}
            className="w-full resize-none rounded border border-zinc-800 bg-zinc-900 px-2 py-1.5 font-mono text-sm text-zinc-300 placeholder-zinc-600 outline-none focus:border-zinc-700"
          />
          <div className="mt-0.5 text-right font-mono text-[10px] text-zinc-600">
            {metaDescription.length}/300
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-[2px] text-zinc-600">
            Tags
          </label>
          <div className="mb-2 flex flex-wrap gap-1">
            {tags.map((tag) => (
              <span
                key={tag}
                className="flex items-center gap-1 rounded-full bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-300"
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="text-zinc-500 hover:text-zinc-300"
                >
                  x
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleAddTag}
            placeholder="Add tag + Enter"
            className="w-full rounded border border-zinc-800 bg-zinc-900 px-2 py-1.5 font-mono text-sm text-zinc-300 placeholder-zinc-600 outline-none focus:border-zinc-700"
          />
        </div>

        {/* Version info (edit mode only) */}
        {!isNew && note && (
          <div className="border-t border-zinc-800 pt-3">
            <div className="font-mono text-[10px] uppercase tracking-[2px] text-zinc-600">
              Version
            </div>
            <div className="font-mono text-sm text-zinc-400">
              v{note.version}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mt-auto flex flex-col gap-2 border-t border-zinc-800 pt-4">
          <Button
            onClick={handleSave}
            disabled={!title || !content || isSaving}
            className="w-full bg-teal-600 font-mono text-sm text-white hover:bg-teal-500 disabled:opacity-50"
          >
            {isSaving ? "Saving..." : "Save"}
          </Button>
          {!isNew && (
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="font-mono text-xs text-red-400 transition-colors hover:text-red-300"
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete note"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
