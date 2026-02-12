"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Lock } from "lucide-react";

import { useAuth, useCurrentUser } from "@/hooks";
import { isBetaGatedPath } from "@/lib/route-access";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function BetaAccessGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading: authLoading, signOut } = useAuth();
  const isGatedPath = isBetaGatedPath(pathname);
  const shouldCheckBeta = isGatedPath && !!user;
  const {
    data: currentUser,
    isLoading: userLoading,
    isFetching: userFetching,
    refetch: refetchCurrentUser,
  } = useCurrentUser(shouldCheckBeta, { staleTimeMs: 0 });

  if (!isGatedPath) {
    return <>{children}</>;
  }

  if (authLoading) {
    return (
      <div className="container mx-auto py-12 px-4">
        <div className="h-48 animate-pulse rounded-lg border bg-muted" />
      </div>
    );
  }

  // If session is missing (signed out / expired), never render gated content.
  if (!user) {
    const loginUrl = `/auth/login?callbackUrl=${encodeURIComponent(pathname)}`;

    return (
      <div className="container mx-auto py-12 px-4">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5 text-amber-600" />
              Sign in for Closed Beta
            </CardTitle>
            <CardDescription>
              This section is invite-only. Sign in to check access, or request
              an invite.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Button asChild>
              <Link href={loginUrl}>Sign in</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link href="/closed-beta">Request Access</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/lab-notes">Browse Lab Notes</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/">Go Home</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (userLoading) {
    return (
      <div className="container mx-auto py-12 px-4">
        <div className="h-48 animate-pulse rounded-lg border bg-muted" />
      </div>
    );
  }

  if (currentUser && !currentUser.is_beta_tester) {
    const hasAccess =
      currentUser.is_beta_tester ||
      currentUser.is_subscriber ||
      currentUser.is_creator ||
      currentUser.is_admin;

    if (hasAccess) {
      return <>{children}</>;
    }

    return (
      <div className="container mx-auto py-12 px-4">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5 text-amber-600" />
              Closed Beta Access Required
            </CardTitle>
            <CardDescription>
              This section is part of the TrainerLab intelligence suite and is
              currently available only to approved beta users.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-border bg-muted/50 p-3 text-sm text-muted-foreground">
              If you were just invited, access can take a moment to propagate.
              Click "Refresh Access" to re-check without signing out.
            </div>
            <div className="flex flex-wrap gap-3">
              <Button
                onClick={() => {
                  void refetchCurrentUser();
                }}
                disabled={userFetching}
              >
                {userFetching ? "Checking..." : "Refresh Access"}
              </Button>
              <Button asChild>
                <Link href="/lab-notes">Browse Lab Notes</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/">Go Home</Link>
              </Button>
              <Button variant="ghost" asChild>
                <Link href="/closed-beta">Request Access</Link>
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  void signOut();
                }}
                disabled={authLoading || userLoading}
              >
                Sign out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
