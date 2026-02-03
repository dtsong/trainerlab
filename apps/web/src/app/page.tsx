import dynamic from "next/dynamic";
import { Hero, JPAlertBanner } from "@/components/home";

// Dynamic imports for below-the-fold components to reduce initial bundle
// Use ssr: false to ensure proper code splitting on the client
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
const JPPreview = dynamic(
  () => import("@/components/home/JPPreview").then((mod) => mod.JPPreview),
  { ssr: true }
);
const WhyTrainerLab = dynamic(
  () =>
    import("@/components/home/WhyTrainerLab").then((mod) => mod.WhyTrainerLab),
  { ssr: true }
);
const ResearchPassWaitlist = dynamic(
  () =>
    import("@/components/home/ResearchPassWaitlist").then(
      (mod) => mod.ResearchPassWaitlist
    ),
  { ssr: true }
);
const TrainersToolkit = dynamic(
  () =>
    import("@/components/home/TrainersToolkit").then(
      (mod) => mod.TrainersToolkit
    ),
  { ssr: true }
);

export default function Home() {
  return (
    <>
      <JPAlertBanner />
      <Hero />
      <MetaSnapshot />
      <EvolutionPreview />
      <ContentGrid />
      <JPPreview />
      <WhyTrainerLab />
      <ResearchPassWaitlist />
      <TrainersToolkit />
    </>
  );
}
