import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/axios";

export function useNotificationPrefs() {
  return useQuery({
    queryKey: ["notification-preferences"],
    queryFn: () => api.get("/api/v1/notifications/preferences").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateNotificationPrefs() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (updates) =>
      api.patch("/api/v1/notifications/preferences", updates).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    },
  });
}
