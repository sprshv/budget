import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import api from "../api/client";

function AccountTypeBadge({ type }) {
  const colors = {
    checking: "var(--color-primary)",
    savings: "var(--color-info, #3b82f6)",
    credit: "var(--color-danger, #ef4444)",
    investment: "var(--color-warning, #f59e0b)",
    brokerage: "var(--color-warning, #f59e0b)",
    loan: "var(--color-danger, #ef4444)",
    mortgage: "var(--color-danger, #ef4444)",
  };
  const bg = colors[type?.toLowerCase()] || "var(--color-text-muted, #6b7280)";
  return (
    <span
      style={{
        background: bg,
        color: "#fff",
        padding: "2px 8px",
        borderRadius: "var(--radius-full, 9999px)",
        fontSize: "var(--text-xs, 0.75rem)",
        fontWeight: 600,
        textTransform: "capitalize",
        whiteSpace: "nowrap",
      }}
    >
      {type}
    </span>
  );
}

function SparklineChart({ accountId }) {
  const { data = [] } = useQuery({
    queryKey: ["sparkline", accountId],
    queryFn: () =>
      api.get(`/api/v1/dashboard/accounts/sparkline/${accountId}`).then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <ResponsiveContainer width="100%" height={48}>
      <LineChart data={data}>
        <Line
          type="monotone"
          dataKey="amount"
          stroke="var(--color-primary)"
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default function AccountOverviewCards() {
  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.get("/api/v1/accounts").then((r) => r.data.accounts ?? []),
    staleTime: 2 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div style={{ display: "flex", gap: "var(--space-4, 1rem)", overflowX: "auto", paddingBottom: "var(--space-2, 0.5rem)" }}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              minWidth: 220,
              height: 140,
              borderRadius: "var(--radius-lg, 0.5rem)",
              background: "var(--color-surface, #1e2130)",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          />
        ))}
      </div>
    );
  }

  if (accounts.length === 0) {
    return (
      <p style={{ color: "var(--color-text-muted, #6b7280)", textAlign: "center", padding: "var(--space-6, 1.5rem)" }}>
        No accounts linked yet.
      </p>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        gap: "var(--space-4, 1rem)",
        overflowX: "auto",
        paddingBottom: "var(--space-2, 0.5rem)",
      }}
    >
      {accounts.map((account) => (
        <div
          key={account.id}
          style={{
            minWidth: 220,
            maxWidth: 260,
            flexShrink: 0,
            borderRadius: "var(--radius-lg, 0.5rem)",
            border: "1px solid var(--color-border, #2d3148)",
            background: "var(--color-surface, #1e2130)",
            padding: "var(--space-4, 1rem)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2, 0.5rem)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span
              style={{
                fontSize: "var(--text-sm, 0.875rem)",
                fontWeight: 600,
                color: "var(--color-text, #f1f5f9)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                maxWidth: 120,
              }}
              title={account.name}
            >
              {account.nickname || account.name}
            </span>
            <AccountTypeBadge type={account.account_type} />
          </div>

          {account.institution_name && (
            <span style={{ fontSize: "var(--text-xs, 0.75rem)", color: "var(--color-text-muted, #6b7280)" }}>
              {account.institution_name}
            </span>
          )}

          <div style={{ marginTop: "var(--space-1, 0.25rem)" }}>
            <span
              style={{
                fontSize: "var(--text-xl, 1.25rem)",
                fontWeight: 700,
                color: "var(--color-text, #f1f5f9)",
              }}
            >
              ${parseFloat(account.balance_current || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <SparklineChart accountId={account.id} />

          {account.last_synced_at && (
            <span style={{ fontSize: "var(--text-xs, 0.75rem)", color: "var(--color-text-muted, #6b7280)" }}>
              Synced {new Date(account.last_synced_at).toLocaleDateString()}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
