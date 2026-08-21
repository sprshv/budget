import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  CreditCard,
  ArrowLeftRight,
  PieChart,
  Target,
  Receipt,
  Repeat,
  BarChart2,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import useUserStore from "../store/useUserStore";
import NotificationBell from "./NotificationBell";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
  { label: "Accounts", icon: CreditCard, path: "/accounts" },
  { label: "Transactions", icon: ArrowLeftRight, path: "/transactions" },
  { label: "Budgets", icon: PieChart, path: "/budgets" },
  { label: "Goals", icon: Target, path: "/goals" },
  { label: "Bills", icon: Receipt, path: "/bills" },
  { label: "Subscriptions", icon: Repeat, path: "/subscriptions" },
  { label: "Analytics", icon: BarChart2, path: "/analytics" },
  { label: "Settings", icon: Settings, path: "/settings" },
];

function NavItem({ item, collapsed, active, onClick }) {
  const Icon = item.icon;
  return (
    <Link
      to={item.path}
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: collapsed ? 0 : "var(--space-3)",
        padding: collapsed ? "var(--space-3)" : "var(--space-3) var(--space-4)",
        borderRadius: "var(--radius-md)",
        borderLeft: active
          ? "3px solid var(--color-primary)"
          : "3px solid transparent",
        background: active ? "var(--color-primary-light)" : "transparent",
        color: active ? "var(--color-primary)" : "var(--color-text-secondary)",
        textDecoration: "none",
        fontSize: "var(--font-size-sm)",
        fontWeight: active
          ? "var(--font-weight-semibold)"
          : "var(--font-weight-normal)",
        transition: "var(--transition-base)",
        justifyContent: collapsed ? "center" : "flex-start",
        whiteSpace: "nowrap",
        overflow: "hidden",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.background = "var(--color-bg-hover)";
          e.currentTarget.style.color = "var(--color-text-primary)";
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.background = "transparent";
          e.currentTarget.style.color = "var(--color-text-secondary)";
        }
      }}
      title={collapsed ? item.label : undefined}
    >
      <Icon size={18} style={{ flexShrink: 0 }} />
      {!collapsed && (
        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          {item.label}
        </span>
      )}
    </Link>
  );
}

function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const location = useLocation();
  const user = useUserStore((s) => s.user);
  const sidebarWidth = collapsed ? 64 : 240;

  const sidebarContent = (
    <nav
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: sidebarWidth,
        background: "var(--color-bg-secondary)",
        borderRight: "1px solid var(--color-border)",
        transition: "width var(--transition-base)",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      {/* Logo area */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed
            ? "var(--space-4) var(--space-3)"
            : "var(--space-4) var(--space-4)",
          borderBottom: "1px solid var(--color-border)",
          height: 60,
          flexShrink: 0,
        }}
      >
        {!collapsed && (
          <span
            style={{
              fontSize: "var(--font-size-xl)",
              fontWeight: "var(--font-weight-bold)",
              color: "var(--color-primary)",
              letterSpacing: "-0.5px",
            }}
          >
            Budgtr
          </span>
        )}
        <button
          onClick={onToggle}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--color-text-secondary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "var(--space-1)",
            borderRadius: "var(--radius-sm)",
            transition: "var(--transition-fast)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--color-bg-hover)";
            e.currentTarget.style.color = "var(--color-text-primary)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "none";
            e.currentTarget.style.color = "var(--color-text-secondary)";
          }}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav items */}
      <div
        style={{
          flex: 1,
          padding: "var(--space-3) var(--space-2)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-1)",
          overflowY: "auto",
        }}
      >
        {NAV_ITEMS.map((item) => (
          <NavItem
            key={item.path}
            item={item}
            collapsed={collapsed}
            active={
              item.path === "/dashboard"
                ? location.pathname === "/dashboard" ||
                  location.pathname === "/"
                : location.pathname.startsWith(item.path)
            }
            onClick={onMobileClose}
          />
        ))}
      </div>

      {/* User info at bottom */}
      <div
        style={{
          borderTop: "1px solid var(--color-border)",
          padding: collapsed ? "var(--space-3)" : "var(--space-3) var(--space-4)",
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          justifyContent: collapsed ? "center" : "flex-start",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "var(--radius-full)",
            background: "var(--color-primary-light)",
            border: "1px solid var(--color-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--color-primary)",
            fontSize: "var(--font-size-sm)",
            fontWeight: "var(--font-weight-semibold)",
            flexShrink: 0,
          }}
        >
          {user?.email?.[0]?.toUpperCase() || "U"}
        </div>
        {!collapsed && (
          <span
            style={{
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-secondary)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {user?.email || "Account"}
          </span>
        )}
      </div>
    </nav>
  );

  return sidebarContent;
}

export default function AppShell({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        overflow: "hidden",
        background: "var(--color-bg)",
      }}
    >
      {/* Desktop sidebar */}
      <div
        style={{
          display: "flex",
          flexShrink: 0,
        }}
        className="desktop-sidebar"
      >
        <style>{`
          @media (max-width: 767px) {
            .desktop-sidebar { display: none !important; }
            .mobile-hamburger { display: flex !important; }
          }
          @media (min-width: 768px) {
            .mobile-hamburger { display: none !important; }
            .mobile-overlay { display: none !important; }
          }
        `}</style>
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((c) => !c)}
          mobileOpen={false}
          onMobileClose={() => {}}
        />
      </div>

      {/* Mobile hamburger button */}
      <button
        className="mobile-hamburger"
        onClick={() => setMobileOpen(true)}
        style={{
          display: "none",
          position: "fixed",
          top: "var(--space-4)",
          left: "var(--space-4)",
          zIndex: "var(--z-sticky)",
          background: "var(--color-bg-secondary)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          padding: "var(--space-2)",
          cursor: "pointer",
          color: "var(--color-text-primary)",
          alignItems: "center",
          justifyContent: "center",
        }}
        aria-label="Open navigation"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="mobile-overlay" style={{ display: "flex" }}>
          {/* Backdrop */}
          <div
            onClick={() => setMobileOpen(false)}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0, 0, 0, 0.6)",
              zIndex: "var(--z-overlay)",
              backdropFilter: "blur(2px)",
            }}
          />
          {/* Sidebar panel */}
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              bottom: 0,
              zIndex: "var(--z-modal)",
              display: "flex",
            }}
          >
            <Sidebar
              collapsed={false}
              onToggle={() => {}}
              mobileOpen={mobileOpen}
              onMobileClose={() => setMobileOpen(false)}
            />
            <button
              onClick={() => setMobileOpen(false)}
              style={{
                position: "absolute",
                top: "var(--space-4)",
                right: "calc(-1 * var(--space-10))",
                background: "var(--color-bg-secondary)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-full)",
                padding: "var(--space-2)",
                cursor: "pointer",
                color: "var(--color-text-primary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
              aria-label="Close navigation"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Main content */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          background: "var(--color-bg)",
        }}
      >
        {/* Top header bar with notification bell */}
        <div
          style={{
            height: 52,
            borderBottom: "1px solid var(--color-border)",
            background: "var(--color-bg-secondary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            padding: "0 var(--space-4)",
            flexShrink: 0,
          }}
        >
          <NotificationBell />
        </div>
        {/* Page content */}
        <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden" }}>
          {children}
        </div>
      </main>
    </div>
  );
}
