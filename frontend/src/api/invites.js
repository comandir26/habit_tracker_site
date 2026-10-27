import { ApiError, apiRequest } from './client.js'

export const inviteLifetimes = [
  { days: 1, label: '1 день' },
  { days: 7, label: '7 дней' },
  { days: 30, label: '30 дней' },
]

export const defaultInviteLifetime = 7

const demoKey = 'inhabit.demoInvites'
// Matches the backend alphabet: no 0/O or 1/I/L, so codes are easy to dictate.
const codeAlphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

export function normalizeInviteCode(value) {
  return value.trim().toUpperCase()
}

export function buildInviteLink(code, origin = window.location.origin) {
  return `${origin}/invite/${encodeURIComponent(code)}`
}

export function isInviteActive(invite, now = new Date()) {
  return new Date(invite.expires_at) > now
}

export function formatInviteExpiry(expiresAt, now = new Date()) {
  const left = new Date(expiresAt) - now
  if (left <= 0) return 'Срок действия истёк'
  const hours = Math.ceil(left / 3_600_000)
  if (hours < 24) return `Действует ещё ${hours} ч`
  return `Действует ещё ${Math.ceil(hours / 24)} дн.`
}

function loadDemoInvites() {
  try {
    return JSON.parse(window.sessionStorage.getItem(demoKey) || '[]')
  } catch {
    return []
  }
}

function demoCode() {
  const bytes = crypto.getRandomValues(new Uint8Array(8))
  return Array.from(bytes, (byte) => codeAlphabet[byte % codeAlphabet.length]).join('')
}

export async function getInvites(guildId) {
  if (guildId === 'demo') return loadDemoInvites().filter((invite) => isInviteActive(invite))
  const payload = await apiRequest(`/guilds/${encodeURIComponent(guildId)}/invites/`)
  const invites = Array.isArray(payload) ? payload : payload?.results
  if (!Array.isArray(invites)) throw new ApiError('Сервер вернул неполный список приглашений.')
  return invites
}

export async function createInvite(guildId, expiresInDays = defaultInviteLifetime) {
  if (guildId !== 'demo') {
    return apiRequest(`/guilds/${encodeURIComponent(guildId)}/invites/`, { method: 'POST', body: { expires_in_days: expiresInDays } })
  }
  const now = new Date()
  const invite = {
    id: crypto.randomUUID(),
    guild: 'demo',
    code: demoCode(),
    created_at: now.toISOString(),
    expires_at: new Date(now.getTime() + expiresInDays * 86_400_000).toISOString(),
    is_expired: false,
  }
  window.sessionStorage.setItem(demoKey, JSON.stringify([invite, ...loadDemoInvites()]))
  return invite
}

export async function getInvite(code) {
  try {
    return await apiRequest(`/invites/${encodeURIComponent(normalizeInviteCode(code))}/`)
  } catch (error) {
    if (error.status === 404) throw new ApiError('Приглашение не найдено. Проверьте код.', { status: 404 })
    if (error.status === 410) throw new ApiError('Срок действия приглашения истёк. Попросите создателя гильдии прислать новое.', { status: 410 })
    throw error
  }
}

export async function joinGuild(code) {
  const normalized = normalizeInviteCode(code)
  if (!new RegExp(`^[${codeAlphabet}]{8}$`).test(normalized)) {
    throw new ApiError('Введите код приглашения из 8 символов.', { status: 400 })
  }
  try {
    return await apiRequest(`/invites/${encodeURIComponent(normalized)}/join/`, { method: 'POST' })
  } catch (error) {
    if (error.status === 404) throw new ApiError('Приглашение не найдено. Проверьте код.', { status: 404 })
    if (error.status === 410) throw new ApiError('Срок действия приглашения истёк. Попросите создателя гильдии прислать новое.', { status: 410 })
    throw error
  }
}
