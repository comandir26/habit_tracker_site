# inHabit

Геймифицированный трекер привычек с гильдиями.

## Стек
Django + DRF + PostgreSQL, React, Docker Compose.

## Запуск

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Приложение будет доступно по адресу `http://localhost:5173`. В режиме
разработки запросы к `/api` Vite перенаправляет на backend-контейнер.

Для production-сборки frontend:

```bash
docker compose up --build frontend
```
