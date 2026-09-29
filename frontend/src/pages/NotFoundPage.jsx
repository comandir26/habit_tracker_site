import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="page-shell">
      <section className="welcome-card" aria-labelledby="page-title">
        <p className="eyebrow">404</p>
        <h1 id="page-title">Страница не найдена</h1>
        <Link to="/">Вернуться на главную</Link>
      </section>
    </main>
  )
}
