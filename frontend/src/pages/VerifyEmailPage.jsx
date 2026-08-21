import { useSearchParams, Link } from 'react-router-dom'

export default function VerifyEmailPage() {
  const [params] = useSearchParams()
  const verified = params.get('verified') === 'true'

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-bg)',
      padding: 'var(--space-4)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        background: 'var(--color-bg-card)',
        borderRadius: 'var(--radius-xl)',
        border: '1px solid var(--color-border)',
        padding: 'var(--space-8)',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '48px', marginBottom: 'var(--space-4)' }}>
          {verified ? '✅' : '📬'}
        </div>
        <h1 style={{
          fontSize: 'var(--font-size-2xl)',
          fontWeight: 'var(--font-weight-bold)',
          color: 'var(--color-text-primary)',
          marginBottom: 'var(--space-3)',
        }}>
          {verified ? 'Email verified!' : 'Verify your email'}
        </h1>
        <p style={{
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--font-size-sm)',
          marginBottom: 'var(--space-6)',
        }}>
          {verified
            ? 'Your email has been confirmed. You can now sign in.'
            : 'Check your inbox for a verification link. Once confirmed, you can sign in.'}
        </p>
        <Link
          to="/login"
          style={{
            display: 'inline-block',
            padding: 'var(--space-3) var(--space-6)',
            background: 'var(--color-primary)',
            color: 'var(--color-primary-foreground)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-base)',
            fontWeight: 'var(--font-weight-semibold)',
            textDecoration: 'none',
          }}
        >
          Go to Login
        </Link>
      </div>
    </div>
  )
}
