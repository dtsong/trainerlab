"use client";

import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { tripsApi, type TripSearchParams } from "@/lib/api";
import type {
  ApiTripCreate,
  ApiTripUpdate,
  ApiTripEventAdd,
} from "@trainerlab/shared-types";

const TRIPS_KEY = ["trips"] as const;

/**
 * Hook to fetch the current user's trips.
 */
export function useTrips(params: TripSearchParams = {}) {
  return useQuery({
    queryKey: [...TRIPS_KEY, params],
    queryFn: () => tripsApi.list(params),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook to fetch a single trip by ID.
 */
export function useTrip(id: string | null) {
  return useQuery({
    queryKey: [...TRIPS_KEY, id],
    queryFn: () => tripsApi.getById(id!),
    enabled: !!id,
    staleTime: 1000 * 60 * 2,
  });
}

/**
 * Hook to create a new trip.
 */
export function useCreateTrip() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: TRIPS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (data: ApiTripCreate) => tripsApi.create(data),
    onSuccess,
  });
}

/**
 * Hook to update an existing trip.
 */
export function useUpdateTrip() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: TRIPS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ApiTripUpdate }) =>
      tripsApi.update(id, data),
    onSuccess,
  });
}

/**
 * Hook to delete a trip.
 */
export function useDeleteTrip() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: TRIPS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (id: string) => tripsApi.delete(id),
    onSuccess,
  });
}

/**
 * Hook to add an event to a trip.
 */
export function useAddTripEvent() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: TRIPS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ tripId, data }: { tripId: string; data: ApiTripEventAdd }) =>
      tripsApi.addEvent(tripId, data),
    onSuccess,
  });
}

/**
 * Hook to remove an event from a trip.
 */
export function useRemoveTripEvent() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: TRIPS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: ({ tripId, eventId }: { tripId: string; eventId: string }) =>
      tripsApi.removeEvent(tripId, eventId),
    onSuccess,
  });
}

/**
 * Hook to fetch a shared trip by token (no auth required).
 */
export function useSharedTrip(token: string | null) {
  return useQuery({
    queryKey: ["shared-trip", token],
    queryFn: () => tripsApi.getShared(token!),
    enabled: !!token,
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Hook to generate/regenerate a share link for a trip.
 */
export function useShareTrip() {
  const queryClient = useQueryClient();

  const onSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: TRIPS_KEY });
  }, [queryClient]);

  return useMutation({
    mutationFn: (id: string) => tripsApi.share(id),
    onSuccess,
  });
}
