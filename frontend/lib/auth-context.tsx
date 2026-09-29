'use client'

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { api, type OrgProfile, type Role } from '@/lib/api'

/**
 * Roles are ranked, matching ROLE_RANK on the backend: an owner can do
 * anything an admin can. Compared by rank rather than equality so call sites
 * ask for a minimum instead of listing every role that qualifies.
 */
const ROLE_RANK: Record<Role, number> = { member: 1, admin: 2, owner: 3 }

interface AuthContextType {
  user: OrgProfile | null
  role: Role
  /**
   * Whether the signed-in user meets a minimum role.
   *
   * This only decides what the interface offers. The API enforces the same
   * rule independently, so hiding a button is a courtesy, never the control.
   */
  can: (minimum: Role) => boolean
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<OrgProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  // The session is an httpOnly cookie this code cannot see, so the only way
  // to know whether there is one is to ask.
  useEffect(() => {
    api.getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  // Protect dashboard routes
  useEffect(() => {
    if (!isLoading && !user && pathname?.startsWith('/dashboard')) {
      router.replace('/auth/login')
    }
  }, [isLoading, user, pathname, router])

  // Both set the session cookie and answer with the profile.
  const login = useCallback(async (email: string, password: string) => {
    setUser(await api.login({ email, password }))
  }, [])

  const register = useCallback(async (name: string, email: string, password: string) => {
    setUser(await api.register({ name, email, password }))
  }, [])

  // Defaults to the least privileged role, so a profile that arrives without
  // one offers fewer actions rather than more.
  const role: Role = user?.role ?? 'member'
  const can = useCallback(
    (minimum: Role) => ROLE_RANK[role] >= ROLE_RANK[minimum],
    [role],
  )

  const logout = useCallback(async () => {
    // Signed out locally even if the request fails; the cookie then simply
    // expires on its own.
    await api.logout().catch(() => {})
    setUser(null)
    router.push('/auth/login')
  }, [router])

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        can,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
