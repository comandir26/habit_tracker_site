import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <main className="page-shell dashboard-home">
      <section className="welcome-card" aria-labelledby="page-title">
        <p className="eyebrow">⚡ inHabit · ваш путь</p>
        <h1 id="page-title">Маленькие шаги. Большие победы.</h1>
        <p>Соберите гильдию, поддерживайте друзей и превращайте привычки в серию достижений.</p>
        <div className="welcome-actions">
          <Link className="button button-primary" to="/guilds/new">
            Создать гильдию <span aria-hidden="true">→</span>
          </Link>
          <Link className="button button-secondary" to="/guilds/demo">
            Открыть пример гильдии
          </Link>
        </div>
      </section>
      <aside className="home-level-card" aria-label="Текущий уровень"><span>◆</span><p>Ваш уровень</p><strong>7</strong><small>1 840 / 2 000 XP</small></aside>
    </main>
  )
}
