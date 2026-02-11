"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth, useWidgets } from "@/hooks";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CreatorGuardProps {
  children: React.ReactNode;
}

export function CreatorGuard({ children }: CreatorGuardProps) {
  const router = useRouter();
  const { user, loading } = useAuth();

  const creatorProbe = useWidgets({ page: 1, limit: 1 });

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/auth/login?callbackUrl=%2Fcreator");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="py-20 text-center text-sm text-muted-foreground">
        Loading creator access...
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (creatorProbe.isLoading) {
    return (
      <div className="py-20 text-center text-sm text-muted-foreground">
        Verifying creator access...
      </div>
    );
  }

  if (creatorProbe.error) {
    const err = creatorProbe.error as Error;
    const isApiError = err instanceof ApiError;

    if (isApiError && err.status === 403) {
      return (
        <Card className="mx-auto mt-8 max-w-2xl border-orange-500/40">
          <CardHeader>
            <CardTitle className="text-xl">Creator access required</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Your account is authenticated, but it does not currently have
              creator access.
            </p>
            <p className="text-sm text-muted-foreground">
              If you are part of the creator program, contact support to enable
              your creator flag.
            </p>
            <Button asChild variant="outline">
              <Link href="/">Back to home</Link>
            </Button>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card className="mx-auto mt-8 max-w-2xl border-destructive">
        <CardHeader>
          <CardTitle className="text-xl">
            Unable to load creator workspace
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">{err.message}</p>
          <Button variant="outline" onClick={() => creatorProbe.refetch()}>
            Try again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
}
