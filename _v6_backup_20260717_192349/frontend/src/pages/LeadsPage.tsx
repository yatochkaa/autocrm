// src/pages/LeadsPage.tsx — Phase 2 HOTFIX.
// Прежний дизайн (toolbar фильтров, полноценная таблица) + Phase 2:
// PaginatedLeads (result.items), приоритет, серверная сортировка, animated toggle
// «Показывать завершённые» со счётчиками, CSV-экспорт всех отфильтрованных строк.
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { downloadLeadsExcel, getLeads } from '../api/leads'
import { getUsers } from '../api/settings'
import { friendlyError } from '../api/client'
import type { Lead, LeadStatus, LeadSource, LeadFilters, UserSummary } from '../types'
import {
  STATUS_LABELS, STATUS_COLORS, SOURCE_LABELS, SOURCE_ORDER,
  KANBAN_COLUMNS, PRIORITY_LABELS, PRIORITY_COLORS, PRIORITY_ORDER,
} from '../utils/constants'
import { formatRub, formatDate, formatManager } from '../utils/format'
import { useToast } from '../hooks/useToast'
import { useAuth } from '../hooks/useAuth'
import { ToastContainer } from '../components/Toast'
import { Icon, SourceIcon } from '../components/Icon'
import './LeadsPage.css'

const PAGE_SIZE = 20
type SortField = NonNullable<LeadFilters['sort']>
const FILTER_STORAGE_KEY = 'autocrm.leads.filters.v1'
type SavedFilters = { searchInput?:string; status?:string; source?:string; priority?:string; managerId?:string; showCompleted?:boolean; sort?:SortField; order?:'asc'|'desc'; page?:number }
function savedFilters(): SavedFilters { try { return JSON.parse(sessionStorage.getItem(FILTER_STORAGE_KEY) || '{}') as SavedFilters } catch { return {} } }

// Бизнес-порядок приоритетов (backend сортирует enum алфавитно)
const PRIORITY_RANK: Record<string, number> = { urgent: 0, high: 1, normal: 2, low: 3 }

function sortByPriority(items: Lead[], order: 'asc' | 'desc'): Lead[] {
  return [...items].sort((a, b) => {
    const d = (PRIORITY_RANK[a.priority] ?? 9) - (PRIORITY_RANK[b.priority] ?? 9)
    return order === 'desc' ? d : -d
  })
}

