import api from './client'
import type { DashboardStats } from '../types'

// Статистика для дашборда
export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/dashboard/stats')
  return data
}
