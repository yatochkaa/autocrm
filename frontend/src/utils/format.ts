export function formatRub(v: number | null | undefined): string {
  if (v == null) return '—'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(v)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function formatPercent(v: number | null | undefined, decimals = 1): string {
  if (v == null) return '—'
  return `${v.toFixed(decimals)}%`
}

/** Преобразует строку-редакцию в число. Для пустой строки возвращает 0. */
export function parseNum(s: string): number {
  const n = parseFloat(s.replace(',', '.'))
  return isNaN(n) ? 0 : n
}

/** То-дей в ISO (YYYY-MM-DD) */
export function toISO(date: Date): string {
  return date.toISOString().slice(0, 10)
}

/** Первый день месяца */
export function startOfMonth(date = new Date()): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

/** Последний день месяца */
export function endOfMonth(date = new Date()): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

/** Первый день квартала */
export function startOfQuarter(date = new Date()): Date {
  const q = Math.floor(date.getMonth() / 3)
  return new Date(date.getFullYear(), q * 3, 1)
}
