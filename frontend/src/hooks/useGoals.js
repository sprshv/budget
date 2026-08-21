import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";

export function useGoals() {
  return useQuery({
    queryKey: ["goals"],
    queryFn: () => api.get("/api/v1/goals").then((r) => r.data),
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.post("/api/v1/goals", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useUpdateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }) =>
      api.patch(`/api/v1/goals/${id}`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useDeleteGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.delete(`/api/v1/goals/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useContributeToGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ goalId, ...data }) =>
      api.post(`/api/v1/goals/${goalId}/contribute`, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useGoalProgress(goalId) {
  return useQuery({
    queryKey: ["goal-progress", goalId],
    queryFn: () => api.get(`/api/v1/goals/${goalId}/progress`).then((r) => r.data),
    enabled: !!goalId,
    staleTime: 60 * 1000,
  });
}

export function useGoalForecast(goalId) {
  return useQuery({
    queryKey: ["goal-forecast", goalId],
    queryFn: () => api.get(`/api/v1/goals/${goalId}/forecast`).then((r) => r.data),
    enabled: !!goalId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useGoalContributions(goalId) {
  return useQuery({
    queryKey: ["goal-contributions", goalId],
    queryFn: () => api.get(`/api/v1/goals/${goalId}/contributions`).then((r) => r.data),
    enabled: !!goalId,
    staleTime: 60 * 1000,
  });
}
