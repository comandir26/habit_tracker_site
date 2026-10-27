import { ApiError, apiRequest } from './client.js'

export async function getLeaderboard(guildId, sort = 'xp') {
  if (!['xp', 'streak'].includes(sort)) throw new ApiError('Неизвестный порядок рейтинга.')
  const result = await apiRequest(`/guilds/${encodeURIComponent(guildId)}/leaderboard/?sort=${sort}`)
  if (!result || !Array.isArray(result.members) || typeof result.guild_name !== 'string'
    || result.sort !== sort || result.members.some((member) => (
      !member || !Number.isInteger(member.member_id) || typeof member.username !== 'string'
      || !Number.isInteger(member.rank) || member.rank < 1
      || !Number.isInteger(member.xp) || member.xp < 0
      || !Number.isInteger(member.streak) || member.streak < 0
      || typeof member.is_current_user !== 'boolean'
    ))) throw new ApiError('Сервер вернул неполный рейтинг участников.')
  return result
}
