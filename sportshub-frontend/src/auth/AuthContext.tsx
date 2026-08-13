import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { User } from '../api/types'
import { AuthContext, type AuthContextValue } from './context'
const TOKEN_KEY = 'sportshub.access_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(token))

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api.me(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const value = useMemo<AuthContextValue>(() => ({
    token,
    user,
    loading,
    login: async (email, password) => {
      const result = await api.login({ email, password })
      localStorage.setItem(TOKEN_KEY, result.access_token)
      setToken(result.access_token)
      setUser(result.user)
    },
    register: async (email, username, password) => {
      const result = await api.register({ email, username, password })
      localStorage.setItem(TOKEN_KEY, result.access_token)
      setToken(result.access_token)
      setUser(result.user)
    },
    logout: () => {
      localStorage.removeItem(TOKEN_KEY)
      setToken(null)
      setUser(null)
    },
  }), [loading, token, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
