import { useState } from "react";
import { Bell } from "lucide-react";
import {
  useUnreadCount,
  useNotifications,
  useMarkRead,
  useMarkAllRead,
} from "../hooks/useNotifications";

const TYPE_ICONS = {
  budget_alert: "📊",
  bill_reminder: "📋",
  low_balance: "⚠️",
  large_purchase: "💸",
  unusual_spending: "🔍",
  weekly_summary: "📅",
  monthly_summary: "📆",
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data: unreadCount = 0 } = useUnreadCount();
  const { data: notifData } = useNotifications({ limit: 20 });
  const notifications = notifData?.notifications ?? [];
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  return (
    <>
      {/* Bell button */}
      <button
        onClick={() => setOpen(true)}
        style={{
          position: "relative",
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "var(--space-2)",
          color: "var(--color-text-muted)",
          display: "flex",
          alignItems: "center",
          borderRadius: "var(--radius-sm)",
          transition: "var(--transition-fast)",
        }}
        aria-label="Notifications"
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "var(--color-bg-hover)";
          e.currentTarget.style.color = "var(--color-text-primary)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "none";
          e.currentTarget.style.color = "var(--color-text-muted)";
        }}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span
            style={{
              position: "absolute",
              top: 2,
              right: 2,
              background: "#ef4444",
              color: "white",
              borderRadius: "9999px",
              fontSize: "10px",
              fontWeight: "700",
              minWidth: 16,
              height: 16,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "0 3px",
              lineHeight: 1,
            }}
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Backdrop overlay */}
      {open && (
        <div
          onClick={() => setOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 40,
            background: "rgba(0,0,0,0.3)",
          }}
        />
      )}

      {/* Slide-in drawer */}
      <div
        style={{
          position: "fixed",
          top: 0,
          right: open ? 0 : "-400px",
          width: 380,
          height: "100vh",
          background: "var(--color-bg-card)",
          borderLeft: "1px solid var(--color-border)",
          zIndex: 50,
          transition: "right 0.25s ease",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Drawer header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "var(--space-4) var(--space-5)",
            borderBottom: "1px solid var(--color-border)",
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontSize: "var(--font-size-base)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-text-primary)",
              margin: 0,
            }}
          >
            Notifications{" "}
            {unreadCount > 0 && (
              <span
                style={{
                  color: "#ef4444",
                  fontSize: "var(--font-size-sm)",
                }}
              >
                ({unreadCount})
              </span>
            )}
          </h2>
          <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center" }}>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllRead.mutate()}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-primary)",
                  fontSize: "var(--font-size-xs)",
                  cursor: "pointer",
                  fontWeight: "var(--font-weight-medium)",
                  padding: 0,
                }}
              >
                Mark all read
              </button>
            )}
            <button
              onClick={() => setOpen(false)}
              style={{
                background: "none",
                border: "none",
                color: "var(--color-text-muted)",
                cursor: "pointer",
                fontSize: "1.2rem",
                lineHeight: 1,
                padding: 0,
                display: "flex",
                alignItems: "center",
              }}
              aria-label="Close notifications"
            >
              ×
            </button>
          </div>
        </div>

        {/* Notification list */}
        <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-2) 0" }}>
          {notifications.length === 0 ? (
            <div
              style={{
                padding: "var(--space-8)",
                textAlign: "center",
                color: "var(--color-text-muted)",
                fontSize: "var(--font-size-sm)",
              }}
            >
              No notifications yet.
            </div>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                onClick={() => !n.is_read && markRead.mutate(n.id)}
                style={{
                  display: "flex",
                  gap: "var(--space-3)",
                  padding: "var(--space-3) var(--space-5)",
                  borderBottom: "1px solid var(--color-border)",
                  background: n.is_read
                    ? "transparent"
                    : "rgba(34,183,128,0.05)",
                  cursor: n.is_read ? "default" : "pointer",
                  transition: "background 0.15s",
                  alignItems: "flex-start",
                }}
              >
                <span style={{ fontSize: "1.1rem", flexShrink: 0, marginTop: 2 }}>
                  {TYPE_ICONS[n.type] || "🔔"}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: "var(--font-size-sm)",
                      fontWeight: n.is_read
                        ? "var(--font-weight-normal)"
                        : "var(--font-weight-semibold)",
                      color: "var(--color-text-primary)",
                      marginBottom: 2,
                    }}
                  >
                    {n.title}
                  </div>
                  <div
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-muted)",
                    }}
                  >
                    {n.message}
                  </div>
                  <div
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-muted)",
                      marginTop: 4,
                    }}
                  >
                    {n.created_at
                      ? new Date(n.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : ""}
                  </div>
                </div>
                {!n.is_read && (
                  <div
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "var(--color-primary)",
                      flexShrink: 0,
                      marginTop: 6,
                    }}
                  />
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}
