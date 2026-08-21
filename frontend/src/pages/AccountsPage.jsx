import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAccounts, useDeleteAccount, useAccountSparkline } from '../hooks/useAccounts'
import PlaidLinkButton from '../components/PlaidLink'
import ReauthBanner from '../components/ReauthBanner'
import { useQueryClient } from '@tanstack/react-query'
import { AreaChart, Area, ResponsiveContainer } from 'recharts'

const ACCOUNT_TYPE_COLORS = {
  checking: { bg: 'rgba(34,183,128,0.12)', text: 'rgb(34,183,128)' },
  savings: { bg: 'rgba(59,130,246,0.12)', text: '#3b82f6' },
  credit: { bg: 'rgba(239,68,68,0.12)', text: '#ef4444' },
  investment: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b' },
  loan: { bg: 'rgba(139,92,246,0.12)', text: '#8b5cf6' },
  mortgage: { bg: 'rgba(139,92,246,0.12)', text: '#8b5cf6' },
}

const ACCOUNT_TYPE_EMOJI = {
  checking: '🏦',
  savings: '💰',
  credit: '💳',
  investment: '📈',
  loan: '📋',
  mortgage: '🏠',
  other: '💼',
}

function formatCurrency(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function timeAgo(dateStr) {
  if (!dateStr) return 'Never synced'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function SyncDot({ status }) {
  const colors = {
    ok: 'var(--color-success)',
    error: 'var(--color-error)',
    reauth_required: 'var(--color-warning)',
  }
  return (
    <span style={{
      display: 'inline-block',
      width: '8px',
      height: '8px',
      borderRadius: 'var(--radius-full)',
      background: colors[status] || 'var(--color-text-muted)',
      flexShrink: 0,
    }} />
  )
}

function AccountSparkline({ accountId }) {
  const { data } = useAccountSparkline(accountId)
  const points = data ?? []

  if (points.length === 0) {
    return <div style={{ height: 60 }} />
  }

  const isPositive = points.reduce((s, p) => s + p.amount, 0) >= 0

  return (
    <ResponsiveContainer width="100%" height={60}>
      <AreaChart data={points} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={`spark-${accountId}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={isPositive ? 'var(--color-primary)' : '#ef4444'} stopOpacity={0.3} />
            <stop offset="95%" stopColor={isPositive ? 'var(--color-primary)' : '#ef4444'} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="amount"
          stroke={isPositive ? 'var(--color-primary)' : '#ef4444'}
          strokeWidth={1.5}
          fill={`url(#spark-${accountId})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function AccountCard({ account, onDelete }) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const typeKey = account.account_type?.toLowerCase()
  const typeColor = ACCOUNT_TYPE_COLORS[typeKey] || { bg: 'rgba(255,255,255,0.08)', text: 'var(--color-text-secondary)' }
  const emoji = ACCOUNT_TYPE_EMOJI[typeKey] || ACCOUNT_TYPE_EMOJI.other
  const balance = account.balance_current ?? account.balance_available

  return (
    <div style={{
      background: 'var(--color-bg-card)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
      padding: 'var(--space-5)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-3)',
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {account.institution_logo ? (
            <img src={account.institution_logo} alt={account.institution_name} style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', objectFit: 'contain', background: '#fff', padding: '4px' }} />
          ) : (
            <div style={{ width: '36px', height: '36px', borderRadius: 'var(--radius-md)', background: 'var(--color-bg-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
              {emoji}
            </div>
          )}
          <div>
            <p style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', lineHeight: 1.3 }}>
              {account.nickname || account.name}
            </p>
            {account.institution_name && (
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                {account.institution_name}
              </p>
            )}
          </div>
        </div>
        <span style={{
          padding: 'var(--space-1) var(--space-2)',
          borderRadius: 'var(--radius-sm)',
          background: typeColor.bg,
          color: typeColor.text,
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-medium)',
          whiteSpace: 'nowrap',
          textTransform: 'capitalize',
        }}>
          {account.account_type}
        </span>
      </div>

      {/* Balance */}
      <div>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>
          {account.account_type === 'credit' ? 'Current Balance' : 'Available Balance'}
        </p>
        <p style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', lineHeight: 1 }}>
          {formatCurrency(balance)}
        </p>
      </div>

      {/* Sparkline */}
      <AccountSparkline accountId={account.id} />

      {/* Footer row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 'var(--space-2)', borderTop: '1px solid var(--color-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <SyncDot status={account.sync_status} />
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            {timeAgo(account.last_synced_at)}
          </span>
        </div>
        {confirmDelete ? (
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button onClick={() => setConfirmDelete(false)} style={{ padding: 'var(--space-1) var(--space-2)', background: 'none', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', cursor: 'pointer' }}>
              Cancel
            </button>
            <button onClick={() => onDelete(account.id)} style={{ padding: 'var(--space-1) var(--space-2)', background: 'var(--color-error)', border: 'none', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: 'var(--font-size-xs)', cursor: 'pointer' }}>
              Confirm
            </button>
          </div>
        ) : (
          <button onClick={() => setConfirmDelete(true)} style={{ padding: 'var(--space-1) var(--space-2)', background: 'none', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', cursor: 'pointer' }}>
            Remove
          </button>
        )}
      </div>
    </div>
  )
}

export default function AccountsPage() {
  const { data: accounts = [], isLoading } = useAccounts()
  const deleteAccount = useDeleteAccount()
  const queryClient = useQueryClient()

  const handleDelete = (accountId) => {
    deleteAccount.mutate(accountId)
  }

  const handleConnectSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['accounts'] })
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
      <ReauthBanner />

      {/* Header */}
      <div style={{ padding: 'var(--space-6) var(--space-6) var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}>
        <div>
          <Link to="/dashboard" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', textDecoration: 'none', display: 'block', marginBottom: 'var(--space-1)' }}>← Dashboard</Link>
          <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>Accounts</h1>
        </div>
        <PlaidLinkButton onSuccess={handleConnectSuccess}>
          + Connect Account
        </PlaidLinkButton>
      </div>

      {/* Content */}
      <div style={{ padding: 'var(--space-6)', maxWidth: '1200px', margin: '0 auto' }}>
        {isLoading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--space-4)' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} style={{ background: 'var(--color-bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)', padding: 'var(--space-5)', height: '160px', opacity: 0.5 }} />
            ))}
          </div>
        ) : accounts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-16)' }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--space-4)' }}>🏦</div>
            <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', marginBottom: 'var(--space-3)' }}>
              No accounts connected
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
              Connect your bank to start tracking transactions automatically.
            </p>
            <PlaidLinkButton onSuccess={handleConnectSuccess} />
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--space-4)' }}>
            {accounts.map((account) => (
              <AccountCard key={account.id} account={account} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
