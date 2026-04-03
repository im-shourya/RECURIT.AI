'use client'

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { api, setToken, clearToken, getToken, type OrgProfile } from '@/lib/api'

interface AuthContextType {
  user: OrgProfile | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<OrgProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  // Check for existing token on mount
  useEffect(() => {
    const token = getToken()
    if (token) {
      api.getMe()
        .then((profile) => {
          setUser(profile)
        })
        .catch(() => {
          clearToken()
          setUser(null)
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [])

  // Protect dashboard routes
  useEffect(() => {
    if (!isLoading && !user && pathname?.startsWith('/dashboard')) {
      router.replace('/auth/login')
    }
  }, [isLoading, user, pathname, router])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login({ email, password })
    setToken(res.access_token)
    const profile = await api.getMe()
    setUser(profile)
  }, [])

  const register = useCallback(async (name: string, email: string, password: string) => {
    const res = await api.register({ name, email, password })
    setToken(res.access_token)
    const profile = await api.getMe()
    setUser(profile)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    router.push('/auth/login')
  }, [router])

  return (
    <AuthContext.Provider
      value={{
        user,
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
