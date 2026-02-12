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
    <div className="container mx-auto px-4 py-12">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 rounded border border-border bg-muted/50 px-2 py-1 text-xs text-muted-foreground">
            <Lock className="h-3.5 w-3.5" />
            Invite-only closed beta
          </div>
          <h1 className="mt-4 text-4xl font-bold tracking-tight">
            TrainerLab Closed Beta
          </h1>
          <p className="mt-3 text-base text-muted-foreground">
            Get launch updates and request access. We are keeping the beta small
            so we can move fast with feedback.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Request access</CardTitle>
            <CardDescription>
              We will reach out if we can add you. If you are already invited,
              sign in with the invited email.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {status === "success" ? (
              <div className="flex items-center gap-2 rounded-md bg-emerald-500/15 p-3 text-sm text-emerald-700 dark:text-emerald-300">
                <Check className="h-4 w-4" />
                You are on the list. Watch your inbox.
              </div>
            ) : (
              <form onSubmit={onSubmit} className="space-y-3">
                <div>
                  <div className="mb-1 text-xs font-medium text-muted-foreground">
                    Email
                  </div>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
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
                  <div className="mb-1 text-xs font-medium text-muted-foreground">
                    Note (optional)
                  </div>
                  <Textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="What are you trying to do with TrainerLab?"
                    rows={4}
                    disabled={status === "loading"}
                  />
                </div>

                {status === "error" ? (
                  <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
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

        <div className="mt-6 text-sm text-muted-foreground">
          If you are invited but still see the gate after signing in, try a
          refresh.
        </div>
      </div>
    </div>
  );
}
