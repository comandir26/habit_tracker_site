const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? '/api'
const TOKEN_STORAGE_KEY = 'inhabit.accessToken'

export class ApiError extends Error {
  constructor(message, { status, details } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

export function getAccessToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setAccessToken(token) {
  if (token) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
    return
  }

  window.localStorage.removeItem(TOKEN_STORAGE_KEY)
}

export async function apiRequest(path, options = {}) {
  const { headers, body, ...requestOptions } = options
  const token = getAccessToken()
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: {
      Accept: 'application/json',
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      // DRF uses TokenAuthentication; an override keeps the client compatible
      // with a future JWT-based deployment.
      ...(token ? { Authorization: `${import.meta.env?.VITE_AUTH_SCHEME ?? 'Token'} ${token}` } : {}),
      ...headers,
    },
  })

  if (response.status === 204) {
    return null
  }

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(payload?.detail ?? 'Не удалось выполнить запрос к API.', {
      status: response.status,
      details: payload,
    })
  }

  return payload
}
