"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FlaskConical, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@/hooks";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/meta", label: "Meta" },
  { href: "/meta/japan", label: "From Japan" },
  { href: "/tournaments", label: "Tournaments" },
  { href: "/lab-notes", label: "Lab Notes" },
];

export function TopNav() {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 0);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const isActive = (href: string) => {
    if (href === "/meta/japan") {
      return pathname === "/meta/japan";
    }
    if (href === "/meta") {
      return (
        pathname === "/meta" ||
        (pathname.startsWith("/meta") && pathname !== "/meta/japan")
      );
    }
    return pathname.startsWith(href);
  };

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 hidden h-16 md:flex items-center bg-white transition-shadow duration-200 motion-reduce:transition-none",
        scrolled && "shadow-md"
      )}
    >
      <div className="container flex items-center justify-between">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 text-slate-900 hover:text-slate-700 transition-colors"
        >
          <FlaskConical className="h-6 w-6 text-teal-500" />
          <span className="font-sans font-semibold text-lg">TrainerLab</span>
        </Link>

        {/* Main Navigation */}
        <nav className="flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "relative py-2 text-[15px] font-medium transition-colors",
                isActive(link.href)
                  ? "text-slate-900"
                  : "text-slate-600 hover:text-slate-900"
              )}
            >
              {link.label}
              {isActive(link.href) && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-500" />
              )}
            </Link>
          ))}
        </nav>

        {/* Right side: Investigate + User */}
        <div className="flex items-center gap-4">
          <Button
            asChild
            className="bg-teal-500 hover:bg-teal-600 text-white font-medium"
          >
            <Link href="/investigate">
              <Search className="mr-2 h-4 w-4" />
              Investigate
            </Link>
          </Button>

          {loading ? (
            <div className="h-9 w-9 animate-pulse rounded-full bg-slate-200" />
          ) : user ? (
            <UserMenu />
          ) : (
            <Button variant="ghost" asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
