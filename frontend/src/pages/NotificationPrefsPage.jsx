import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useNotificationPrefs, useUpdateNotificationPrefs } from "../hooks/useNotificationPrefs";

const TYPE_LABELS = {
  budget_alert: {
    label: "Budget Alerts",
    desc: "Notify when spending reaches your budget threshold",
  },
  bill_reminder: {
    label: "Bill Reminders",
    desc: "Remind you before bills are due",
  },
  low_balance: {
    label: "Low Balance Alerts",
    desc: "Alert when account balance drops below threshold",
  },
  large_purchase: {
    label: "Large Purchase Alerts",
    desc: "Alert for purchases above threshold",
  },
  unusual_spending: {
    label: "Unusual Spending",
    desc: "Detect anomalous transactions",
  },
  weekly_summary: {
    label: "Weekly Summary",
    desc: "Weekly spending recap every Monday",
  },
  monthly_summary: {
    label: "Monthly Summary",
    desc: "End-of-month financial summary",
  },
};

const THRESHOLD_TYPES = new Set(["low_balance", "large_purchase"]);

export default function NotificationPrefsPage() {
  const { data: prefs = [], isLoading } = useNotificationPrefs();
  const updatePrefs = useUpdateNotificationPrefs();
  const [local, setLocal] = useState([]);

  useEffect(() => {
    if (prefs.length > 0) setLocal(prefs);
  }, [prefs]);

  function toggle(notifType, field) {
    setLocal((prev) =>
      prev.map((p) =>
        p.notif_type === notifType ? { ...p, [field]: !p[field] } : p
      )
    );
  }

  function setThreshold(notifType, value) {
    setLocal((prev) =>
      prev.map((p) =>
        p.notif_type === notifType
          ? { ...p, threshold_amount: parseFloat(value) || null }
          : p
      )
    );
  }

  function save() {
    updatePrefs.mutate(local);
  }

  const headerStyle = {
    padding: "var(--space-4) var(--space-6)",
    borderBottom: "1px solid var(--color-border)",
    display: "flex",
    alignItems: "center",
    gap: "var(--space-4)",
    background: "var(--color-bg-secondary)",
  };

  if (isLoading) {
    return (
      <div style={{ padding: "var(--space-6)", color: "var(--color-text-muted)" }}>
        Loading preferences...
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)" }}>
      <div style={headerStyle}>
        <Link
          to="/settings"
          style={{
            color: "var(--color-text-secondary)",
            textDecoration: "none",
            fontSize: "var(--font-size-sm)",
          }}
        >
          ← Settings
        </Link>
        <h1
          style={{
            fontSize: "var(--font-size-xl)",
            fontWeight: "var(--font-weight-semibold)",
            color: "var(--color-text-primary)",
          }}
        >
          Notification Preferences
        </h1>
      </div>

      <div
        style={{
          maxWidth: "640px",
          margin: "0 auto",
          padding: "var(--space-8) var(--space-4)",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          {local.map((pref) => {
            const meta = TYPE_LABELS[pref.notif_type] || {
              label: pref.notif_type,
              desc: "",
            };
            return (
              <div
                key={pref.notif_type}
                style={{
                  background: "var(--color-bg-card)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-4)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    gap: "var(--space-4)",
                    marginBottom:
                      THRESHOLD_TYPES.has(pref.notif_type) && pref.push_enabled
                        ? "var(--space-3)"
                        : 0,
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontWeight: "var(--font-weight-semibold)",
                        color: "var(--color-text-primary)",
                        fontSize: "var(--font-size-sm)",
                      }}
                    >
                      {meta.label}
                    </div>
                    <div
                      style={{
                        fontSize: "var(--font-size-xs)",
                        color: "var(--color-text-muted)",
                        marginTop: "var(--space-1)",
                      }}
                    >
                      {meta.desc}
                    </div>
                  </div>
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-2)",
                      cursor: "pointer",
                      flexShrink: 0,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={pref.push_enabled}
                      onChange={() => toggle(pref.notif_type, "push_enabled")}
                      style={{
                        width: 16,
                        height: 16,
                        accentColor: "var(--color-primary)",
                        cursor: "pointer",
                      }}
                    />
                    <span
                      style={{
                        fontSize: "var(--font-size-xs)",
                        color: "var(--color-text-muted)",
                      }}
                    >
                      Enabled
                    </span>
                  </label>
                </div>

                {THRESHOLD_TYPES.has(pref.notif_type) && pref.push_enabled && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--space-2)",
                      paddingTop: "var(--space-2)",
                      borderTop: "1px solid var(--color-border)",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "var(--font-size-xs)",
                        color: "var(--color-text-muted)",
                      }}
                    >
                      Alert threshold: $
                    </span>
                    <input
                      type="number"
                      value={pref.threshold_amount ?? ""}
                      onChange={(e) => setThreshold(pref.notif_type, e.target.value)}
                      style={{
                        width: 80,
                        padding: "var(--space-1) var(--space-2)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "var(--radius-md)",
                        background: "var(--color-bg)",
                        color: "var(--color-text-primary)",
                        fontSize: "var(--font-size-sm)",
                      }}
                      min={0}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {updatePrefs.isSuccess && (
          <p
            style={{
              marginTop: "var(--space-4)",
              fontSize: "var(--font-size-sm)",
              color: "var(--color-primary)",
            }}
          >
            Preferences saved.
          </p>
        )}

        {updatePrefs.isError && (
          <p
            style={{
              marginTop: "var(--space-4)",
              fontSize: "var(--font-size-sm)",
              color: "var(--color-error)",
            }}
          >
            Failed to save preferences. Please try again.
          </p>
        )}

        <button
          onClick={save}
          disabled={updatePrefs.isPending}
          style={{
            marginTop: "var(--space-6)",
            padding: "var(--space-2) var(--space-6)",
            background: "var(--color-primary)",
            color: "white",
            border: "none",
            borderRadius: "var(--radius-md)",
            cursor: updatePrefs.isPending ? "not-allowed" : "pointer",
            fontWeight: "var(--font-weight-semibold)",
            fontSize: "var(--font-size-sm)",
            opacity: updatePrefs.isPending ? 0.7 : 1,
          }}
        >
          {updatePrefs.isPending ? "Saving..." : "Save Preferences"}
        </button>
      </div>
    </div>
  );
}
