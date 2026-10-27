import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { normalizeInviteCode } from '../api/invites'

export function GuildJoinPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    const normalized = normalizeInviteCode(code)
    if (!/^[ABCDEFGHJKMNPQRSTUVWXYZ2-9]{8}$/.test(normalized)) {
      setError('Введите код приглашения из 8 символов.')
      return
    }
    navigate(`/invite/${encodeURIComponent(normalized)}`)
  }

  return <main className="page-shell"><section className="auth-card" aria-labelledby="page-title">
    <Link className="brand" to="/">inHabit</Link>
    <p className="eyebrow">Вместе к цели</p><h1 id="page-title">Вступить в гильдию</h1>
    <p className="auth-description">Введите код от создателя гильдии. Перед вступлением вы увидите, куда вас приглашают.</p>
    <form className="auth-form" onSubmit={handleSubmit}>
      <label>Код приглашения<input value={code} onChange={(event) => { setCode(event.target.value); setError('') }} autoCapitalize="characters" autoComplete="off" spellCheck={false} required autoFocus aria-invalid={Boolean(error)} aria-describedby={error ? 'code-error' : undefined} /></label>
      {error && <p id="code-error" className="form-error" role="alert">{error}</p>}
      <button className="button button-primary" type="submit">Открыть приглашение</button>
    </form>
    <p className="auth-footer"><Link to="/">На главную</Link></p>
  </section></main>
}
