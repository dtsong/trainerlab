import type { Metadata } from "next";
import { Playfair_Display, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Footer, MobileNav, ScrollToTop, TopNav } from "@/components/layout";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "TrainerLab",
  description: "Competitive intelligence platform for Pokemon TCG",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" style={{ colorScheme: "light dark" }}>
      <body
        className={`${playfair.variable} ${dmSans.variable} ${jetbrainsMono.variable} font-sans`}
      >
        <Providers>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:z-[100] focus:bg-white focus:px-4 focus:py-2 focus:text-teal-600 focus:underline"
          >
            Skip to main content
          </a>
          <ScrollToTop />
          <TopNav />
          <div className="flex min-h-screen flex-col pt-16 pb-14 md:pb-0">
            <main id="main-content" className="flex-1">
              {children}
            </main>
            <Footer />
          </div>
          <MobileNav />
        </Providers>
      </body>
    </html>
  );
}
