"use client";

import { useAuth } from "@/hooks";
import { Button } from "@/components/ui/button";

interface AdminHeaderProps {
  title: string;
}

export function AdminHeader({ title }: AdminHeaderProps) {
  const { user, signOut } = useAuth();

  return (
    <header className="flex items-center justify-between border-b border-zinc-800 bg-[#0a0e12] px-6 py-3">
      <h1 className="font-mono text-lg font-semibold text-zinc-100">{title}</h1>
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs text-zinc-500">{user?.email}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => signOut()}
          className="font-mono text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
        >
          Sign out
        </Button>
      </div>
    </header>
  );
}
