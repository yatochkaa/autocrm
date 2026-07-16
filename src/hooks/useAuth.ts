import { useState, useEffect } from 'react'
import { getMe, logout as apiLogout } from '../api/auth'
import type { User } from '../types'

// Простой хук для текущего пользователя
export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }
    getMe()
      .then(setUser)
      .catch(() => { localStorage.removeItem('access_token') })
      .finally(() => setLoading(false))
  }, [])

  const logout = () => {
    apiLogout()
    setUser(null)
  }

  return { user, loading, logout }
}
