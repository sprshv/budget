import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useMfa } from '../hooks/useMfa'

/**
 * MfaSetupPage — three-step flow:
 *   1. loading  — call Supabase enroll, show spinner
 *   2. scan     — display QR code + manual entry option
 *   3. verify   — enter 6-digit code to confirm setup
 *   4. done     — success state with link to dashboard
 *
 * All colours and spacing use tokens.css variables only.
 */
export default function MfaSetupPage() {
  const { enrollTotp, verifyTotp, loading, error } = useMfa()
  const [factorData, setFactorData] = useState(null)
  const [code, setCode] = useState('')
  const [step, setStep] = useState('loading')
  const [verifyError, setVerifyError] = useState(null)

  // Kick off enrollment as soon as the page mounts
  useEffect(() => {
    enrollTotp().then((data) => {
      if (data) {
        setFactorData(data)
        setStep('scan')
      } else {
        setStep('error')
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleVerify = async (e) => {
    e.preventDefault()
    setVerifyError(null)
    const result = await verifyTotp(factorData.id, code)
    if (result) {
      setStep('done')
    } else {
      setVerifyError('Invalid code. Please try again.')
    }
  }

  const containerStyle = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--color-bg)',
    padding: 'var(--space-4)',
  }

  const cardStyle = {
    width: '100%',
    maxWidth: '440px',
    background: 'var(--color-bg-card)',
    borderRadius: 'var(--radius-xl)',
    border: '1px solid var(--color-border)',
    padding: 'var(--space-8)',
  }

  const headingStyle = {
    fontSize: 'var(--font-size-2xl)',
    fontWeight: 'var(--font-weight-bold)',
    color: 'var(--color-text-primary)',
    marginBottom: 'var(--space-2)',
  }

  const subtitleStyle = {
    color: 'var(--color-text-secondary)',
    fontSize: 'var(--font-size-sm)',
    marginBottom: 'var(--space-6)',
  }

  const primaryButtonStyle = {
    width: '100%',
    padding: 'var(--space-3)',
    background: 'var(--color-primary)',
    color: 'var(--color-primary-foreground)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    fontSize: 'var(--font-size-base)',
    fontWeight: 'var(--font-weight-semibold)',
    cursor: 'pointer',
  }

  const disabledButtonStyle = {
    ...primaryButtonStyle,
    background: 'var(--color-bg-elevated)',
    color: 'var(--color-text-muted)',
    cursor: 'not-allowed',
  }

  const errorBoxStyle = {
    padding: 'var(--space-3)',
    borderRadius: 'var(--radius-md)',
    background: 'var(--color-error-light)',
    border: '1px solid var(--color-error)',
    color: 'var(--color-error)',
    fontSize: 'var(--font-size-sm)',
  }

  // ── Loading ──────────────────────────────────────────────────────────────
  if (step === 'loading') {
    return (
      <div style={containerStyle}>
        <div style={{ ...cardStyle, textAlign: 'center' }}>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Setting up 2FA&hellip;
          </p>
        </div>
      </div>
    )
  }

  // ── Error (enrollment failed) ────────────────────────────────────────────
  if (step === 'error') {
    return (
      <div style={containerStyle}>
        <div style={{ ...cardStyle, textAlign: 'center' }}>
          <div style={errorBoxStyle}>
            {error ?? 'Failed to start 2FA setup. Please try again.'}
          </div>
          <button
            onClick={() => { setStep('loading'); enrollTotp().then((d) => { if (d) { setFactorData(d); setStep('scan') } }) }}
            style={{ ...primaryButtonStyle, marginTop: 'var(--space-4)' }}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // ── Done ─────────────────────────────────────────────────────────────────
  if (step === 'done') {
    return (
      <div style={containerStyle}>
        <div style={{ ...cardStyle, textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: 'var(--space-4)' }}>
            &#128274;
          </div>
          <h1 style={headingStyle}>2FA Enabled</h1>
          <p style={{ ...subtitleStyle, marginBottom: 'var(--space-6)' }}>
            Your account is now protected with two-factor authentication.
          </p>
          <Link
            to="/dashboard"
            style={{
              display: 'inline-block',
              padding: 'var(--space-3) var(--space-6)',
              background: 'var(--color-primary)',
              color: 'var(--color-primary-foreground)',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              fontWeight: 'var(--font-weight-semibold)',
              fontSize: 'var(--font-size-base)',
            }}
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  // ── Scan + Verify ─────────────────────────────────────────────────────────
  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h1 style={headingStyle}>Set up Two-Factor Auth</h1>

        {/* ── Step: scan QR ── */}
        {step === 'scan' && (
          <>
            <p style={subtitleStyle}>
              Scan the QR code below with your authenticator app (Google
              Authenticator, Authy, 1Password, etc.)
            </p>

            {/* QR code — Supabase returns an SVG string */}
            {factorData?.totp?.qr_code ? (
              <div
                style={{
                  background: 'white',
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-6)',
                  display: 'flex',
                  justifyContent: 'center',
                }}
                /* Supabase returns a trusted SVG; dangerouslySetInnerHTML is
                   intentional here — this content never comes from user input. */
                dangerouslySetInnerHTML={{ __html: factorData.totp.qr_code }}
              />
            ) : null}

            {/* Manual entry fallback */}
            {(factorData?.totp?.secret || factorData?.totp?.uri) && (
              <details style={{ marginBottom: 'var(--space-6)' }}>
                <summary
                  style={{
                    color: 'var(--color-text-muted)',
                    fontSize: 'var(--font-size-xs)',
                    cursor: 'pointer',
                  }}
                >
                  Can&apos;t scan? Enter code manually
                </summary>
                <code
                  style={{
                    display: 'block',
                    marginTop: 'var(--space-2)',
                    padding: 'var(--space-3)',
                    background: 'var(--color-bg-elevated)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--color-text-secondary)',
                    wordBreak: 'break-all',
                  }}
                >
                  {factorData.totp.secret ?? factorData.totp.uri}
                </code>
              </details>
            )}

            <button
              onClick={() => setStep('verify')}
              style={primaryButtonStyle}
            >
              I&apos;ve Scanned It &mdash; Continue
            </button>
          </>
        )}

        {/* ── Step: verify code ── */}
        {step === 'verify' && (
          <form
            onSubmit={handleVerify}
            style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
          >
            <p style={subtitleStyle}>
              Enter the 6-digit code from your authenticator app to confirm
              setup.
            </p>

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
              disabled={loading || code.length !== 6}
              style={loading || code.length !== 6 ? disabledButtonStyle : primaryButtonStyle}
            >
              {loading ? 'Verifying…' : 'Verify & Enable 2FA'}
            </button>

            <button
              type="button"
              onClick={() => setStep('scan')}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-text-muted)',
                fontSize: 'var(--font-size-sm)',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              &larr; Back to QR Code
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
