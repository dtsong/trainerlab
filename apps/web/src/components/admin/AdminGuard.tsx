"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks";
import { isAdminEmail } from "@/lib/admin";

interface AdminGuardProps {
  children: React.ReactNode;
}

export function AdminGuard({ children }: AdminGuardProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/auth/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center bg-[#0f1419]">
        <div className="font-mono text-sm text-zinc-500">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (!isAdminEmail(user.email)) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 bg-[#0f1419]">
        <div className="font-mono text-sm text-red-400">Access Denied</div>
        <div className="font-mono text-xs text-zinc-500">
          {user.email} is not authorized to view this page.
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
