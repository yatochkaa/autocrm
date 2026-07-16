import api from './client'
import type { User } from '../types'

// Список всех менеджеров (для фильтра)
export async function getManagers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/users')
  return data
}
