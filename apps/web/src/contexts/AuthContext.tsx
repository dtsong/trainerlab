"use client";

/**
 * Authentication context provider.
 *
 * Manages Firebase authentication state and provides:
 * - Current user state
 * - Loading state
 * - Sign out function
 * - Token refresh for API calls
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import {
  User as FirebaseUser,
  onAuthStateChanged,
  signOut as firebaseSignOut,
} from "firebase/auth";
import { auth } from "@/lib/firebase";

interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

interface AuthContextValue {
  /** Current authenticated user, null if not authenticated */
  user: AuthUser | null;
  /** True while checking initial auth state */
  loading: boolean;
  /** Sign out the current user */
  signOut: () => Promise<void>;
  /** Get the current ID token for API calls */
  getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Maps Firebase's full User object to our minimal AuthUser interface.
 * This prevents exposing Firebase internals throughout the application.
 */
function mapFirebaseUser(firebaseUser: FirebaseUser): AuthUser {
  return {
    uid: firebaseUser.uid,
    email: firebaseUser.email,
    displayName: firebaseUser.displayName,
    photoURL: firebaseUser.photoURL,
  };
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);

  useEffect(() => {
    // If Firebase auth is not configured, mark as loaded with no user
    if (!auth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (fbUser) => {
      if (fbUser) {
        setUser(mapFirebaseUser(fbUser));
        setFirebaseUser(fbUser);
      } else {
        setUser(null);
        setFirebaseUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signOut = useCallback(async () => {
    if (!auth) {
      console.warn("Cannot sign out: Firebase not configured");
      return;
    }
    try {
      await firebaseSignOut(auth);
      // Only clear state after successful sign out
      // onAuthStateChanged will also fire, but we clear eagerly for immediate UI update
      setUser(null);
      setFirebaseUser(null);
    } catch (error) {
      // Don't clear local state - session may still be valid server-side
      // Re-throw so callers can show an error to the user
      console.error("Sign out failed:", error);
      throw error;
    }
  }, []);

  const getIdToken = useCallback(async (): Promise<string | null> => {
    if (!firebaseUser) {
      return null;
    }
    try {
      // forceRefresh: false - SDK uses cached token or auto-refreshes if near expiration
      return await firebaseUser.getIdToken(false);
    } catch (error) {
      // Token refresh can fail due to network errors, revoked session, etc.
      // Return null so callers can handle gracefully (e.g., prompt re-login)
      console.error(
        "Failed to get ID token (session may need refresh):",
        error,
      );
      return null;
    }
  }, [firebaseUser]);

  const value: AuthContextValue = {
    user,
    loading,
    signOut,
    getIdToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access authentication state and functions.
 *
 * @throws Error if used outside of AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
