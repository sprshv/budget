import { useState } from "react";
import {
  useGoals,
  useCreateGoal,
  useDeleteGoal,
  useContributeToGoal,
  useGoalForecast,
  useGoalContributions,
} from "../hooks/useGoals";

const GOAL_TYPE_COLORS = {
  savings: { bg: "rgba(34,183,128,0.12)", text: "rgb(34,183,128)" },
  debt_payoff: { bg: "rgba(239,68,68,0.12)", text: "#ef4444" },
  emergency_fund: { bg: "rgba(59,130,246,0.12)", text: "#3b82f6" },
  custom: { bg: "rgba(245,158,11,0.12)", text: "#f59e0b" },
};

const GOAL_TYPE_LABELS = {
  savings: "Savings",
  debt_payoff: "Debt Payoff",
  emergency_fund: "Emergency Fund",
  custom: "Custom",
};

const GOAL_TYPE_OPTIONS = [
  { value: "savings", label: "Savings" },
  { value: "debt_payoff", label: "Debt Payoff" },
  { value: "emergency_fund", label: "Emergency Fund" },
  { value: "custom", label: "Custom" },
];

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

function formatDate(dateStr) {
  if (!dateStr) return null;
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/* ─── Modal backdrop ─── */
function Modal({ onClose, children }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.55)",
        backdropFilter: "blur(3px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--space-4)",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--color-bg-secondary)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-6)",
          width: "100%",
          maxWidth: 480,
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        {children}
      </div>
    </div>
  );
}

