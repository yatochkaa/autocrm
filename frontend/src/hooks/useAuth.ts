import { useState, useEffect, createContext, useContext, type ReactNode } from 'react'
import { getMe } from '../api/auth'
import type { User } from '../types'

interface AuthCtx {
  user: User | null
  loading: boolean
  isAdmin: boolean
  logout: () => void
  refresh: () => Promise<void>
}

import React from 'react'
const AuthContext = createContext<AuthCtx>({
  user: null, loading: true, isAdmin: false,
  logout: () => {}, refresh: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]     = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchMe = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) { setUser(null); setLoading(false); return }
    try { setUser(await getMe()) } catch { setUser(null) } finally { setLoading(false) }
  }

  useEffect(() => { fetchMe() }, [])

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  return React.createElement(
    AuthContext.Provider,
    { value: { user, loading, isAdmin: user?.role === 'admin', logout, refresh: fetchMe } },
    children,
  )
}

export function useAuth() { return useContext(AuthContext) }
