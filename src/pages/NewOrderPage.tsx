import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { createOrder } from '../api/orders'
import type { OrderSource } from '../types'
import { SOURCE_LABELS } from '../utils/constants'
import './NewOrderPage.css'

export default function NewOrderPage() {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    client_name: '',
    client_phone: '',
    vin: '',
    car_model: '',
    source: 'manual' as OrderSource,
    comment: '',
  })

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const order = await createOrder({ ...form, status: 'new' })
      navigate(`/orders/${order.id}`)
    } finally {
      setSaving(false)
    }
  }

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [key]: e.target.value }))

  return (
    <div className="new-order-page">
      <button className="btn-back" onClick={() => navigate('/orders')}>← Назад</button>
      <h1 className="page-title">Новая заявка</h1>
      <form className="card new-order-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label className="field-label">Имя клиента *
            <input className="field-input" value={form.client_name} onChange={set('client_name')} required />
          </label>
          <label className="field-label">Телефон
            <input className="field-input" value={form.client_phone} onChange={set('client_phone')} />
          </label>
          <label className="field-label">VIN
            <input className="field-input" value={form.vin} onChange={set('vin')} maxLength={17} />
          </label>
          <label className="field-label">Модель авто
            <input className="field-input" value={form.car_model} onChange={set('car_model')} />
          </label>
          <label className="field-label">Источник
            <select className="field-input" value={form.source} onChange={set('source')}>
              {(Object.keys(SOURCE_LABELS) as OrderSource[]).map(s => (
                <option key={s} value={s}>{SOURCE_LABELS[s]}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="field-label">Комментарий
          <textarea className="field-input" rows={3} value={form.comment} onChange={set('comment')} />
        </label>
        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? 'Создаю...' : 'Создать заявку'}
          </button>
          <button className="btn" type="button" onClick={() => navigate('/orders')}>Отмена</button>
        </div>
      </form>
    </div>
  )
}
