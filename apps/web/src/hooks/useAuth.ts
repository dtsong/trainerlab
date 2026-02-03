"use client";

/**
 * Authentication hook backed by NextAuth.js.
 *
 * Provides the same interface as the old Firebase AuthContext
 * so consumers (TopNav, UserMenu, MobileNav, AdminGuard, etc.)
 * don't need changes beyond import paths.
 */

import { useSession, signOut as nextAuthSignOut } from "next-auth/react";
import { useCallback } from "react";

interface AuthUser {
  id: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

interface AuthHookReturn {
  user: AuthUser | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

export function useAuth(): AuthHookReturn {
  const { data: session, status } = useSession();

  const user: AuthUser | null = session?.user
    ? {
        id: session.user.id!,
        email: session.user.email ?? null,
        displayName: session.user.name ?? null,
        photoURL: session.user.image ?? null,
      }
    : null;

  const signOut = useCallback(async () => {
    await nextAuthSignOut({ redirectTo: "/" });
  }, []);

  return {
    user,
    loading: status === "loading",
    signOut,
  };
}
