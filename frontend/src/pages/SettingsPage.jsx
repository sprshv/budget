import { useAuth } from '../hooks/useAuth'
import { useSessions, useRevokeSession } from '../hooks/useSessions'
import { useNavigate, Link } from 'react-router-dom'
import CategorizationRulesPanel from '../components/CategorizationRulesPanel'
import CategoriesPanel from '../components/CategoriesPanel'

function formatDate(dateStr) {
  if (!dateStr) return 'Unknown'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function SettingsPage() {
  const { user, signOut } = useAuth()
  const { data: sessions = [], isLoading } = useSessions()
  const revokeSession = useRevokeSession()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const headerStyle = {
    padding: 'var(--space-4) var(--space-6)',
    borderBottom: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--space-4)',
    background: 'var(--color-bg-secondary)',
  }

  const sectionStyle = {
    background: 'var(--color-bg-card)',
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--color-border)',
    overflow: 'hidden',
    marginBottom: 'var(--space-6)',
  }

  const sectionHeaderStyle = {
    padding: 'var(--space-4) var(--space-6)',
    borderBottom: '1px solid var(--color-border)',
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
      <div style={headerStyle}>
        <Link
          to="/dashboard"
          style={{
            color: 'var(--color-text-secondary)',
            textDecoration: 'none',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          ← Dashboard
        </Link>
        <h1
          style={{
            fontSize: 'var(--font-size-xl)',
            fontWeight: 'var(--font-weight-semibold)',
            color: 'var(--color-text-primary)',
          }}
        >
          Settings
        </h1>
      </div>

      <div
        style={{
          maxWidth: '680px',
          margin: '0 auto',
          padding: 'var(--space-8) var(--space-4)',
        }}
      >
        {/* Account section */}
        <div style={sectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              Account
            </h2>
          </div>
          <div style={{ padding: 'var(--space-4) var(--space-6)' }}>
            <p
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-text-secondary)',
              }}
            >
              Signed in as{' '}
              <span
                style={{
                  color: 'var(--color-text-primary)',
                  fontWeight: 'var(--font-weight-medium)',
                }}
              >
                {user?.email}
              </span>
            </p>
          </div>
        </div>

        {/* Security section */}
        <div style={sectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              Security
            </h2>
          </div>
          <div
            style={{
              padding: 'var(--space-4) var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)',
            }}
          >
            <Link
              to="/mfa-setup"
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-primary)',
                textDecoration: 'none',
              }}
            >
              Set up Two-Factor Authentication →
            </Link>
            <Link
              to="/forgot-password"
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-primary)',
                textDecoration: 'none',
              }}
            >
              Change Password →
            </Link>
          </div>
        </div>

        {/* Active Sessions section */}
        <div style={sectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              Active Sessions
            </h2>
            <p
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                marginTop: 'var(--space-1)',
              }}
            >
              Revoke sessions on devices you don&apos;t recognize.
            </p>
          </div>

          {isLoading ? (
            <div
              style={{
                padding: 'var(--space-6)',
                color: 'var(--color-text-muted)',
                fontSize: 'var(--font-size-sm)',
              }}
            >
              Loading sessions…
            </div>
          ) : sessions.length === 0 ? (
            <div
              style={{
                padding: 'var(--space-6)',
                color: 'var(--color-text-muted)',
                fontSize: 'var(--font-size-sm)',
              }}
            >
              No active sessions found.
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                style={{
                  padding: 'var(--space-4) var(--space-6)',
                  borderBottom: '1px solid var(--color-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--space-4)',
                }}
              >
                <div>
                  <p
                    style={{
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text-primary)',
                      fontWeight: 'var(--font-weight-medium)',
                    }}
                  >
                    {session.user_agent || 'Unknown device'}
                  </p>
                  <p
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--color-text-muted)',
                      marginTop: 'var(--space-1)',
                    }}
                  >
                    Created {formatDate(session.created_at)}
                    {session.ip && ` · ${session.ip}`}
                  </p>
                </div>
                <button
                  onClick={() => revokeSession.mutate(session.id)}
                  disabled={revokeSession.isPending}
                  style={{
                    padding: 'var(--space-2) var(--space-3)',
                    background: 'var(--color-error-light)',
                    color: 'var(--color-error)',
                    border: '1px solid var(--color-error)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: 'var(--font-weight-medium)',
                    cursor: revokeSession.isPending ? 'not-allowed' : 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Revoke
                </button>
              </div>
            ))
          )}
        </div>

        {/* Notifications section */}
        <div style={sectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              Notifications
            </h2>
          </div>
          <div
            style={{
              padding: 'var(--space-4) var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)',
            }}
          >
            <Link
              to="/settings/notifications"
              style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--color-primary)',
                textDecoration: 'none',
              }}
            >
              Notification Preferences →
            </Link>
          </div>
        </div>

        {/* Categorization Rules section */}
        <div style={sectionStyle}>
          <div style={sectionHeaderStyle}>
            <h2
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              Auto-Categorization Rules
            </h2>
            <p
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                marginTop: 'var(--space-1)',
              }}
            >
              Rules are applied in priority order before Plaid categories.
            </p>
          </div>
          <div style={{ padding: 'var(--space-4) var(--space-6)' }}>
            <CategorizationRulesPanel />
          </div>
        </div>

        {/* Categories section */}
        <section
          style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-xl)',
            padding: 'var(--space-6)',
            marginTop: 'var(--space-6)',
            marginBottom: 'var(--space-6)',
          }}
        >
          <CategoriesPanel />
        </section>

        {/* Sign out */}
        <button
          onClick={handleSignOut}
          style={{
            width: '100%',
            padding: 'var(--space-3)',
            background: 'transparent',
            color: 'var(--color-error)',
            border: '1px solid var(--color-error)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-base)',
            fontWeight: 'var(--font-weight-medium)',
            cursor: 'pointer',
          }}
        >
          Sign Out
        </button>
      </div>
    </div>
  )
}
