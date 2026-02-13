"use client";

import dynamic from "next/dynamic";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { useAuth, useCurrentUser } from "@/hooks";

import { Hero } from "./Hero";
import { JPAlertBanner } from "./JPAlertBanner";
import { PublicTeaserSnapshot } from "./PublicTeaserSnapshot";
import { ResearchPassWaitlist } from "./ResearchPassWaitlist";
import { TrendingMovers } from "./TrendingMovers";
import { TrainersToolkit } from "./TrainersToolkit";
import { WhyTrainerLab } from "./WhyTrainerLab";

const MetaSnapshot = dynamic(
  () =>
    import("@/components/home/MetaSnapshot").then((mod) => mod.MetaSnapshot),
  { ssr: true }
);
const EvolutionPreview = dynamic(
  () =>
    import("@/components/home/EvolutionPreview").then(
      (mod) => mod.EvolutionPreview
    ),
  { ssr: true }
);
const ContentGrid = dynamic(
  () => import("@/components/home/ContentGrid").then((mod) => mod.ContentGrid),
  { ssr: true }
);
const FormatForecast = dynamic(
  () =>
    import("@/components/home/FormatForecast").then(
      (mod) => mod.FormatForecast
    ),
  { ssr: true }
);

export function HomePageContent() {
  const { user } = useAuth();
  const { data: currentUser } = useCurrentUser(!!user);

  const hasFullAccess =
    !!currentUser?.is_beta_tester ||
    !!currentUser?.is_subscriber ||
    !!currentUser?.is_creator ||
    !!currentUser?.is_admin;
  const shouldRenderTeaser = !hasFullAccess;

  return (
    <>
      <ErrorBoundary fallback={null}>
        <JPAlertBanner />
      </ErrorBoundary>

      <ErrorBoundary>
        <Hero hasFullAccess={hasFullAccess} />
      </ErrorBoundary>

      {hasFullAccess && (
        <ErrorBoundary fallback={null}>
          <TrendingMovers />
        </ErrorBoundary>
      )}

      {shouldRenderTeaser ? (
        <ErrorBoundary fallback={null}>
          <PublicTeaserSnapshot />
        </ErrorBoundary>
      ) : (
        <>
          <ErrorBoundary fallback={null}>
            <MetaSnapshot />
          </ErrorBoundary>
          <ErrorBoundary fallback={null}>
            <FormatForecast />
          </ErrorBoundary>
          <ErrorBoundary fallback={null}>
            <EvolutionPreview />
          </ErrorBoundary>
          <ErrorBoundary fallback={null}>
            <ContentGrid />
          </ErrorBoundary>
        </>
      )}

      {/* Keep public positioning and conversion content always visible */}
      <WhyTrainerLab />
      <ResearchPassWaitlist />
      <TrainersToolkit />
    </>
  );
}
