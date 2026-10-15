import { createContext, useContext, useEffect, useState } from 'react'
import { getAccessToken, setAccessToken } from '../api/client'
import { getCurrentUser, login as loginRequest, logout as logoutRequest, register as registerRequest } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(getAccessToken()))
  useEffect(() => {
    if (!getAccessToken()) return
    getCurrentUser().then(setUser).catch(() => { setAccessToken(null); setUser(null) }).finally(() => setLoading(false))
  }, [])
  const value = {
    user, loading,
    async login(credentials) { const currentUser = await loginRequest(credentials); setUser(currentUser); return currentUser },
    async register(credentials) { const currentUser = await registerRequest(credentials); setUser(currentUser); return currentUser },
    async logout() { await logoutRequest(); setUser(null) },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error('useAuth должен использоваться внутри AuthProvider'); return context }
