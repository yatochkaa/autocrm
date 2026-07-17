// src/utils/constants.ts — Phase 2 HOTFIX.
// Исправлены подписи/цвета статусов по ТЗ, добавлены SOURCE_ORDER и PRIORITY_ORDER.
// Все остальные экспорты сохранены.

import type { LeadStatus, LeadSource, LeadPriority } from '../types'

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  selection: 'Подбор',
  invoice: 'Счёт',
  won: 'Продажа',
  lost: 'Отказ',
}

export const STATUS_COLORS: Record<LeadStatus, string> = {
  new: '#6366f1',
  in_progress: '#3b82f6',
  selection: '#f59e0b',
  invoice: '#8b5cf6',
  won: '#10b981',
  lost: '#ef4444',
}

export const KANBAN_ACTIVE: LeadStatus[] = ['new', 'in_progress', 'selection', 'invoice']
export const KANBAN_COMPLETED: LeadStatus[] = ['won', 'lost']
export const KANBAN_COLUMNS: LeadStatus[] = [...KANBAN_ACTIVE, ...KANBAN_COMPLETED]

export const ALLOWED_TRANSITIONS: Record<LeadStatus, LeadStatus[]> = {
  new: ['in_progress'],
  in_progress: ['selection'],
  selection: ['invoice'],
  invoice: ['won', 'lost'],
  won: [],
  lost: [],
}

export function canTransition(from: LeadStatus, to: LeadStatus): boolean {
  return ALLOWED_TRANSITIONS[from]?.includes(to) ?? false
}

export const SOURCE_LABELS: Record<LeadSource, string> = {
  telegram: 'Telegram',
  manual: 'Вручную',
  site: 'Сайт',
}

export const SOURCE_TOOLTIPS: Record<LeadSource, string> = {
  telegram: 'Заявка через Telegram',
  manual: 'Добавлена вручную',
  site: 'Заявка с сайта',
}

export const SOURCE_ICONS: Record<LeadSource, string> = {
  telegram: '📬',
  manual: '✍️',
  site: '🌐',
}

/** Бизнес-порядок источников */
export const SOURCE_ORDER: LeadSource[] = ['telegram', 'manual', 'site']

// ── Phase 2: Priority ──────────────────────────────────────────────────────
export type { LeadPriority }

export const PRIORITY_LABELS: Record<LeadPriority, string> = {
  low: 'Низкий',
  normal: 'Обычный',
  high: 'Высокий',
  urgent: 'Срочный',
}

export const PRIORITY_COLORS: Record<LeadPriority, string> = {
  low: '#94a3b8',
  normal: '#64748b',
  high: '#f59e0b',
  urgent: '#ef4444',
}

/** Бизнес-порядок приоритетов: urgent → high → normal → low */
export const PRIORITY_ORDER: LeadPriority[] = ['urgent', 'high', 'normal', 'low']
