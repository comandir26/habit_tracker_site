import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { getLeaderboard } from '../api/leaderboard'
import { AuthControls } from '../auth/AuthControls'

export function GuildLeaderboardPage() {
  const { guildId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const sort = searchParams.get('sort') === 'streak' ? 'streak' : 'xp'
  const [state, setState] = useState({ loading: true, result: null, error: '' })
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    setState({ loading: true, result: null, error: '' })
    getLeaderboard(guildId, sort)
      .then((result) => active && setState({ loading: false, result, error: '' }))
      .catch((error) => active && setState({ loading: false, result: null, error: error.message || 'Не удалось загрузить рейтинг.' }))
    return () => { active = false }
  }, [guildId, sort, retry])

  const current = state.result?.members.find((member) => member.is_current_user)

  return <main className="app-page">
    <header className="topbar"><Link className="brand" to="/">inHabit</Link><AuthControls /></header>
    <section className="leaderboard-page" aria-labelledby="page-title">
      <Link className="back-link" to={`/guilds/${encodeURIComponent(guildId)}`}>← В гильдию</Link>
      <p className="eyebrow">{state.result?.guild_name || 'Соревнуемся вместе'}</p>
      <h1 id="page-title">Лидерборд участников</h1>
      <p className="auth-description">XP учитывается только в этой гильдии. Стрик — последовательные дни с выполнением хотя бы одной её привычки в часовом поясе участника. Если сегодня ещё нет выполнения, вчерашняя серия сохраняется.</p>
      <div className="leaderboard-sort" role="group" aria-label="Сортировка рейтинга">
        <button className={`button ${sort === 'xp' ? 'button-primary' : 'button-ghost'}`} type="button" aria-pressed={sort === 'xp'} onClick={() => setSearchParams({ sort: 'xp' })}>По XP</button>
        <button className={`button ${sort === 'streak' ? 'button-primary' : 'button-ghost'}`} type="button" aria-pressed={sort === 'streak'} onClick={() => setSearchParams({ sort: 'streak' })}>По стрику</button>
      </div>
      {state.loading && <p role="status">Загружаем рейтинг…</p>}
      {state.error && <div><p className="form-error" role="alert">{state.error}</p><button className="button button-ghost" type="button" onClick={() => setRetry((value) => value + 1)}>Повторить</button></div>}
      {state.result && <>
        {current && <p className="leaderboard-position" role="status">Ваше место: <strong>{current.rank}</strong> · {current.xp.toLocaleString('ru-RU')} XP · Стрик: {current.streak} дн.</p>}
        {state.result.members.length ? <div className="leaderboard-table-wrap"><table className="leaderboard-table">
          <caption className="sr-only">Рейтинг по {sort === 'xp' ? 'XP' : 'стрику'}, по убыванию</caption>
          <thead><tr><th scope="col">Место</th><th scope="col">Участник</th><th scope="col" aria-sort={sort === 'xp' ? 'descending' : undefined}>XP</th><th scope="col" aria-sort={sort === 'streak' ? 'descending' : undefined}>Стрик, дн.</th></tr></thead>
          <tbody>{state.result.members.map((member) => <tr key={member.member_id} className={member.is_current_user ? 'leaderboard-current' : undefined}>
            <td>{member.rank}</td><th scope="row">{member.username}{member.is_current_user && <span className="leaderboard-you">Вы</span>}</th><td>{member.xp.toLocaleString('ru-RU')}</td><td>{member.streak}</td>
          </tr>)}</tbody>
        </table></div> : <p>В гильдии пока нет участников.</p>}
        <p className="muted leaderboard-rules">При равенстве основного показателя учитывается второй. Если оба равны — порядок по ID пользователя.</p>
      </>}
    </section>
  </main>
}
