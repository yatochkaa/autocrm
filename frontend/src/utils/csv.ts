import type { DashboardStats } from '../types'
import { SOURCE_LABELS, STATUS_LABELS } from './constants'

function esc(v: string | number | null | undefined): string {
  const s = String(v ?? '')
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function row(...cells: (string | number | null | undefined)[]): string {
  return cells.map(esc).join(',') + '\n'
}

export function buildDashboardCsv(stats: DashboardStats, dateFrom: string, dateTo: string): string {
  let csv = '\uFEFF' // BOM для Excel

  csv += row('Отчёт AutoCRM')
  csv += row('Период', `${dateFrom} - ${dateTo}`)
  csv += '\n'

  // Overview
  csv += row('Обзор')
  csv += row('Показатель', 'Значение')
  csv += row('Всего заявок',        stats.overview.total_leads)
  csv += row('Продажи',              stats.overview.sales)
  csv += row('Конверсия, %',        stats.overview.conversion_percent)
  csv += row('Выручка, ₽',            stats.overview.revenue)
  csv += row('Средний чек, ₽',        stats.overview.average_check)
  csv += '\n'

  // Sources
  if (stats.sources.items.length) {
    csv += row('Источники')
    csv += row('Источник', 'Заявок', 'Доля, %')
    for (const s of stats.sources.items) {
      csv += row(SOURCE_LABELS[s.source] ?? s.source, s.leads, s.share_percent)
    }
    csv += '\n'
  }

  // Managers
  if (stats.managers.items.length) {
    csv += row('Менеджеры')
    csv += row('Email', 'Продажи', 'Выручка, ₽')
    for (const m of stats.managers.items) {
      csv += row(m.email, m.sales, m.revenue)
    }
    csv += '\n'
  }

  // Stage times
  if (stats.stage_times.items.length) {
    csv += row('Среднее время по этапам')
    csv += row('Этап', 'Выборка', 'Среднее время (час)', 'Среднее время (мин)')
    for (const s of stats.stage_times.items) {
      csv += row(
        STATUS_LABELS[s.stage] ?? s.stage,
        s.sample_count,
        s.average_hours.toFixed(2),
        Math.round(s.average_seconds / 60),
      )
    }
  }

  return csv
}

export function downloadCsv(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
