import { createBrowserRouter } from 'react-router-dom'

import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { GuildCreatePage } from './pages/GuildCreatePage'
import { GuildDetailsPage } from './pages/GuildDetailsPage'
import { HabitCreatePage } from './pages/HabitCreatePage'
import { GuildInvitesPage } from './pages/GuildInvitesPage'
import { InvitePage } from './pages/InvitePage'
import { GuildJoinPage } from './pages/GuildJoinPage'
import { GuildLeaderboardPage } from './pages/GuildLeaderboardPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { RequireAuth } from './auth/RequireAuth'

export const router = createBrowserRouter([
  {
    path: '/guilds/:guildId/leaderboard',
    element: <RequireAuth><GuildLeaderboardPage /></RequireAuth>,
  },
  {
    path: '/guilds/join',
    element: <RequireAuth><GuildJoinPage /></RequireAuth>,
  },
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
    path: '/guilds/:guildId/invites',
    element: <RequireAuth><GuildInvitesPage /></RequireAuth>,
  },
  {
    path: '/invite/:code',
    element: <RequireAuth><InvitePage /></RequireAuth>,
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
