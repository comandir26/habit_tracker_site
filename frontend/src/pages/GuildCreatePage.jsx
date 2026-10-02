import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createGuild } from '../api/guilds'

const colors = [
  { name: 'Индиго', value: '#5b5bd6' },
  { name: 'Мята', value: '#0f9f81' },
  { name: 'Коралл', value: '#e66b57' },
  { name: 'Золото', value: '#dd9b28' },
]

export function GuildCreatePage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState(colors[0].value)
  const [isPrivate, setIsPrivate] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      const { guild, isDemo } = await createGuild({
        name: name.trim(), description: description.trim(), color, is_private: isPrivate,
      })
      navigate(`/guilds/${guild.id}${isDemo ? '?demo=1' : ''}`)
    } catch (requestError) {
      setError(requestError.message || 'Не удалось создать гильдию. Попробуйте ещё раз.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <header className="topbar">
        <Link className="brand" to="/">inHabit</Link>
        <span className="topbar-caption">Новая гильдия</span>
        <div className="avatar" aria-label="Профиль Алексея">А</div>
      </header>

      <section className="form-layout" aria-labelledby="page-title">
        <div className="form-intro">
          <Link className="back-link" to="/">← К моим гильдиям</Link>
          <p className="eyebrow">Гильдии</p>
          <h1 id="page-title">Соберите команду для новых побед</h1>
          <p>Гильдия — общее пространство, где привычки и маленькие шаги помогают не сбиться с пути.</p>
          <div className="tip-card">
            <span aria-hidden="true">✦</span>
            <p><strong>Совет</strong><br />Начните с небольшой команды: так проще поддерживать темп и замечать прогресс каждого.</p>
          </div>
        </div>

        <form className="guild-form" onSubmit={handleSubmit}>
          <div className="form-step">Шаг 1 из 1 · Основное</div>
          <label>
            Название гильдии
            <input value={name} onChange={(event) => setName(event.target.value)} maxLength="48" minLength="2" required placeholder="Например, Ранние пташки" autoFocus />
            <small>{name.length}/48</small>
          </label>
          <label>
            О чём ваша команда?
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength="180" rows="4" placeholder="Опишите общую цель или настроение вашей гильдии" />
            <small>{description.length}/180</small>
          </label>
          <fieldset>
            <legend>Цвет гильдии</legend>
            <div className="color-picker">
              {colors.map((option) => (
                <button key={option.value} className={`color-option${color === option.value ? ' selected' : ''}`} type="button" aria-label={option.name} aria-pressed={color === option.value} onClick={() => setColor(option.value)} style={{ '--guild-color': option.value }} />
              ))}
            </div>
          </fieldset>
          <label className="switch-row">
            <input type="checkbox" checked={isPrivate} onChange={(event) => setIsPrivate(event.target.checked)} />
            <span><strong>Закрытая гильдия</strong><small>Вступить можно только по приглашению</small></span>
          </label>
          <div className="form-actions">
            <Link className="button button-ghost" to="/">Отмена</Link>
            <button className="button button-primary" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Создаём…' : 'Создать гильдию'}</button>
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
        </form>
      </section>
    </main>
  )
}
