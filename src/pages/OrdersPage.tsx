import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { getOrders } from '../api/orders'
import { getManagers } from '../api/users'
import type { Order, OrderFilters, OrderStatus, OrderSource, User } from '../types'
import { STATUS_LABELS, STATUS_COLORS, SOURCE_LABELS } from '../utils/constants'
import { formatRub, formatDate } from '../utils/format'
import './OrdersPage.css'

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [managers, setManagers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<OrderFilters>({
    status: '', source: '', manager_id: '', page: 1, size: 20,
  })

  // Загружаем список менеджеров один раз
  useEffect(() => {
    getManagers().then(setManagers).catch(console.error)
  }, [])

  const fetchOrders = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getOrders(filters)
      setOrders(res.items)
      setTotal(res.total)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { fetchOrders() }, [fetchOrders])

  const totalPages = Math.ceil(total / filters.size)

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Заявки</h1>
        <Link to="/orders/new" className="btn btn-primary">+ Новая заявка</Link>
      </div>

      {/* Фильтры */}
      <div className="filters card">
        <select
          value={filters.status}
          onChange={e => setFilters(f => ({ ...f, status: e.target.value as OrderStatus | '', page: 1 }))}
        >
          <option value="">Все статусы</option>
          {(Object.keys(STATUS_LABELS) as OrderStatus[]).map(s => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>

        <select
          value={filters.source}
          onChange={e => setFilters(f => ({ ...f, source: e.target.value as OrderSource | '', page: 1 }))}
        >
          <option value="">Все источники</option>
          {(Object.keys(SOURCE_LABELS) as OrderSource[]).map(s => (
            <option key={s} value={s}>{SOURCE_LABELS[s]}</option>
          ))}
        </select>

        <select
          value={filters.manager_id}
          onChange={e => setFilters(f => ({ ...f, manager_id: e.target.value ? Number(e.target.value) : '', page: 1 }))}
        >
          <option value="">Все менеджеры</option>
          {managers.map(m => (
            <option key={m.id} value={m.id}>{m.full_name || m.username}</option>
          ))}
        </select>
      </div>

      {/* Таблица */}
      <div className="card orders-table-wrap">
        {loading ? (
          <div className="loading">Загрузка...</div>
        ) : (
          <table className="orders-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Статус</th>
                <th>Клиент</th>
                <th>VIN / Авто</th>
                <th>Источник</th>
                <th>Менеджер</th>
                <th>Сумма</th>
                <th>Маржа</th>
                <th>Создана</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 && (
                <tr><td colSpan={9} className="empty">Заявок не найдено</td></tr>
              )}
              {orders.map(o => (
                <tr key={o.id}>
                  <td>
                    <Link to={`/orders/${o.id}`} className="order-link">#{o.id}</Link>
                  </td>
                  <td>
                    <span className="status-badge" style={{ background: STATUS_COLORS[o.status] }}>
                      {STATUS_LABELS[o.status]}
                    </span>
                  </td>
                  <td>{o.client_name}<br /><span className="muted">{o.client_phone}</span></td>
                  <td>{o.vin}<br /><span className="muted">{o.car_model}</span></td>
                  <td>{SOURCE_LABELS[o.source]}</td>
                  <td>{o.manager?.full_name ?? '—'}</td>
                  <td>{formatRub(o.total_sell)}</td>
                  <td className={o.total_margin >= 0 ? 'positive' : 'negative'}>{formatRub(o.total_margin)}</td>
                  <td className="muted">{formatDate(o.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Пагинация */}
      {totalPages > 1 && (
        <div className="pagination">
          <button disabled={filters.page === 1} onClick={() => setFilters(f => ({ ...f, page: f.page - 1 }))}>←</button>
          <span>Стр. {filters.page} из {totalPages}</span>
          <button disabled={filters.page === totalPages} onClick={() => setFilters(f => ({ ...f, page: f.page + 1 }))}>→</button>
        </div>
      )}
    </div>
  )
}
