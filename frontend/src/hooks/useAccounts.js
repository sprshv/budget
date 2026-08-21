import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'

export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/accounts')
      return data.accounts || []
    },
  })
}

export function useAccountsHealth() {
  return useQuery({
    queryKey: ['accounts-health'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/accounts/health')
      return data.accounts || []
    },
    refetchInterval: 60000, // check every minute
  })
}

export function useDeleteAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (accountId) => {
      await api.delete(`/api/v1/accounts/${accountId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['accounts-health'] })
    },
  })
}

export function useAccountSparkline(accountId) {
  return useQuery({
    queryKey: ['account-sparkline', accountId],
    queryFn: () => api.get(`/api/v1/dashboard/accounts/sparkline/${accountId}`).then((r) => r.data),
    enabled: !!accountId,
    staleTime: 10 * 60 * 1000,
  })
}
