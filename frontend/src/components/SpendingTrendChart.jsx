import { useQuery } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import api from "../api/client";

function formatMonth(monthStr) {
  const [year, month] = monthStr.split("-");
  return new Date(parseInt(year), parseInt(month) - 1).toLocaleString("default", {
    month: "short",
  });
}

function formatCurrency(value) {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
  return `$${value.toFixed(0)}`;
}

export default function SpendingTrendChart() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["spending-trends"],
    queryFn: () =>
      api.get("/api/v1/dashboard/spending-trends").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div
        style={{
          height: 300,
          borderRadius: "var(--radius-lg, 0.5rem)",
          background: "var(--color-surface, #1e2130)",
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      />
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    label: formatMonth(d.month),
  }));

  return (
    <div
      style={{
        background: "var(--color-surface, #1e2130)",
        borderRadius: "var(--radius-lg, 0.5rem)",
        border: "1px solid var(--color-border, #2d3148)",
        padding: "var(--space-4, 1rem)",
      }}
    >
      <h3
        style={{
          margin: "0 0 var(--space-4, 1rem)",
          fontSize: "var(--text-base, 1rem)",
          fontWeight: 600,
          color: "var(--color-text, #f1f5f9)",
        }}
      >
        Income vs Expenses
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
          <defs>
            <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="rgb(34,183,128)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="rgb(34,183,128)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #2d3148)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: "var(--color-text-muted, #6b7280)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: "var(--color-text-muted, #6b7280)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip
            formatter={(value, name) => [formatCurrency(value), name === "income" ? "Income" : "Expenses"]}
            labelStyle={{ color: "var(--color-text, #f1f5f9)", fontSize: 13 }}
            contentStyle={{
              background: "var(--color-surface, #1e2130)",
              border: "1px solid var(--color-border, #2d3148)",
              borderRadius: "var(--radius-md, 0.375rem)",
              color: "var(--color-text, #f1f5f9)",
              fontSize: 13,
            }}
          />
          <Legend
            formatter={(value) => (
              <span style={{ color: "var(--color-text, #f1f5f9)", fontSize: "var(--text-sm, 0.875rem)" }}>
                {value === "income" ? "Income" : "Expenses"}
              </span>
            )}
          />
          <Area
            type="monotone"
            dataKey="income"
            stroke="rgb(34,183,128)"
            strokeWidth={2}
            fill="url(#incomeGrad)"
          />
          <Area
            type="monotone"
            dataKey="expenses"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#expenseGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
