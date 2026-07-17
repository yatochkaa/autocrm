import { useEffect, useState } from 'react'
import { createManager, getSettings, getUsers, updateManager, updateSettings } from '../api/settings'
import { friendlyError } from '../api/client'
import type { ManagerAccountPayload, RuntimeSettings, UserSummary } from '../types'
import { useToast } from '../hooks/useToast'
import { ToastContainer } from '../components/Toast'
import './SettingsPage.css'

const defaults: RuntimeSettings = { auto_priority_enabled: true, normal_after_minutes: 60, high_after_minutes: 180, urgent_after_minutes: 420 }
const emptyAccount: ManagerAccountPayload = { full_name: '', username: '', password: '' }

export default function SettingsPage() {
  const { toasts, toast, removeToast } = useToast()
  const [value, setValue] = useState<RuntimeSettings>(defaults)
  const [users, setUsers] = useState<UserSummary[]>([])
  const [account, setAccount] = useState<ManagerAccountPayload>(emptyAccount)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [settings, people] = await Promise.all([getSettings(), getUsers()])
      setValue(settings); setUsers(people)
    } catch (error) { toast.error(friendlyError(error, 'Не удалось загрузить настройки')) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const saveSettings = async () => {
    if (!(value.normal_after_minutes < value.high_after_minutes && value.high_after_minutes < value.urgent_after_minutes)) {
      toast.error('Пороги должны идти по возрастанию'); return
    }
    setSaving(true)
    try { setValue(await updateSettings(value)); toast.success('Настройки приоритета сохранены') }
    catch (error) { toast.error(friendlyError(error, 'Не удалось сохранить настройки')) }
    finally { setSaving(false) }
  }

  const saveAccount = async () => {
    if (!account.full_name.trim() || !account.username.trim() || (!editingId && (account.password ?? '').length < 8)) {
      toast.error('Заполни фамилию/имя, логин и пароль минимум из 8 символов'); return
    }
    setSaving(true)
    try {
      if (editingId) await updateManager(editingId, { ...account, password: account.password || undefined })
      else await createManager(account)
      toast.success(editingId ? 'Учётная запись обновлена' : 'Менеджер создан')
      setAccount(emptyAccount); setEditingId(null); await load()
    } catch (error) { toast.error(friendlyError(error, 'Не удалось сохранить пользователя')) }
    finally { setSaving(false) }
  }

  const editUser = (user: UserSummary) => {
    setEditingId(user.id)
    setAccount({ full_name: user.full_name, username: user.username, password: '' })
  }
  const numberField = (key: 'normal_after_minutes' | 'high_after_minutes' | 'urgent_after_minutes') => (event: React.ChangeEvent<HTMLInputElement>) => setValue(previous => ({ ...previous, [key]: Math.max(0, Number(event.target.value)) }))

  return (
    <div className="settings-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <div className="page-header"><h1 className="page-title">Настройки</h1></div>
      <section className="card settings-card">
        <div className="settings-heading"><div><h2 className="section-title">Автоматический приоритет</h2><p className="muted">Чем дольше активная заявка остаётся в CRM, тем выше её приоритет.</p></div><label className="switch"><input type="checkbox" checked={value.auto_priority_enabled} onChange={e => setValue(v => ({ ...v, auto_priority_enabled: e.target.checked }))}/><span className="switch-track"/><span className="switch-label-text">Включено</span></label></div>
        <div className="priority-rules">
          <label><span className="rule-dot rule-low"/>Низкий<div>до первого порога в минутах</div></label>
          <label><span className="rule-dot rule-normal"/>Обычный с <input type="number" min="0" value={value.normal_after_minutes} onChange={numberField('normal_after_minutes')} disabled={!value.auto_priority_enabled}/> минут</label>
          <label><span className="rule-dot rule-high"/>Высокий с <input type="number" min="1" value={value.high_after_minutes} onChange={numberField('high_after_minutes')} disabled={!value.auto_priority_enabled}/> минут</label>
          <label><span className="rule-dot rule-urgent"/>Срочный с <input type="number" min="2" value={value.urgent_after_minutes} onChange={numberField('urgent_after_minutes')} disabled={!value.auto_priority_enabled}/> минут</label>
        </div>
        <button className="btn btn-primary" onClick={saveSettings} disabled={saving || loading}>Сохранить настройки</button>
      </section>

      <section className="card settings-card">
        <div className="settings-heading"><div><h2 className="section-title">Пользователи</h2><p className="muted">Все менеджеры видят все заявки. Ответственный используется для контроля и аналитики. Учётные записи создаёт только директор.</p></div></div>
        <div className="manager-form">
          <label className="field-label">Фамилия и имя<input className="field-input" value={account.full_name} onChange={e => setAccount(a => ({ ...a, full_name: e.target.value }))} placeholder="Иванов Иван"/></label>
          <label className="field-label">Логин<input className="field-input" value={account.username} onChange={e => setAccount(a => ({ ...a, username: e.target.value.toLowerCase() }))} placeholder="ivanov"/></label>
          <label className="field-label">{editingId ? 'Новый пароль (необязательно)' : 'Пароль'}<input className="field-input" type="password" value={account.password ?? ''} onChange={e => setAccount(a => ({ ...a, password: e.target.value }))} placeholder="Минимум 8 символов"/></label>
          <div className="manager-form-actions"><button className="btn btn-primary" onClick={saveAccount} disabled={saving}>{editingId ? 'Сохранить пользователя' : 'Создать менеджера'}</button>{editingId && <button className="btn" onClick={() => { setEditingId(null); setAccount(emptyAccount) }}>Отмена</button>}</div>
        </div>
        <div className="settings-table-wrap"><table className="data-table settings-users-table"><thead><tr><th>Фамилия и имя</th><th>Логин</th><th>Роль</th><th>Ответственный за активные</th><th>Всего</th><th/></tr></thead><tbody>{users.map(user => <tr key={user.id}><td><b>{user.full_name}</b></td><td>{user.username}</td><td>{user.role === 'admin' ? 'Директор' : 'Менеджер'}</td><td>{user.active_leads}</td><td>{user.total_leads}</td><td>{user.role === 'manager' && <button className="btn btn-sm" onClick={() => editUser(user)}>Изменить</button>}</td></tr>)}</tbody></table></div>
      </section>
    </div>
  )
}
