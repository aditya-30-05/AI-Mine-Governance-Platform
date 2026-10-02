import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthUser, UserRole } from '@/types'

interface AuthState {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  selectedMineId: string | null
  login: (user: AuthUser, token: string) => void
  logout: () => void
  setMine: (mineId: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      selectedMineId: null,
      login: (user, token) => set({ user, token, isAuthenticated: true, selectedMineId: user.mine_id }),
      logout: () => set({ user: null, token: null, isAuthenticated: false, selectedMineId: null }),
      setMine: (mineId) => set({ selectedMineId: mineId }),
    }),
    { name: 'coalmine-auth' }
  )
)

// Role helpers
export const useRole = (): UserRole | null => useAuthStore((s) => s.user?.role ?? null)
export const useIsMineManager = () => {
  const role = useRole()
  return role === 'mine_manager' || role === 'admin'
}
export const useIsCompliance = () => {
  const role = useRole()
  return role === 'compliance_officer' || role === 'admin' || role === 'corporate_manager'
}
export const useCanVerify = () => {
  const role = useRole()
  return role === 'compliance_officer' || role === 'mine_manager' || role === 'admin' || role === 'corporate_manager'
}
