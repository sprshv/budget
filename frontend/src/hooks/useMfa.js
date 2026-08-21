import { useState } from 'react'
import { supabase } from '../lib/supabase'

/**
 * useMfa — wraps Supabase client-side MFA APIs.
 *
 * All three operations (enroll, verify, unenroll) go directly through
 * supabase-js, which handles the challenge/response flow and updates
 * the local session to AAL2 on successful verification.
 */
export function useMfa() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Enroll a new TOTP factor.
   * Returns the Supabase MFA enroll data (includes totp.qr_code, totp.uri,
   * totp.secret, and the factor id).
   */
  const enrollTotp = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data, error: enrollError } = await supabase.auth.mfa.enroll({
        factorType: 'totp',
        issuer: 'BudgetingApp',
      })
      if (enrollError) throw enrollError
      return data
    } catch (err) {
      setError(err.message ?? 'Failed to start 2FA setup.')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * Create an MFA challenge and immediately verify it with the given code.
   * On success the Supabase session is upgraded to AAL2.
   */
  const verifyTotp = async (factorId, code) => {
    setLoading(true)
    setError(null)
    try {
      // Step 1: create challenge
      const { data: challengeData, error: challengeError } =
        await supabase.auth.mfa.challenge({ factorId })
      if (challengeError) throw challengeError

      // Step 2: verify
      const { data, error: verifyError } = await supabase.auth.mfa.verify({
        factorId,
        challengeId: challengeData.id,
        code,
      })
      if (verifyError) throw verifyError
      return data
    } catch (err) {
      setError(err.message ?? 'Invalid code. Please try again.')
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * Remove an enrolled TOTP factor.
   * Returns true on success, false on failure (error is set).
   */
  const unenroll = async (factorId) => {
    setLoading(true)
    setError(null)
    try {
      const { error: unenrollError } = await supabase.auth.mfa.unenroll({
        factorId,
      })
      if (unenrollError) throw unenrollError
      return true
    } catch (err) {
      setError(err.message ?? 'Failed to remove 2FA.')
      return false
    } finally {
      setLoading(false)
    }
  }

  /**
   * List enrolled factors for the current user.
   * Returns the factors object or null on error.
   */
  const listFactors = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data, error: listError } = await supabase.auth.mfa.listFactors()
      if (listError) throw listError
      return data
    } catch (err) {
      setError(err.message ?? 'Failed to list 2FA factors.')
      return null
    } finally {
      setLoading(false)
    }
  }

  return { enrollTotp, verifyTotp, unenroll, listFactors, loading, error }
}
