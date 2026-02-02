import {
  Hero,
  JPAlertBanner,
  MetaSnapshot,
  EvolutionPreview,
  ContentGrid,
  JPPreview,
  WhyTrainerLab,
  ResearchPassWaitlist,
  TrainersToolkit,
} from "@/components/home";

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
