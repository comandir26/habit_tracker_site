import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getGuild } from '../api/guilds'
import { completeHabit, getHabits } from '../api/habits'
import { habitSchedule, demoDifficulties } from '../api/habitOptions'

export function GuildDetailsPage() {
  const { guildId } = useParams()
  const [state, setState] = useState({ loading: true, guild: null, isDemo: false, error: '' })
  const [habitsState, setHabitsState] = useState({ loading: true, habits: [], error: '' })
  const [retry, setRetry] = useState(0)
  const [completion, setCompletion] = useState({ pendingId: null, completedIds: new Set(), error: '' })

  useEffect(() => {
    let active = true
    setState({ loading: true, guild: null, isDemo: false, error: '' })
    getGuild(guildId).then(({ guild, isDemo }) => active && setState({ loading: false, guild, isDemo, error: '' }))
      .catch((error) => active && setState({ loading: false, guild: null, isDemo: false, error: error.message }))
    return () => { active = false }
  }, [guildId])

  useEffect(() => {
    let active = true
    setHabitsState({ loading: true, habits: [], error: '' })
    getHabits(guildId).then((habits) => active && setHabitsState({ loading: false, habits, error: '' }))
      .catch((error) => active && setHabitsState({ loading: false, habits: [], error: error.message || 'Не удалось загрузить привычки.' }))
    return () => { active = false }
  }, [guildId, retry])

  if (state.loading) return <main className="app-page page-status">Загружаем гильдию…</main>
  if (state.error || !state.guild) return <main className="app-page page-status"><p>{state.error || 'Гильдия не найдена.'}</p><Link className="button button-primary" to="/">На главную</Link></main>

  const { guild, isDemo } = state
  const percentage = Math.min(100, Math.round((guild.experience / guild.experienceToLevel) * 100))

  async function markComplete(habit) {
    setCompletion((current) => ({ ...current, pendingId: habit.id, error: '' }))
    try {
      const result = await completeHabit(guildId, habit)
      setCompletion((current) => ({
        pendingId: null,
        error: '',
        completedIds: new Set([...current.completedIds, habit.id]),
      }))
      if (result.created) {
        setState((current) => ({
          ...current,
          guild: {
            ...current.guild,
            experience: current.guild.experience + result.awarded_xp,
            members: current.guild.members.map((member) => (
              String(member.id) === String(result.member_id)
                ? { ...member, xp: result.member_xp ?? member.xp + result.awarded_xp }
                : member
            )),
          },
        }))
      }
    } catch (error) {
      setCompletion((current) => ({ ...current, pendingId: null, error: error.message || 'Не удалось отметить выполнение.' }))
    }
  }

  return (
    <main className="app-page">
      <header className="topbar">
        <Link className="brand" to="/">inHabit</Link>
        <nav aria-label="Основная навигация"><Link to="/">Сегодня</Link><span className="active-nav">Гильдии</span></nav>
        <div className="avatar" aria-label="Профиль Алексея">А</div>
      </header>

      <section className="guild-hero" style={{ '--guild-color': guild.color }}>
        <div className="guild-symbol" aria-hidden="true">✦</div>
        <div>
          <Link className="back-link hero-back" to="/">← Все гильдии</Link>
          <p className="eyebrow">Ваша гильдия</p>
          <h1>{guild.name}</h1>
          <p>{guild.description}</p>
        </div>
        <button className="button button-light" type="button">Пригласить</button>
      </section>
      {isDemo && <p className="demo-note">Демо-режим: гильдия и привычки хранятся локально в этой вкладке браузера.</p>}

      <section className="guild-dashboard" aria-label="Страница гильдии">
        <article className="progress-card">
          <div className="card-heading"><div><p className="section-label">Общий прогресс</p><h2>До нового уровня</h2></div><strong>{guild.experience.toLocaleString('ru-RU')} <small>/ {guild.experienceToLevel.toLocaleString('ru-RU')} XP</small></strong></div>
          <div className="progress-track"><span style={{ width: `${percentage}%` }} /></div>
          <p className="muted">Ещё {Math.max(0, guild.experienceToLevel - guild.experience).toLocaleString('ru-RU')} XP — и ваша гильдия достигнет {guild.level + 1} уровня.</p>
        </article>

        <article className="members-card">
          <div className="card-heading"><div><p className="section-label">Участники</p><h2>{guild.members.length} {guild.members.length === 1 ? 'человек' : 'участника'}</h2></div><button className="text-button" type="button">Смотреть всех</button></div>
          <ul className="members-list">
            {guild.members.map((member) => <li key={member.id}><span className="member-avatar">{member.name.slice(0, 1).toUpperCase()}</span><span><strong>{member.name}</strong>{member.role === 'owner' && <small>Создатель</small>}</span><strong className="member-xp">{member.xp.toLocaleString('ru-RU')} XP</strong></li>)}
          </ul>
        </article>

        <article className="habits-card">
          <div className="card-heading"><div><p className="section-label">Привычки гильдии</p><h2>Общие шаги к цели</h2></div>{guild.isOwner && <Link className="button button-primary" to={`/guilds/${encodeURIComponent(guildId)}/habits/new`}>Добавить привычку</Link>}</div>
          {completion.error && <p className="form-error" role="alert">{completion.error}</p>}
          {habitsState.loading ? <p className="habit-status" role="status">Загружаем привычки…</p> : habitsState.error ? <div className="habit-status"><p className="form-error" role="alert">{habitsState.error}</p><button className="button button-ghost" type="button" onClick={() => setRetry((value) => value + 1)}>Повторить</button></div> : habitsState.habits.length ? <ul className="habits-list">{habitsState.habits.map((habit) => { const isCompleted = completion.completedIds.has(habit.id); const isPending = completion.pendingId === habit.id; return <li key={habit.id}><span className="empty-icon" aria-hidden="true">✓</span><div><h3>{habit.name}</h3><p>{habitSchedule(habit)} · {demoDifficulties.find((option) => option.value === habit.difficulty)?.label || habit.difficulty} · Вес {habit.xp_weight}</p></div><strong className="habit-reward">+{habit.xp_reward} XP</strong><button className="button button-ghost habit-complete" type="button" disabled={isCompleted || isPending} onClick={() => markComplete(habit)}>{isPending ? 'Сохраняем…' : isCompleted ? 'Выполнено' : 'Отметить'}</button></li> })}</ul> : <div className="habit-empty"><span className="empty-icon" aria-hidden="true">✓</span><div><h3>Привычек пока нет</h3><p>{guild.isOwner ? 'Добавьте первую общую привычку для вашей команды.' : 'Владелец гильдии скоро сможет добавить общую привычку.'}</p></div></div>}
        </article>
      </section>
    </main>
  )
}
