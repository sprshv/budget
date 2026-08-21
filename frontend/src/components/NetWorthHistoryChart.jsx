import { useQuery } from "@tanstack/react-query";
import {
  ComposedChart,
  Bar,
  Line,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import api from "../api/client";

function formatMonth(monthStr) {
  const [year, month] = monthStr.split("-");
  return new Date(parseInt(year), parseInt(month) - 1).toLocaleString("default", {
    month: "short",
    year: "2-digit",
  });
}

function formatCurrency(value) {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1000) {
    return `${sign}$${(abs / 1000).toFixed(1)}k`;
  }
  return `${sign}$${abs.toFixed(0)}`;
}

export default function NetWorthHistoryChart() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["net-worth-history"],
    queryFn: () =>
      api.get("/api/v1/dashboard/net-worth-history").then((r) => r.data),
    staleTime: 10 * 60 * 1000,
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
        Net Worth History
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border, #2d3148)"
            vertical={false}
          />
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
            formatter={(value) => [formatCurrency(value), "Net Worth"]}
            labelStyle={{ color: "var(--color-text, #f1f5f9)", fontSize: 13 }}
            contentStyle={{
              background: "var(--color-surface, #1e2130)",
              border: "1px solid var(--color-border, #2d3148)",
              borderRadius: "var(--radius-md, 0.375rem)",
              color: "var(--color-text, #f1f5f9)",
              fontSize: 13,
            }}
          />
          <ReferenceLine y={0} stroke="var(--color-border, #2d3148)" />
          <Bar dataKey="net_worth" radius={[3, 3, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.net_worth >= 0 ? "var(--color-primary)" : "#ef4444"}
              />
            ))}
          </Bar>
          <Line
            type="monotone"
            dataKey="net_worth"
            stroke="rgba(255,255,255,0.3)"
            strokeWidth={1.5}
            dot={false}
            activeDot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
