import { createBrowserRouter } from 'react-router-dom'

import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { GuildCreatePage } from './pages/GuildCreatePage'
import { GuildDetailsPage } from './pages/GuildDetailsPage'
import { HabitCreatePage } from './pages/HabitCreatePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { RequireAuth } from './auth/RequireAuth'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/guilds/new',
    element: <RequireAuth><GuildCreatePage /></RequireAuth>,
  },
  {
    path: '/guilds/:guildId',
    element: <RequireAuth><GuildDetailsPage /></RequireAuth>,
  },
  {
    path: '/guilds/:guildId/habits/new',
    element: <RequireAuth><HabitCreatePage /></RequireAuth>,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
