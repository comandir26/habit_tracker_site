import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getInvite, joinGuild } from '../api/invites'

export function InvitePage() {
  const { code } = useParams()
  const [state, setState] = useState({ loading: true, invite: null, error: '' })
  const [joining, setJoining] = useState(false)
  const [joinError, setJoinError] = useState('')
  const [joined, setJoined] = useState(false)
  const requestVersion = useRef(0)

  async function handleJoin() {
    if (joining) return
    const version = requestVersion.current
    setJoining(true)
    setJoinError('')
    try {
      await joinGuild(code)
      if (version === requestVersion.current) setJoined(true)
    } catch (error) {
      if (version === requestVersion.current) setJoinError(error.message || 'Не удалось вступить в гильдию. Попробуйте ещё раз.')
    } finally {
      if (version === requestVersion.current) setJoining(false)
    }
  }

  useEffect(() => {
    let active = true
    setJoining(false)
    setJoined(false)
    setJoinError('')
    setState({ loading: true, invite: null, error: '' })
    getInvite(code).then((invite) => active && setState({ loading: false, invite, error: '' }))
      .catch((error) => active && setState({ loading: false, invite: null, error: error.message || 'Не удалось открыть приглашение.' }))
    return () => { active = false; requestVersion.current += 1 }
  }, [code])

  if (state.loading) return <main className="page-shell">Открываем приглашение…</main>
  if (state.error) return <main className="page-shell"><section className="auth-card"><Link className="brand" to="/">inHabit</Link><p className="eyebrow">Приглашение</p><h1>Не получилось</h1><p className="auth-description" role="alert">{state.error}</p><Link className="button button-primary" to="/guilds/join">Ввести другой код</Link></section></main>

  const { invite } = state
  const { guild } = invite

  return (
    <main className="page-shell">
      <section className="auth-card invite-preview" style={{ '--guild-color': guild.color }} aria-labelledby="page-title">
        <Link className="brand" to="/">inHabit</Link>
        <div className="guild-symbol" aria-hidden="true">✦</div>
        <p className="eyebrow">{guild.owner} приглашает вас в гильдию</p>
        <h1 id="page-title">{guild.name}</h1>
        {guild.description && <p className="auth-description">{guild.description}</p>}
        <p className="muted">Участников: {guild.members_count} · Код {invite.code}</p>
        {joined && <p role="status">Вы вступили в гильдию! Теперь вам доступны её привычки.</p>}
        {joinError && <p className="form-error" role="alert">{joinError}</p>}
        {invite.is_member || joined
          ? <Link className="button button-primary" to={`/guilds/${guild.id}`}>Перейти в гильдию</Link>
          : <button className="button button-primary" type="button" disabled={joining} onClick={handleJoin}>{joining ? 'Вступаем…' : 'Вступить в гильдию'}</button>}
        {invite.is_member && !joined && <p className="muted">Вы уже участник этой гильдии.</p>}
      </section>
    </main>
  )
}
