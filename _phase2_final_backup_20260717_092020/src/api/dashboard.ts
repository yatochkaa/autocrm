import api from './client'
import type { DashboardStats } from '../types'
import { toISO } from '../utils/format'

// Даты по умолчанию: последние 30 дней
export function defaultDateRange(): { date_from: string; date_to: string } {
  const to   = new Date()
  const from = new Date()
  from.setDate(from.getDate() - 30)
  return { date_from: toISO(from), date_to: toISO(to) }
}

export async function getDashboardStats(
  date_from: string,
  date_to: string,
  manager_limit = 10,
): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/analytics/dashboard', {
    params: { date_from, date_to, manager_limit },
  })
  return data
}
