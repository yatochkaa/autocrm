import api from './client'
import type { LoginResponse, User } from '../types'

// Логин: сохраняем токен в localStorage
export async function login(username: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams({ username, password })
  const { data } = await api.post<LoginResponse>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('access_token', data.access_token)
  return data
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export function logout(): void {
  localStorage.removeItem('access_token')
}
