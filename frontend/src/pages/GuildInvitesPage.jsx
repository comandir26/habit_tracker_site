import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getGuild } from '../api/guilds'
import { buildInviteLink, createInvite, defaultInviteLifetime, formatInviteExpiry, getInvites, inviteLifetimes } from '../api/invites'
import { AuthControls } from '../auth/AuthControls'

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return
  } catch {
    // The async Clipboard API is missing on plain HTTP and may be blocked by
    // the browser; the legacy copy command still works in those cases.
  }
  const field = document.createElement('textarea')
  field.value = text
  field.setAttribute('readonly', '')
  field.style.position = 'fixed'
  field.style.opacity = '0'
  document.body.append(field)
  field.select()
  const copied = document.execCommand('copy')
  field.remove()
  if (!copied) throw new Error('Не удалось скопировать')
}

export function GuildInvitesPage() {
  const { guildId } = useParams()
  const [state, setState] = useState({ loading: true, guild: null, isDemo: false, invites: [], error: '' })
  const [lifetime, setLifetime] = useState(defaultInviteLifetime)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [copied, setCopied] = useState('')

  useEffect(() => {
    let active = true
    setState({ loading: true, guild: null, isDemo: false, invites: [], error: '' })
    getGuild(guildId)
      .then(async ({ guild, isDemo }) => {
        // Members are refused by the API anyway; skipping the request keeps
        // the page from showing a raw 403 next to the owner-only notice.
        const invites = guild.isOwner ? await getInvites(guildId) : []
        if (active) setState({ loading: false, guild, isDemo, invites, error: '' })
      })
      .catch((error) => active && setState({ loading: false, guild: null, isDemo: false, invites: [], error: error.message || 'Не удалось загрузить приглашения.' }))
    return () => { active = false }
  }, [guildId])

  async function handleCreate(event) {
    event.preventDefault()
    setCreateError('')
    setCreating(true)
    try {
      const invite = await createInvite(guildId, lifetime)
      setState((current) => ({ ...current, invites: [invite, ...current.invites] }))
    } catch (error) {
      setCreateError(error.message || 'Не удалось создать приглашение.')
    } finally {
      setCreating(false)
    }
  }

  async function handleCopy(key, text) {
    try {
      await copyText(text)
      setCopied(key)
    } catch {
      setCopied(`${key}:failed`)
    }
  }

  if (state.loading) return <main className="app-page page-status">Загружаем приглашения…</main>
  if (state.error || !state.guild) return <main className="app-page page-status"><p>{state.error || 'Гильдия не найдена.'}</p><Link className="button button-primary" to="/">На главную</Link></main>

  const { guild, isDemo, invites } = state
  const guildPath = `/guilds/${encodeURIComponent(guildId)}`

  return (
    <main className="app-page">
      <header className="topbar">
        <Link className="brand" to="/">inHabit</Link>
        <span className="topbar-caption">Приглашения</span>
        <AuthControls />
      </header>

      <section className="form-layout" aria-labelledby="page-title">
        <div className="form-intro">
          <Link className="back-link" to={guildPath}>← К гильдии «{guild.name}»</Link>
          <p className="eyebrow">Пригласить друзей</p>
          <h1 id="page-title">Соревнуйтесь вместе в одних привычках</h1>
          <p>Отправьте друзьям ссылку или продиктуйте код. Приглашение работает, пока не истечёт его срок.</p>
          {isDemo && <p className="habit-demo-note">Демо-режим: приглашения хранятся только в этой вкладке и никуда не отправляются.</p>}
        </div>

        {!guild.isOwner ? (
          <div className="guild-form">
            <p className="form-step">Только для создателя</p>
            <p className="muted">Приглашать друзей может только создатель гильдии — попросите прислать вам ссылку.</p>
            <div className="form-actions"><Link className="button button-ghost" to={guildPath}>Вернуться к гильдии</Link></div>
          </div>
        ) : (
          <div className="invite-panel">
            <form className="guild-form" onSubmit={handleCreate}>
              <div className="form-step">Новое приглашение</div>
              <fieldset>
                <legend>Срок действия</legend>
                <div className="habit-choice-row invite-lifetimes">
                  {inviteLifetimes.map((option) => (
                    <label key={option.days}>
                      <input type="radio" name="lifetime" value={option.days} checked={lifetime === option.days} onChange={() => setLifetime(option.days)} />
                      {option.label}
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="form-actions">
                <button className="button button-primary" type="submit" disabled={creating}>{creating ? 'Создаём…' : 'Создать приглашение'}</button>
              </div>
              {createError && <p className="form-error" role="alert">{createError}</p>}
            </form>

            <section className="invites-card" aria-labelledby="invites-title">
              <p className="section-label">Активные приглашения</p>
              <h2 id="invites-title">{invites.length ? `${invites.length} шт.` : 'Пока нет'}</h2>
              {invites.length === 0 ? (
                <p className="muted">Создайте приглашение — здесь появятся код и ссылка, которые можно отправить друзьям.</p>
              ) : (
                <ul className="invites-list">
                  {invites.map((invite) => {
                    const link = buildInviteLink(invite.code)
                    return (
                      <li key={invite.id}>
                        <div className="invite-code-row">
                          <strong className="invite-code" aria-label={`Код приглашения ${invite.code.split('').join(' ')}`}>{invite.code}</strong>
                          <small>{formatInviteExpiry(invite.expires_at)}</small>
                        </div>
                        <input className="invite-link" value={link} readOnly aria-label="Ссылка-приглашение" onFocus={(event) => event.target.select()} />
                        <div className="invite-actions">
                          <button className="button button-ghost button-small" type="button" onClick={() => handleCopy(`${invite.id}:link`, link)}>Копировать ссылку</button>
                          <button className="button button-ghost button-small" type="button" onClick={() => handleCopy(`${invite.id}:code`, invite.code)}>Копировать код</button>
                        </div>
                        <p className="invite-copy-status" role="status">
                          {copied === `${invite.id}:link` && 'Ссылка скопирована.'}
                          {copied === `${invite.id}:code` && 'Код скопирован.'}
                          {copied.startsWith(`${invite.id}:`) && copied.endsWith(':failed') && 'Не удалось скопировать — выделите текст вручную.'}
                        </p>
                      </li>
                    )
                  })}
                </ul>
              )}
            </section>
          </div>
        )}
      </section>
    </main>
  )
}
