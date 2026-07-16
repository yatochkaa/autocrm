import type { OrderStatus, OrderSource } from '../types'

// Человекочитаемые названия статусов
export const STATUS_LABELS: Record<OrderStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  selection: 'Подбор',
  invoice: 'Счёт',
  sold: 'Продажа',
  rejected: 'Отказ',
}

// Цвета бейджей статусов
export const STATUS_COLORS: Record<OrderStatus, string> = {
  new: '#3b82f6',
  in_progress: '#f59e0b',
  selection: '#8b5cf6',
  invoice: '#06b6d4',
  sold: '#10b981',
  rejected: '#ef4444',
}

// Названия источников
export const SOURCE_LABELS: Record<OrderSource, string> = {
  telegram: 'Telegram',
  manual: 'Вручную',
  website: 'Сайт',
}

// Порядок колонок канбана
export const KANBAN_COLUMNS: OrderStatus[] = [
  'new', 'in_progress', 'selection', 'invoice', 'sold', 'rejected',
]
