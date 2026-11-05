import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AuthControls } from '../auth/AuthControls'
import { useAuth } from '../auth/AuthContext'
import { getGuilds } from '../api/guilds'
import { ProfileProgress } from '../components/ProfileProgress'

import { getTodayHabits, getTodayHabitsFromApi } from '../api/habits'
import { habitSchedule } from '../api/habitOptions'

function formatTodayDate(date) {
  return new Intl.DateTimeFormat('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date(`${date}T12:00:00`))
}

export function HomePage() {
  const { user, loading: authLoading } = useAuth()
  const [state, setState] = useState({ loading: true, today: null, error: '' })
  const [guildsState, setGuildsState] = useState({ loading: true, guilds: [], error: '' })
  const [guildsRetry, setGuildsRetry] = useState(0)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    setState({ loading: true, today: null, error: '' })
    if (authLoading) return () => { active = false }
    const request = user ? getTodayHabitsFromApi() : getTodayHabits()
    request
      .then((today) => active && setState({ loading: false, today, error: '' }))
      .catch((error) => active && setState({ loading: false, today: null, error: error.message || 'Не удалось загрузить привычки.' }))
    return () => { active = false }
  }, [retry, user?.id, authLoading])

  useEffect(() => {
    let active = true
    setGuildsState({ loading: true, guilds: [], error: '' })
    if (authLoading || !user) return () => { active = false }
    getGuilds()
      .then((guilds) => active && setGuildsState({ loading: false, guilds, error: '' }))
      .catch((error) => active && setGuildsState({ loading: false, guilds: [], error: error.message || 'Не удалось загрузить гильдии.' }))
    return () => { active = false }
  }, [user?.id, authLoading, guildsRetry])

  return (
    <main className="page-shell dashboard-home">
      <section className="welcome-card" aria-labelledby="page-title">
        <div className="home-auth"><AuthControls /></div>
        <p className="eyebrow">⚡ inHabit · ваш путь</p>
        <h1 id="page-title">Привычки на сегодня</h1>
        {state.loading && <p role="status">Собираем ваш список…</p>}
        {state.error && (
          <div>
            <p className="form-error" role="alert">{state.error}</p>
            <button className="button button-secondary" type="button" onClick={() => setRetry((value) => value + 1)}>
              Повторить
            </button>
          </div>
        )}
        {state.today && (
          <>
            <p className="today-caption">{formatTodayDate(state.today.date)} · {state.today.timezone}</p>
            {state.today.habits.length ? (
              <ul className="today-habits-list">
                {state.today.habits.map((habit) => (
                  <li key={habit.id}>
                    <span className="today-guild-dot" style={{ backgroundColor: habit.guild_color }} aria-hidden="true" />
                    <div>
                      <strong>{habit.name}</strong>
                      <small><Link to={`/guilds/${encodeURIComponent(user ? habit.guild : 'demo')}`}>{habit.guild_name}</Link> · {habitSchedule(habit)}</small>
                    </div>
                    <span>+{habit.xp_reward} XP</span>
                    <Link className="today-open-guild" to={`/guilds/${encodeURIComponent(user ? habit.guild : 'demo')}`}>Открыть гильдию и отметить →</Link>
                  </li>
                ))}
              </ul>
            ) : <p>На сегодня привычек нет. Создайте первую для своей гильдии.</p>}
          </>
        )}
        {user && <section className="home-guilds" aria-labelledby="my-guilds-title">
          <h2 id="my-guilds-title">Мои гильдии</h2>
          <p className="muted">Откройте гильдию, чтобы отмечать выполнение привычек. Создатель также может добавлять новые привычки.</p>
          {guildsState.loading ? <p role="status">Загружаем ваши гильдии…</p> : guildsState.error ? <div><p className="form-error" role="alert">{guildsState.error}</p><button className="button button-secondary" type="button" onClick={() => setGuildsRetry((value) => value + 1)}>Повторить загрузку гильдий</button></div> : guildsState.guilds.length ? <ul className="home-guilds-list">
            {guildsState.guilds.map((guild) => <li key={guild.id}>
              <Link className="home-guild-title" to={`/guilds/${encodeURIComponent(guild.id)}`}>{guild.name} →</Link>
              <p className="muted">{guild.members.length} участн. · {guild.isOwner ? 'Вы создатель' : 'Вы участник'}</p>
              {guild.isOwner && <Link className="text-button" to={`/guilds/${encodeURIComponent(guild.id)}/habits/new`}>Добавить привычку</Link>}
            </li>)}
          </ul> : <p>Вы пока не состоите в гильдиях. Создайте свою или вступите по коду.</p>}
        </section>}
        <div className="welcome-actions">
          <Link className="button button-primary" to="/guilds/new">Создать гильдию <span aria-hidden="true">→</span></Link>
          <Link className="button button-secondary" to="/guilds/join">Вступить по коду</Link>
          <Link className="button button-secondary" to="/guilds/demo">Открыть пример гильдии</Link>
        </div>
      </section>
      {user && <aside aria-label="Текущий уровень"><ProfileProgress compact /></aside>}
    </main>
  )
}
