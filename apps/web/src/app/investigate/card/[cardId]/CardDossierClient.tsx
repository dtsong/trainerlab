"use client";

import Link from "next/link";
import { ArrowLeft, Lock, Search } from "lucide-react";

import { CardDetail } from "@/components/cards";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth, useCard, useCurrentUser } from "@/hooks";

interface CardDossierClientProps {
  cardId: string;
}

function CardDossierSkeleton() {
  return (
    <div className="flex flex-col md:flex-row gap-8 animate-pulse">
      <div
        className="bg-muted rounded-lg flex-shrink-0 mx-auto md:mx-0"
        style={{ width: 320, height: 448 }}
      />
      <div className="flex-1 space-y-4">
        <div className="h-8 bg-muted rounded w-1/2" />
        <div className="h-4 bg-muted rounded w-1/3" />
        <div className="flex gap-2">
          <div className="h-6 bg-muted rounded w-20" />
          <div className="h-6 bg-muted rounded w-20" />
        </div>
        <div className="h-24 bg-muted rounded" />
        <div className="h-24 bg-muted rounded" />
      </div>
    </div>
  );
}

function AccessTeaser({
  title,
  description,
  primaryAction,
  secondaryAction,
}: {
  title: string;
  description: string;
  primaryAction: React.ReactNode;
  secondaryAction?: React.ReactNode;
}) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5 text-amber-600" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-3">
        {primaryAction}
        {secondaryAction}
      </CardContent>
    </Card>
  );
}

export function CardDossierClient({ cardId }: CardDossierClientProps) {
  const { user, loading: authLoading } = useAuth();
  const { data: currentUser, isLoading: currentUserLoading } =
    useCurrentUser(!!user);
  const {
    data: card,
    isLoading: cardLoading,
    isError,
    error,
  } = useCard(cardId);

  const hasFullAccess =
    !!currentUser?.is_beta_tester ||
    !!currentUser?.is_subscriber ||
    !!currentUser?.is_creator ||
    !!currentUser?.is_admin;

  const callbackUrl = `/investigate/card/${encodeURIComponent(cardId)}`;
  const loginUrl = `/auth/login?callbackUrl=${encodeURIComponent(callbackUrl)}`;

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6 flex flex-wrap gap-2">
        <Button variant="ghost" asChild>
          <Link href="/investigate">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Investigate
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/cards">Card Database</Link>
        </Button>
      </div>

      {authLoading || (user && currentUserLoading) ? (
        <div className="h-24 animate-pulse rounded-lg border bg-muted mb-6" />
      ) : !user ? (
        <AccessTeaser
          title="Sign in to view the dossier"
          description="You can browse the Investigate hub without an account, but card dossiers are part of the intelligence suite."
          primaryAction={
            <Button asChild className="bg-teal-500 hover:bg-teal-600">
              <Link href={loginUrl}>
                <Search className="h-4 w-4 mr-2" />
                Sign in
              </Link>
            </Button>
          }
          secondaryAction={
            <Button variant="outline" asChild>
              <Link href="/closed-beta">Request Access</Link>
            </Button>
          }
        />
      ) : !hasFullAccess ? (
        <AccessTeaser
          title="Closed Beta Access Required"
          description="You are signed in, but this dossier is currently available only to approved beta users."
          primaryAction={
            <Button asChild className="bg-teal-500 hover:bg-teal-600">
              <Link href="/closed-beta">Request Access</Link>
            </Button>
          }
          secondaryAction={
            <Button variant="outline" asChild>
              <Link href="/lab-notes">Browse Lab Notes</Link>
            </Button>
          }
        />
      ) : null}

      {cardLoading && <CardDossierSkeleton />}

      {isError && (
        <div className="text-center py-12">
          <p className="text-destructive font-medium text-lg">
            Error loading card
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            {error instanceof Error ? error.message : "Card not found"}
          </p>
          <Button asChild className="mt-4">
            <Link href="/investigate">Back to Investigate</Link>
          </Button>
        </div>
      )}

      {card && !cardLoading ? (
        hasFullAccess ? (
          <CardDetail card={card} />
        ) : (
          <div className="opacity-70">
            <CardDetail card={card} />
          </div>
        )
      ) : null}
    </div>
  );
}
