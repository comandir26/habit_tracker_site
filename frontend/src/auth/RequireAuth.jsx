import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <main className="app-page page-status">Проверяем вход…</main>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}
