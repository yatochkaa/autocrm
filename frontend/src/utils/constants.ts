import type { LeadStatus, LeadSource } from '../types'

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new:         'Новая',
  in_progress: 'В работе',
  selection:   'Подбор',
  invoice:     'Счёт',
  won:         'Продажа',
  lost:        'Отказ',
}

export const STATUS_COLORS: Record<LeadStatus, string> = {
  new:         '#6366f1',
  in_progress: '#3b82f6',
  selection:   '#f59e0b',
  invoice:     '#8b5cf6',
  won:         '#10b981',
  lost:        '#ef4444',
}

export const KANBAN_ACTIVE: LeadStatus[]    = ['new', 'in_progress', 'selection', 'invoice']
export const KANBAN_COMPLETED: LeadStatus[] = ['won', 'lost']
export const KANBAN_COLUMNS: LeadStatus[]   = [...KANBAN_ACTIVE, ...KANBAN_COMPLETED]

// Разрешённые переходы статусов (forward-only)
export const ALLOWED_TRANSITIONS: Partial<Record<LeadStatus, LeadStatus[]>> = {
  new:         ['in_progress'],
  in_progress: ['selection'],
  selection:   ['invoice'],
  invoice:     ['won', 'lost'],
  won:         [],
  lost:        [],
}

export function canTransition(from: LeadStatus, to: LeadStatus): boolean {
  return (ALLOWED_TRANSITIONS[from] ?? []).includes(to)
}

export const SOURCE_LABELS: Record<LeadSource, string> = {
  manual:   'Вручную',
  telegram: 'Telegram',
  site:     'Сайт',
}

export const SOURCE_TOOLTIPS: Record<LeadSource, string> = {
  manual:   'Менеджер создал заявку самостоятельно',
  telegram: 'Заявка создана Telegram-ботом',
  site:     'Заявка отправлена через форму сайта',
}

// Иконки для источников
export const SOURCE_ICONS: Record<LeadSource, string> = {
  manual:   '✍️',
  telegram: '✈️',
  site:     '🌐',
}
