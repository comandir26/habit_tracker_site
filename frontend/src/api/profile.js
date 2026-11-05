import { ApiError, apiRequest } from './client.js'

export async function getProfile() {
  const result = await apiRequest('/auth/profile/')
  const metrics = ['total_xp', 'level', 'streak', 'xp_in_level', 'xp_per_level', 'xp_to_next_level']
  if (!result || typeof result.username !== 'string'
    || metrics.some((key) => !Number.isSafeInteger(result[key]) || result[key] < 0)
    || result.level < 1 || result.xp_per_level < 1
    || result.xp_in_level >= result.xp_per_level
    || result.xp_to_next_level !== result.xp_per_level - result.xp_in_level) {
    throw new ApiError('Сервер вернул неполный профиль.')
  }
  return result
}
