import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getGuild } from '../api/guilds'
import { createHabit, getHabitDifficulties } from '../api/habits'
import { validateHabit, weekdays } from '../api/habitOptions'

export function HabitCreatePage() {
  const { guildId } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ loading: true, guild: null, difficulties: [], error: '' })
  const [name, setName] = useState('')
  const [schedule, setSchedule] = useState('daily')
  const [days, setDays] = useState([])
  const [difficulty, setDifficulty] = useState('easy')
  const [weight, setWeight] = useState('1')
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const guildPath = `/guilds/${encodeURIComponent(guildId)}`

  useEffect(() => {
    let active = true
    setState({ loading: true, guild: null, difficulties: [], error: '' })
    Promise.all([getGuild(guildId), getHabitDifficulties(guildId)])
      .then(([{ guild }, difficulties]) => {
        if (!active) return
        setState({ loading: false, guild, difficulties, error: '' })
        if (difficulties.length) setDifficulty(difficulties[0].value)
      })
      .catch((requestError) => active && setState({ loading: false, guild: null, difficulties: [], error: requestError.message }))
    return () => { active = false }
  }, [guildId])

  async function handleSubmit(event) {
    event.preventDefault()
    if (submitting) return
    const data = { name: name.trim(), schedule, weekdays: schedule === 'daily' ? [] : [...days].sort((a, b) => a - b), difficulty, xp_weight: Number(weight) }
    const fieldErrors = validateHabit(data)
    setErrors(fieldErrors)
    setError('')
    if (Object.keys(fieldErrors).length) return
    setSubmitting(true)
    try {
      await createHabit(guildId, data)
      navigate(guildPath)
    } catch (requestError) {
      const details = requestError.details ?? {}
      setErrors(details)
      setError(requestError.status === 403 ? 'Добавлять привычки может только владелец гильдии.' : requestError.message || 'Не удалось создать привычку.')
    } finally {
      setSubmitting(false)
    }
  }

  function fieldError(field) {
    if (!errors[field]) return null
    return <span className="field-error" id={`${field}-error`}>{Array.isArray(errors[field]) ? errors[field].join(' ') : String(errors[field])}</span>
  }

  if (state.loading) return <main className="app-page page-status" role="status">Загружаем настройки привычки…</main>
  if (state.error || !state.guild?.isOwner || !state.difficulties.length) return <main className="app-page page-status"><p role="alert">{state.error || (!state.guild?.isOwner ? 'Добавлять привычки может только владелец гильдии.' : 'Список сложности пока недоступен.')}</p><Link className="button button-primary" to={guildPath}>К гильдии</Link></main>

  const selectedDifficulty = state.difficulties.find((option) => option.value === difficulty)
  const validWeight = Number.isInteger(Number(weight)) && Number(weight) >= 1 && Number(weight) <= 10

  return <main className="app-page">
    <header className="topbar"><Link className="brand" to="/">inHabit</Link><span className="topbar-caption">Новая привычка</span></header>
    <section className="form-layout" aria-labelledby="page-title">
      <div className="form-intro">
        <Link className="back-link" to={guildPath}>← К гильдии</Link>
        <p className="eyebrow">{state.guild.name}</p>
        <h1 id="page-title">Маленький шаг к общей цели</h1>
        <p>Задайте привычку, расписание и награду за выполнение для вашей команды.</p>
        <div className="tip-card"><span aria-hidden="true">✦</span><p><strong>Награда за выполнение</strong><br />Базовый XP выбранной сложности умножается на вес привычки.</p></div>
        {guildId === 'demo' && <p className="habit-demo-note">Демо-режим: привычки сохраняются только в этой вкладке браузера.</p>}
      </div>
      <form className="guild-form habit-form" onSubmit={handleSubmit}>
        <label>Название привычки<input value={name} onChange={(event) => setName(event.target.value)} required maxLength={120} placeholder="Например, Читать 20 минут" autoFocus aria-invalid={Boolean(errors.name)} aria-describedby={errors.name ? 'name-error' : undefined} />{fieldError('name')}</label>
        <fieldset><legend>Расписание</legend><div className="habit-choice-row">
          <label><input type="radio" name="schedule" value="daily" checked={schedule === 'daily'} onChange={() => setSchedule('daily')} />Каждый день</label>
          <label><input type="radio" name="schedule" value="weekdays" checked={schedule === 'weekdays'} onChange={() => setSchedule('weekdays')} />Выбрать дни</label>
        </div>{fieldError('schedule')}</fieldset>
        {schedule === 'weekdays' && <fieldset aria-describedby={errors.weekdays ? 'weekdays-error' : undefined}><legend>Дни недели</legend><div className="weekday-picker">{weekdays.map((day, index) => <label key={day}><input type="checkbox" checked={days.includes(index + 1)} onChange={(event) => setDays(event.target.checked ? [...days, index + 1] : days.filter((value) => value !== index + 1))} /><span>{day}</span></label>)}</div>{fieldError('weekdays')}</fieldset>}
        <label>Сложность<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} aria-invalid={Boolean(errors.difficulty)} aria-describedby={errors.difficulty ? 'difficulty-error' : undefined}>{state.difficulties.map((option) => <option key={option.value} value={option.value}>{option.label} · {option.base_xp} XP</option>)}</select>{fieldError('difficulty')}</label>
        <label>Вес привычки<input type="number" min="1" max="10" step="1" required value={weight} onChange={(event) => setWeight(event.target.value)} aria-invalid={Boolean(errors.xp_weight)} aria-describedby={`weight-help${errors.xp_weight ? ' xp_weight-error' : ''}`} /><small id="weight-help">Целое число от 1 до 10</small>{fieldError('xp_weight')}</label>
        <p className="reward-preview" role="status">За выполнение: <strong>{validWeight && selectedDifficulty ? `${selectedDifficulty.base_xp * Number(weight)} XP` : 'Укажите вес от 1 до 10'}</strong></p>
        {error && <p className="form-error" role="alert">{error}</p>}
        {errors.non_field_errors && <p className="form-error" role="alert">{errors.non_field_errors.join(' ')}</p>}
        <div className="form-actions"><Link className="button button-ghost" to={guildPath}>Отмена</Link><button className="button button-primary" type="submit" disabled={submitting}>{submitting ? 'Создаём…' : 'Создать привычку'}</button></div>
      </form>
    </section>
  </main>
}
