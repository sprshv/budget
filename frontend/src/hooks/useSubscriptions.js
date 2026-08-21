import { useQuery } from "@tanstack/react-query";
import api from "../api/client";

export function useSubscriptions() {
  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => api.get("/api/v1/subscriptions").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSubscriptionsSummary() {
  return useQuery({
    queryKey: ["subscriptions-summary"],
    queryFn: () => api.get("/api/v1/subscriptions/summary").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAnnualSummary() {
  return useQuery({
    queryKey: ["subscriptions-annual-summary"],
    queryFn: () => api.get("/api/v1/subscriptions/annual-summary").then((r) => r.data),
    staleTime: 10 * 60 * 1000,
  });
}
