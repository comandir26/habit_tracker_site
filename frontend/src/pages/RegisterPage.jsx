import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

function messageFor(error) {
  const details = error?.details
  if (details && typeof details === 'object') {
    return Object.values(details).flat().join(' ')
  }
  return error?.message || 'Не удалось создать аккаунт.'
}

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function update(field) { return (event) => setForm((current) => ({ ...current, [field]: event.target.value })) }
  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await register({ ...form, username: form.username.trim(), email: form.email.trim(), timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' })
      navigate('/', { replace: true })
    } catch (requestError) {
      setError(messageFor(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="page-shell"><section className="auth-card" aria-labelledby="page-title">
    <Link className="brand" to="/">inHabit</Link>
    <p className="eyebrow">Новый аккаунт</p><h1 id="page-title">Начните свой путь</h1>
    <p className="auth-description">Создайте аккаунт, чтобы создавать гильдии и сохранять свой прогресс.</p>
    <form className="auth-form" onSubmit={handleSubmit}>
      <label>Логин<input value={form.username} onChange={update('username')} autoComplete="username" required autoFocus /></label>
      <label>Электронная почта<input type="email" value={form.email} onChange={update('email')} autoComplete="email" required /></label>
      <label>Пароль<input type="password" value={form.password} onChange={update('password')} autoComplete="new-password" minLength="8" required /><small>Не менее 8 символов.</small></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button button-primary" type="submit" disabled={submitting}>{submitting ? 'Создаём…' : 'Создать аккаунт'}</button>
    </form>
    <p className="auth-footer">Уже есть аккаунт? <Link to="/login">Войти</Link></p>
  </section></main>
}
