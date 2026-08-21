import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'

export function useBudgets({ month, year } = {}) {
  return useQuery({
    queryKey: ['budgets', month, year],
    queryFn: async () => {
      const params = {}
      if (month) params.period_month = month
      if (year) params.period_year = year
      const { data } = await api.get('/api/v1/budgets', { params })
      return data
    },
  })
}

export function useCreateBudget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await api.post('/api/v1/budgets', body)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['budgets'] }),
  })
}

export function useUpdateBudget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }) => {
      const { data } = await api.patch(`/api/v1/budgets/${id}`, body)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['budgets'] }),
  })
}

export function useDeleteBudget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id) => {
      await api.delete(`/api/v1/budgets/${id}`)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['budgets'] }),
  })
}

export function useBudgetProgress({ month, year } = {}) {
  return useQuery({
    queryKey: ['budget-progress', month, year],
    queryFn: async () => {
      const params = {}
      if (month) params.period_month = month
      if (year) params.period_year = year
      const { data } = await api.get('/api/v1/budgets/progress', { params })
      return data
    },
  })
}

export function useIncomeSummary({ month, year } = {}) {
  return useQuery({
    queryKey: ['income-summary', month, year],
    queryFn: async () => {
      const params = {}
      if (month) params.period_month = month
      if (year) params.period_year = year
      const { data } = await api.get('/api/v1/budgets/income-summary', { params })
      return data
    },
  })
}

export function useBudgetForecast({ month, year } = {}) {
  return useQuery({
    queryKey: ['budget-forecast', month, year],
    queryFn: async () => {
      const params = {}
      if (month) params.period_month = month
      if (year) params.period_year = year
      const { data } = await api.get('/api/v1/budgets/forecast', { params })
      return data
    },
  })
}

export function useBudgetHistory({ months = 6 } = {}) {
  return useQuery({
    queryKey: ['budget-history', months],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/budgets/history', { params: { months } })
      return data
    },
  })
}

export function useZeroBasedSummary({ month, year } = {}) {
  return useQuery({
    queryKey: ['zero-based', month, year],
    queryFn: async () => {
      const params = {}
      if (month) params.period_month = month
      if (year) params.period_year = year
      const { data } = await api.get('/api/v1/budgets/zero-based', { params })
      return data
    },
  })
}
