import { useSubscriptionsSummary, useAnnualSummary } from "../hooks/useSubscriptions";

const FREQ_LABELS = {
  weekly: "Weekly",
  biweekly: "Bi-weekly",
  monthly: "Monthly",
  quarterly: "Quarterly",
  annual: "Annual",
};

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

export default function SubscriptionsPage() {
  const { data: summaryData, isLoading: summaryLoading } = useSubscriptionsSummary();
  const { data: annualData, isLoading: annualLoading } = useAnnualSummary();

  const isLoading = summaryLoading || annualLoading;

  const totalMonthly = annualData?.total_monthly ?? summaryData?.total_monthly ?? 0;
  const totalAnnual = annualData?.total_annual ?? summaryData?.total_annual ?? 0;
  const count = annualData?.count ?? summaryData?.count ?? 0;
  const subscriptions = annualData?.subscriptions_by_cost ?? summaryData?.subscriptions ?? [];
  const top3Savings = annualData?.top3_annual_savings ?? 0;

  if (isLoading) {
    return (
      <div style={{ padding: "var(--space-6)" }}>
        <h1 style={{ fontSize: "var(--font-size-2xl)", fontWeight: "var(--font-weight-bold)", marginBottom: "var(--space-6)", color: "var(--color-text-primary)" }}>
          Subscriptions
        </h1>
        <div style={{ height: 100, borderRadius: "var(--radius-lg)", background: "var(--color-bg-card)", animation: "pulse 1.5s ease-in-out infinite", marginBottom: "var(--space-4)" }} />
        {[1, 2, 3].map(i => (
          <div key={i} style={{ height: 64, marginBottom: "var(--space-3)", borderRadius: "var(--radius-lg)", background: "var(--color-bg-card)", animation: "pulse 1.5s ease-in-out infinite" }} />
        ))}
      </div>
    );
  }

  return (
    <div style={{ padding: "var(--space-6)", maxWidth: 800, margin: "0 auto" }}>
      <h1 style={{ fontSize: "var(--font-size-2xl)", fontWeight: "var(--font-weight-bold)", marginBottom: "var(--space-6)", color: "var(--color-text-primary)" }}>
        Subscriptions
      </h1>

      {/* Summary card */}
      <div style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-6)",
        marginBottom: "var(--space-4)",
        display: "flex",
        gap: "var(--space-8)",
        flexWrap: "wrap",
      }}>
        <div>
          <div style={{ color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>Monthly Total</div>
          <div style={{ fontSize: "var(--font-size-3xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-primary)" }}>
            {formatCurrency(totalMonthly)}
          </div>
        </div>
        <div>
          <div style={{ color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>Annual Total</div>
          <div style={{ fontSize: "var(--font-size-3xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-text-primary)" }}>
            {formatCurrency(totalAnnual)}
          </div>
        </div>
        <div>
          <div style={{ color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>Active</div>
          <div style={{ fontSize: "var(--font-size-3xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-text-primary)" }}>
            {count}
          </div>
        </div>
      </div>

      {/* Savings Opportunity card */}
      {count > 0 && (
        <div style={{
          background: "var(--color-bg-card)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-4) var(--space-6)",
          marginBottom: "var(--space-6)",
          display: "flex",
          alignItems: "flex-start",
          gap: "var(--space-3)",
        }}>
          <span style={{ fontSize: "var(--font-size-xl)", flexShrink: 0 }}>💡</span>
          <div>
            <div style={{ color: "var(--color-text-primary)", fontSize: "var(--font-size-sm)", marginBottom: "var(--space-1)" }}>
              You&apos;re spending <strong>{formatCurrency(totalAnnual)}/year</strong> on subscriptions.
            </div>
            {count >= 1 && top3Savings > 0 && (
              <div style={{ color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)" }}>
                Cancelling your top {Math.min(count, 3)} most expensive {Math.min(count, 3) === 1 ? "subscription" : "subscriptions"} would save{" "}
                <strong style={{ color: "var(--color-primary)" }}>{formatCurrency(top3Savings)}/year</strong>.
              </div>
            )}
          </div>
        </div>
      )}

      {subscriptions.length === 0 ? (
        <div style={{ textAlign: "center", padding: "var(--space-12)", color: "var(--color-text-muted)" }}>
          No subscriptions detected yet. They'll appear after your transactions are synced and analyzed.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          {subscriptions.map((sub) => (
            <div key={sub.id} style={{
              background: "var(--color-bg-card)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "var(--space-4)",
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1)" }}>
                  <span style={{ fontWeight: "var(--font-weight-semibold)", color: "var(--color-text-primary)", fontSize: "var(--font-size-md)" }}>
                    {sub.merchant_name}
                  </span>
                  <span style={{ background: "var(--color-bg-elevated)", color: "var(--color-text-secondary)", padding: "1px 6px", borderRadius: "var(--radius-full)", fontSize: "var(--font-size-xs)" }}>
                    {FREQ_LABELS[sub.frequency] || sub.frequency}
                  </span>
                </div>
                <div style={{ color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)" }}>
                  {formatCurrency(sub.monthly_cost)}/mo · <strong>{formatCurrency(sub.annual_cost)}/yr</strong>
                </div>
              </div>
              <div style={{ fontWeight: "var(--font-weight-bold)", fontSize: "var(--font-size-lg)", color: "var(--color-text-primary)", flexShrink: 0 }}>
                {formatCurrency(sub.average_amount)}
                <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", fontWeight: "normal", marginLeft: 2 }}>
                  /{sub.frequency === "monthly" ? "mo" : sub.frequency === "annual" ? "yr" : sub.frequency}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
