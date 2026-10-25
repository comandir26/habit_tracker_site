import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getInvite } from '../api/invites'

export function InvitePage() {
  const { code } = useParams()
  const [state, setState] = useState({ loading: true, invite: null, error: '' })

  useEffect(() => {
    let active = true
    setState({ loading: true, invite: null, error: '' })
    getInvite(code).then((invite) => active && setState({ loading: false, invite, error: '' }))
      .catch((error) => active && setState({ loading: false, invite: null, error: error.message || 'Не удалось открыть приглашение.' }))
    return () => { active = false }
  }, [code])

  if (state.loading) return <main className="page-shell">Открываем приглашение…</main>
  if (state.error) return <main className="page-shell"><section className="auth-card"><Link className="brand" to="/">inHabit</Link><p className="eyebrow">Приглашение</p><h1>Не получилось</h1><p className="auth-description" role="alert">{state.error}</p><Link className="button button-primary" to="/">На главную</Link></section></main>

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
        {invite.is_member
          ? <Link className="button button-primary" to={`/guilds/${guild.id}`}>Перейти в гильдию</Link>
          : <p className="habit-demo-note">Вы ещё не в этой гильдии. Вступление по приглашению появится в следующем обновлении — сохраните ссылку.</p>}
      </section>
    </main>
  )
}
