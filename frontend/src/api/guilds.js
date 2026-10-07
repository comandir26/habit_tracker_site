import { ApiError, apiRequest } from './client'

const DEMO_GUILD_KEY = 'inhabit.demoGuild'

export const demoGuild = {
  id: 'demo',
  name: 'Режим зверя',
  description: 'Сильнее вместе: маленькие шаги каждый день создают большую победу.',
  color: '#7c4dff',
  isPrivate: false,
  isOwner: true,
  level: 3,
  experience: 3470,
  experienceToLevel: 5000,
  members: [
    { id: '1', name: 'Алексей', xp: 1240, role: 'owner' },
    { id: '2', name: 'Катя', xp: 980 },
    { id: '3', name: 'Илья', xp: 740 },
    { id: '4', name: 'Соня', xp: 510 },
  ],
}

function normalizeGuild(payload) {
  const source = payload?.guild ?? payload
  if (!source?.id && !source?.uuid) return null
  const members = source.members ?? source.participants ?? []
  const experience = Number(source.experience ?? source.xp ?? source.total_xp ?? 0)

  return {
    ...demoGuild,
    ...source,
    id: source.id ?? source.uuid,
    name: source.name ?? source.title ?? demoGuild.name,
    description: source.description ?? demoGuild.description,
    color: source.color ?? source.theme_color ?? demoGuild.color,
    isPrivate: source.is_private ?? source.isPrivate ?? false,
    isOwner: source.is_owner === true,
    level: Number(source.level ?? demoGuild.level),
    experience,
    experienceToLevel: Number(source.experience_to_level ?? source.xp_to_level ?? source.next_level_xp ?? demoGuild.experienceToLevel),
    members: members.map((member, index) => ({
      id: member.id ?? index,
      name: member.display_name ?? member.name ?? member.username ?? member.user?.username ?? 'Участник',
      xp: Number(member.xp ?? member.experience ?? member.total_xp ?? 0),
      role: member.role ?? (member.is_owner ? 'owner' : ''),
    })),
  }
}

function loadStoredDemo() {
  try {
    const stored = window.sessionStorage.getItem(DEMO_GUILD_KEY)
    return stored ? { ...demoGuild, ...JSON.parse(stored) } : demoGuild
  } catch {
    return demoGuild
  }
}

function saveDemo(guild) {
  window.sessionStorage.setItem(DEMO_GUILD_KEY, JSON.stringify(guild))
}

function canUseDemo(error) {
  // A 404 can be an intentional access-isolation response from the backend,
  // so it must remain visible instead of being replaced with local demo data.
  return error instanceof TypeError || error?.status >= 500
}

export async function createGuild(data) {
  try {
    const created = normalizeGuild(await apiRequest('/guilds/', { method: 'POST', body: data }))
    if (created) return { guild: created, isDemo: false }
    throw new ApiError('Сервер вернул неполный ответ.')
  } catch (error) {
    if (!canUseDemo(error)) throw error
    const guild = { ...loadStoredDemo(), ...data, id: 'demo', level: 1, experience: 0, members: [demoGuild.members[0]] }
    saveDemo(guild)
    window.sessionStorage.removeItem('inhabit.demoHabits')
    return { guild, isDemo: true }
  }
}

export async function getGuild(id) {
  if (id === 'demo') return { guild: loadStoredDemo(), isDemo: true }
  const guild = normalizeGuild(await apiRequest(`/guilds/${encodeURIComponent(id)}/`))
  if (guild) return { guild, isDemo: false }
  throw new ApiError('Сервер вернул неполный ответ.')
}
