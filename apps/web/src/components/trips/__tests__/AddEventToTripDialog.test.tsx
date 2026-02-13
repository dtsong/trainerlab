import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { AddEventToTripDialog } from "../AddEventToTripDialog";

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
}));

// Minimal Select mock to avoid Radix portal complexity
vi.mock("@/components/ui/select", async () => {
  const ReactLib = await import("react");
  const SelectContext = ReactLib.createContext<
    ((value: string) => void) | null
  >(null);

  return {
    Select: ({
      children,
      onValueChange,
    }: {
      children: React.ReactNode;
      onValueChange?: (value: string) => void;
    }) => (
      <SelectContext.Provider value={onValueChange ?? null}>
        <div>{children}</div>
      </SelectContext.Provider>
    ),
    SelectContent: ({ children }: { children: React.ReactNode }) => (
      <div>{children}</div>
    ),
    SelectItem: ({
      children,
      value,
    }: {
      children: React.ReactNode;
      value: string;
    }) => {
      const onValueChange = ReactLib.useContext(SelectContext);
      return (
        <button type="button" onClick={() => onValueChange?.(value)}>
          {children}
        </button>
      );
    },
    SelectTrigger: ({ children }: { children: React.ReactNode }) => (
      <div>{children}</div>
    ),
    SelectValue: () => <span />,
  };
});

const mockAddTripEvent = {
  mutateAsync: vi.fn(),
  isPending: false,
};
const mockCreateTrip = {
  mutateAsync: vi.fn(),
  isPending: false,
};

vi.mock("@/hooks/useTrips", () => ({
  useAddTripEvent: () => mockAddTripEvent,
  useCreateTrip: () => mockCreateTrip,
}));

describe("AddEventToTripDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAddTripEvent.mutateAsync.mockResolvedValue({});
    mockCreateTrip.mutateAsync.mockResolvedValue({ id: "trip-new" });
  });

  it("does not auto-add; requires explicit trip selection", async () => {
    render(
      <AddEventToTripDialog
        open
        onOpenChange={() => undefined}
        eventId="event-123"
        trips={[
          {
            id: "trip-1",
            name: "Trip One",
            status: "planning",
            event_count: 0,
            created_at: "",
            next_event_date: null,
          },
        ]}
      />
    );

    expect(mockAddTripEvent.mutateAsync).not.toHaveBeenCalled();
  });

  it("adds event to a selected trip", async () => {
    render(
      <AddEventToTripDialog
        open
        onOpenChange={() => undefined}
        eventId="event-123"
        trips={[
          {
            id: "trip-1",
            name: "Trip One",
            status: "planning",
            event_count: 0,
            created_at: "",
            next_event_date: null,
          },
        ]}
      />
    );

    fireEvent.click(screen.getByText("Trip One"));

    const addButton = screen.getByRole("button", { name: /Add to Trip/i });
    await waitFor(() => expect(addButton).toBeEnabled());
    fireEvent.click(addButton);

    await waitFor(() =>
      expect(mockAddTripEvent.mutateAsync).toHaveBeenCalledWith({
        tripId: "trip-1",
        data: { tournament_id: "event-123" },
      })
    );
    await waitFor(() =>
      expect(mockReplace).toHaveBeenCalledWith("/trips/trip-1")
    );
  });

  it("creates a trip and then adds the event when no trips exist", async () => {
    render(
      <AddEventToTripDialog
        open
        onOpenChange={() => undefined}
        eventId="event-123"
        trips={[]}
      />
    );

    fireEvent.change(screen.getByLabelText("Trip Name"), {
      target: { value: "My New Trip" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Create Trip & Add/i }));

    await waitFor(() => expect(mockCreateTrip.mutateAsync).toHaveBeenCalled());
    await waitFor(() =>
      expect(mockAddTripEvent.mutateAsync).toHaveBeenCalledWith({
        tripId: "trip-new",
        data: { tournament_id: "event-123" },
      })
    );
    await waitFor(() =>
      expect(mockReplace).toHaveBeenCalledWith("/trips/trip-new")
    );
  });
});
