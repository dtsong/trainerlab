/**
 * Firebase client configuration.
 *
 * Initializes Firebase on the client side for authentication.
 * Config values are read from environment variables.
 */

import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import { getAuth, Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

/**
 * Get the Firebase app instance.
 * Creates a new instance on first call, returns existing on subsequent calls.
 */
function getFirebaseApp(): FirebaseApp | null {
  // Check if Firebase is configured
  if (!firebaseConfig.apiKey || !firebaseConfig.projectId) {
    if (typeof window !== "undefined") {
      console.warn(
        "Firebase not configured. Set NEXT_PUBLIC_FIREBASE_* environment variables.",
      );
    }
    return null;
  }

  // Return existing app or create new one
  if (getApps().length > 0) {
    return getApp();
  }

  return initializeApp(firebaseConfig);
}

/**
 * Get the Firebase Auth instance.
 * Returns null if Firebase is not configured.
 */
function getFirebaseAuth(): Auth | null {
  const app = getFirebaseApp();
  if (!app) {
    return null;
  }
  return getAuth(app);
}

// Export singleton instances
export const firebaseApp = getFirebaseApp();
export const auth = getFirebaseAuth();
