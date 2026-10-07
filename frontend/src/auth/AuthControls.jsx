import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

export function AuthControls() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  if (!user) return <Link className="button button-secondary button-small" to="/login">Войти</Link>
  return <div className="auth-controls"><span className="avatar" title={user.username}>{user.username.slice(0, 1).toUpperCase()}</span><button className="text-button" type="button" onClick={handleLogout}>Выйти</button></div>
}
