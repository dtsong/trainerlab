"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/admin", label: "Overview" },
  { href: "/admin/access", label: "Access" },
  { href: "/admin/tournaments", label: "Tournaments" },
  { href: "/admin/meta", label: "Meta" },
  { href: "/admin/cards", label: "Cards" },
  { href: "/admin/lab-notes", label: "Lab Notes" },
  { href: "/admin/data", label: "Data" },
] as const;

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-48 shrink-0 flex-col border-r border-zinc-800 bg-[#0a0e12] py-6 px-3">
      <div className="mb-6 px-2 font-mono text-xs uppercase tracking-widest text-zinc-500">
        Admin
      </div>
      <nav className="flex flex-col gap-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded px-2 py-1.5 font-mono text-sm transition-colors",
                isActive
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
