"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  BarChart3,
  Flag,
  Calendar,
  CalendarDays,
  Menu,
  FileText,
  Settings,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useAuth } from "@/hooks";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/", label: "Home", icon: Home },
  { href: "/meta", label: "Meta", icon: BarChart3 },
  { href: "/meta/japan", label: "JP", icon: Flag },
  { href: "/events", label: "Events", icon: CalendarDays },
];

const drawerLinks = [
  { href: "/tournaments", label: "Tournaments", icon: Calendar },
  { href: "/lab-notes", label: "Lab Notes", icon: FileText },
  { href: "/creator", label: "Creator", icon: Sparkles },
  { href: "/investigate", label: "Investigate", icon: Search },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();
  const { user, loading, signOut } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
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

  const handleSignOut = async () => {
    try {
      await signOut();
      setDrawerOpen(false);
    } catch (error) {
      console.error("Sign out failed:", error);
    }
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-14 items-center justify-around border-t bg-white pb-safe md:hidden">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const active = isActive(tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "flex flex-col items-center justify-center gap-0.5 px-3 py-1 transition-colors",
              active ? "text-teal-500" : "text-slate-500"
            )}
          >
            <Icon className="h-5 w-5" />
            <span className="text-[10px] font-medium">{tab.label}</span>
          </Link>
        );
      })}

      {/* More button with drawer */}
      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetTrigger asChild>
          <button
            className={cn(
              "flex flex-col items-center justify-center gap-0.5 px-3 py-1 transition-colors",
              drawerOpen ? "text-teal-500" : "text-slate-500"
            )}
            aria-expanded={drawerOpen}
          >
            <Menu className="h-5 w-5" />
            <span className="text-[10px] font-medium">More</span>
          </button>
        </SheetTrigger>
        <SheetContent
          side="bottom"
          className="h-auto max-h-[80vh] rounded-t-2xl"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>More Options</SheetTitle>
          </SheetHeader>

          <div className="flex flex-col gap-2 py-4">
            {/* User info if logged in */}
            {!loading && user && (
              <div className="mb-4 flex items-center gap-3 border-b pb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-100 text-teal-600 font-medium">
                  {user.displayName?.[0] || user.email?.[0] || "U"}
                </div>
                <div className="flex flex-col">
                  <span className="font-medium text-slate-900">
                    {user.displayName || "User"}
                  </span>
                  <span className="text-sm text-slate-500">{user.email}</span>
                </div>
              </div>
            )}

            {/* Drawer links */}
            {drawerLinks.map((link) => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setDrawerOpen(false)}
                  className="flex items-center gap-3 rounded-lg px-3 py-3 text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <Icon className="h-5 w-5 text-slate-500" />
                  <span className="font-medium">{link.label}</span>
                </Link>
              );
            })}

            {/* Auth actions */}
            <div className="mt-4 border-t pt-4">
              {loading ? (
                <div className="h-10 w-full animate-pulse rounded bg-slate-100" />
              ) : user ? (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleSignOut}
                >
                  Sign Out
                </Button>
              ) : (
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/auth/login" onClick={() => setDrawerOpen(false)}>
                    Sign In
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </nav>
  );
}
