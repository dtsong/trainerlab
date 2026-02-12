"use client";

import Link from "next/link";
import { useState } from "react";
import { Check, Loader2, Lock, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type Status = "idle" | "loading" | "success" | "error";

export default function ClosedBetaPage() {
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const normalized = email.trim().toLowerCase();
    if (!normalized || !normalized.includes("@")) {
      setStatus("error");
      setErrorMessage("Please enter a valid email address");
      return;
    }

    setStatus("loading");
    setErrorMessage("");

    try {
      const resp = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: normalized,
          note: note.trim() || undefined,
          intent: "both",
          source: "closed_beta_page",
        }),
      });

      if (!resp.ok) throw new Error("request_failed");

      setStatus("success");
      setEmail("");
      setNote("");
    } catch {
      setStatus("error");
      setErrorMessage("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-zinc-950 via-zinc-950 to-teal-950/30 px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 rounded border border-teal-500/20 bg-teal-500/10 px-2 py-1 font-mono text-[11px] text-teal-200">
            <Lock className="h-3.5 w-3.5" />
            Invite-only closed beta
          </div>
          <h1 className="mt-4 font-display text-4xl font-bold tracking-tight text-zinc-50">
            TrainerLab Closed Beta
          </h1>
          <p className="mt-3 max-w-2xl text-base text-zinc-300">
            Get launch updates and request access. We are keeping the beta small
            so we can move fast with feedback.
          </p>
        </div>

        <Card className="border-zinc-800 bg-zinc-900/40">
          <CardHeader>
            <CardTitle className="text-zinc-50">Request access</CardTitle>
            <CardDescription>
              We will reach out if we can add you. If you are already invited,
              sign in with the invited email.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {status === "success" ? (
              <div className="flex items-center gap-2 rounded border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 font-mono text-sm text-emerald-200">
                <Check className="h-4 w-4" />
                You are on the list. Watch your inbox.
              </div>
            ) : (
              <form onSubmit={onSubmit} className="space-y-3">
                <div>
                  <div className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Email
                  </div>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        if (status === "error") setStatus("idle");
                      }}
                      placeholder="you@example.com"
                      className="pl-9"
                      autoComplete="email"
                      disabled={status === "loading"}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-1 font-mono text-xs uppercase tracking-wider text-zinc-500">
                    Note (optional)
                  </div>
                  <Textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="What are you trying to do with TrainerLab?"
                    rows={4}
                    disabled={status === "loading"}
                    className="bg-zinc-950"
                  />
                </div>

                {status === "error" ? (
                  <div className="rounded border border-rose-500/20 bg-rose-500/10 px-3 py-2 font-mono text-xs text-rose-200">
                    {errorMessage}
                  </div>
                ) : null}

                <div className="flex flex-wrap items-center gap-2">
                  <Button type="submit" disabled={status === "loading"}>
                    {status === "loading" ? (
                      <span className="inline-flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Submitting...
                      </span>
                    ) : (
                      "Join list"
                    )}
                  </Button>
                  <Button variant="outline" asChild>
                    <Link href="/auth/login">Sign in</Link>
                  </Button>
                  <Button variant="ghost" asChild>
                    <Link href="/">Home</Link>
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        <div className="mt-6 text-sm text-zinc-400">
          If you are invited but still see the gate after signing in, try a
          refresh.
        </div>
      </div>
    </div>
  );
}
