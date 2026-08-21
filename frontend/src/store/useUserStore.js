import { create } from 'zustand'

const useUserStore = create((set) => ({
  user: null,
  session: undefined,
  setUser: (user) => set({ user }),
  setSession: (session) => set({ session }),
  clearUser: () => set({ user: null, session: null }),
}))

export default useUserStore
