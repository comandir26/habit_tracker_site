import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProfile } from '../api/profile'
import { useAuth } from '../auth/AuthContext'

export function ProfileProgress({ compact = false }) {
  const { user } = useAuth()
  const [state, setState] = useState({ loading: true, profile: null, error: '' })
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    setState({ loading: true, profile: null, error: '' })
    getProfile()
      .then((profile) => active && setState({ loading: false, profile, error: '' }))
      .catch((error) => active && setState({ loading: false, profile: null, error: error.message || 'Не удалось загрузить профиль.' }))
    return () => { active = false }
  }, [user?.id, retry])

  const profile = state.profile
  return <section className={`profile-progress ${compact ? 'profile-compact' : ''}`} aria-label="Личный прогресс">
    {state.loading && <p role="status">Загружаем прогресс…</p>}
    {state.error && <div><p className="form-error" role="alert">{state.error}</p><button className="button button-secondary" type="button" onClick={() => setRetry((value) => value + 1)}>Повторить</button></div>}
    {profile && <>
      <p className="eyebrow">{profile.username}</p>
      <h2>Уровень {profile.level}</h2>
      <p>{profile.xp_in_level} / {profile.xp_per_level} XP до уровня {profile.level + 1}</p>
      <progress value={profile.xp_in_level} max={profile.xp_per_level} aria-label="Прогресс до следующего уровня" />
      <p className="muted">Ещё {profile.xp_to_next_level} XP до следующего уровня</p>
      <dl className="profile-metrics"><div><dt>Всего XP</dt><dd>{profile.total_xp.toLocaleString('ru-RU')}</dd></div><div><dt>Текущий стрик</dt><dd>{profile.streak} дн.</dd></div></dl>
      {!compact && <p className="muted">XP суммируется по вашим гильдиям. Каждый уровень требует 100 XP. Стрик — дни подряд с выполнением хотя бы одной привычки в ваших гильдиях по вашему часовому поясу. Пока сегодня нет выполнения, вчерашняя серия сохраняется.</p>}
      {compact && <Link to="/profile">Открыть профиль →</Link>}
    </>}
  </section>
}
