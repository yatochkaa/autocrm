import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { getLeads } from '../api/leads'
import { friendlyError } from '../api/client'
import type { Lead, LeadStatus, LeadSource } from '../types'
import { STATUS_LABELS, STATUS_COLORS, SOURCE_LABELS, SOURCE_ICONS } from '../utils/constants'
import { formatRub, formatDate } from '../utils/format'
import { useToast } from '../hooks/useToast'
import { ToastContainer } from '../components/Toast'
import './LeadsPage.css'

const ALL = '' as const

export default function LeadsPage() {
  const navigate = useNavigate()
  const { toasts, toast, removeToast } = useToast()
  const [leads, setLeads]   = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)

  // Фильтры
  const [search, setSearch]       = useState('')
  const [status, setStatus]       = useState<LeadStatus | ''>( ALL)
  const [source, setSource]       = useState<LeadSource | ''>( ALL)
  const [dateFrom, setDateFrom]   = useState('')
  const [dateTo, setDateTo]       = useState('')

  useEffect(() => {
    setLoading(true)
    getLeads()
      .then(setLeads)
      .catch(e => toast.error(friendlyError(e, 'Не удалось загрузить заявки')))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return leads.filter(l => {
      if (status && l.status !== status) return false
      if (source && l.source !== source) return false
      if (dateFrom && l.created_at < dateFrom) return false
      if (dateTo   && l.created_at.slice(0, 10) > dateTo) return false
      if (!q) return true
      return (
        String(l.id).includes(q) ||
        l.name.toLowerCase().includes(q) ||
        (l.phone ?? '').toLowerCase().includes(q) ||
        (l.vin ?? '').toLowerCase().includes(q) ||
        (l.car_info ?? '').toLowerCase().includes(q)
      )
    })
  }, [leads, search, status, source, dateFrom, dateTo])

  const resetFilters = () => {
    setSearch(''); setStatus(ALL); setSource(ALL); setDateFrom(''); setDateTo('')
  }

  const hasFilters = search || status || source || dateFrom || dateTo

  return (
    <div className="leads-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <div className="page-header">
        <h1 className="page-title">Заявки</h1>
        <button className="btn btn-primary" onClick={() => navigate('/leads/new')}>+ Новая заявка</button>
      </div>

      {/* Фильтры */}
      <div className="card filters-bar">
        <input
          className="field-input search-input"
          placeholder="🔍 Поиск по ID, имени, телефону, VIN, авто..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select className="field-input filter-select" value={status} onChange={e => setStatus(e.target.value as LeadStatus | '')}>
          <option value="">Статус: все</option>
          {(Object.keys(STATUS_LABELS) as LeadStatus[]).map(s => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
        <select className="field-input filter-select" value={source} onChange={e => setSource(e.target.value as LeadSource | '')}>
          <option value="">Источник: все</option>
          {(Object.keys(SOURCE_LABELS) as LeadSource[]).map(s => (
            <option key={s} value={s}>{SOURCE_ICONS[s]} {SOURCE_LABELS[s]}</option>
          ))}
        </select>
        <div className="filter-date-group">
          <input type="date" className="field-input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} title="Дата с" />
          <span className="filter-date-sep">—</span>
          <input type="date" className="field-input" value={dateTo} onChange={e => setDateTo(e.target.value)} title="Дата по" />
        </div>
        {hasFilters && (
          <button className="btn btn-ghost btn-sm" onClick={resetFilters}>× Сбросить</button>
        )}
      </div>

      {/* Таблица */}
      {loading ? (
        <div className="card">
          {[1,2,3,4].map(i => (
            <div key={i} className="skeleton-row">
              <div className="skeleton skeleton-text" style={{ width: '6%' }} />
              <div className="skeleton skeleton-text" style={{ width: '20%' }} />
              <div className="skeleton skeleton-text" style={{ width: '14%' }} />
              <div className="skeleton skeleton-text" style={{ width: '10%' }} />
              <div className="skeleton skeleton-text" style={{ width: '10%' }} />
            </div>
          ))}
        </div>
      ) : (
        <div className="card table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Клиент</th>
                <th>Телефон</th>
                <th>Авто</th>
                <th>Источник</th>
                <th>Статус</th>
                <th className="col-num">Сумма</th>
                <th className="col-num">Маржа</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={9}>
                    <div className="empty-state">
                      <div className="empty-state-icon">📋</div>
                      <div className="empty-state-title">Заявок нет</div>
                      <div className="empty-state-desc">
                        {hasFilters ? 'По вашим фильтрам ничего не найдено' : 'Создайте первую заявку'}
                      </div>
                      {!hasFilters && (
                        <button className="btn btn-primary" onClick={() => navigate('/leads/new')}>+ Новая заявка</button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
              {filtered.map(lead => (
                <tr key={lead.id} className="lead-row" onClick={() => navigate(`/leads/${lead.id}`)}>
                  <td><span className="lead-id">#{lead.id}</span></td>
                  <td><b>{lead.name}</b></td>
                  <td className="muted">{lead.phone ?? '—'}</td>
                  <td className="muted">{lead.car_info ? <span title={lead.vin ?? ''}>{lead.car_info}</span> : (lead.vin ? <code>{lead.vin}</code> : '—')}</td>
                  <td>
                    <span className="source-chip">
                      {SOURCE_ICONS[lead.source]} {SOURCE_LABELS[lead.source]}
                    </span>
                  </td>
                  <td>
                    <span
                      className="status-dot"
                      style={{ background: STATUS_COLORS[lead.status] }}
                    />
                    <span className={`badge badge-${lead.status}`}>{STATUS_LABELS[lead.status]}</span>
                  </td>
                  <td className="col-num">{formatRub(lead.total_amount)}</td>
                  <td className="col-num">
                    <span className={lead.total_margin != null && lead.total_margin >= 0 ? 'positive' : 'negative'}>
                      {formatRub(lead.total_margin)}
                    </span>
                  </td>
                  <td className="muted">{formatDate(lead.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length > 0 && (
            <div className="table-footer">Показано: {filtered.length} из {leads.length}</div>
          )}
        </div>
      )}
    </div>
  )
}
