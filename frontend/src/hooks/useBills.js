import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";

export function useBills() {
  return useQuery({
    queryKey: ["bills"],
    queryFn: () => api.get("/api/v1/bills").then((r) => r.data),
    staleTime: 2 * 60 * 1000,
  });
}

export function useMarkBillPaid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (billId) => api.post(`/api/v1/bills/${billId}/mark-paid`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bills"] }),
  });
}