/* ─── Input helper ─── */
function Field({ label, children }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
      <label
        style={{
          fontSize: "var(--font-size-sm)",
          fontWeight: "var(--font-weight-medium)",
          color: "var(--color-text-secondary)",
        }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "var(--space-2) var(--space-3)",
  background: "var(--color-bg)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-md)",
  color: "var(--color-text-primary)",
  fontSize: "var(--font-size-sm)",
  outline: "none",
  boxSizing: "border-box",
};

/* ─── New Goal Modal ─── */
function NewGoalModal({ onClose }) {
  const createGoal = useCreateGoal();
  const [form, setForm] = useState({
    name: "",
    goal_type: "savings",
    target_amount: "",
    target_date: "",
    icon: "",
    color: "",
  });
  const [error, setError] = useState("");

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!form.name.trim()) return setError("Name is required.");
    const target = parseFloat(form.target_amount);
    if (!target || target <= 0) return setError("Target amount must be positive.");

    const payload = {
      name: form.name.trim(),
      goal_type: form.goal_type,
      target_amount: target,
      ...(form.target_date ? { target_date: form.target_date } : {}),
      ...(form.icon ? { icon: form.icon.trim() } : {}),
      ...(form.color ? { color: form.color } : {}),
    };

    try {
      await createGoal.mutateAsync(payload);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to create goal.");
    }
  }

  return (
    <Modal onClose={onClose}>
      <h2
        style={{
          margin: "0 0 var(--space-5)",
          fontSize: "var(--font-size-lg)",
          fontWeight: "var(--font-weight-semibold)",
          color: "var(--color-text-primary)",
        }}
      >
        New Goal
      </h2>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}
      >
        <Field label="Goal Name">
          <input
            style={inputStyle}
            placeholder="e.g. Vacation Fund"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            required
          />
        </Field>

        <Field label="Type">
          <select
            style={inputStyle}
            value={form.goal_type}
            onChange={(e) => set("goal_type", e.target.value)}
          >
            {GOAL_TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Target Amount ($)">
          <input
            style={inputStyle}
            type="number"
            min="0.01"
            step="0.01"
            placeholder="5000.00"
            value={form.target_amount}
            onChange={(e) => set("target_amount", e.target.value)}
            required
          />
        </Field>

        <Field label="Target Date (optional)">
          <input
            style={inputStyle}
            type="date"
            value={form.target_date}
            onChange={(e) => set("target_date", e.target.value)}
          />
        </Field>

        <Field label="Icon (emoji, optional)">
          <input
            style={inputStyle}
            placeholder="✈️"
            value={form.icon}
            onChange={(e) => set("icon", e.target.value)}
            maxLength={4}
          />
        </Field>

        {error && (
          <p
            style={{
              margin: 0,
              color: "#ef4444",
              fontSize: "var(--font-size-sm)",
            }}
          >
            {error}
          </p>
        )}

        <div style={{ display: "flex", gap: "var(--space-3)", justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: "var(--space-2) var(--space-4)",
              background: "transparent",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              color: "var(--color-text-secondary)",
              cursor: "pointer",
              fontSize: "var(--font-size-sm)",
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createGoal.isPending}
            style={{
              padding: "var(--space-2) var(--space-4)",
              background: "var(--color-primary)",
              border: "none",
              borderRadius: "var(--radius-md)",
              color: "#fff",
              cursor: createGoal.isPending ? "not-allowed" : "pointer",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              opacity: createGoal.isPending ? 0.7 : 1,
            }}
          >
            {createGoal.isPending ? "Creating…" : "Create Goal"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/* ─── Add Funds Modal ─── */
function AddFundsModal({ goal, onClose }) {
  const contribute = useContributeToGoal();
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) return setError("Amount must be positive.");

    try {
      await contribute.mutateAsync({ goalId: goal.id, amount: amt, note: note.trim() || undefined });
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to add funds.");
    }
  }

  const remaining = Math.max(goal.target_amount - goal.current_amount, 0);

  return (
    <Modal onClose={onClose}>
      <h2
        style={{
          margin: "0 0 var(--space-2)",
          fontSize: "var(--font-size-lg)",
          fontWeight: "var(--font-weight-semibold)",
          color: "var(--color-text-primary)",
        }}
      >
        Add Funds
      </h2>
      <p
        style={{
          margin: "0 0 var(--space-5)",
          fontSize: "var(--font-size-sm)",
          color: "var(--color-text-secondary)",
        }}
      >
        {goal.icon && <span style={{ marginRight: 6 }}>{goal.icon}</span>}
        {goal.name} — {formatCurrency(remaining)} remaining
      </p>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}
      >
        <Field label="Amount ($)">
          <input
            style={inputStyle}
            type="number"
            min="0.01"
            step="0.01"
            placeholder="100.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            autoFocus
            required
          />
        </Field>
        <Field label="Note (optional)">
          <input
            style={inputStyle}
            placeholder="Monthly contribution"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </Field>

        {error && (
          <p style={{ margin: 0, color: "#ef4444", fontSize: "var(--font-size-sm)" }}>
            {error}
          </p>
        )}

        <div style={{ display: "flex", gap: "var(--space-3)", justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: "var(--space-2) var(--space-4)",
              background: "transparent",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              color: "var(--color-text-secondary)",
              cursor: "pointer",
              fontSize: "var(--font-size-sm)",
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={contribute.isPending}
            style={{
              padding: "var(--space-2) var(--space-4)",
              background: "var(--color-primary)",
              border: "none",
              borderRadius: "var(--radius-md)",
              color: "#fff",
              cursor: contribute.isPending ? "not-allowed" : "pointer",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              opacity: contribute.isPending ? 0.7 : 1,
            }}
          >
            {contribute.isPending ? "Adding…" : "Add Funds"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/* ─── Goal Contributions List ─── */
function GoalContributionsList({ goalId, visible }) {
  const { data: contributions = [], isLoading } = useGoalContributions(visible ? goalId : null);

  if (!visible) return null;

  if (isLoading) {
    return (
      <div
        style={{
          padding: "var(--space-3)",
          color: "var(--color-text-muted, #6b7280)",
          fontSize: "var(--font-size-sm)",
        }}
      >
        Loading...
      </div>
    );
  }

  if (contributions.length === 0) {
    return (
      <div
        style={{
          padding: "var(--space-3)",
          color: "var(--color-text-muted, #6b7280)",
          fontSize: "var(--font-size-sm)",
        }}
      >
        No contributions yet.
      </div>
    );
  }

  return (
    <div
      style={{
        borderTop: "1px solid var(--color-border)",
        marginTop: "var(--space-2)",
        paddingTop: "var(--space-2)",
      }}
    >
      {contributions.map((c) => (
        <div
          key={c.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "var(--space-1) 0",
            fontSize: "var(--font-size-sm)",
          }}
        >
          <span style={{ color: "var(--color-text-muted, #6b7280)" }}>{c.contributed_at}</span>
          {c.note && (
            <span
              style={{
                color: "var(--color-text-secondary)",
                flex: 1,
                marginLeft: "var(--space-2)",
              }}
            >
              {c.note}
            </span>
          )}
          <span style={{ color: "var(--color-primary)", fontWeight: 600 }}>
            +{formatCurrency(c.amount)}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ─── Goal Card ─── */
function GoalCard({ goal, onAddFunds }) {
  const deleteGoal = useDeleteGoal();
  const typeColor = GOAL_TYPE_COLORS[goal.goal_type] || GOAL_TYPE_COLORS.custom;
  const { data: forecast } = useGoalForecast(goal.is_complete ? null : goal.id);
  const [showHistory, setShowHistory] = useState(false);

  // Days remaining calculated from target_date
  const daysRemaining =
    goal.target_date && !goal.is_complete
      ? Math.max(
          0,
          Math.ceil(
            (new Date(goal.target_date + "T00:00:00") - new Date()) /
              (1000 * 60 * 60 * 24)
          )
        )
      : null;

  async function handleDelete() {
    if (!window.confirm(`Delete "${goal.name}"? This cannot be undone.`)) return;
    await deleteGoal.mutateAsync(goal.id);
  }

  return (
    <div
      style={{
        background: "var(--color-bg-secondary)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4)",
        position: "relative",
        opacity: goal.is_complete ? 0.85 : 1,
      }}
    >
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: "var(--space-3)" }}>
        {goal.icon && (
          <span style={{ fontSize: 28, lineHeight: 1, flexShrink: 0 }}>{goal.icon}</span>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
            <h3
              style={{
                margin: 0,
                fontSize: "var(--font-size-base)",
                fontWeight: "var(--font-weight-semibold)",
                color: "var(--color-text-primary)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {goal.name}
            </h3>
            {goal.is_complete && (
              <span
                style={{
                  fontSize: 14,
                  color: "rgb(34,183,128)",
                  flexShrink: 0,
                }}
                title="Completed"
              >
                ✓
              </span>
            )}
          </div>
          <span
            style={{
              display: "inline-block",
              marginTop: "var(--space-1)",
              padding: "2px var(--space-2)",
              background: typeColor.bg,
              color: typeColor.text,
              borderRadius: "var(--radius-full)",
              fontSize: "var(--font-size-xs)",
              fontWeight: "var(--font-weight-medium)",
            }}
          >
            {GOAL_TYPE_LABELS[goal.goal_type] || goal.goal_type}
          </span>
        </div>

        {/* Delete button */}
        <button
          onClick={handleDelete}
          disabled={deleteGoal.isPending}
          style={{
            background: "none",
            border: "none",
            color: "var(--color-text-secondary)",
            cursor: "pointer",
            fontSize: 16,
            padding: "var(--space-1)",
            flexShrink: 0,
            opacity: deleteGoal.isPending ? 0.5 : 1,
          }}
          title="Delete goal"
          aria-label="Delete goal"
        >
          ×
        </button>
      </div>

      {/* Progress bar */}
      <div>
        <div
          style={{
            height: 8,
            background: "var(--color-border)",
            borderRadius: "var(--radius-full)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${goal.percentage}%`,
              background: goal.is_complete
                ? "rgb(34,183,128)"
                : typeColor.text,
              borderRadius: "var(--radius-full)",
              transition: "width 0.4s ease",
            }}
          />
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: "var(--space-1)",
          }}
        >
          <span
            style={{
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-primary)",
              fontWeight: "var(--font-weight-medium)",
            }}
          >
            {formatCurrency(goal.current_amount)}
          </span>
          <span
            style={{
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-secondary)",
            }}
          >
            {goal.percentage}% of {formatCurrency(goal.target_amount)}
          </span>
        </div>
      </div>

      {/* Days remaining + forecast chip row */}
      {(!goal.is_complete) && (daysRemaining !== null || forecast?.monthly_rate) && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "var(--space-2)",
          }}
        >
          {daysRemaining !== null && (
            <span
              style={{
                fontSize: "var(--font-size-xs)",
                color: "var(--color-text-secondary)",
              }}
            >
              {daysRemaining === 0 ? "Due today" : `${daysRemaining} days left`}
            </span>
          )}
          {forecast?.monthly_rate != null && (
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <span
                style={{
                  fontSize: "var(--font-size-xs)",
                  color: "var(--color-text-secondary)",
                }}
              >
                ~{formatCurrency(forecast.monthly_rate)}/mo to complete
              </span>
              {forecast.on_track === true && (
                <span
                  style={{
                    padding: "1px var(--space-2)",
                    background: "rgba(34,183,128,0.12)",
                    color: "rgb(34,183,128)",
                    borderRadius: "var(--radius-full)",
                    fontSize: "var(--font-size-xs)",
                    fontWeight: "var(--font-weight-medium)",
                  }}
                >
                  On Track
                </span>
              )}
              {forecast.on_track === false && (
                <span
                  style={{
                    padding: "1px var(--space-2)",
                    background: "rgba(245,158,11,0.12)",
                    color: "#f59e0b",
                    borderRadius: "var(--radius-full)",
                    fontSize: "var(--font-size-xs)",
                    fontWeight: "var(--font-weight-medium)",
                  }}
                >
                  Behind
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Target date */}
      {goal.target_date && (
        <p
          style={{
            margin: 0,
            fontSize: "var(--font-size-xs)",
            color: "var(--color-text-secondary)",
          }}
        >
          Target date: {formatDate(goal.target_date)}
        </p>
      )}

      {/* Add Funds + History buttons */}
      <div style={{ display: "flex", gap: "var(--space-2)" }}>
        {!goal.is_complete && (
          <button
            onClick={() => onAddFunds(goal)}
            style={{
              flex: 1,
              padding: "var(--space-2) var(--space-3)",
              background: "var(--color-primary-light)",
              border: "1px solid var(--color-primary)",
              borderRadius: "var(--radius-md)",
              color: "var(--color-primary)",
              cursor: "pointer",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              transition: "var(--transition-fast)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--color-primary)";
              e.currentTarget.style.color = "#fff";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--color-primary-light)";
              e.currentTarget.style.color = "var(--color-primary)";
            }}
          >
            Add Funds
          </button>
        )}

        {goal.is_complete && (
          <div
            style={{
              flex: 1,
              textAlign: "center",
              fontSize: "var(--font-size-sm)",
              color: "rgb(34,183,128)",
              fontWeight: "var(--font-weight-medium)",
              padding: "var(--space-2) 0",
            }}
          >
            Goal Completed!
          </div>
        )}

        <button
          onClick={() => setShowHistory((v) => !v)}
          style={{
            padding: "var(--space-2) var(--space-3)",
            background: showHistory ? "var(--color-border)" : "transparent",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            color: "var(--color-text-secondary)",
            cursor: "pointer",
            fontSize: "var(--font-size-sm)",
            fontWeight: "var(--font-weight-medium)",
            transition: "var(--transition-fast)",
            whiteSpace: "nowrap",
          }}
        >
          {showHistory ? "Hide History" : "History"}
        </button>
      </div>

      {/* Contributions history */}
      <GoalContributionsList goalId={goal.id} visible={showHistory} />
    </div>
  );
}

/* ─── Main Page ─── */
export default function GoalsPage() {
  const { data: goals, isLoading, isError } = useGoals();
  const [showNewGoal, setShowNewGoal] = useState(false);
  const [contributeGoal, setContributeGoal] = useState(null);

  const activeGoals = goals ? goals.filter((g) => !g.is_complete) : [];
  const completedGoals = goals ? goals.filter((g) => g.is_complete) : [];

  return (
    <div
      style={{
        padding: "var(--space-6) var(--space-6)",
        maxWidth: 1100,
        margin: "0 auto",
      }}
    >
      {/* Page header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--space-6)",
          flexWrap: "wrap",
          gap: "var(--space-3)",
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "var(--font-size-2xl)",
              fontWeight: "var(--font-weight-bold)",
              color: "var(--color-text-primary)",
            }}
          >
            Goals
          </h1>
          <p
            style={{
              margin: "var(--space-1) 0 0",
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-secondary)",
            }}
          >
            Track your savings milestones
          </p>
        </div>
        <button
          onClick={() => setShowNewGoal(true)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "var(--space-2) var(--space-4)",
            background: "var(--color-primary)",
            border: "none",
            borderRadius: "var(--radius-md)",
            color: "#fff",
            cursor: "pointer",
            fontSize: "var(--font-size-sm)",
            fontWeight: "var(--font-weight-medium)",
          }}
        >
          + New Goal
        </button>
      </div>

      {/* Loading / error states */}
      {isLoading && (
        <p style={{ color: "var(--color-text-secondary)", fontSize: "var(--font-size-sm)" }}>
          Loading goals…
        </p>
      )}
      {isError && (
        <p style={{ color: "#ef4444", fontSize: "var(--font-size-sm)" }}>
          Failed to load goals. Please try again.
        </p>
      )}

      {/* Empty state */}
      {!isLoading && !isError && goals && goals.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "var(--space-12) var(--space-6)",
            color: "var(--color-text-secondary)",
          }}
        >
          <div style={{ fontSize: 48, marginBottom: "var(--space-4)" }}>🎯</div>
          <h2
            style={{
              margin: "0 0 var(--space-2)",
              fontSize: "var(--font-size-lg)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-text-primary)",
            }}
          >
            No goals yet
          </h2>
          <p style={{ margin: "0 0 var(--space-5)", fontSize: "var(--font-size-sm)" }}>
            Set your first financial goal and start tracking your progress.
          </p>
          <button
            onClick={() => setShowNewGoal(true)}
            style={{
              padding: "var(--space-2) var(--space-5)",
              background: "var(--color-primary)",
              border: "none",
              borderRadius: "var(--radius-md)",
              color: "#fff",
              cursor: "pointer",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
            }}
          >
            Create Goal
          </button>
        </div>
      )}

      {/* Active goals grid */}
      {activeGoals.length > 0 && (
        <section style={{ marginBottom: "var(--space-8)" }}>
          <h2
            style={{
              margin: "0 0 var(--space-4)",
              fontSize: "var(--font-size-xs)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Active ({activeGoals.length})
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: "var(--space-4)",
            }}
          >
            {activeGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onAddFunds={setContributeGoal}
              />
            ))}
          </div>
        </section>
      )}

      {/* Completed goals grid */}
      {completedGoals.length > 0 && (
        <section>
          <h2
            style={{
              margin: "0 0 var(--space-4)",
              fontSize: "var(--font-size-xs)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Completed ({completedGoals.length})
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: "var(--space-4)",
            }}
          >
            {completedGoals.map((goal) => (
              <GoalCard
                key={goal.id}
                goal={goal}
                onAddFunds={setContributeGoal}
              />
            ))}
          </div>
        </section>
      )}

      {/* Modals */}
      {showNewGoal && <NewGoalModal onClose={() => setShowNewGoal(false)} />}
      {contributeGoal && (
        <AddFundsModal
          goal={contributeGoal}
          onClose={() => setContributeGoal(null)}
        />
      )}
    </div>
  );
}
