import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import AccountOverviewCards from "../components/AccountOverviewCards";
import SpendingBreakdownChart from "../components/SpendingBreakdownChart";
import NetWorthHistoryChart from "../components/NetWorthHistoryChart";
import SpendingTrendChart from "../components/SpendingTrendChart";
import RecentActivityFeed from "../components/RecentActivityFeed";
import { useSavingsOpportunities, useHealthScore, useInsightsSummary } from "../hooks/useInsights";

/* ── Stat tile ──────────────────────────────────────────────── */
function StatTile({ label, value, subtext, loading }) {
  return (
    <div
      style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-5) var(--space-6)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-1)",
        flex: 1,
        minWidth: 180,
      }}
    >
      <span
        style={{
          fontSize: "var(--font-size-sm)",
          color: "var(--color-text-secondary)",
          fontWeight: "var(--font-weight-medium)",
        }}
      >
        {label}
      </span>
      {loading ? (
        <div
          style={{
            height: 28,
            width: 120,
            background: "var(--color-bg-elevated)",
            borderRadius: "var(--radius-sm)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      ) : (
        <span
          style={{
            fontSize: "var(--font-size-3xl)",
            fontWeight: "var(--font-weight-bold)",
            color: "var(--color-text-primary)",
            lineHeight: "var(--line-height-tight)",
          }}
        >
          {value ?? "—"}
        </span>
      )}
      {subtext && (
        <span
          style={{
            fontSize: "var(--font-size-xs)",
            color: "var(--color-text-muted)",
          }}
        >
          {subtext}
        </span>
      )}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}

/* ── Currency formatter ─────────────────────────────────────── */
function fmt(val) {
  if (val == null) return "—";
  const num = Number(val);
  const abs = Math.abs(num);
  const sign = num < 0 ? "-" : "";
  if (abs >= 1_000_000) {
    return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  }
  if (abs >= 1_000) {
    return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}$${abs.toFixed(2)}`;
}

/* ── Section wrapper ────────────────────────────────────────── */
function Section({ children, style }) {
  return (
    <section
      style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        ...style,
      }}
    >
      {children}
    </section>
  );
}

/* ── Safe href helper — blocks javascript: and data: URLs ───── */
function safeHref(url) {
  if (!url) return "#";
  // Allow only relative paths starting with / or explicit safe protocols
  if (/^\/[^/]/.test(url) || url === "/" || url.startsWith("https://") || url.startsWith("http://")) {
    return url;
  }
  return "#";
}

/* ── Insight icon map ───────────────────────────────────────── */
const INSIGHT_ICONS = {
  "health_score": "❤️",
  "spending_increase": "📈",
  "anomaly": "⚠️",
  "savings_opportunity": "💰",
  "forecast_warning": "📅",
};

/* ── Dashboard page ─────────────────────────────────────────── */
export default function DashboardPage() {
  const { data: netWorth, isLoading: nwLoading } = useQuery({
    queryKey: ["net-worth"],
    queryFn: () => api.get("/api/v1/dashboard/net-worth").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const { data: cashFlow, isLoading: cfLoading } = useQuery({
    queryKey: ["cash-flow"],
    queryFn: () => api.get("/api/v1/dashboard/cash-flow").then((r) => r.data),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const { data: insightsList } = useInsightsSummary();
  const insights = insightsList ?? [];

  const { data: savingsData } = useSavingsOpportunities();
  const topOpportunities = (savingsData ?? []).slice(0, 3);

  const { data: healthData } = useHealthScore();
  const healthScore = healthData?.overall_score ?? null;
  const components = healthData?.components ? Object.values(healthData.components) : [];

  const cashFlowVal = cashFlow?.net_this_month ?? cashFlow?.net ?? null;
  const cashFlowColor =
    cashFlowVal == null
      ? "var(--color-text-primary)"
      : cashFlowVal >= 0
      ? "var(--color-success)"
      : "var(--color-error)";

  return (
    <div
      style={{
        padding: "var(--space-6)",
        maxWidth: 1280,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-6)",
      }}
    >
      {/* Page heading */}
      <h1
        style={{
          fontSize: "var(--font-size-3xl)",
          fontWeight: "var(--font-weight-bold)",
          color: "var(--color-text-primary)",
          lineHeight: "var(--line-height-tight)",
        }}
      >
        Dashboard
      </h1>

      {/* ── Row 0: Stat tiles ── */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-4)",
          flexWrap: "wrap",
        }}
      >
        <StatTile
          label="Net Worth"
          value={netWorth ? fmt(netWorth.net_worth ?? netWorth.total) : null}
          subtext="Across all linked accounts"
          loading={nwLoading}
        />
        <StatTile
          label="Cash Flow — This Month"
          value={
            cashFlowVal != null ? (
              <span style={{ color: cashFlowColor }}>{fmt(cashFlowVal)}</span>
            ) : null
          }
          subtext="Income minus expenses"
          loading={cfLoading}
        />
      </div>

      {/* ── Row 1: Account overview (full width, horizontally scrollable) ── */}
      <div
        style={{
          overflowX: "auto",
          WebkitOverflowScrolling: "touch",
        }}
      >
        <AccountOverviewCards />
      </div>

      {/* ── Row 2: Spending breakdown + spending trend ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 3fr",
          gap: "var(--space-4)",
        }}
        className="dashboard-row-2"
      >
        <Section>
          <SpendingBreakdownChart />
        </Section>
        <Section>
          <SpendingTrendChart />
        </Section>
      </div>

      {/* ── Row 3: Net worth history + recent activity ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "3fr 2fr",
          gap: "var(--space-4)",
        }}
        className="dashboard-row-3"
      >
        <Section>
          <NetWorthHistoryChart />
        </Section>
        <Section>
          <RecentActivityFeed />
        </Section>
      </div>

      {/* ── Row 4: Ways to Save ── */}
      <Section style={{ padding: "var(--space-5) var(--space-6)" }}>
        {/* Header */}
        <div style={{ marginBottom: "var(--space-4)" }}>
          <h2
            style={{
              fontSize: "var(--font-size-lg)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-text-primary)",
              margin: 0,
            }}
          >
            Ways to Save
          </h2>
          <p
            style={{
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-secondary)",
              margin: "var(--space-1) 0 0",
            }}
          >
            vs 3-month average
          </p>
        </div>

        {topOpportunities.length === 0 ? (
          <p
            style={{
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-muted)",
              margin: 0,
            }}
          >
            Looking good — spending is on track this month.
          </p>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
            }}
          >
            {topOpportunities.map((opp) => (
              <div
                key={opp.category_id}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "var(--space-3)",
                }}
              >
                {/* Colored dot */}
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: opp.category_color || "var(--color-text-muted)",
                    flexShrink: 0,
                    marginTop: 4,
                  }}
                />
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
                  <span
                    style={{
                      fontSize: "var(--font-size-sm)",
                      fontWeight: "var(--font-weight-semibold)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {opp.category_name}
                  </span>
                  <span
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-secondary)",
                    }}
                  >
                    Spending {fmt(opp.current_month_spend)} ({opp.pct_over_average}% over avg)
                  </span>
                  <span
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-success)",
                      fontWeight: "var(--font-weight-medium)",
                    }}
                  >
                    Potential savings: {fmt(opp.potential_savings)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* ── Row 5: Financial Health Score + Ways to Save side by side ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-4)",
        }}
        className="dashboard-row-5"
      >
        {/* Health Score card */}
        {healthScore !== null && (
          <div style={{
            background: "var(--color-bg-card)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)", marginBottom: "var(--space-4)" }}>
              <div style={{
                fontSize: "3rem",
                fontWeight: "var(--font-weight-bold)",
                color: healthScore >= 70 ? "var(--color-primary)" : healthScore >= 50 ? "#f59e0b" : "#ef4444",
                lineHeight: 1,
              }}>
                {Math.round(healthScore)}
              </div>
              <div>
                <div style={{ fontSize: "var(--font-size-base)", fontWeight: "var(--font-weight-semibold)", color: "var(--color-text-primary)" }}>
                  Financial Health Score
                </div>
                <div style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>out of 100</div>
              </div>
            </div>

            {/* Overall bar */}
            <div style={{ height: 8, background: "var(--color-bg)", borderRadius: 4, marginBottom: "var(--space-4)", overflow: "hidden" }}>
              <div style={{
                height: "100%",
                width: `${healthScore}%`,
                background: healthScore >= 70 ? "var(--color-primary)" : healthScore >= 50 ? "#f59e0b" : "#ef4444",
                borderRadius: 4,
                transition: "width 0.5s ease",
              }} />
            </div>

            {/* Components */}
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
              {components.map((comp) => (
                <div key={comp.label}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-primary)" }}>
                      {comp.label} <span style={{ color: "var(--color-text-muted)", fontSize: "var(--font-size-xs)" }}>({comp.weight}%)</span>
                    </span>
                    <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>{Math.round(comp.score)}/100</span>
                  </div>
                  <div style={{ height: 4, background: "var(--color-bg)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{
                      height: "100%",
                      width: `${comp.score}%`,
                      background: comp.score >= 70 ? "var(--color-primary)" : comp.score >= 50 ? "#f59e0b" : "#ef4444",
                      borderRadius: 2,
                    }} />
                  </div>
                  <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", marginTop: 2 }}>{comp.detail}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Row 6: Insights panel ── */}
      {insights.length > 0 && (
        <div style={{
          background: "var(--color-bg-card)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-6)",
        }}>
          <h2 style={{ fontSize: "var(--font-size-lg)", fontWeight: "var(--font-weight-semibold)", marginBottom: "var(--space-4)", color: "var(--color-text-primary)", margin: "0 0 var(--space-4) 0" }}>
            Insights
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {insights.map((insight, i) => (
              <a
                key={i}
                href={safeHref(insight.action_url)}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "var(--space-3)",
                  padding: "var(--space-3)",
                  background: "var(--color-bg)",
                  borderRadius: "var(--radius-md)",
                  textDecoration: "none",
                  border: "1px solid transparent",
                  transition: "border-color 0.15s",
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = "var(--color-primary)"}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = "transparent"}
              >
                <span style={{ fontSize: "1.25rem", flexShrink: 0, marginTop: 2 }}>
                  {INSIGHT_ICONS[insight.type] || "💡"}
                </span>
                <div>
                  <div style={{ fontWeight: "var(--font-weight-medium)", color: "var(--color-text-primary)", fontSize: "var(--font-size-sm)", marginBottom: 2 }}>
                    {insight.title}
                  </div>
                  <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" }}>
                    {insight.description}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Responsive grid stacking */}
      <style>{`
        @media (max-width: 900px) {
          .dashboard-row-2,
          .dashboard-row-3,
          .dashboard-row-5 {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
