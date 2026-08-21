import { useState, useCallback } from 'react'
import { useAccountsHealth } from '../hooks/useAccounts'
import { usePlaidLink } from 'react-plaid-link'
import { useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'

function RelinkButton({ account, onSuccess }) {
  const [linkToken, setLinkToken] = useState(null)
  const [fetching, setFetching] = useState(false)

  const handleSuccess = useCallback(() => {
    setLinkToken(null)
    onSuccess()
  }, [onSuccess])

  const handleExit = useCallback(() => {
    setLinkToken(null)
  }, [])

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: handleSuccess,
    onExit: handleExit,
  })

  const handleClick = async () => {
    setFetching(true)
    try {
      const { data } = await api.post('/api/v1/plaid/link-token')
      setLinkToken(data.link_token)
    } catch (err) {
      console.error('Failed to get link token for reauth', err)
    } finally {
      setFetching(false)
    }
  }

  // Auto-open once token arrives and Plaid SDK is ready
  if (linkToken && ready) {
    open()
  }

  return (
    <button
      onClick={handleClick}
      disabled={fetching}
      style={{
        padding: 'var(--space-2) var(--space-3)',
        background: 'var(--color-warning)',
        color: '#000',
        border: 'none',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-xs)',
        fontWeight: 'var(--font-weight-semibold)',
        cursor: fetching ? 'not-allowed' : 'pointer',
      }}
    >
      {fetching ? 'Connecting…' : `Reconnect ${account.institution_name || account.name}`}
    </button>
  )
}

export default function ReauthBanner() {
  const { data: accounts = [] } = useAccountsHealth()
  const [dismissed, setDismissed] = useState(false)
  const queryClient = useQueryClient()

  if (dismissed || accounts.length === 0) return null

  const handleSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['accounts-health'] })
    queryClient.invalidateQueries({ queryKey: ['accounts'] })
  }

  return (
    <div style={{
      background: 'var(--color-warning-light)',
      border: '1px solid var(--color-warning)',
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-4) var(--space-6)',
      margin: 'var(--space-4)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: 'var(--space-4)',
    }}>
      <span style={{ fontSize: '20px' }}>⚠️</span>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-warning)', marginBottom: 'var(--space-1)' }}>
          {accounts.length === 1
            ? `${accounts[0].institution_name || accounts[0].name} needs to be reconnected`
            : `${accounts.length} accounts need to be reconnected`}
        </p>
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
          Your bank connection expired. Re-link to keep your transactions up to date.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          {accounts.map((account) => (
            <RelinkButton key={account.id} account={account} onSuccess={handleSuccess} />
          ))}
        </div>
      </div>
      <button
        onClick={() => setDismissed(true)}
        style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 'var(--font-size-lg)', lineHeight: 1 }}
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}
