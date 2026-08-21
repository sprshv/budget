import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import TransactionDrawer from "./TransactionDrawer";

function formatAmount(amount) {
  const abs = Math.abs(amount).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return amount >= 0 ? `+$${abs}` : `-$${abs}`;
}

function formatDate(dateStr) {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function RecentActivityFeed() {
  const [selectedTx, setSelectedTx] = useState(null);

  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ["recent-transactions"],
    queryFn: () =>
      api.get("/api/v1/dashboard/recent-transactions").then((r) => r.data),
    staleTime: 2 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div
        style={{
          background: "var(--color-surface, #1e2130)",
          borderRadius: "var(--radius-lg, 0.5rem)",
          border: "1px solid var(--color-border, #2d3148)",
          padding: "var(--space-4, 1rem)",
        }}
      >
        <h3 style={{ margin: "0 0 var(--space-4, 1rem)", fontSize: "var(--text-base, 1rem)", fontWeight: 600, color: "var(--color-text, #f1f5f9)" }}>
          Recent Activity
        </h3>
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            style={{
              height: 48,
              marginBottom: "var(--space-2, 0.5rem)",
              borderRadius: "var(--radius-md, 0.375rem)",
              background: "var(--color-bg, #141624)",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <>
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
            margin: "0 0 var(--space-3, 0.75rem)",
            fontSize: "var(--text-base, 1rem)",
            fontWeight: 600,
            color: "var(--color-text, #f1f5f9)",
          }}
        >
          Recent Activity
        </h3>

        {transactions.length === 0 ? (
          <p style={{ color: "var(--color-text-muted, #6b7280)", textAlign: "center", padding: "var(--space-4, 1rem)" }}>
            No recent transactions.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1, 0.25rem)" }}>
            {transactions.map((tx) => (
              <button
                key={tx.id}
                onClick={() => setSelectedTx(tx)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "var(--space-3, 0.75rem) var(--space-2, 0.5rem)",
                  borderRadius: "var(--radius-md, 0.375rem)",
                  border: "none",
                  background: "transparent",
                  cursor: "pointer",
                  width: "100%",
                  textAlign: "left",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-bg, #141624)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: 2, flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2, 0.5rem)" }}>
                    <span
                      style={{
                        fontSize: "var(--text-sm, 0.875rem)",
                        fontWeight: 500,
                        color: "var(--color-text, #f1f5f9)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {tx.merchant_name || tx.description}
                    </span>
                    {tx.pending && (
                      <span
                        style={{
                          fontSize: "var(--text-xs, 0.75rem)",
                          color: "var(--color-text-muted, #6b7280)",
                          border: "1px solid var(--color-border, #2d3148)",
                          borderRadius: "var(--radius-full, 9999px)",
                          padding: "0 6px",
                          flexShrink: 0,
                        }}
                      >
                        Pending
                      </span>
                    )}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2, 0.5rem)" }}>
                    {tx.category_name && (
                      <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            background: tx.category_color || "var(--color-primary)",
                            flexShrink: 0,
                          }}
                        />
                        <span style={{ fontSize: "var(--text-xs, 0.75rem)", color: "var(--color-text-muted, #6b7280)" }}>
                          {tx.category_name}
                        </span>
                      </span>
                    )}
                    <span style={{ fontSize: "var(--text-xs, 0.75rem)", color: "var(--color-text-muted, #6b7280)" }}>
                      {formatDate(tx.date)}
                    </span>
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "var(--text-sm, 0.875rem)",
                    fontWeight: 600,
                    color: tx.amount >= 0 ? "rgb(34, 183, 128)" : "#ef4444",
                    flexShrink: 0,
                    marginLeft: "var(--space-3, 0.75rem)",
                  }}
                >
                  {formatAmount(tx.amount)}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedTx && (
        <TransactionDrawer
          transaction={selectedTx}
          onClose={() => setSelectedTx(null)}
        />
      )}
    </>
  );
}