export default function LeadsPage() {
  const navigate = useNavigate()
  const { toasts, toast, removeToast } = useToast()
  const { isAdmin } = useAuth()

  const [rows, setRows] = useState<Lead[]>([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [page, setPage] = useState(() => savedFilters().page ?? 1)
  const [loading, setLoading] = useState(true)

  const [searchInput, setSearchInput] = useState(() => savedFilters().searchInput ?? '')
  const [search, setSearch] = useState(() => savedFilters().searchInput?.trim() ?? '')
  const [status, setStatus] = useState(() => savedFilters().status ?? '')
  const [source, setSource] = useState(() => savedFilters().source ?? '')
  const [priority, setPriority] = useState(() => savedFilters().priority ?? '')
  const [managerId, setManagerId] = useState(() => savedFilters().managerId ?? '')
  const [users, setUsers] = useState<UserSummary[]>([])
  const [showCompleted, setShowCompleted] = useState(() => savedFilters().showCompleted ?? false)
  const [sort, setSort] = useState<SortField>(() => savedFilters().sort ?? 'created_at')
  const [order, setOrder] = useState<'asc' | 'desc'>(() => savedFilters().order ?? 'desc')
  const [counts, setCounts] = useState({ won: 0, lost: 0 })
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    getUsers().then(setUsers).catch(() => undefined)
  }, [isAdmin])

  useEffect(() => {
    sessionStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify({ searchInput, status, source, priority, managerId, showCompleted, sort, order, page }))
  }, [searchInput, status, source, priority, managerId, showCompleted, sort, order, page])

  // Debounce поиска
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput.trim()); setPage(1) }, 350)
    return () => clearTimeout(t)
  }, [searchInput])

  const baseFilters = useCallback((): LeadFilters => {
    const f: LeadFilters = { include_completed: showCompleted, sort, order }
    if (search) f.search = search
    if (status) f.status = status as LeadStatus
    if (source) f.source = source as LeadSource
    if (priority) f.priority = priority as NonNullable<LeadFilters['priority']>
    if (managerId) f.manager_id = Number(managerId)
    return f
  }, [search, status, source, priority, managerId, showCompleted, sort, order])

  // Загрузка страницы
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getLeads({ ...baseFilters(), page, limit: PAGE_SIZE })
      .then(res => {
        if (cancelled) return
        const items = sort === 'priority' ? sortByPriority(res.items, order) : res.items
        setRows(items); setTotal(res.total); setPages(res.pages)
      })
      .catch(e => { if (!cancelled) toast.error(friendlyError(e, 'Не удалось загрузить заявки')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseFilters, page])

  // Счётчики завершённых (Продажа: N · Отказ: N)
  useEffect(() => {
    let cancelled = false
    Promise.all([
      getLeads({ status: 'won', include_completed: true, page: 1, limit: 1 }),
      getLeads({ status: 'lost', include_completed: true, page: 1, limit: 1 }),
    ])
      .then(([w, l]) => { if (!cancelled) setCounts({ won: w.total, lost: l.total }) })
      .catch(() => undefined)
    return () => { cancelled = true }
  }, [])

  const resetFilters = () => {
    setSearchInput(''); setSearch(''); setStatus(''); setSource(''); setPriority(''); setManagerId('')
    setShowCompleted(false); setSort('created_at'); setOrder('desc'); setPage(1)
    sessionStorage.removeItem(FILTER_STORAGE_KEY)
  }

  const handleSort = (field: SortField) => {
    if (sort === field) setOrder(o => (o === 'asc' ? 'desc' : 'asc'))
    else { setSort(field); setOrder(field === 'name' ? 'asc' : 'desc') }
    setPage(1)
  }
  const sortArrow = (field: SortField) => (sort === field ? (order === 'asc' ? ' ▲' : ' ▼') : '')

  const handleExport = async () => {
    setExporting(true)
    try { await downloadLeadsExcel(baseFilters()); toast.success('Excel-файл сформирован') }
    catch (e) { toast.error(friendlyError(e, 'Не удалось сформировать Excel')) }
    finally { setExporting(false) }
  }


  const pageWindow = useMemo(() => {
    const res: Array<number | '…'> = []
    for (let i = 1; i <= pages; i++) {
      if (i === 1 || i === pages || Math.abs(i - page) <= 2) res.push(i)
      else if (res[res.length - 1] !== '…') res.push('…')
    }
    return res
  }, [page, pages])

  return (
    <div className="leads-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <div className="page-header">
        <h1 className="page-title">Заявки</h1>
        <div className="leads-toolbar-right">
          <button className="btn" onClick={handleExport} disabled={exporting || loading}>{exporting ? 'Экспорт…' : <><Icon name="download" size={14}/> Excel</>}</button>
          <button className="btn btn-primary" onClick={() => navigate('/leads/new')}><><Icon name="plus" size={14}/> Новая заявка</></button>
        </div>
      </div>

      {/* Единый toolbar фильтров */}
      <div className="card filters-bar">
        <input
          className="field-input search-input"
          placeholder="Поиск: имя, телефон, VIN, авто…"
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
        />
        <select className="field-input filter-select" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
          <option value="">Все статусы</option>
          {KANBAN_COLUMNS.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
        <select className="field-input filter-select" value={source} onChange={e => { setSource(e.target.value); setPage(1) }}>
          <option value="">Все источники</option>
          {SOURCE_ORDER.map(s => <option key={s} value={s}>{SOURCE_LABELS[s]}</option>)}
        </select>
        <select className="field-input filter-select" value={priority} onChange={e => { setPriority(e.target.value); setPage(1) }}>
          <option value="">Все приоритеты</option>
          {PRIORITY_ORDER.map(p => <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>)}
        </select>
        {isAdmin && (
          <select className="field-input filter-select" value={managerId} onChange={e => { setManagerId(e.target.value); setPage(1) }}>
            <option value="">Все менеджеры</option>
            {users.filter(item => item.role === 'manager').map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}
          </select>
        )}
        <label className="switch">
          <input type="checkbox" checked={showCompleted} onChange={e => { setShowCompleted(e.target.checked); setPage(1) }} />
          <span className="switch-track" />
          <span className="switch-label-text">Показывать завершённые</span>
        </label>
        <span className="completed-switch-counts">Продажа: {counts.won} · Отказ: {counts.lost}</span>
        <button className="btn btn-sm filters-reset" onClick={resetFilters}><Icon name="reset" size={14}/>Сбросить</button>
      </div>

      <div className="card leads-table-card">
        <div className="leads-table-wrap">
          <table className="data-table leads-table">
            <thead>
              <tr>
                <th>ID</th>
                <th className="th-sortable" onClick={() => handleSort('name')}>Клиент{sortArrow('name')}</th>
                <th>Телефон</th>
                <th>Автомобиль</th>
                <th className="th-sortable" onClick={() => handleSort('status')}>Статус{sortArrow('status')}</th>
                <th className="th-sortable" onClick={() => handleSort('priority')}>Приоритет{sortArrow('priority')}</th>
                <th>Источник</th>
                <th className="th-sortable" onClick={() => handleSort('total_amount')}>Сумма{sortArrow('total_amount')}</th>
                <th>Маржа</th>
                <th>Ответственный</th>
                <th className="th-sortable" onClick={() => handleSort('created_at')}>Дата{sortArrow('created_at')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}><td colSpan={11}><div className="skeleton skeleton-text" /></td></tr>
                ))
              ) : rows.length === 0 ? (
                <tr><td colSpan={11}>
                  <div className="empty-state">
                    <div className="empty-state-icon">📭</div>
                    <div className="empty-state-title">Заявки не найдены</div>
                    <div className="empty-state-desc">Попробуйте изменить фильтры или поиск</div>
                  </div>
                </td></tr>
              ) : rows.map(l => (
                <tr key={l.id} className="lead-row" onClick={() => navigate(`/leads/${l.id}`)}>
                  <td>#{l.id}</td>
                  <td><b>{l.name}</b></td>
                  <td>{l.phone ?? '—'}</td>
                  <td>{l.car_info ?? '—'}</td>
                  <td><span className="status-dot" style={{ background: STATUS_COLORS[l.status] }} />{STATUS_LABELS[l.status]}</td>
                  <td><span className="priority-chip" style={{ background: PRIORITY_COLORS[l.priority] }}>{PRIORITY_LABELS[l.priority]}</span></td>
                  <td><span className="source-inline" title={SOURCE_LABELS[l.source]}><SourceIcon source={l.source}/>{SOURCE_LABELS[l.source]}</span></td>
                  <td>{formatRub(l.total_amount)}</td>
                  <td><span className={l.total_margin != null && l.total_margin < 0 ? 'negative' : 'positive'}>{formatRub(l.total_margin)}</span></td>
                  <td>{users.find(item => item.id === l.manager_id)?.full_name ?? formatManager(l.manager_id)}</td>
                  <td>{formatDate(l.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-footer">
          <span className="muted">Всего: {total} · Страница {page} из {pages}</span>
          {pages > 1 && (
            <div className="pagination">
              <button className="page-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>‹</button>
              {pageWindow.map((p, i) => p === '…'
                ? <span key={`e${i}`} className="pagination-ellipsis">…</span>
                : <button key={p} className={`page-btn${p === page ? ' active' : ''}`} onClick={() => setPage(p)}>{p}</button>)}
              <button className="page-btn" disabled={page >= pages} onClick={() => setPage(p => p + 1)}>›</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
