// src/utils/csv.ts — Phase 2 HOTFIX.
// CSV для русского Excel: UTF-8 BOM, первая строка sep=;, разделитель «;»,
// CRLF, все значения в кавычках, числа без ₽/% с десятичной запятой, даты DD.MM.YYYY.
import type { Lead, DashboardStats } from '../types'
import { STATUS_LABELS, SOURCE_LABELS, PRIORITY_LABELS } from './constants'
import { formatManager } from './format'

const SEP = ';'
const EOL = '\r\n'
const BOM = '\uFEFF'

/** Безопасная ячейка: всегда в кавычках, " → "" */
export function csvCell(value: unknown): string {
  const text = value == null ? '' : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

/** Число: десятичная запятая, без символов валюты/процентов/разделителей тысяч. */
export function csvNum(value: number | null | undefined, decimals = 2): string {
  if (value == null) return csvCell('')
  const factor = 10 ** decimals
  const rounded = Math.round(value * factor) / factor
  return csvCell(String(rounded).replace('.', ','))
}

function fmtDate(iso: string): string {
  const d = new Date(iso)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  return `${dd}.${mm}.${d.getFullYear()}`
}

/** Дата в формате DD.MM.YYYY (ячейкой) */
export function csvDate(iso: string | null | undefined): string {
  if (!iso) return csvCell('')
  return csvCell(fmtDate(iso))
}

const row = (cells: string[]): string => cells.join(SEP)

/** Имя файла <prefix>-YYYY-MM-DD.csv */
export function csvFileName(prefix = 'autocrm-report'): string {
  const d = new Date()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${prefix}-${d.getFullYear()}-${mm}-${dd}.csv`
}

/** CSV аналитики (секции через пустую строку) */
export function buildDashboardCsv(stats: DashboardStats, dateFrom: string, dateTo: string): string {
  const lines: string[] = []
  lines.push('sep=;')
  lines.push(row([csvCell('Отчёт AutoCRM')]))
  lines.push(row([csvCell('Период'), csvCell(`${fmtDate(dateFrom)} — ${fmtDate(dateTo)}`)]))
  lines.push('')

  const ov = stats.overview
  lines.push(row([csvCell('Обзор')]))
  lines.push(row([csvCell('Показатель'), csvCell('Значение')]))
  lines.push(row([csvCell('Всего заявок'), csvNum(ov.total_leads, 0)]))
  lines.push(row([csvCell('Продажи'), csvNum(ov.sales, 0)]))
  lines.push(row([csvCell('Конверсия, %'), csvNum(ov.conversion_percent)]))
  lines.push(row([csvCell('Выручка'), csvNum(ov.revenue)]))
  lines.push(row([csvCell('Средний чек'), csvNum(ov.average_check)]))
  lines.push('')

  lines.push(row([csvCell('Источники')]))
  lines.push(row([csvCell('Источник'), csvCell('Заявок'), csvCell('Доля, %')]))
  for (const s of stats.sources.items) {
    lines.push(row([
      csvCell((SOURCE_LABELS as Record<string, string>)[s.source] ?? s.source),
      csvNum(s.leads, 0),
      csvNum(s.share_percent),
    ]))
  }
  lines.push('')

  lines.push(row([csvCell('Менеджеры')]))
  lines.push(row([csvCell('Email'), csvCell('Продажи'), csvCell('Выручка'), csvCell('Средний чек')]))
  for (const m of stats.managers.items) {
    lines.push(row([
      csvCell(m.email),
      csvNum(m.sales, 0),
      csvNum(m.revenue),
      csvNum(m.sales > 0 ? m.revenue / m.sales : 0),
    ]))
  }
  lines.push('')

  lines.push(row([csvCell('Среднее время')]))
  lines.push(row([csvCell('Этап'), csvCell('Выборка'), csvCell('Часы'), csvCell('Минуты')]))
  for (const s of stats.stage_times.items) {
    lines.push(row([
      csvCell((STATUS_LABELS as Record<string, string>)[s.stage] ?? s.stage),
      csvNum(s.sample_count, 0),
      csvNum(s.average_hours),
      csvNum(Math.round(s.average_seconds / 60), 0),
    ]))
  }

  return BOM + lines.join(EOL) + EOL
}

/** CSV отфильтрованного списка заявок (13 колонок) */
export function buildLeadsCsv(leads: Lead[]): string {
  const lines: string[] = []
  lines.push('sep=;')
  lines.push(row([
    'ID', 'Клиент', 'Телефон', 'Автомобиль', 'VIN', 'Статус', 'Приоритет',
    'Источник', 'Ответственный', 'Сумма', 'Маржа', 'Причина отказа', 'Дата создания',
  ].map(csvCell)))
  for (const l of leads) {
    lines.push(row([
      csvNum(l.id, 0),
      csvCell(l.name),
      csvCell(l.phone ?? ''),
      csvCell(l.car_info ?? ''),
      csvCell(l.vin ?? ''),
      csvCell((STATUS_LABELS as Record<string, string>)[l.status] ?? l.status),
      csvCell((PRIORITY_LABELS as Record<string, string>)[l.priority] ?? l.priority),
      csvCell((SOURCE_LABELS as Record<string, string>)[l.source] ?? l.source),
      csvCell(l.manager_id != null ? formatManager(l.manager_id) : ''),
      csvNum(l.total_amount),
      csvNum(l.total_margin),
      csvCell(l.rejection_reason ?? ''),
      csvDate(l.created_at),
    ]))
  }
  return BOM + lines.join(EOL) + EOL
}

/** Скачивание CSV (MIME text/csv;charset=utf-8) */
export function downloadCsv(fileName: string, content: string): void {
  // Русский настольный Excel часто игнорирует UTF-8 BOM при двойном клике.
  // UTF-16LE BOM надёжно сохраняет кириллицу и sep=; на Windows.
  const text = content.replace(/^\uFEFF/, '')
  const bytes = new Uint8Array(2 + text.length * 2)
  bytes[0] = 0xff
  bytes[1] = 0xfe
  for (let i = 0; i < text.length; i += 1) {
    const code = text.charCodeAt(i)
    bytes[2 + i * 2] = code & 0xff
    bytes[3 + i * 2] = code >> 8
  }
  const blob = new Blob([bytes], { type: 'text/csv;charset=utf-16le' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
