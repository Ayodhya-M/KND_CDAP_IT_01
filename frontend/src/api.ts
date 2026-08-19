const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

type ApiError = { detail?: string }

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiError
    throw new Error(body.detail ?? 'Something went wrong. Please try again.')
  }

  return response.json() as Promise<T>
}

export type User = { id: string; email: string; full_name: string }

export type LoginResult = {
  access_token: string
  refresh_token: string
  expires_in: number | null
  token_type: string
}

export const api = {
  register: (email: string, password: string, fullName: string) =>
    request<{ id: string; email: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),
  login: (email: string, password: string) =>
    request<LoginResult>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: (accessToken: string) =>
    request<User>('/auth/me', { headers: { Authorization: `Bearer ${accessToken}` } }),
}
