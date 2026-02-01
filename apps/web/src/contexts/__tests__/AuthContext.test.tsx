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
  const { user, loading, signOut, getIdToken } = useAuth();

  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user">{user ? user.email : "null"}</div>
      <button onClick={signOut}>Sign Out</button>
      <button
        onClick={async () => {
          const token = await getIdToken();
          document.body.setAttribute("data-token", token || "null");
        }}
      >
        Get Token
      </button>
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
});
