import { useQuery } from "@tanstack/react-query";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import api from "../api/client";

const FALLBACK_COLORS = [
  "#22b780", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#10b981", "#f97316", "#ec4899", "#6366f1",
];

function formatCurrency(amount) {
  return "$" + parseFloat(amount).toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

function CenterLabel({ viewBox, totalSpent }) {
  const { cx, cy } = viewBox;
  return (
    <g>
      <text
        x={cx}
        y={cy - 10}
        textAnchor="middle"
        fill="var(--color-text-muted, #6b7280)"
        fontSize="12"
      >
        Total Spent
      </text>
      <text
        x={cx}
        y={cy + 14}
        textAnchor="middle"
        fill="var(--color-text, #f1f5f9)"
        fontSize="20"
        fontWeight="700"
      >
        {formatCurrency(totalSpent)}
      </text>
    </g>
  );
}

export default function SpendingBreakdownChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["spending-breakdown"],
    queryFn: () =>
      api.get("/api/v1/dashboard/spending-breakdown").then((r) => r.data),
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

  const categories = data?.categories ?? [];
  const totalSpent = data?.total_spent ?? 0;

  if (categories.length === 0) {
    return (
      <div
        style={{
          height: 300,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--color-text-muted, #6b7280)",
          background: "var(--color-surface, #1e2130)",
          borderRadius: "var(--radius-lg, 0.5rem)",
          border: "1px solid var(--color-border, #2d3148)",
        }}
      >
        No spending data for this month.
      </div>
    );
  }

  const chartData = categories.map((cat, i) => ({
    name: cat.name,
    value: cat.amount,
    percentage: cat.percentage,
    color: cat.color || FALLBACK_COLORS[i % FALLBACK_COLORS.length],
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
        Spending Breakdown
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={110}
            paddingAngle={2}
            dataKey="value"
            labelLine={false}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
            <CenterLabel totalSpent={totalSpent} />
          </Pie>
          <Tooltip
            formatter={(value, name, props) => [
              `${formatCurrency(value)} (${props.payload.percentage}%)`,
              name,
            ]}
            contentStyle={{
              background: "var(--color-surface, #1e2130)",
              border: "1px solid var(--color-border, #2d3148)",
              borderRadius: "var(--radius-md, 0.375rem)",
              color: "var(--color-text, #f1f5f9)",
              fontSize: "var(--text-sm, 0.875rem)",
            }}
          />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            formatter={(value, entry) => (
              <span style={{ color: "var(--color-text, #f1f5f9)", fontSize: "var(--text-sm, 0.875rem)" }}>
                {value}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
