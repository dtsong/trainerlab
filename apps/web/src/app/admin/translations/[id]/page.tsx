"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { AdminHeader } from "@/components/admin";
import { useTranslationsAdmin, useUpdateTranslation } from "@/hooks/useTranslationsAdmin";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { TranslationStatus } from "@trainerlab/shared-types";

const STATUS_COLORS: Record<TranslationStatus, string> = {
  pending: "border-amber-600 text-amber-400",
  completed: "border-teal-600 text-teal-400",
  failed: "border-red-600 text-red-400",
};

export default function TranslationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data, isLoading } = useTranslationsAdmin({ limit: 100 });
  const updateMutation = useUpdateTranslation();

  const translation = data?.content.find((t) => t.id === id);

  const [editedText, setEditedText] = useState("");

  useEffect(() => {
    if (translation?.translated_text) {
      setEditedText(translation.translated_text);
    }
  }, [translation?.translated_text]);

  const handleSave = async (newStatus?: TranslationStatus) => {
    try {
      await updateMutation.mutateAsync({
        id,
        data: {
          translated_text: editedText || null,
          status: newStatus ?? null,
        },
      });
    } catch (error) {
      console.error("Failed to update translation:", error);
    }
  };

  if (isLoading) {
    return (
      <>
        <AdminHeader title="Translation Review" />
        <div className="flex-1 p-6">
          <div className="h-96 animate-pulse rounded bg-zinc-800" />
        </div>
      </>
    );
  }

  if (!translation) {
    return (
      <>
        <AdminHeader title="Translation Review" />
        <div className="flex-1 p-6">
          <p className="text-zinc-400">Translation not found</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => router.push("/admin/translations")}
          >
            Back to Translations
          </Button>
        </div>
      </>
    );
  }

  return (
    <>
      <AdminHeader title="Translation Review" />
      <div className="flex-1 overflow-auto p-6">
        <div className="mb-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/admin/translations")}
            className="font-mono text-xs text-zinc-400"
          >
            ← Back
          </Button>
          <Badge
            variant="outline"
            className={`font-mono text-xs ${STATUS_COLORS[translation.status as TranslationStatus]}`}
          >
            {translation.status}
          </Badge>
          <Badge variant="outline" className="border-zinc-700 font-mono text-xs text-zinc-400">
            {translation.content_type}
          </Badge>
        </div>

        <div className="mb-4">
          <a
            href={translation.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-sm text-teal-400 hover:underline"
          >
            {translation.source_url}
          </a>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="mb-2 font-mono text-sm text-zinc-400">Original (Japanese)</h3>
            <div className="max-h-[60vh] overflow-auto rounded-lg border border-zinc-700 bg-zinc-900 p-4">
              <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-300">
                {translation.original_text || "(No original text)"}
              </pre>
            </div>
          </div>

          <div>
            <h3 className="mb-2 font-mono text-sm text-zinc-400">Translation (English)</h3>
            <Textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="max-h-[60vh] min-h-[40vh] border-zinc-700 bg-zinc-900 font-mono text-sm"
              placeholder="Translated text will appear here..."
            />
          </div>
        </div>

        {translation.uncertainties && translation.uncertainties.length > 0 && (
          <div className="mt-4 rounded-lg border border-amber-800 bg-amber-900/20 p-4">
            <h4 className="mb-2 font-mono text-sm text-amber-400">Translation Uncertainties</h4>
            <ul className="list-inside list-disc text-sm text-amber-300">
              {translation.uncertainties.map((u, i) => (
                <li key={i}>{u}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-6 flex gap-2">
          <Button
            onClick={() => handleSave()}
            disabled={updateMutation.isPending}
            variant="outline"
            className="border-zinc-700 font-mono text-xs"
          >
            {updateMutation.isPending ? "Saving..." : "Save Draft"}
          </Button>
          <Button
            onClick={() => handleSave("completed")}
            disabled={updateMutation.isPending || !editedText.trim()}
            className="bg-teal-600 font-mono text-xs text-white hover:bg-teal-500"
          >
            Mark Complete
          </Button>
        </div>
      </div>
    </>
  );
}
