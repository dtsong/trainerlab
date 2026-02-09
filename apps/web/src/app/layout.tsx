import type { Metadata } from "next";
import { Playfair_Display, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { LayoutChrome } from "@/components/layout";

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
          <LayoutChrome>{children}</LayoutChrome>
        </Providers>
      </body>
    </html>
  );
}
