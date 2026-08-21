import { useQuery } from "@tanstack/react-query";
import api from "../api/client";

export function useCategorySpending({ startDate, endDate } = {}) {
  const params = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  return useQuery({
    queryKey: ["category-spending", startDate, endDate],
    queryFn: () => api.get("/api/v1/analytics/category-spending", { params }).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMerchantSpending({ startDate, endDate, limit } = {}) {
  const params = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (limit) params.limit = limit;

  return useQuery({
    queryKey: ["merchant-spending", startDate, endDate, limit],
    queryFn: () => api.get("/api/v1/analytics/merchants", { params }).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useIncomeVsExpenses({ months } = {}) {
  const params = {};
  if (months) params.months = months;

  return useQuery({
    queryKey: ["income-vs-expenses", months],
    queryFn: () => api.get("/api/v1/analytics/income-vs-expenses", { params }).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useYearOverYear() {
  return useQuery({
    queryKey: ["year-over-year"],
    queryFn: () => api.get("/api/v1/analytics/year-over-year").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTaxSummary({ year } = {}) {
  const params = {};
  if (year) params.year = year;

  return useQuery({
    queryKey: ["tax-summary", year],
    queryFn: () => api.get("/api/v1/analytics/tax-summary", { params }).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}
