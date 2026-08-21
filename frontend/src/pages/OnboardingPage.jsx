import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUpdateProfile } from '../hooks/useProfile'

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [fullName, setFullName] = useState('')
  const updateProfile = useUpdateProfile()

  const handleComplete = async () => {
    await updateProfile.mutateAsync({
      full_name: fullName,
      onboarding_complete: true,
    })
    navigate('/dashboard')
  }

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
        maxWidth: '480px',
        background: 'var(--color-bg-card)',
        borderRadius: 'var(--radius-xl)',
        border: '1px solid var(--color-border)',
        padding: 'var(--space-10)',
        textAlign: 'center',
      }}>
        {/* Progress dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-8)' }}>
          {[1, 2, 3].map((s) => (
            <div key={s} style={{
              width: '8px',
              height: '8px',
              borderRadius: 'var(--radius-full)',
              background: s <= step ? 'var(--color-primary)' : 'var(--color-border-strong)',
              transition: 'var(--transition-base)',
            }} />
          ))}
        </div>

        {step === 1 && (
          <>
            <div style={{ fontSize: '48px', marginBottom: 'var(--space-6)' }}>💰</div>
            <h1 style={{
              fontSize: 'var(--font-size-3xl)',
              fontWeight: 'var(--font-weight-bold)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-4)',
            }}>
              Welcome to your financial dashboard
            </h1>
            <p style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-8)',
              lineHeight: 'var(--line-height-relaxed)',
            }}>
              Track spending, set budgets, and reach your financial goals — all in one place.
            </p>
            <button
              onClick={() => setStep(2)}
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                background: 'var(--color-primary)',
                color: 'var(--color-primary-foreground)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                cursor: 'pointer',
              }}
            >
              Get Started
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h1 style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 'var(--font-weight-bold)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-2)',
            }}>
              What's your name?
            </h1>
            <p style={{
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--space-6)',
            }}>
              We'll use this to personalize your experience.
            </p>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your full name"
              style={{
                width: '100%',
                padding: 'var(--space-3) var(--space-4)',
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-size-base)',
                outline: 'none',
                marginBottom: 'var(--space-6)',
                textAlign: 'center',
                boxSizing: 'border-box',
              }}
            />
            <button
              onClick={() => setStep(3)}
              disabled={!fullName.trim()}
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                background: fullName.trim() ? 'var(--color-primary)' : 'var(--color-bg-elevated)',
                color: fullName.trim() ? 'var(--color-primary-foreground)' : 'var(--color-text-muted)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                cursor: fullName.trim() ? 'pointer' : 'not-allowed',
              }}
            >
              Continue
            </button>
          </>
        )}

        {step === 3 && (
          <>
            <div style={{ fontSize: '48px', marginBottom: 'var(--space-6)' }}>🎉</div>
            <h1 style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: 'var(--font-weight-bold)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-4)',
            }}>
              You're all set, {fullName}!
            </h1>
            <p style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-8)',
            }}>
              Your financial dashboard is ready. Let's start tracking.
            </p>
            <button
              onClick={handleComplete}
              disabled={updateProfile.isPending}
              style={{
                width: '100%',
                padding: 'var(--space-3)',
                background: 'var(--color-primary)',
                color: 'var(--color-primary-foreground)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                cursor: updateProfile.isPending ? 'not-allowed' : 'pointer',
                opacity: updateProfile.isPending ? 0.7 : 1,
              }}
            >
              {updateProfile.isPending ? 'Saving…' : 'Go to Dashboard'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
