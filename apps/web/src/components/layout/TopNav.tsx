"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@/hooks";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/meta", label: "Meta Overview" },
  { href: "/meta/japan", label: "JP Intelligence", pulse: true },
  { href: "/tournaments", label: "Tournaments" },
  { href: "/lab-notes", label: "Lab Notes" },
  { href: "/decks", label: "Deck Profiles" },
];

export function TopNav() {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () =>
      setTime(
        new Date().toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
        })
      );
    update();
    const id = setInterval(update, 60000);
    return () => clearInterval(id);
  }, []);

  const isActive = (href: string) => {
    if (href === "/meta/japan") {
      return pathname.startsWith("/meta/japan");
    }
    if (href === "/meta") {
      return (
        pathname === "/meta" ||
        (pathname.startsWith("/meta") && !pathname.startsWith("/meta/japan"))
      );
    }
    return pathname.startsWith(href);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 hidden h-[52px] md:flex items-center bg-[var(--lab-bg)]/[0.94] backdrop-blur-[12px] border-b border-lab-border px-5">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2.5 mr-8 group">
        <div className="w-[30px] h-[30px] rounded-lg bg-gradient-to-br from-flame to-flame-dim flex items-center justify-center shadow-[0_2px_12px_var(--flame)/0.19]">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#fff"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M9 3h6v7l5 8a2 2 0 0 1-1.7 3H5.7A2 2 0 0 1 4 18l5-8V3z" />
            <line x1="9" y1="3" x2="15" y2="3" />
          </svg>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-display text-[17px] font-bold text-lab-text tracking-tight">
            Trainer<span className="text-flame">Lab</span>
          </span>
          <span className="font-mono text-[8px] text-lab-text-muted tracking-[1.5px] uppercase">
            Research Floor
          </span>
        </div>
      </Link>

      {/* Nav tabs (Grafana-style flat tabs) */}
      <nav className="flex gap-0.5 h-full">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "h-full flex items-center gap-1.5 px-4 border-b-2 font-body text-[13px] transition-colors duration-150",
              isActive(link.href)
                ? "border-flame text-lab-text font-semibold"
                : "border-transparent text-lab-text-muted hover:text-lab-text-soft"
            )}
          >
            {link.label}
            {link.pulse && (
              <span
                className="w-1.5 h-1.5 rounded-full bg-jp animate-lab-pulse"
                style={{ boxShadow: "0 0 6px var(--jp)" }}
              />
            )}
          </Link>
        ))}
      </nav>

      <div className="flex-1" />

      {/* Search / command palette */}
      <div className="flex items-center gap-2 bg-lab-warm border border-lab-border rounded-lg px-3.5 py-1.5 min-w-[220px] cursor-pointer hover:border-lab-border-focus transition-colors duration-150">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--lab-text-muted)"
          strokeWidth="2"
          strokeLinecap="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <span className="font-body text-xs text-lab-text-muted">
          Investigate...
        </span>
        <span className="ml-auto font-mono text-[9px] text-lab-text-dim px-1.5 py-0.5 rounded bg-lab-border">
          ⌘K
        </span>
      </div>

      {/* Format + Clock */}
      <div className="ml-4 flex items-center gap-2.5 font-mono text-[10px]">
        <span className="text-lab-text-muted tracking-[1px]">SVI–ASC</span>
        <span className="text-flame">{time}</span>
      </div>

      {/* User menu */}
      <div className="ml-4 flex items-center">
        {loading ? (
          <div className="h-8 w-8 animate-pulse rounded-full bg-lab-warm" />
        ) : user ? (
          <UserMenu />
        ) : (
          <Button variant="ghost" asChild>
            <Link
              href="/auth/login"
              className="text-lab-text-muted hover:text-lab-text text-xs"
            >
              Sign In
            </Link>
          </Button>
        )}
      </div>
    </header>
  );
}
