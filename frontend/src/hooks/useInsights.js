import { useQuery } from "@tanstack/react-query";
import api from "../api/axios";

export function useAnomalies() {
  return useQuery({
    queryKey: ["anomalies"],
    queryFn: () => api.get("/api/v1/insights/anomalies").then((r) => r.data),
    staleTime: 10 * 60 * 1000,
  });
}

export function useForecast() {
  return useQuery({
    queryKey: ["forecast"],
    queryFn: () => api.get("/api/v1/insights/forecast").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSavingsOpportunities() {
  return useQuery({
    queryKey: ["savings-opportunities"],
    queryFn: () => api.get("/api/v1/insights/savings-opportunities").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useBudgetRecommendations() {
  return useQuery({
    queryKey: ["budget-recommendations"],
    queryFn: () => api.get("/api/v1/insights/budget-recommendations").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useHealthScore() {
  return useQuery({
    queryKey: ["health-score"],
    queryFn: () => api.get("/api/v1/insights/health-score").then((r) => r.data),
    staleTime: 10 * 60 * 1000,
  });
}

export function useInsightsSummary() {
  return useQuery({
    queryKey: ["insights-summary"],
    queryFn: () => api.get("/api/v1/insights/summary").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}
