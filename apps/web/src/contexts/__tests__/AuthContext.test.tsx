import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "../AuthContext";

// Mock firebase/auth
const mockOnAuthStateChanged = vi.fn();
const mockSignOut = vi.fn();
const mockGetIdToken = vi.fn();

vi.mock("firebase/auth", () => ({
  onAuthStateChanged: (...args: unknown[]) => mockOnAuthStateChanged(...args),
  signOut: (...args: unknown[]) => mockSignOut(...args),
}));

// Mock our firebase lib
vi.mock("@/lib/firebase", () => ({
  auth: { name: "mock-auth" },
}));

// Test component that uses the hook
function TestConsumer() {
  const { user, loading, signOut, getIdToken, authError, clearAuthError } =
    useAuth();

  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user">{user ? user.email : "null"}</div>
      <div data-testid="auth-error">
        {authError ? authError.message : "null"}
      </div>
      <button onClick={signOut}>Sign Out</button>
      <button
        onClick={async () => {
          const token = await getIdToken();
          document.body.setAttribute("data-token", token || "null");
        }}
      >
        Get Token
      </button>
      <button onClick={clearAuthError}>Clear Error</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAuthStateChanged.mockImplementation(() => vi.fn()); // Return unsubscribe
  });

  afterEach(() => {
    document.body.removeAttribute("data-token");
  });

  it("shows loading state initially", () => {
    // Don't call the callback immediately
    mockOnAuthStateChanged.mockImplementation(() => vi.fn());

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId("loading")).toHaveTextContent("true");
    expect(screen.getByTestId("user")).toHaveTextContent("null");
  });

  it("sets user when auth state changes to logged in", async () => {
    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: "Test User",
      photoURL: "https://example.com/photo.jpg",
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      // Simulate auth state change
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");
  });

  it("sets user to null when logged out", async () => {
    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(null), 0);
      return vi.fn();
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    expect(screen.getByTestId("user")).toHaveTextContent("null");
  });

  it("calls Firebase signOut when signOut is called", async () => {
    mockSignOut.mockResolvedValue(undefined);
    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(null), 0);
      return vi.fn();
    });

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    await user.click(screen.getByText("Sign Out"));

    expect(mockSignOut).toHaveBeenCalled();
  });

  it("getIdToken returns token from Firebase user", async () => {
    mockGetIdToken.mockResolvedValue("test-token-123");

    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: null,
      photoURL: null,
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    await user.click(screen.getByText("Get Token"));

    await waitFor(() => {
      expect(document.body.getAttribute("data-token")).toBe("test-token-123");
    });
  });

  it("getIdToken returns null when not authenticated", async () => {
    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(null), 0);
      return vi.fn();
    });

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    await user.click(screen.getByText("Get Token"));

    await waitFor(() => {
      expect(document.body.getAttribute("data-token")).toBe("null");
    });
  });

  it("throws error when useAuth is used outside provider", () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      render(<TestConsumer />);
    }).toThrow("useAuth must be used within an AuthProvider");

    consoleSpy.mockRestore();
  });

  it("cleans up auth listener on unmount", () => {
    const unsubscribe = vi.fn();
    mockOnAuthStateChanged.mockReturnValue(unsubscribe);

    const { unmount } = render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    unmount();

    expect(unsubscribe).toHaveBeenCalled();
  });

  it("signOut throws error and does not clear state on failure", async () => {
    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: "Test User",
      photoURL: null,
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    // Make sign out fail
    const signOutError = new Error("Network error");
    mockSignOut.mockRejectedValue(signOutError);

    const user = userEvent.setup();

    // Track if error was thrown
    let caughtError: Error | null = null;

    // Component that catches sign out errors
    function TestConsumerWithErrorHandling() {
      const { user, loading, signOut } = useAuth();

      const handleSignOut = async () => {
        try {
          await signOut();
        } catch (error) {
          caughtError = error as Error;
        }
      };

      return (
        <div>
          <div data-testid="loading">{String(loading)}</div>
          <div data-testid="user">{user ? user.email : "null"}</div>
          <button onClick={handleSignOut}>Sign Out</button>
        </div>
      );
    }

    render(
      <AuthProvider>
        <TestConsumerWithErrorHandling />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    // User should be logged in
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");

    // Suppress console.error for this expected error
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    await user.click(screen.getByText("Sign Out"));

    await waitFor(() => {
      expect(caughtError).toBe(signOutError);
    });

    // User should still be logged in (state not cleared on error)
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");

    consoleSpy.mockRestore();
  });

  it("signOut clears state on success", async () => {
    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: "Test User",
      photoURL: null,
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    mockSignOut.mockResolvedValue(undefined);

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    // User should be logged in
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");

    await user.click(screen.getByText("Sign Out"));

    // User should be logged out (state cleared on success)
    await waitFor(() => {
      expect(screen.getByTestId("user")).toHaveTextContent("null");
    });
  });

  it("sets authError when getIdToken fails", async () => {
    const tokenError = new Error("Token refresh failed");
    mockGetIdToken.mockRejectedValue(tokenError);

    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: null,
      photoURL: null,
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    const user = userEvent.setup();

    // Suppress console.error for this expected error
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    // authError should be null initially
    expect(screen.getByTestId("auth-error")).toHaveTextContent("null");

    await user.click(screen.getByText("Get Token"));

    // authError should be set
    await waitFor(() => {
      expect(screen.getByTestId("auth-error")).toHaveTextContent(
        "Token refresh failed",
      );
    });

    // Token should be null
    expect(document.body.getAttribute("data-token")).toBe("null");

    consoleSpy.mockRestore();
  });

  it("clears authError on successful getIdToken", async () => {
    // First call fails, second succeeds
    mockGetIdToken
      .mockRejectedValueOnce(new Error("Token refresh failed"))
      .mockResolvedValueOnce("new-token");

    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: null,
      photoURL: null,
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    const user = userEvent.setup();

    // Suppress console.error for the expected error
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    // First call fails
    await user.click(screen.getByText("Get Token"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-error")).toHaveTextContent(
        "Token refresh failed",
      );
    });

    // Second call succeeds and clears error
    await user.click(screen.getByText("Get Token"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-error")).toHaveTextContent("null");
    });

    expect(document.body.getAttribute("data-token")).toBe("new-token");

    consoleSpy.mockRestore();
  });

  it("clearAuthError clears the error", async () => {
    mockGetIdToken.mockRejectedValue(new Error("Token refresh failed"));

    const mockUser = {
      uid: "test-uid",
      email: "test@example.com",
      displayName: null,
      photoURL: null,
      getIdToken: mockGetIdToken,
    };

    mockOnAuthStateChanged.mockImplementation((auth, callback) => {
      setTimeout(() => callback(mockUser), 0);
      return vi.fn();
    });

    const user = userEvent.setup();

    // Suppress console.error for the expected error
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    // Trigger error
    await user.click(screen.getByText("Get Token"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-error")).toHaveTextContent(
        "Token refresh failed",
      );
    });

    // Clear the error
    await user.click(screen.getByText("Clear Error"));

    await waitFor(() => {
      expect(screen.getByTestId("auth-error")).toHaveTextContent("null");
    });

    consoleSpy.mockRestore();
  });
});
