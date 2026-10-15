import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

function messageFor(error) {
  const detail = error?.details?.detail
  return Array.isArray(detail) ? detail.join(' ') : detail || error.message || 'Не удалось выполнить вход.'
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const next = location.state?.from || '/'

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login({ username: username.trim(), password })
      navigate(next, { replace: true })
    } catch (requestError) {
      setError(messageFor(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="page-shell"><section className="auth-card" aria-labelledby="page-title">
    <Link className="brand" to="/">inHabit</Link>
    <p className="eyebrow">С возвращением</p><h1 id="page-title">Войдите в аккаунт</h1>
    <p className="auth-description">Продолжайте развивать полезные привычки вместе с гильдией.</p>
    <form className="auth-form" onSubmit={handleSubmit}>
      <label>Логин<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required autoFocus /></label>
      <label>Пароль<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button button-primary" type="submit" disabled={submitting}>{submitting ? 'Входим…' : 'Войти'}</button>
    </form>
    <p className="auth-footer">Ещё нет аккаунта? <Link to="/register">Зарегистрироваться</Link></p>
  </section></main>
}
