// src/pages/LeadsPage.tsx  — FULL REPLACEMENT (Phase 2).
// Пагинация + фильтр по priority + поиск.
import React, { useEffect, useState, useCallback } from 'react'
import { getLeads } from '../api/leads'
import type { Lead, LeadStatus, LeadSource, LeadPriority, PaginatedLeads } from '../types'
import { STATUS_LABELS, SOURCE_LABELS, PRIORITY_LABELS } from '../utils/constants'

const PAGE_SIZE = 20

export default function LeadsPage() {
  const [data, setData]         = useState<PaginatedLeads | null>(null)
  const [page, setPage]         = useState(1)
  const [status, setStatus]     = useState<LeadStatus | ''>('')
  const [source, setSource]     = useState<LeadSource | ''>('')
  const [priority, setPriority] = useState<LeadPriority | ''>('')
  const [search, setSearch]     = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getLeads({ status, source, priority, search, page, limit: PAGE_SIZE })
      setData(result)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error')
    } finally {
      setLoading(false)
    }
  }, [status, source, priority, search, page])

  useEffect(() => { load() }, [load])

  const handleTextFilter =
    (setter: React.Dispatch<React.SetStateAction<string>>) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setter(e.target.value)
      setPage(1)
    }

  const leads: Lead[] = data?.items ?? []
  const pages = data?.pages ?? 1

  return (
    <div className="leads-page">
      <h1>Заявки</h1>

      <div className="leads-filters">
        <input placeholder="Поиск…" value={search} onChange={handleTextFilter(setSearch)} />
        <select value={status} onChange={e => { setStatus(e.target.value as LeadStatus | ''); setPage(1) }}>
          <option value="">Все статусы</option>
          {(Object.keys(STATUS_LABELS) as LeadStatus[]).map(s => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
        <select value={source} onChange={e => { setSource(e.target.value as LeadSource | ''); setPage(1) }}>
          <option value="">Все источники</option>
          {(Object.keys(SOURCE_LABELS) as LeadSource[]).map(s => (
            <option key={s} value={s}>{SOURCE_LABELS[s]}</option>
          ))}
        </select>
        <select value={priority} onChange={e => { setPriority(e.target.value as LeadPriority | ''); setPage(1) }}>
          <option value="">Все приоритеты</option>
          {(Object.keys(PRIORITY_LABELS) as LeadPriority[]).map(p => (
            <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
          ))}
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Загрузка…</div>}

      <table className="leads-table">
        <thead>
          <tr>
            <th>ID</th><th>Имя</th><th>Статус</th><th>Приоритет</th>
            <th>Источник</th><th>Сумма</th><th>Создано</th>
          </tr>
        </thead>
        <tbody>
          {leads.map(lead => (
            <tr key={lead.id}>
              <td>{lead.id}</td>
              <td>{lead.name}</td>
              <td>{STATUS_LABELS[lead.status]}</td>
              <td>{PRIORITY_LABELS[lead.priority]}</td>
              <td>{SOURCE_LABELS[lead.source]}</td>
              <td>{lead.total_amount.toLocaleString('ru-RU')} ₽</td>
              <td>{new Date(lead.created_at).toLocaleDateString('ru-RU')}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {pages > 1 && (
        <div className="pagination">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>&laquo;</button>
          {Array.from({ length: pages }, (_, i) => i + 1).map(p => (
            <button key={p} onClick={() => setPage(p)} className={p === page ? 'active' : ''}>{p}</button>
          ))}
          <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages}>&raquo;</button>
        </div>
      )}

      {data && (
        <div className="leads-meta">
          Всего: {data.total} заявок • Страница {page} / {pages}
        </div>
      )}
    </div>
  )
}
