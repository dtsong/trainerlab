"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@/hooks";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/cards", label: "Cards" },
  { href: "/decks", label: "Decks" },
  { href: "/meta", label: "Meta" },
];

export function Header() {
  const pathname = usePathname();
  const { user, loading, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSignOut = async () => {
    try {
      await signOut();
      setMobileMenuOpen(false);
    } catch (error) {
      console.error("Sign out failed:", error);
      toast.error("Failed to sign out. Please try again.");
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <span className="font-bold text-xl">TrainerLab</span>
        </Link>

        {/* Desktop navigation */}
        <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "transition-colors hover:text-foreground/80",
                pathname.startsWith(link.href)
                  ? "text-foreground"
                  : "text-foreground/60",
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex flex-1 items-center justify-end space-x-4">
          {/* Desktop auth buttons */}
          <div className="hidden md:flex items-center space-x-2">
            {loading ? (
              <div className="h-9 w-20 animate-pulse rounded bg-muted" />
            ) : user ? (
              <UserMenu />
            ) : (
              <>
                <Button variant="ghost" asChild>
                  <Link href="/auth/login">Sign In</Link>
                </Button>
                <Button asChild>
                  <Link href="/auth/register">Sign Up</Link>
                </Button>
              </>
            )}
          </div>

          {/* Mobile menu */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <nav className="flex flex-col space-y-4 mt-6">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      "text-lg font-medium transition-colors hover:text-foreground/80",
                      pathname.startsWith(link.href)
                        ? "text-foreground"
                        : "text-foreground/60",
                    )}
                  >
                    {link.label}
                  </Link>
                ))}

                <div className="border-t pt-4 mt-4">
                  {loading ? (
                    <div className="h-10 w-full animate-pulse rounded bg-muted" />
                  ) : user ? (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3">
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {user.displayName || "User"}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            {user.email}
                          </span>
                        </div>
                      </div>
                      <Link
                        href="/decks"
                        onClick={() => setMobileMenuOpen(false)}
                        className="block text-foreground/60 hover:text-foreground"
                      >
                        My Decks
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setMobileMenuOpen(false)}
                        className="block text-foreground/60 hover:text-foreground"
                      >
                        Settings
                      </Link>
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={handleSignOut}
                      >
                        Sign Out
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Button className="w-full" asChild>
                        <Link
                          href="/auth/login"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          Sign In
                        </Link>
                      </Button>
                      <Button variant="outline" className="w-full" asChild>
                        <Link
                          href="/auth/register"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          Sign Up
                        </Link>
                      </Button>
                    </div>
                  )}
                </div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
