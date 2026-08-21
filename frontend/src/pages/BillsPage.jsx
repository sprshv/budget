import { useState } from "react";
import { useBills, useMarkBillPaid } from "../hooks/useBills";

function DaysUntilBadge({ days }) {
  let bg, text;
  if (days === null || days === undefined) {
    bg = "var(--color-border)";
    text = "var(--color-text-muted)";
  } else if (days <= 3) {
    bg = "rgba(239,68,68,0.12)";
    text = "#ef4444";
  } else if (days <= 7) {
    bg = "rgba(245,158,11,0.12)";
    text = "#f59e0b";
  } else {
    bg = "var(--color-success-light)";
    text = "var(--color-success)";
  }

  const label =
    days === null
      ? "Unknown"
      : days === 0
      ? "Due Today"
      : days < 0
      ? "Overdue"
      : `${days}d`;

  return (
    <span
      style={{
        background: bg,
        color: text,
        padding: "2px 8px",
        borderRadius: "var(--radius-full)",
        fontSize: "var(--font-size-xs)",
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
}

const FREQ_LABELS = {
  weekly: "Weekly",
  biweekly: "Bi-weekly",
  monthly: "Monthly",
  quarterly: "Quarterly",
  annual: "Annual",
};

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function BillCalendar({ bills, onMarkPaid }) {
  const [viewDate, setViewDate] = useState(new Date());

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth(); // 0-indexed

  const firstDay = new Date(year, month, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  const cells = [];
  // Leading days from prev month
  for (let i = firstDay - 1; i >= 0; i--) {
    cells.push({ day: daysInPrevMonth - i, currentMonth: false });
  }
  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, currentMonth: true });
  }
  // Trailing days to fill to 42 cells (6 rows)
  const remaining = 42 - cells.length;
  for (let d = 1; d <= remaining; d++) {
    cells.push({ day: d, currentMonth: false });
  }

  // Map bills to their due day in the current month
  const billsByDay = {};
  bills.forEach((bill) => {
    if (!bill.next_expected_date) return;
    const dueDate = new Date(bill.next_expected_date + "T00:00:00");
    if (dueDate.getFullYear() === year && dueDate.getMonth() === month) {
      const d = dueDate.getDate();
      if (!billsByDay[d]) billsByDay[d] = [];
      billsByDay[d].push(bill);
    }
  });

  const today = new Date();
  const isToday = (day) =>
    today.getFullYear() === year &&
    today.getMonth() === month &&
    today.getDate() === day;

  return (
    <div>
      {/* Month navigation */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--space-4)",
        }}
      >
        <button
          onClick={() => setViewDate(new Date(year, month - 1, 1))}
          style={{
            background: "var(--color-bg-elevated)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-2) var(--space-3)",
            color: "var(--color-text-primary)",
            cursor: "pointer",
            fontSize: "var(--font-size-md)",
            lineHeight: 1,
          }}
        >
          ←
        </button>
        <span
          style={{
            fontWeight: "var(--font-weight-semibold)",
            fontSize: "var(--font-size-lg)",
            color: "var(--color-text-primary)",
          }}
        >
          {MONTH_NAMES[month]} {year}
        </span>
        <button
          onClick={() => setViewDate(new Date(year, month + 1, 1))}
          style={{
            background: "var(--color-bg-elevated)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-2) var(--space-3)",
            color: "var(--color-text-primary)",
            cursor: "pointer",
            fontSize: "var(--font-size-md)",
            lineHeight: 1,
          }}
        >
          →
        </button>
      </div>

      {/* Day-of-week headers */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(7, 1fr)",
          gap: 1,
          marginBottom: 2,
        }}
      >
        {DAY_NAMES.map((d) => (
          <div
            key={d}
            style={{
              textAlign: "center",
              fontSize: "var(--font-size-xs)",
              color: "var(--color-text-muted)",
              padding: "var(--space-1)",
              fontWeight: "var(--font-weight-medium)",
            }}
          >
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(7, 1fr)",
          gap: 1,
        }}
      >
        {cells.map((cell, idx) => {
          const dayBills = cell.currentMonth ? billsByDay[cell.day] || [] : [];
          const first = dayBills[0];
          const extra = dayBills.length - 1;
          const todayCell = cell.currentMonth && isToday(cell.day);
          const isUrgent =
            first &&
            first.days_until_due !== null &&
            first.days_until_due <= 3;

          return (
            <div
              key={idx}
              style={{
                minHeight: 72,
                background: todayCell
                  ? "rgba(34,183,128,0.08)"
                  : "var(--color-bg-card)",
                border: todayCell
                  ? "1px solid var(--color-primary)"
                  : "1px solid var(--color-border)",
                borderRadius: "var(--radius-sm)",
                padding: "var(--space-1)",
                opacity: cell.currentMonth ? 1 : 0.35,
              }}
            >
              {/* Day number */}
              <div
                style={{
                  fontSize: "var(--font-size-xs)",
                  color: todayCell
                    ? "var(--color-primary)"
                    : "var(--color-text-muted)",
                  fontWeight: todayCell ? "var(--font-weight-bold)" : "normal",
                  marginBottom: 2,
                }}
              >
                {cell.day}
              </div>

              {/* First bill chip */}
              {first && (
                <div
                  onClick={() => onMarkPaid && onMarkPaid(first)}
                  title={`${first.merchant_name} — $${parseFloat(first.average_amount).toFixed(2)}\nClick to mark paid`}
                  style={{
                    background: isUrgent
                      ? "rgba(239,68,68,0.15)"
                      : "rgba(34,183,128,0.12)",
                    borderRadius: "var(--radius-sm)",
                    padding: "1px 4px",
                    fontSize: 10,
                    color: isUrgent ? "#ef4444" : "var(--color-primary)",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    cursor: "pointer",
                    marginBottom: 1,
                  }}
                >
                  {first.merchant_name}
                </div>
              )}

              {/* Overflow count */}
              {extra > 0 && (
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--color-text-muted)",
                  }}
                >
                  +{extra} more
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function BillsPage() {
  const { data: bills = [], isLoading } = useBills();
  const markPaid = useMarkBillPaid();
  const [view, setView] = useState("list");

  if (isLoading) {
    return (
      <div style={{ padding: "var(--space-6)" }}>
        <h1
          style={{
            fontSize: "var(--font-size-2xl)",
            fontWeight: "var(--font-weight-bold)",
            marginBottom: "var(--space-6)",
            color: "var(--color-text-primary)",
          }}
        >
          Upcoming Bills
        </h1>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              height: 72,
              marginBottom: "var(--space-3)",
              borderRadius: "var(--radius-lg)",
              background: "var(--color-bg-card)",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div style={{ padding: "var(--space-6)", maxWidth: 800, margin: "0 auto" }}>
      <h1
        style={{
          fontSize: "var(--font-size-2xl)",
          fontWeight: "var(--font-weight-bold)",
          marginBottom: "var(--space-4)",
          color: "var(--color-text-primary)",
        }}
      >
        Upcoming Bills
      </h1>

      {/* List / Calendar toggle */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-2)",
          marginBottom: "var(--space-6)",
        }}
      >
        {["list", "calendar"].map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            style={{
              background:
                view === v ? "var(--color-primary)" : "var(--color-bg-elevated)",
              color: view === v ? "#fff" : "var(--color-text-secondary)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-2) var(--space-4)",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              cursor: "pointer",
              textTransform: "capitalize",
            }}
          >
            {v}
          </button>
        ))}
      </div>

      {/* Calendar view */}
      {view === "calendar" && (
        <div
          style={{
            background: "var(--color-bg-card)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-4)",
          }}
        >
          <BillCalendar
            bills={bills}
            onMarkPaid={(bill) => markPaid.mutate(bill.id)}
          />
        </div>
      )}

      {/* List view */}
      {view === "list" && (
        <>
          {bills.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "var(--space-12)",
                color: "var(--color-text-muted)",
              }}
            >
              No bills detected yet. Transactions will be analyzed automatically
              after your next sync.
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
              }}
            >
              {bills.map((bill) => (
                <div
                  key={bill.id}
                  style={{
                    background: "var(--color-bg-card)",
                    border:
                      bill.days_until_due !== null && bill.days_until_due <= 3
                        ? "1px solid rgba(239,68,68,0.3)"
                        : "1px solid var(--color-border)",
                    borderRadius: "var(--radius-lg)",
                    padding: "var(--space-4)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "var(--space-4)",
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "var(--space-2)",
                        marginBottom: "var(--space-1)",
                      }}
                    >
                      <span
                        style={{
                          fontWeight: "var(--font-weight-semibold)",
                          color: "var(--color-text-primary)",
                          fontSize: "var(--font-size-md)",
                        }}
                      >
                        {bill.merchant_name}
                      </span>
                      <span
                        style={{
                          background: "var(--color-bg-elevated)",
                          color: "var(--color-text-secondary)",
                          padding: "1px 6px",
                          borderRadius: "var(--radius-full)",
                          fontSize: "var(--font-size-xs)",
                        }}
                      >
                        {FREQ_LABELS[bill.frequency] || bill.frequency}
                      </span>
                    </div>
                    <div
                      style={{
                        color: "var(--color-text-muted)",
                        fontSize: "var(--font-size-sm)",
                      }}
                    >
                      Due:{" "}
                      {bill.next_expected_date
                        ? new Date(
                            bill.next_expected_date + "T00:00:00"
                          ).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })
                        : "Unknown"}
                    </div>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-3)",
                      flexShrink: 0,
                    }}
                  >
                    <DaysUntilBadge days={bill.days_until_due} />
                    <span
                      style={{
                        fontWeight: "var(--font-weight-bold)",
                        fontSize: "var(--font-size-lg)",
                        color: "var(--color-text-primary)",
                      }}
                    >
                      ${parseFloat(bill.average_amount).toFixed(2)}
                    </span>
                    <button
                      onClick={() => markPaid.mutate(bill.id)}
                      disabled={markPaid.isPending}
                      style={{
                        background: "var(--color-primary)",
                        color: "#fff",
                        border: "none",
                        borderRadius: "var(--radius-md)",
                        padding: "var(--space-2) var(--space-3)",
                        fontSize: "var(--font-size-sm)",
                        fontWeight: "var(--font-weight-semibold)",
                        cursor: markPaid.isPending ? "not-allowed" : "pointer",
                        opacity: markPaid.isPending ? 0.6 : 1,
                        whiteSpace: "nowrap",
                      }}
                    >
                      Mark Paid
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
