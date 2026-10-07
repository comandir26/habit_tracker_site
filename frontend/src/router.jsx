import { createBrowserRouter } from 'react-router-dom'

import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { GuildCreatePage } from './pages/GuildCreatePage'
import { GuildDetailsPage } from './pages/GuildDetailsPage'
import { HabitCreatePage } from './pages/HabitCreatePage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/guilds/new',
    element: <GuildCreatePage />,
  },
  {
    path: '/guilds/:guildId',
    element: <GuildDetailsPage />,
  },
  {
    path: '/guilds/:guildId/habits/new',
    element: <HabitCreatePage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
])
