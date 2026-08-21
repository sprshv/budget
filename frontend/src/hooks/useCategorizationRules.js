import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'

export function useCategorizationRules() {
  return useQuery({
    queryKey: ['categorization-rules'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/categorization-rules')
      return data
    },
  })
}

export function useCreateRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body) => {
      const { data } = await api.post('/api/v1/categorization-rules', body)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categorization-rules'] }),
  })
}

export function useUpdateRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }) => {
      const { data } = await api.patch(`/api/v1/categorization-rules/${id}`, body)
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categorization-rules'] }),
  })
}

export function useDeleteRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id) => {
      await api.delete(`/api/v1/categorization-rules/${id}`)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categorization-rules'] }),
  })
}
