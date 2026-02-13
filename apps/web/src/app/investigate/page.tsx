"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Search, Sparkles, FileText, Lock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks";

function buildCardsUrl(query: string): string {
  const q = query.trim();
  if (!q) {
    return "/cards";
  }
  return `/cards?q=${encodeURIComponent(q)}`;
}

export default function InvestigatePage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [query, setQuery] = useState("");

  const destination = useMemo(() => buildCardsUrl(query), [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const href = destination;

    // Keep the hub public, but require sign-in for the actual card database.
    if (!user) {
      router.push(`/auth/login?callbackUrl=${encodeURIComponent(href)}`);
      return;
    }

    router.push(href);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Investigate</h1>
        <p className="text-muted-foreground mt-2 max-w-2xl">
          Fast card intel, meta context, and clean links into the database.
        </p>
      </div>

      <Card className="overflow-hidden border-primary/20">
        <CardHeader className="bg-gradient-to-br from-primary/10 via-background to-background">
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5 text-teal-600" />
            Card Search
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-3 sm:flex-row"
          >
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Try: Charizard ex, Buddy-Buddy Poffin, Lost Vacuum"
              className="sm:flex-1"
            />
            <Button
              type="submit"
              disabled={loading}
              className="bg-teal-500 hover:bg-teal-600"
            >
              {user ? "Search" : "Sign in to search"}
            </Button>
          </form>

          {!user && (
            <div className="mt-4 rounded-lg border bg-muted/40 p-4 text-sm">
              <div className="flex items-start gap-2">
                <Lock className="h-4 w-4 mt-0.5 text-muted-foreground" />
                <div>
                  <div className="font-medium">Public hub, gated database</div>
                  <div className="text-muted-foreground mt-1">
                    You can browse the hub without an account. Searching cards
                    requires sign-in.
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Sparkles className="h-4 w-4 text-teal-600" />
                  Dossier entrypoints
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Jump from a question to the exact card page in one step.
                </p>
                <Button variant="outline" className="mt-3" asChild>
                  <Link
                    href={
                      user ? destination : "/auth/login?callbackUrl=%2Fcards"
                    }
                  >
                    Open card database
                  </Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <FileText className="h-4 w-4 text-teal-600" />
                  Learn the meta
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Start with analysis, then pivot into cards and tournaments.
                </p>
                <Button variant="outline" className="mt-3" asChild>
                  <Link href="/lab-notes">Browse Lab Notes</Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Search className="h-4 w-4 text-teal-600" />
                  Upcoming events
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Plan targets by region and timeline, then add them to trips.
                </p>
                <Button variant="outline" className="mt-3" asChild>
                  <Link href="/events">View Events</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
