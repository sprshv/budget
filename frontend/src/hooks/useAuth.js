import { useEffect } from 'react'
import { supabase } from '../lib/supabase'
import useUserStore from '../store/useUserStore'

export function useAuth() {
  const { user, session, setUser, setSession, clearUser } = useUserStore()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [setUser, setSession])

  const signOut = async () => {
    await supabase.auth.signOut()
    clearUser()
  }

  return { user, session, signOut, isAuthenticated: !!session }
}
