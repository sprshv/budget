import { useCallback, useState } from 'react'
import { usePlaidLink } from 'react-plaid-link'
import api from '../api/axios'

export default function PlaidLinkButton({ onSuccess, children, style }) {
  const [linkToken, setLinkToken] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchLinkToken = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post('/api/v1/plaid/link-token')
      setLinkToken(data.link_token)
    } catch (err) {
      setError('Could not connect to bank. Please try again.')
      setLoading(false)
    }
  }

  const handleSuccess = useCallback(async (publicToken, metadata) => {
    try {
      await api.post('/api/v1/plaid/exchange-token', {
        public_token: publicToken,
        institution_id: metadata?.institution?.institution_id,
        institution_name: metadata?.institution?.name,
      })
      onSuccess?.()
    } catch (err) {
      setError('Failed to link account. Please try again.')
    }
    setLinkToken(null)
    setLoading(false)
  }, [onSuccess])

  const handleExit = useCallback(() => {
    setLinkToken(null)
    setLoading(false)
  }, [])

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: handleSuccess,
    onExit: handleExit,
  })

  // Auto-open Plaid Link when token is fetched
  if (linkToken && ready) {
    open()
  }

  const defaultStyle = {
    padding: 'var(--space-3) var(--space-6)',
    background: 'var(--color-primary)',
    color: 'var(--color-primary-foreground)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: 'var(--font-size-base)',
    fontWeight: 'var(--font-weight-semibold)',
    cursor: loading ? 'not-allowed' : 'pointer',
    transition: 'var(--transition-base)',
    ...style,
  }

  return (
    <div>
      <button
        onClick={fetchLinkToken}
        disabled={loading}
        style={defaultStyle}
      >
        {loading ? 'Connecting…' : (children || 'Connect Bank Account')}
      </button>
      {error && (
        <p style={{ marginTop: 'var(--space-2)', fontSize: 'var(--font-size-sm)', color: 'var(--color-error)' }}>
          {error}
        </p>
      )}
    </div>
  )
}
