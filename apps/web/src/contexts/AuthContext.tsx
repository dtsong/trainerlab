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
  useRef,
  ReactNode,
} from "react";
import {
  User as FirebaseUser,
  onAuthStateChanged,
  signOut as firebaseSignOut,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  updateProfile,
  UserCredential,
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
  /** Error from token refresh failure, null if no error */
  authError: Error | null;
  /** Sign in with email and password */
  signIn: (email: string, password: string) => Promise<UserCredential>;
  /** Create a new account with email and password */
  signUp: (
    email: string,
    password: string,
    displayName?: string,
  ) => Promise<UserCredential>;
  /** Sign in with Google popup */
  signInWithGoogle: () => Promise<UserCredential>;
  /** Sign out the current user */
  signOut: () => Promise<void>;
  /** Get the current ID token for API calls. Throws on refresh failure. */
  getIdToken: () => Promise<string | null>;
  /** Clear the auth error (e.g., after user acknowledges) */
  clearAuthError: () => void;
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
  // Use ref for firebaseUser since it's only needed for getIdToken, not for rendering
  const firebaseUserRef = useRef<FirebaseUser | null>(null);
  const [authError, setAuthError] = useState<Error | null>(null);

  const clearAuthError = useCallback(() => {
    setAuthError(null);
  }, []);

  useEffect(() => {
    // If Firebase auth is not configured, mark as loaded with no user
    if (!auth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (fbUser) => {
      firebaseUserRef.current = fbUser;
      if (fbUser) {
        setUser(mapFirebaseUser(fbUser));
      } else {
        setUser(null);
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
      firebaseUserRef.current = null;
    } catch (error) {
      // Don't clear local state - session may still be valid server-side
      // Re-throw so callers can show an error to the user
      console.error("Sign out failed:", error);
      throw error;
    }
  }, []);

  const getIdToken = useCallback(async (): Promise<string | null> => {
    const firebaseUser = firebaseUserRef.current;
    if (!firebaseUser) {
      return null;
    }
    try {
      // forceRefresh: false - SDK uses cached token or auto-refreshes if near expiration
      const token = await firebaseUser.getIdToken(false);
      // Clear any previous error on success
      setAuthError(null);
      return token;
    } catch (error) {
      // Token refresh can fail due to network errors, revoked session, etc.
      // Set authError so UI can prompt re-login, then re-throw
      const authErr =
        error instanceof Error ? error : new Error("Token refresh failed");
      setAuthError(authErr);
      console.error(
        "Failed to get ID token (session may need refresh):",
        error,
      );
      throw authErr;
    }
  }, []);

  const signIn = useCallback(
    async (email: string, password: string): Promise<UserCredential> => {
      if (!auth) {
        throw new Error("Firebase not configured");
      }
      return signInWithEmailAndPassword(auth, email, password);
    },
    [],
  );

  const signUp = useCallback(
    async (
      email: string,
      password: string,
      displayName?: string,
    ): Promise<UserCredential> => {
      if (!auth) {
        throw new Error("Firebase not configured");
      }
      const credential = await createUserWithEmailAndPassword(
        auth,
        email,
        password,
      );
      if (displayName && credential.user) {
        await updateProfile(credential.user, { displayName });
      }
      return credential;
    },
    [],
  );

  const signInWithGoogleFn = useCallback(async (): Promise<UserCredential> => {
    if (!auth) {
      throw new Error("Firebase not configured");
    }
    const provider = new GoogleAuthProvider();
    return signInWithPopup(auth, provider);
  }, []);

  const value: AuthContextValue = {
    user,
    loading,
    authError,
    signIn,
    signUp,
    signInWithGoogle: signInWithGoogleFn,
    signOut,
    getIdToken,
    clearAuthError,
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
