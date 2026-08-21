import { Navigate } from 'react-router-dom'
import { useProfile } from '../hooks/useProfile'

export default function OnboardingGuard({ children }) {
  const { data: profile, isLoading } = useProfile()

  if (isLoading) return null

  if (profile && !profile.onboarding_complete) {
    return <Navigate to="/onboarding" replace />
  }

  return children
}
