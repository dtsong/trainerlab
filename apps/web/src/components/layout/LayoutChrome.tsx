"use client";

import { usePathname } from "next/navigation";

import {
  BetaAccessGate,
  Footer,
  MobileNav,
  ScrollToTop,
  TopNav,
} from "@/components/layout";

export function LayoutChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isEmbed = pathname.startsWith("/embed");

  if (isEmbed) {
    return <>{children}</>;
  }

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[100] focus:bg-white focus:px-4 focus:py-2 focus:text-teal-600 focus:underline"
      >
        Skip to main content
      </a>
      <ScrollToTop />
      <TopNav />
      <div className="flex min-h-screen flex-col pt-[52px] pb-14 md:pb-0">
        <main id="main-content" className="flex-1">
          <BetaAccessGate>{children}</BetaAccessGate>
        </main>
        <Footer />
      </div>
      <MobileNav />
    </>
  );
}
