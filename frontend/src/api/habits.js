import { ApiError, apiRequest } from './client.js'
import { demoDifficulties } from './habitOptions.js'

const demoKey = 'inhabit.demoHabits'

function loadDemoHabits() {
  try {
    return JSON.parse(window.sessionStorage.getItem(demoKey) || '[]')
  } catch {
    return []
  }
}

export async function getHabits(guildId) {
  if (guildId === 'demo') return loadDemoHabits()
  const payload = await apiRequest(`/guilds/${encodeURIComponent(guildId)}/habits/`)
  const habits = Array.isArray(payload) ? payload : payload?.results
  if (!Array.isArray(habits)) throw new ApiError('Сервер вернул неполный список привычек.')
  return habits
}

export async function getHabitDifficulties(guildId) {
  if (guildId === 'demo') return demoDifficulties
  return apiRequest('/habit-difficulties/')
}

export async function createHabit(guildId, data) {
  if (guildId !== 'demo') return apiRequest(`/guilds/${encodeURIComponent(guildId)}/habits/`, { method: 'POST', body: data })
  const difficulty = demoDifficulties.find((option) => option.value === data.difficulty)
  const habit = { ...data, id: crypto.randomUUID(), guild: 'demo', xp_reward: difficulty.base_xp * data.xp_weight, created_at: new Date().toISOString() }
  window.sessionStorage.setItem(demoKey, JSON.stringify([...loadDemoHabits(), habit]))
  return habit
}
