import api from './client'
import type { ManagerAccountPayload, RuntimeSettings, UserSummary } from '../types'

export async function getSettings(): Promise<RuntimeSettings> {
  const { data } = await api.get<RuntimeSettings>('/settings')
  return data
}
export async function updateSettings(value: RuntimeSettings): Promise<RuntimeSettings> {
  const { data } = await api.patch<RuntimeSettings>('/settings', value)
  return data
}
export async function getUsers(): Promise<UserSummary[]> {
  const { data } = await api.get<UserSummary[]>('/settings/users')
  return data
}
export async function createManager(value: ManagerAccountPayload): Promise<UserSummary> {
  const { data } = await api.post<UserSummary>('/settings/users', value)
  return data
}
export async function updateManager(id: number, value: ManagerAccountPayload): Promise<UserSummary> {
  const { data } = await api.patch<UserSummary>(`/settings/users/${id}`, value)
  return data
}
