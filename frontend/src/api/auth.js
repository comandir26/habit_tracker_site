import { apiRequest, setAccessToken } from './client'

const REFRESH_STORAGE_KEY = 'inhabit.refreshToken'

function saveSession(payload) {
  setAccessToken(payload.access)
  window.localStorage.setItem(REFRESH_STORAGE_KEY, payload.refresh)
  return payload.user
}

export async function register(credentials) { return saveSession(await apiRequest('/auth/register/', { method: 'POST', body: credentials })) }
export async function login(credentials) { return saveSession(await apiRequest('/auth/login/', { method: 'POST', body: credentials })) }
export async function getCurrentUser() { return apiRequest('/auth/me/') }
export async function logout() {
  const refresh = window.localStorage.getItem(REFRESH_STORAGE_KEY)
  try { if (refresh) await apiRequest('/auth/logout/', { method: 'POST', body: { refresh } }) }
  finally { setAccessToken(null); window.localStorage.removeItem(REFRESH_STORAGE_KEY) }
}
