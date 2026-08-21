import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'

export function useTransactions(filters = {}) {
  return useInfiniteQuery({
    queryKey: ['transactions', filters],
    queryFn: async ({ pageParam = 0 }) => {
      const params = new URLSearchParams()
      params.set('limit', '50')
      params.set('offset', String(pageParam))
      if (filters.accountId) params.set('account_id', filters.accountId)
      if (filters.categoryId) params.set('category_id', filters.categoryId)
      if (filters.dateFrom) params.set('date_from', filters.dateFrom)
      if (filters.dateTo) params.set('date_to', filters.dateTo)
      if (filters.search) params.set('search', filters.search)
      if (filters.pending !== undefined) params.set('pending', String(filters.pending))
      if (filters.taxDeductible) params.set('tax_deductible', 'true')

      const { data } = await api.get(`/api/v1/transactions?${params}`)
      return data
    },
    getNextPageParam: (lastPage) => {
      const { offset, limit, total } = lastPage
      const nextOffset = offset + limit
      return nextOffset < total ? nextOffset : undefined
    },
    initialPageParam: 0,
  })
}

export function useCreateTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data) => {
      const { data: resp } = await api.post('/api/v1/transactions', data)
      return resp
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...data }) => {
      const { data: resp } = await api.patch(`/api/v1/transactions/${id}`, data)
      return resp
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}

export function useSplitTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ transactionId, splits }) => {
      const { data } = await api.post(`/api/v1/transactions/${transactionId}/split`, { splits })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}

export function useBulkUpdateTransactions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ transactionIds, updates }) => {
      const { data } = await api.patch('/api/v1/transactions/bulk', {
        transaction_ids: transactionIds,
        updates,
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}
