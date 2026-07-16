import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getOrder, updateOrder, updateOrderStatus, deleteOrder } from '../api/orders'
import type { Order, OrderStatus, OrderItem } from '../types'
import { STATUS_LABELS, STATUS_COLORS, SOURCE_LABELS, KANBAN_COLUMNS } from '../utils/constants'
import { formatRub, formatDate } from '../utils/format'
import './OrderDetailPage.css'

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [form, setForm] = useState<Partial<Order>>({})

  useEffect(() => {
    if (!id) return
    setLoading(true)
    getOrder(Number(id))
      .then(o => { setOrder(o); setForm(o) })
      .finally(() => setLoading(false))
  }, [id])

  const handleStatusChange = async (status: OrderStatus) => {
    if (!order) return
    setSaving(true)
    try {
      const updated = await updateOrderStatus(order.id, status)
      setOrder(updated)
    } finally { setSaving(false) }
  }

  const handleSave = async () => {
    if (!order) return
    setSaving(true)
    try {
      const updated = await updateOrder(order.id, form)
      setOrder(updated)
      setForm(updated)
      setEditMode(false)
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (!order || !confirm(`Удалить заявку #${order.id}?`)) return
    await deleteOrder(order.id)
    navigate('/orders')
  }

  if (loading) return <div className="detail-loading">Загрузка...</div>
  if (!order) return <div className="detail-loading">Заявка не найдена</div>

  return (
    <div className="detail-page">
      {/* Заголовок */}
      <div className="detail-header">
        <div>
          <button className="btn-back" onClick={() => navigate('/orders')}>← Назад</button>
          <h1 className="page-title">Заявка #{order.id}</h1>
          <span className="muted">{formatDate(order.created_at)}</span>
        </div>
        <div className="detail-actions">
          {editMode ? (
            <>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>Сохранить</button>
              <button className="btn" onClick={() => setEditMode(false)}>Отмена</button>
            </>
          ) : (
            <>
              <button className="btn btn-primary" onClick={() => setEditMode(true)}>Редактировать</button>
              <button className="btn btn-danger" onClick={handleDelete}>Удалить</button>
            </>
          )}
        </div>
      </div>

      {/* Статусная воронка */}
      <div className="card status-pipeline">
        {KANBAN_COLUMNS.map(s => (
          <button
            key={s}
            className={`pipeline-step${order.status === s ? ' pipeline-step--active' : ''}`}
            style={order.status === s ? { background: STATUS_COLORS[s], color: '#fff' } : {}}
            onClick={() => handleStatusChange(s)}
            disabled={saving}
          >
            {STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <div className="detail-grid">
        {/* Данные клиента */}
        <div className="card">
          <h2 className="section-title">Клиент</h2>
          {editMode ? (
            <div className="edit-fields">
              <label className="field-label">Имя
                <input className="field-input" value={form.client_name ?? ''}
                  onChange={e => setForm(f => ({ ...f, client_name: e.target.value }))} />
              </label>
              <label className="field-label">Телефон
                <input className="field-input" value={form.client_phone ?? ''}
                  onChange={e => setForm(f => ({ ...f, client_phone: e.target.value }))} />
              </label>
            </div>
          ) : (
            <>
              <p><b>Имя:</b> {order.client_name}</p>
              <p><b>Телефон:</b> {order.client_phone}</p>
              <p><b>Источник:</b> {SOURCE_LABELS[order.source]}</p>
              <p><b>Менеджер:</b> {order.manager?.full_name ?? '—'}</p>
            </>
          )}
        </div>

        {/* Данные авто по VIN */}
        <div className="card">
          <h2 className="section-title">Автомобиль</h2>
          {editMode ? (
            <div className="edit-fields">
              <label className="field-label">VIN
                <input className="field-input" value={form.vin ?? ''}
                  onChange={e => setForm(f => ({ ...f, vin: e.target.value }))} />
              </label>
              <label className="field-label">Модель
                <input className="field-input" value={form.car_model ?? ''}
                  onChange={e => setForm(f => ({ ...f, car_model: e.target.value }))} />
              </label>
            </div>
          ) : (
            <>
              <p><b>VIN:</b> <code>{order.vin || '—'}</code></p>
              <p><b>Модель:</b> {order.car_model || '—'}</p>
            </>
          )}
          {editMode && (
            <label className="field-label" style={{ marginTop: 12 }}>Комментарий
              <textarea className="field-input" rows={3} value={form.comment ?? ''}
                onChange={e => setForm(f => ({ ...f, comment: e.target.value }))} />
            </label>
          )}
          {!editMode && order.comment && (
            <p><b>Комментарий:</b> {order.comment}</p>
          )}
        </div>
      </div>

      {/* Позиции */}
      <div className="card items-section">
        <h2 className="section-title">Позиции</h2>
        {order.items.length === 0 ? (
          <div className="empty">Позиций нет</div>
        ) : (
          <table className="items-table">
            <thead>
              <tr>
                <th>Название</th>
                <th>Артикул</th>
                <th>Кол-во</th>
                <th>Закуп</th>
                <th>Продажа</th>
                <th>Маржа</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item: OrderItem) => (
                <tr key={item.id}>
                  <td>{item.part_name}</td>
                  <td><code>{item.part_number}</code></td>
                  <td>{item.quantity}</td>
                  <td>{formatRub(item.buy_price)}</td>
                  <td>{formatRub(item.sell_price)}</td>
                  <td className={item.sell_price - item.buy_price >= 0 ? 'positive' : 'negative'}>
                    {formatRub((item.sell_price - item.buy_price) * item.quantity)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={4}></td>
                <td><b>{formatRub(order.total_sell)}</b></td>
                <td className="positive"><b>{formatRub(order.total_margin)}</b></td>
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </div>
  )
}
