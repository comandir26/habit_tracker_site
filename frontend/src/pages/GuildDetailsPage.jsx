import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getGuild } from '../api/guilds'

export function GuildDetailsPage() {
  const { guildId } = useParams()
  const [state, setState] = useState({ loading: true, guild: null, isDemo: false, error: '' })

  useEffect(() => {
    let active = true
    getGuild(guildId).then(({ guild, isDemo }) => active && setState({ loading: false, guild, isDemo, error: '' }))
      .catch((error) => active && setState({ loading: false, guild: null, isDemo: false, error: error.message }))
    return () => { active = false }
  }, [guildId])

  if (state.loading) return <main className="app-page page-status">Загружаем гильдию…</main>
  if (state.error || !state.guild) return <main className="app-page page-status"><p>{state.error || 'Гильдия не найдена.'}</p><Link className="button button-primary" to="/">На главную</Link></main>

  const { guild, isDemo } = state
  const percentage = Math.min(100, Math.round((guild.experience / guild.experienceToLevel) * 100))

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
      {isDemo && <p className="demo-note">Демо-режим: API гильдий пока недоступен, поэтому показаны локальные данные.</p>}

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

        <article className="empty-habits">
          <span className="empty-icon" aria-hidden="true">✓</span>
          <div><p className="section-label">Привычки гильдии</p><h2>Первый шаг — ваша общая привычка</h2><p>Добавьте её, чтобы команда могла отмечать выполнение и зарабатывать XP.</p><button className="button button-primary" type="button">Добавить привычку</button></div>
        </article>
      </section>
    </main>
  )
}
