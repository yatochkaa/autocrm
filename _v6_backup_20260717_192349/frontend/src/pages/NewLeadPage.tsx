import { useEffect, useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { createLead } from '../api/leads'
import { getUsers } from '../api/settings'
import { friendlyError } from '../api/client'
import type { LeadSource, UserSummary } from '../types'
import { SOURCE_LABELS, SOURCE_TOOLTIPS } from '../utils/constants'
import { useToast } from '../hooks/useToast'
import { useAuth } from '../hooks/useAuth'
import { ToastContainer } from '../components/Toast'
import { SourceIcon } from '../components/Icon'
import './NewLeadPage.css'

export default function NewLeadPage() {
  const navigate = useNavigate()
  const { toasts, toast, removeToast } = useToast()
  const { isAdmin } = useAuth()
  const [users, setUsers] = useState<UserSummary[]>([])
  const [managerId, setManagerId] = useState('')
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    name: '',
    phone: '',
    vin: '',
    car_info: '',
    source: 'manual' as LeadSource,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (isAdmin) getUsers().then(setUsers).catch(() => undefined)
  }, [isAdmin])

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    if (!form.name.trim()) e.name = 'Введите имя клиента'
    if (form.vin && form.vin.replace(/\s/g, '').length !== 17) e.vin = 'VIN должен содержать ровно 17 символов'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setSaving(true)
    try {
      const lead = await createLead({
        name: form.name.trim(),
        phone: form.phone.trim() || null,
        vin: form.vin.trim() || null,
        car_info: form.car_info.trim() || null,
        source: form.source,
        manager_id: isAdmin && managerId ? Number(managerId) : undefined,
      })
      toast.success('Заявка создана')
      setTimeout(() => navigate(`/leads/${lead.id}`), 400)
    } catch (err) {
      toast.error(friendlyError(err, 'Не удалось создать заявку'))
    } finally {
      setSaving(false)
    }
  }

  const set = (key: string) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setForm(f => ({ ...f, [key]: e.target.value }))
      if (errors[key]) setErrors(p => ({ ...p, [key]: '' }))
    }

  return (
    <div className="new-lead-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <button className="btn-back" onClick={() => navigate('/leads')}>← Список заявок</button>
      <h1 className="page-title">Новая заявка</h1>

      {/* Подсказка о позициях */}
      <div className="lead-hint">
        💡 Сумма и прибыль заявки рассчитываются автоматически из добавленных позиций.
        После создания заявки добавьте нужные детали в её карточке.
      </div>

      <form className="card new-lead-form" onSubmit={handleSubmit}>
        <div className="form-section">
          <h3 className="form-section-title">Клиент</h3>
          <div className="form-grid">
            <div>
              <label className="field-label">Имя клиента *
                <input
                  className={`field-input${errors.name ? ' error' : ''}`}
                  value={form.name}
                  onChange={set('name')}
                  placeholder="Например: Иванов Иван"
                />
                {errors.name && <span className="field-error">{errors.name}</span>}
              </label>
            </div>
            <div>
              <label className="field-label">Телефон
                <input className="field-input" value={form.phone} onChange={set('phone')} placeholder="+7 900 000-00-00" />
              </label>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">Автомобиль</h3>
          <div className="form-grid">
            <div>
              <label className="field-label">VIN (ровно 17 знаков)
                <input
                  className={`field-input${errors.vin ? ' error' : ''}`}
                  value={form.vin}
                  onChange={set('vin')}
                  maxLength={17}
                  placeholder="WAUZZZ8K4AA123456"
                  style={{ fontFamily: 'monospace', letterSpacing: '0.05em' }}
                />
                {errors.vin && <span className="field-error">{errors.vin}</span>}
              </label>
            </div>
            <div>
              <label className="field-label">Инфо об авто
                <input className="field-input" value={form.car_info} onChange={set('car_info')} placeholder="Audi A4 2018, 2.0 TDI" />
              </label>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3 className="form-section-title">
            Источник
            <span className="form-section-hint">— откуда поступила заявка</span>
          </h3>
          <div className="source-options">
            {(Object.keys(SOURCE_LABELS) as LeadSource[]).map(s => (
              <label
                key={s}
                className={`source-option${form.source === s ? ' source-option--selected' : ''}`}
              >
                <input
                  type="radio"
                  name="source"
                  value={s}
                  checked={form.source === s}
                  onChange={() => setForm(f => ({ ...f, source: s }))}
                  hidden
                />
                <span className="source-option-icon"><SourceIcon source={s} size={18}/></span>
                <span className="source-option-label">{SOURCE_LABELS[s]}</span>
                <span className="source-option-hint">{SOURCE_TOOLTIPS[s]}</span>
              </label>
            ))}
          </div>
        </div>


        {isAdmin && (
          <div className="form-section">
            <h3 className="form-section-title">Ответственный менеджер</h3>
            <label className="field-label">Назначить заявку
              <select className="field-input" value={managerId} onChange={e => setManagerId(e.target.value)}>
                <option value="">Оставить на администраторе</option>
                {users.filter(item => item.role === 'manager').map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}
              </select>
            </label>
          </div>
        )}

        <div className="form-actions">
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? 'Создаю...' : 'Создать заявку'}
          </button>
          <button className="btn" type="button" onClick={() => navigate('/leads')}>Отмена</button>
        </div>
      </form>
    </div>
  )
}
