import { useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from "recharts";
import { useCategorySpending, useMerchantSpending, useIncomeVsExpenses, useYearOverYear, useTaxSummary } from "../hooks/useAnalytics";

function getPresetDates(preset) {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();

  if (preset === "this-month") {
    return {
      startDate: new Date(year, month, 1).toISOString().slice(0, 10),
      endDate: new Date(year, month + 1, 0).toISOString().slice(0, 10),
    };
  }
  if (preset === "last-month") {
    const lm = month === 0 ? 11 : month - 1;
    const ly = month === 0 ? year - 1 : year;
    return {
      startDate: new Date(ly, lm, 1).toISOString().slice(0, 10),
      endDate: new Date(ly, lm + 1, 0).toISOString().slice(0, 10),
    };
  }
  if (preset === "last-3-months") {
    const start = new Date(today);
    start.setMonth(start.getMonth() - 3);
    start.setDate(1);
    return {
      startDate: start.toISOString().slice(0, 10),
      endDate: today.toISOString().slice(0, 10),
    };
  }
  if (preset === "this-year") {
    return {
      startDate: `${year}-01-01`,
      endDate: `${year}-12-31`,
    };
  }
  return { startDate: null, endDate: null };
}

const PRESETS = [
  { key: "this-month", label: "This Month" },
  { key: "last-month", label: "Last Month" },
  { key: "last-3-months", label: "Last 3 Months" },
  { key: "this-year", label: "This Year" },
];

const FALLBACK_COLORS = [
  "#22b780", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#10b981", "#f97316", "#ec4899", "#6366f1",
];

function formatCurrency(value) {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
  return `$${value.toFixed(0)}`;
}

function sanitizeCsvField(value) {
  if (value && /^[=+\-@\t\r]/.test(value)) {
    return '\t' + value;
  }
  return value;
}

function exportTaxCsv(transactions, year) {
  const header = "Date,Description,Merchant,Tax Category,Amount\n";
  const rows = transactions.map(t =>
    `${t.date},"${sanitizeCsvField((t.description || "")).replace(/"/g, '""')}","${sanitizeCsvField((t.merchant_name || "")).replace(/"/g, '""')}","${sanitizeCsvField(t.tax_category || "")}",${t.amount.toFixed(2)}`
  ).join("\n");
  const csv = header + rows;
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `tax-summary-${year}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function AnalyticsPage() {
  const [preset, setPreset] = useState("this-month");
  const { startDate, endDate } = getPresetDates(preset);

  const { data, isLoading } = useCategorySpending({ startDate, endDate });
  const categories = data?.categories ?? [];

  const { data: merchantData, isLoading: merchantLoading } = useMerchantSpending({ startDate, endDate });
  const merchants = merchantData?.merchants ?? [];

  const { data: incomeExpData, isLoading: incomeExpLoading } = useIncomeVsExpenses();
  const incomeExpRows = incomeExpData ?? [];

  const { data: yoyData, isLoading: yoyLoading } = useYearOverYear();
  const yoySeries = yoyData?.series ?? [];
  const currentYear = yoyData?.current_year ?? new Date().getFullYear();
  const priorYear = yoyData?.prior_year ?? new Date().getFullYear() - 1;

  const [taxYear, setTaxYear] = useState(new Date().getFullYear());
  const { data: taxData, isLoading: taxLoading } = useTaxSummary({ year: taxYear });
  const taxTotal = taxData?.total_deductible ?? 0;
  const taxCategories = taxData?.by_tax_category ?? [];
  const taxTxs = taxData?.transactions ?? [];
  const yearOptions = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  return (
    <div style={{ padding: "var(--space-6)", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ fontSize: "var(--font-size-2xl)", fontWeight: "var(--font-weight-bold)", marginBottom: "var(--space-6)", color: "var(--color-text-primary)" }}>
        Analytics
      </h1>

      {/* Date range presets */}
      <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-6)", flexWrap: "wrap" }}>
        {PRESETS.map((p) => (
          <button
            key={p.key}
            onClick={() => setPreset(p.key)}
            style={{
              background: preset === p.key ? "var(--color-primary)" : "var(--color-bg-elevated)",
              color: preset === p.key ? "#fff" : "var(--color-text-secondary)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-2) var(--space-4)",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              cursor: "pointer",
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Category spending chart */}
      <div style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-6)",
      }}>
        <h2 style={{ fontSize: "var(--font-size-lg)", fontWeight: "var(--font-weight-semibold)", marginBottom: "var(--space-4)", color: "var(--color-text-primary)" }}>
          Spending by Category
        </h2>

        {isLoading ? (
          <div style={{ height: 300, background: "var(--color-bg)", borderRadius: "var(--radius-md)", animation: "pulse 1.5s ease-in-out infinite" }} />
        ) : categories.length === 0 ? (
          <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-text-muted)" }}>
            No spending data for this period.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(200, categories.length * 36)}>
            <BarChart
              layout="vertical"
              data={categories}
              margin={{ top: 4, right: 80, left: 8, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={formatCurrency}
                tick={{ fill: "var(--color-text-muted)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={110}
              />
              <Tooltip
                formatter={(value) => [formatCurrency(value), "Spent"]}
                contentStyle={{
                  background: "var(--color-bg-card)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--color-text-primary)",
                  fontSize: 13,
                }}
              />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]} label={{ position: "right", formatter: formatCurrency, fill: "var(--color-text-muted)", fontSize: 11 }}>
                {categories.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color || FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Merchant spending ranked list */}
      <div style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-6)",
        marginTop: "var(--space-6)",
      }}>
        <h2 style={{ fontSize: "var(--font-size-lg)", fontWeight: "var(--font-weight-semibold)", marginBottom: "var(--space-4)", color: "var(--color-text-primary)" }}>
          Top Merchants
        </h2>

        {merchantLoading ? (
          <div style={{ height: 200, background: "var(--color-bg)", borderRadius: "var(--radius-md)", animation: "pulse 1.5s ease-in-out infinite" }} />
        ) : merchants.length === 0 ? (
          <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--color-text-muted)" }}>
            No merchant data for this period.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {merchants.map((m, i) => (
              <div key={m.merchant_name} style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "var(--space-3) var(--space-2)",
                borderRadius: "var(--radius-md)",
                background: i % 2 === 0 ? "transparent" : "var(--color-bg)",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
                  <span style={{ width: 24, textAlign: "center", fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)", fontWeight: "var(--font-weight-semibold)" }}>
                    {i + 1}
                  </span>
                  <div>
                    <div style={{ fontWeight: "var(--font-weight-medium)", color: "var(--color-text-primary)", fontSize: "var(--font-size-sm)" }}>
                      {m.merchant_name}
                    </div>
                    <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)" }}>
                      {m.transaction_count} transaction{m.transaction_count !== 1 ? "s" : ""}
                    </div>
                  </div>
                </div>
                <span style={{ fontWeight: "var(--font-weight-bold)", color: "var(--color-text-primary)", fontSize: "var(--font-size-sm)" }}>
                  ${m.total_spent.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      {/* Income vs Expenses grouped bar chart */}
      <div style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-6)",
        marginTop: "var(--space-6)",
      }}>
        <h2 style={{ fontSize: "var(--font-size-lg)", fontWeight: "var(--font-weight-semibold)", marginBottom: "var(--space-4)", color: "var(--color-text-primary)" }}>
          Income vs Expenses (12 Months)
        </h2>

        {incomeExpLoading ? (
          <div style={{ height: 300, background: "var(--color-bg)", borderRadius: "var(--radius-md)", animation: "pulse 1.5s ease-in-out infinite" }} />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={incomeExpRows} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="month"
                tick={{ fill: "var(--color-text-muted)", fontSize: 11 }}
                tickFormatter={(v) => {
                  const [y, m] = v.split("-");
                  return new Date(Number(y), Number(m) - 1).toLocaleString("en-US", { month: "short", year: "2-digit" });
                }}
              />
              <YAxis
                tick={{ fill: "var(--color-text-muted)", fontSize: 11 }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{ background: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)" }}
                labelStyle={{ color: "var(--color-text-primary)" }}
                formatter={(value, name) => [`$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name === "income" ? "Income" : "Expenses"]}
              />
              <Legend formatter={(value) => value === "income" ? "Income" : "Expenses"} />
              <Bar dataKey="income" fill="var(--color-primary)" radius={[3, 3, 0, 0]} />
              <Bar dataKey="expenses" fill="#ef4444" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Tax Summary */}
      <div style={{
        background: "var(--color-bg-card)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-6)",
        marginTop: "var(--space-6)",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-4)" }}>
          <h2 style={{ fontSize: "var(--font-size-lg)", fontWeight: "var(--font-weight-semibold)", color: "var(--color-text-primary)" }}>
            Tax Summary
          </h2>
          <select
            value={taxYear}
            onChange={(e) => setTaxYear(Number(e.target.value))}
            style={{ padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-border)", background: "var(--color-bg)", color: "var(--color-text-primary)", fontSize: "var(--font-size-sm)" }}
          >
            {yearOptions.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>

        {taxLoading ? (
          <div style={{ height: 200, background: "var(--color-bg)", borderRadius: "var(--radius-md)", animation: "pulse 1.5s ease-in-out infinite" }} />
        ) : (
          <>
            <div style={{ fontSize: "var(--font-size-2xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-primary)", marginBottom: "var(--space-4)" }}>
              ${taxTotal.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)", fontWeight: "var(--font-weight-normal)", marginLeft: "var(--space-2)" }}>total deductible</span>
            </div>

            {taxCategories.length > 0 && (
              <div style={{ marginBottom: "var(--space-4)" }}>
                {taxCategories.map(tc => (
                  <div key={tc.tax_category} style={{ display: "flex", justifyContent: "space-between", padding: "var(--space-2) 0", borderBottom: "1px solid var(--color-border)", fontSize: "var(--font-size-sm)" }}>
                    <span style={{ color: "var(--color-text-primary)" }}>{tc.tax_category}</span>
                    <span style={{ color: "var(--color-text-muted)" }}>{tc.transaction_count} txns · <strong style={{ color: "var(--color-text-primary)" }}>${tc.total.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong></span>
                  </div>
                ))}
              </div>
            )}

            {taxTxs.length > 0 && (
              <>
                <div style={{ maxHeight: 240, overflowY: "auto", marginBottom: "var(--space-4)" }}>
                  {taxTxs.map(tx => (
                    <div key={tx.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "var(--space-2)", borderRadius: "var(--radius-sm)", fontSize: "var(--font-size-xs)" }}>
                      <div>
                        <div style={{ color: "var(--color-text-primary)", fontWeight: "var(--font-weight-medium)" }}>{tx.merchant_name || tx.description}</div>
                        <div style={{ color: "var(--color-text-muted)" }}>{tx.date} · {tx.tax_category}</div>
                      </div>
                      <span style={{ color: "var(--color-text-primary)", fontWeight: "var(--font-weight-semibold)" }}>${tx.amount.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => exportTaxCsv(taxTxs, taxYear)}
                  style={{ padding: "var(--space-2) var(--space-4)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-primary)", background: "transparent", color: "var(--color-primary)", cursor: "pointer", fontSize: "var(--font-size-sm)", fontWeight: "var(--font-weight-medium)" }}
                >
                  Export as CSV
                </button>
              </>
            )}

            {taxTxs.length === 0 && taxCategories.length === 0 && (
              <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)" }}>
                No tax-deductible transactions for {taxYear}. Mark transactions as tax deductible in the Transactions view.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
