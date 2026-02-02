"use client";

import { useState } from "react";
import { Mail, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ResearchPassWaitlist() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !email.includes("@")) {
      setStatus("error");
      setErrorMessage("Please enter a valid email address");
      return;
    }

    setStatus("loading");

    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error("Failed to join waitlist");
      }

      setStatus("success");
      setEmail("");
    } catch {
      setStatus("error");
      setErrorMessage("Something went wrong. Please try again.");
    }
  };

  return (
    <section className="bg-gradient-to-r from-teal-600 to-teal-500 py-12 md:py-16">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold text-white md:text-4xl">
            Research Pass
          </h2>
          <p className="mt-4 text-lg text-teal-50">
            Get early access to premium features: advanced matchup data, JP
            translation tools, and personalized meta alerts.
          </p>

          {status === "success" ? (
            <div className="mt-8 flex items-center justify-center gap-2 text-white">
              <Check className="h-5 w-5" />
              <span className="font-medium">
                You&apos;re on the list! We&apos;ll be in touch soon.
              </span>
            </div>
          ) : (
            <form
              onSubmit={handleSubmit}
              className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center"
            >
              <div className="relative w-full max-w-sm">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (status === "error") setStatus("idle");
                  }}
                  className="pl-10 bg-white"
                  disabled={status === "loading"}
                  autoComplete="email"
                />
              </div>
              <Button
                type="submit"
                size="lg"
                className="w-full bg-slate-900 hover:bg-slate-800 sm:w-auto"
                disabled={status === "loading"}
              >
                {status === "loading" ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Joining...
                  </>
                ) : (
                  "Join Waitlist"
                )}
              </Button>
            </form>
          )}

          {status === "error" && (
            <p className="mt-3 text-sm text-rose-200" role="alert">
              {errorMessage}
            </p>
          )}

          <p className="mt-6 text-sm text-teal-100">
            Free during beta. No spam, just launch updates.
          </p>
        </div>
      </div>
    </section>
  );
}
