import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMfa } from '../hooks/useMfa'
import { supabase } from '../lib/supabase'

/**
 * MfaVerifyPage — shown during login when the user has a TOTP factor enrolled
 * and the session is still at AAL1.
 *
 * Flow:
 *   1. User has already authenticated with email/password (AAL1 session exists).
 *   2. Supabase redirects (or the app navigates) here because a TOTP factor
 *      is enrolled and the requested resource requires AAL2.
 *   3. User enters 6-digit code → session upgraded to AAL2 → redirect to /dashboard.
 *
 * All colours and spacing use tokens.css variables only.
 */
export default function MfaVerifyPage() {
  const navigate = useNavigate()
  const { verifyTotp, loading, error } = useMfa()
  const [code, setCode] = useState('')
  const [verifyError, setVerifyError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setVerifyError(null)

    // Discover the enrolled TOTP factor for the current user
    const { data: factorsData } = await supabase.auth.mfa.listFactors()
    const totpFactor = factorsData?.totp?.[0]

    // If no factor is enrolled, the user doesn't need to verify — go straight to dashboard
    if (!totpFactor) {
      navigate('/dashboard', { replace: true })
      return
    }

    const result = await verifyTotp(totpFactor.id, code)
    if (result) {
      navigate('/dashboard', { replace: true })
    } else {
      setVerifyError('Invalid code. Please try again.')
    }
  }

  const errorBoxStyle = {
    padding: 'var(--space-3)',
    borderRadius: 'var(--radius-md)',
    background: 'var(--color-error-light)',
    border: '1px solid var(--color-error)',
    color: 'var(--color-error)',
    fontSize: 'var(--font-size-sm)',
  }

  const isDisabled = loading || code.length !== 6

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-bg)',
        padding: 'var(--space-4)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          background: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--color-border)',
          padding: 'var(--space-8)',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
          <div style={{ fontSize: '40px', marginBottom: 'var(--space-3)' }}>
            &#128274;
          </div>
          <h1
            style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 'var(--font-weight-bold)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-2)',
            }}
          >
            Two-Factor Authentication
          </h1>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            Enter the 6-digit code from your authenticator app.
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
        >
          {(verifyError || error) && (
            <div style={errorBoxStyle}>{verifyError ?? error}</div>
          )}

          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
            placeholder="000000"
            required
            autoFocus
            style={{
              width: '100%',
              padding: 'var(--space-4)',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-3xl)',
              fontWeight: 'var(--font-weight-bold)',
              outline: 'none',
              textAlign: 'center',
              letterSpacing: '0.3em',
              boxSizing: 'border-box',
            }}
          />

          <button
            type="submit"
            disabled={isDisabled}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              background: isDisabled
                ? 'var(--color-bg-elevated)'
                : 'var(--color-primary)',
              color: isDisabled
                ? 'var(--color-text-muted)'
                : 'var(--color-primary-foreground)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: isDisabled ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Verifying…' : 'Verify'}
          </button>
        </form>
      </div>
    </div>
  )
}
