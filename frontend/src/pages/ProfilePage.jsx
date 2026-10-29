import { Link } from 'react-router-dom'
import { AuthControls } from '../auth/AuthControls'
import { ProfileProgress } from '../components/ProfileProgress'

export function ProfilePage() {
  return <main className="app-page">
    <header className="topbar"><Link className="brand" to="/">inHabit</Link><AuthControls /></header>
    <section className="leaderboard-page" aria-labelledby="page-title">
      <Link className="back-link" to="/">← На главную</Link>
      <h1 id="page-title">Мой профиль</h1>
      <ProfileProgress />
    </section>
  </main>
}
