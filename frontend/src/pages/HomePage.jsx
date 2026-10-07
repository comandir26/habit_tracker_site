import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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
  const [state, setState] = useState({ loading: true, today: null, error: '' })
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    setState({ loading: true, today: null, error: '' })
    getTodayHabitsFromApi()
      .catch(() => getTodayHabits())
      .then((today) => active && setState({ loading: false, today, error: '' }))
      .catch((error) => active && setState({ loading: false, today: null, error: error.message || 'Не удалось загрузить привычки.' }))
    return () => { active = false }
  }, [retry])

  return (
    <main className="page-shell dashboard-home">
      <section className="welcome-card" aria-labelledby="page-title">
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
                      <small>{habit.guild_name} · {habitSchedule(habit)}</small>
                    </div>
                    <span>+{habit.xp_reward} XP</span>
                  </li>
                ))}
              </ul>
            ) : <p>На сегодня привычек нет. Создайте первую для своей гильдии.</p>}
          </>
        )}
        <div className="welcome-actions">
          <Link className="button button-primary" to="/guilds/new">Создать гильдию <span aria-hidden="true">→</span></Link>
          <Link className="button button-secondary" to="/guilds/demo">Открыть пример гильдии</Link>
        </div>
      </section>
      <aside className="home-level-card" aria-label="Текущий уровень"><span>◆</span><p>Ваш уровень</p><strong>7</strong><small>1 840 / 2 000 XP</small></aside>
    </main>
  )
}
