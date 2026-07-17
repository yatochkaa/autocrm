import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getLead, updateLead, changeLeadStatus, deleteLead,
  getLeadItems, createLeadItem, deleteLeadItem,
  getLeadHistory, getLeadAudit,
} from '../api/leads'
import {
  getComments, addComment, editComment, deleteComment,
} from '../api/comments'
import { getSettings, getUsers } from '../api/settings'
import { friendlyError } from '../api/client'
import type {
  Lead, LeadStatus, LeadItem, Comment,
  StatusHistoryEntry, AuditLogEntry, RuntimeSettings, UserSummary,
} from '../types'
import {
  STATUS_LABELS, STATUS_COLORS, SOURCE_LABELS,
  PRIORITY_LABELS, PRIORITY_COLORS,
  KANBAN_ACTIVE, ALLOWED_TRANSITIONS, canTransition,
} from '../utils/constants'
import { formatRub, formatDate, formatDateTime, parseNum } from '../utils/format'
import { useToast } from '../hooks/useToast'
import { useAuth } from '../hooks/useAuth'
import { ToastContainer } from '../components/Toast'
import { SourceIcon } from '../components/Icon'
import './LeadDetailPage.css'

// ---- Форма позиции ----
interface ItemForm {
  name: string
  oem: string
  brand: string
  qty: string       // string для нормального редактирования
  price: string
  purchase_price: string
  is_analog: boolean
}

const blank = (): ItemForm => ({ name: '', oem: '', brand: '', qty: '1', price: '', purchase_price: '', is_analog: false })

function calcPreview(f: ItemForm) {
  const qty = parseNum(f.qty)
  const price = parseNum(f.price)
  const pp = parseNum(f.purchase_price)
  const line_total  = price * qty
  const line_margin = (price - pp) * qty
  const margin_pct  = line_total > 0 ? (line_margin / line_total) * 100 : 0
  return { line_total, line_margin, margin_pct }
}

function marginColor(pct: number): string {
  if (pct >= 20) return 'var(--color-success)'
  if (pct >= 5)  return 'var(--color-warning)'
  return 'var(--color-danger)'
}

// ---- Маржа в таблице ----
function lineMarginPct(item: LeadItem): number {
  const total = (item.price ?? 0) * item.qty
  const margin = item.line_margin ?? 0
  return total > 0 ? (margin / total) * 100 : 0
}

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toasts, toast, removeToast } = useToast()
  const { user, isAdmin } = useAuth()

  const [lead, setLead]     = useState<Lead | null>(null)
  const [items, setItems]   = useState<LeadItem[]>([])
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [form, setForm]         = useState<Partial<Lead>>({})
  const [showItemForm, setShowItemForm] = useState(false)
  const [newItem, setNewItem]   = useState<ItemForm>(blank())
  const [itemSaving, setItemSaving] = useState(false)
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof ItemForm, string>>>({})
  const firstItemRef = useRef<HTMLInputElement>(null)

  const [history, setHistory] = useState<StatusHistoryEntry[]>([])
  const [comments, setComments] = useState<Comment[]>([])
  const [audit, setAudit] = useState<AuditLogEntry[]>([])
  const [extrasLoading, setExtrasLoading] = useState(true)
  const [commentText, setCommentText] = useState('')
  const [commentSaving, setCommentSaving] = useState(false)
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null)
  const [editingCommentText, setEditingCommentText] = useState('')
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings | null>(null)
  const [users, setUsers] = useState<UserSummary[]>([])

  const loadExtras = async (leadId: number) => {
    setExtrasLoading(true)
    const [historyResult, commentsResult, auditResult] = await Promise.allSettled([
      getLeadHistory(leadId),
      getComments(leadId),
      isAdmin ? getLeadAudit(leadId) : Promise.resolve([] as AuditLogEntry[]),
    ])
    if (historyResult.status === 'fulfilled') setHistory(historyResult.value)
    else toast.error('Не удалось загрузить историю статусов')
    if (commentsResult.status === 'fulfilled') setComments(commentsResult.value)
    else toast.error('Не удалось загрузить комментарии')
    if (auditResult.status === 'fulfilled') setAudit(auditResult.value)
    else if (isAdmin) toast.error('Не удалось загрузить audit log')
    setExtrasLoading(false)
  }

  useEffect(() => {
    if (!id) return
    const leadId = Number(id)
    setLoading(true)
    Promise.all([getLead(leadId), getLeadItems(leadId)])
      .then(([l, its]) => {
        setLead(l)
        setForm(l)
        setItems(its)
        return loadExtras(leadId)
      })
      .catch(() => toast.error('Не удалось загрузить заявку'))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, isAdmin])

  useEffect(() => {
    if (showItemForm) setTimeout(() => firstItemRef.current?.focus(), 50)
  }, [showItemForm])

  useEffect(() => {
    getSettings().then(setRuntimeSettings).catch(() => undefined)
    getUsers().then(setUsers).catch(() => undefined)
  }, [isAdmin])

  const handleStatusChange = async (status: LeadStatus) => {
    if (!lead) return
    if (!isAdmin && !canTransition(lead.status, status)) {
      toast.error(`Нельзя перевести заявку из «${STATUS_LABELS[lead.status]}» в «${STATUS_LABELS[status]}»`)
      return
    }
    let rejectionReason: string | undefined
    if (status === 'lost') {
      const value = window.prompt('Укажите причину отказа:')
      if (value == null || value.trim() === '') return
      rejectionReason = value.trim()
    }
    setSaving(true)
    try {
      const updated = await changeLeadStatus(lead.id, status, rejectionReason)
      setLead(updated)
      setForm(updated)
      await loadExtras(lead.id)
      toast.success(`Статус — «${STATUS_LABELS[status]}»`)
    } catch (e) {
      toast.error(friendlyError(e, 'Недопустимый переход статуса'))
    } finally { setSaving(false) }
  }

  const handleSave = async () => {
    if (!lead) return
    // Валидация VIN
    if (form.vin && form.vin.replace(/\s/g, '').length !== 17) {
      toast.error('VIN должен содержать 17 символов')
      return
    }
    setSaving(true)
    try {
      const updated = await updateLead(lead.id, form)
      setLead(updated); setForm(updated); setEditMode(false)
      toast.success('Заявка сохранена')
    } catch (e) { toast.error(friendlyError(e, 'Не удалось сохранить')) }
    finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (!lead || !confirm(`Удалить заявку #${lead.id}? Действие необратимо.`)) return
    try {
      await deleteLead(lead.id)
      toast.success('Заявка удалена')
      setTimeout(() => navigate('/leads'), 800)
    } catch (e) { toast.error(friendlyError(e, 'Не удалось удалить заявку')) }
  }

  // ---- Валидация и сохранение позиции ----
  const validateItem = (): boolean => {
    const errors: typeof formErrors = {}
    if (!newItem.name.trim()) errors.name = 'Введите название'
    const qty = parseNum(newItem.qty)
    if (!newItem.qty.trim()) errors.qty = 'Укажите количество'
    else if (qty < 1) errors.qty = 'Количество не менее 1'
    const price = parseNum(newItem.price)
    if (newItem.price.trim() && price < 0) errors.price = 'Цена не может быть отрицательной'
    const pp = parseNum(newItem.purchase_price)
    if (newItem.purchase_price.trim() && pp < 0) errors.purchase_price = 'Закупцена не может быть отрицательной'
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleAddItem = async () => {
    if (!lead || !validateItem()) return
    setItemSaving(true)
    try {
      const payload = {
        name: newItem.name.trim(),
        oem: newItem.oem.trim(),
        brand: newItem.brand.trim(),
        qty: Math.max(1, Math.round(parseNum(newItem.qty))),
        price: parseNum(newItem.price),
        purchase_price: parseNum(newItem.purchase_price),
        is_analog: newItem.is_analog,
      }
      const created = await createLeadItem(lead.id, payload)
      setItems(prev => [...prev, created])
      setNewItem(blank())
      setFormErrors({})
      setShowItemForm(false)
      const fresh = await getLead(lead.id)
      setLead(fresh)
      toast.success('Позиция добавлена')
    } catch (e) { toast.error(friendlyError(e, 'Не удалось сохранить позицию')) }
    finally { setItemSaving(false) }
  }

  const handleDeleteItem = async (itemId: number) => {
    if (!lead || !confirm('Удалить позицию?')) return
    try {
      await deleteLeadItem(lead.id, itemId)
      setItems(prev => prev.filter(i => i.id !== itemId))
      const fresh = await getLead(lead.id)
      setLead(fresh)
      toast.success('Позиция удалена')
    } catch (e) { toast.error(friendlyError(e, 'Не удалось удалить позицию')) }
  }

  const handleAddComment = async () => {
    if (!lead || !commentText.trim()) return
    setCommentSaving(true)
    try {
      const created = await addComment(lead.id, commentText.trim())
      setComments(prev => [...prev, created])
      setCommentText('')
      toast.success('Комментарий добавлен')
    } catch (e) {
      toast.error(friendlyError(e, 'Не удалось добавить комментарий'))
    } finally { setCommentSaving(false) }
  }

  const startEditComment = (comment: Comment) => {
    setEditingCommentId(comment.id)
    setEditingCommentText(comment.text)
  }

  const handleEditComment = async (commentId: number) => {
    if (!lead || !editingCommentText.trim()) return
    setCommentSaving(true)
    try {
      const updated = await editComment(lead.id, commentId, editingCommentText.trim())
      setComments(prev => prev.map(c => (c.id === commentId ? updated : c)))
      setEditingCommentId(null)
      setEditingCommentText('')
      toast.success('Комментарий обновлён')
    } catch (e) {
      toast.error(friendlyError(e, 'Не удалось обновить комментарий'))
    } finally { setCommentSaving(false) }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!lead || !confirm('Удалить комментарий?')) return
    try {
      await deleteComment(lead.id, commentId)
      setComments(prev => prev.filter(c => c.id !== commentId))
      toast.success('Комментарий удалён')
    } catch (e) {
      toast.error(friendlyError(e, 'Не удалось удалить комментарий'))
    }
  }

  const setNI = (key: keyof ItemForm) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const val = e.target.type === 'checkbox'
        ? (e.target as HTMLInputElement).checked
        : e.target.value
      setNewItem(p => ({ ...p, [key]: val }))
      if (formErrors[key]) setFormErrors(p => ({ ...p, [key]: undefined }))
    }

  if (loading) {
    return (
      <div className="detail-page">
        <div className="skeleton skeleton-block" style={{ height: 48, marginBottom: 16 }} />
        <div className="skeleton skeleton-block" style={{ height: 120, marginBottom: 16 }} />
        <div className="skeleton skeleton-block" style={{ height: 200 }} />
      </div>
    )
  }
  if (!lead) return <div className="empty-state"><div className="empty-state-title">Заявка не найдена</div></div>

  const isCompleted = lead.status === 'won' || lead.status === 'lost'
  const allowedNext = ALLOWED_TRANSITIONS[lead.status] ?? []
  const preview = calcPreview(newItem)
  const ageMinutes = Math.max(0, Math.floor((Date.now() - new Date(lead.created_at).getTime()) / 60_000))
  const managerName = (managerId: number | null | undefined) => {
    if (managerId == null) return 'Не назначен'
    return users.find(item => item.id === managerId)?.full_name ?? `Менеджер #${managerId}`
  }
  const auditAction = (value: string) => ({ status_changed:'Изменён статус', manager_assigned:'Назначен ответственный', lead_created:'Создана заявка', lead_updated:'Изменена заявка', update:'Изменена заявка', status_change:'Изменён статус' }[value] ?? value)
  const auditField = (value: string | null) => value === 'status' ? 'Статус' : value === 'manager_id' ? 'Ответственный' : value || '—'
  const auditValue = (field: string | null, value: string | null) => {
    if (!value) return '—'
    if (field === 'status') return STATUS_LABELS[value as LeadStatus] ?? value
    if (field === 'manager_id') return managerName(Number(value))
    return value
  }

  return (
    <div className="detail-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Заголовок */}
      <div className="page-header">
        <div>
          <button className="btn-back" onClick={() => navigate('/leads')}>← Список заявок</button>
          <h1 className="page-title">Заявка #{lead.id}</h1>
          <span className="muted" style={{ fontSize: '.85rem' }}>Создана {formatDate(lead.created_at)}</span>
        </div>
        <div className="detail-actions">
          {editMode ? (
            <>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>Сохранить</button>
              <button className="btn" onClick={() => { setEditMode(false); setForm(lead) }}>Отмена</button>
            </>
          ) : (
            <>
              <button className="btn btn-primary" onClick={() => setEditMode(true)}>Редактировать</button>
              {isAdmin && <button className="btn btn-danger" onClick={handleDelete}>Удалить</button>}
            </>
          )}
        </div>
      </div>

      {/* Воронка статусов */}
      {isCompleted ? (
        <div className="card completed-banner">
          <span className={`badge badge-${lead.status}`}>{STATUS_LABELS[lead.status]}</span>
          <span className="completed-text">Заявка завершена. Для считайтесь в аналитике.</span>
        </div>
      ) : (
        <div className="card status-pipeline">
          <div className="pipeline-label">Текущий этап: <b>{STATUS_LABELS[lead.status]}</b></div>
          <div className="pipeline-steps">
            {KANBAN_ACTIVE.map(s => {
              const isActive   = lead.status === s
              const isAllowed  = isAdmin || canTransition(lead.status, s)
              return (
                <button
                  key={s}
                  className={`pipeline-step${isActive ? ' pipeline-step--current' : ''}${isAllowed ? ' pipeline-step--allowed' : ''}`}
                  style={isActive ? { background: STATUS_COLORS[s], color: '#fff', borderColor: STATUS_COLORS[s] } : {}}
                  onClick={() => isAllowed && handleStatusChange(s)}
                  disabled={saving || (!isActive && !isAllowed)}
                  title={!isActive && !isAllowed ? `Нельзя перейти из «${STATUS_LABELS[lead.status]}» в «${STATUS_LABELS[s]}»` : ''}
                >
                  {STATUS_LABELS[s]}
                </button>
              )
            })}
            <div className="pipeline-separator" />
            {(['won', 'lost'] as LeadStatus[]).map(s => (
              <button
                key={s}
                className={`pipeline-step pipeline-step--terminal badge-${s}`}
                onClick={() => (isAdmin || canTransition(lead.status, s)) && handleStatusChange(s)}
                disabled={saving || (!isAdmin && !canTransition(lead.status, s))}
                title={!isAdmin && !canTransition(lead.status, s) ? `Нельзя перейти из «${STATUS_LABELS[lead.status]}» в «${STATUS_LABELS[s]}»` : ''}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
          {allowedNext.length > 0 && (
            <div className="pipeline-hint">Следующий шаг: {allowedNext.map(s => STATUS_LABELS[s]).join(', ')}</div>
          )}
        </div>
      )}

      {/* Инфо */}
      <div className="detail-grid">
        <div className="card">
          <h2 className="section-title">Клиент</h2>
          {editMode ? (
            <div className="edit-fields">
              <label className="field-label">Имя
                <input className="field-input" value={form.name ?? ''} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </label>
              <label className="field-label">Телефон
                <input className="field-input" value={form.phone ?? ''} onChange={e => setForm(f => ({ ...f, phone: e.target.value || null }))} placeholder="+7..."/>
              </label>
            </div>
          ) : (
            <dl className="info-list">
              <dt>Имя</dt><dd>{lead.name}</dd>
              <dt>Телефон</dt><dd>{lead.phone ?? '—'}</dd>
              <dt>Источник</dt><dd><span className="source-badge"><SourceIcon source={lead.source}/>{SOURCE_LABELS[lead.source]}</span></dd>
            </dl>
          )}
        </div>
        <div className="card">
          <h2 className="section-title">Автомобиль</h2>
          {editMode ? (
            <div className="edit-fields">
              <label className="field-label">VIN (ровно 17 знаков)
                <input className="field-input" value={form.vin ?? ''}
                  maxLength={17}
                  onChange={e => setForm(f => ({ ...f, vin: e.target.value || null }))} />
              </label>
              <label className="field-label">Инфо об авто
                <input className="field-input" value={form.car_info ?? ''}
                  onChange={e => setForm(f => ({ ...f, car_info: e.target.value || null }))} />
              </label>
            </div>
          ) : (
            <dl className="info-list">
              <dt>VIN</dt><dd><code>{lead.vin ?? '—'}</code></dd>
              <dt>Авто</dt><dd>{lead.car_info ?? '—'}</dd>
            </dl>
          )}
        </div>
        <div className="card totals-card">
          <h2 className="section-title">Итоги</h2>
          <div className="totals-row"><span>Сумма</span><strong>{formatRub(lead.total_amount)}</strong></div>
          <div className="totals-row"><span>Маржа</span><strong className={lead.total_margin && lead.total_margin >= 0 ? 'positive' : 'negative'}>{formatRub(lead.total_margin)}</strong></div>
          <div className="totals-row"><span>Оригинал</span><span>{formatRub(lead.original_total)}</span></div>
          <div className="totals-row"><span>Аналог</span><span>{formatRub(lead.analog_total)}</span></div>
        </div>
        <div className="card crm-card">
          <h2 className="section-title">CRM</h2>
          {editMode ? (
            <div className="edit-fields">
              <label className="field-label">Приоритет
                <select
                  className="field-input"
                  value={form.priority ?? 'normal'}
                  disabled={runtimeSettings?.auto_priority_enabled}
                  onChange={e => setForm(f => ({ ...f, priority: e.target.value as Lead['priority'] }))}
                >
                  <option value="low">Низкий</option>
                  <option value="normal">Обычный</option>
                  <option value="high">Высокий</option>
                  <option value="urgent">Срочный</option>
                </select>
                {runtimeSettings?.auto_priority_enabled && <span className="field-help">Управляется автоматически по возрасту заявки</span>}
              </label>
              {isAdmin && (
                <label className="field-label">Ответственный
                  <select className="field-input" value={form.manager_id ?? ''} onChange={e => setForm(f => ({ ...f, manager_id: e.target.value ? Number(e.target.value) : null }))}>
                    <option value="">Не назначен</option>
                    {users.filter(item => item.role === 'manager').map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}
                  </select>
                </label>
              )}
              <label className="field-label">Причина отказа
                <textarea
                  className="field-input field-textarea"
                  value={form.rejection_reason ?? ''}
                  onChange={e => setForm(f => ({ ...f, rejection_reason: e.target.value || null }))}
                  placeholder="Заполняется для статуса «Отказ»"
                />
              </label>
            </div>
          ) : (
            <dl className="info-list">
              <dt>Приоритет</dt>
              <dd><span className="priority-chip" style={{ borderColor: PRIORITY_COLORS[lead.priority], color: PRIORITY_COLORS[lead.priority] }}>{PRIORITY_LABELS[lead.priority]}</span><span className="priority-age">{runtimeSettings?.auto_priority_enabled ? `Авто · заявке ${ageMinutes} мин.` : 'Вручную'}</span></dd>
              <dt>Ответственный</dt><dd>{managerName(lead.manager_id)}</dd>
              <dt>Обновлена</dt><dd>{formatDate(lead.updated_at)}</dd>
              <dt>Причина отказа</dt><dd>{lead.rejection_reason || '—'}</dd>
            </dl>
          )}
        </div>
      </div>

      {/* История, комментарии и audit */}
      <div className="detail-secondary-grid">
        <section className="card detail-section-card">
          <div className="section-header"><h2 className="section-title">История статусов</h2></div>
          {extrasLoading ? <div className="muted">Загрузка…</div> : history.length === 0 ? (
            <div className="empty-compact">История пока пуста</div>
          ) : (
            <div className="timeline-list">
              {[...history].sort((a, b) => String(b.changed_at ?? '').localeCompare(String(a.changed_at ?? ''))).map(event => (
                <div className="timeline-item" key={event.id}>
                  <span className="timeline-dot" style={{ background: STATUS_COLORS[event.to_status as LeadStatus] ?? 'var(--color-muted)' }} />
                  <div>
                    <div className="timeline-title">
                      {event.from_status ? `${STATUS_LABELS[event.from_status as LeadStatus] ?? event.from_status} → ` : ''}
                      <b>{STATUS_LABELS[event.to_status as LeadStatus] ?? event.to_status}</b>
                    </div>
                    <div className="timeline-meta">
                      {event.changed_at ? formatDateTime(event.changed_at) : 'Дата неизвестна'}
                      {event.changed_by != null ? ` · ${users.find(item => item.id === event.changed_by)?.full_name ?? `Пользователь #${event.changed_by}`}` : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="card detail-section-card">
          <div className="section-header"><h2 className="section-title">Комментарии</h2></div>
          <div className="comment-compose">
            <textarea
              className="field-input field-textarea"
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              placeholder="Добавить комментарий…"
              maxLength={5000}
            />
            <button className="btn btn-primary" onClick={handleAddComment} disabled={commentSaving || !commentText.trim()}>
              {commentSaving ? 'Сохраняю…' : 'Добавить'}
            </button>
          </div>
          {extrasLoading ? <div className="muted">Загрузка…</div> : comments.length === 0 ? (
            <div className="empty-compact">Комментариев пока нет</div>
          ) : (
            <div className="comments-list">
              {comments.map(comment => {
                const canManage = isAdmin || comment.author_id === user?.id
                return (
                  <article className="comment-item" key={comment.id}>
                    <div className="comment-head">
                      <span>{comment.author_id != null ? users.find(item => item.id === comment.author_id)?.full_name ?? `Пользователь #${comment.author_id}` : 'Удалённый пользователь'}</span>
                      <span>{formatDateTime(comment.updated_at || comment.created_at)}</span>
                    </div>
                    {editingCommentId === comment.id ? (
                      <div className="comment-edit">
                        <textarea className="field-input field-textarea" value={editingCommentText} onChange={e => setEditingCommentText(e.target.value)} maxLength={5000} />
                        <div className="comment-actions">
                          <button className="btn btn-primary btn-sm" onClick={() => handleEditComment(comment.id)} disabled={commentSaving || !editingCommentText.trim()}>Сохранить</button>
                          <button className="btn btn-sm" onClick={() => setEditingCommentId(null)}>Отмена</button>
                        </div>
                      </div>
                    ) : (
                      <p className="comment-text">{comment.text}</p>
                    )}
                    {canManage && editingCommentId !== comment.id && (
                      <div className="comment-actions">
                        <button className="btn btn-sm" onClick={() => startEditComment(comment)}>Изменить</button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeleteComment(comment.id)}>Удалить</button>
                      </div>
                    )}
                  </article>
                )
              })}
            </div>
          )}
        </section>
      </div>



      {/* Позиции */}
      <div className="card">
        <div className="section-header">
          <h2 className="section-title">Позиции</h2>
          {!showItemForm && (
            <button className="btn btn-primary btn-sm" onClick={() => setShowItemForm(true)}>+ Добавить</button>
          )}
        </div>

        {/* Форма добавления позиции */}
        {showItemForm && (
          <div className="item-form">
            <div className="item-form-header">
              <h3>Новая позиция</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => { setShowItemForm(false); setNewItem(blank()); setFormErrors({}) }}>× Отмена</button>
            </div>

            {/* Пояснение */}
            <div className="item-form-info">
              ℹ️ Оригинал и аналог нужны для раздельной аналитики.
              Прибыль считается независимо от типа: (price − purchase_price) × qty.
            </div>

            <div className="item-form-grid">
              {/* Название */}
              <div className="item-form-field item-form-field--wide">
                <label className="field-label">Название детали *</label>
                <input
                  ref={firstItemRef}
                  className={`field-input${formErrors.name ? ' error' : ''}`}
                  value={newItem.name}
                  onChange={setNI('name')}
                  placeholder="Например: Фильтр масля"
                />
                {formErrors.name && <span className="field-error">{formErrors.name}</span>}
              </div>

              {/* OEM */}
              <div className="item-form-field">
                <label className="field-label">OEM / Артикул</label>
                <input className="field-input" value={newItem.oem} onChange={setNI('oem')} placeholder="06E 115 562" />
              </div>

              {/* Бренд */}
              <div className="item-form-field">
                <label className="field-label">Бренд</label>
                <input className="field-input" value={newItem.brand} onChange={setNI('brand')} placeholder="Bosch, Mann..." />
              </div>

              {/* Количество */}
              <div className="item-form-field">
                <label className="field-label">Количество</label>
                <div className="input-unit-wrap">
                  <input
                    className={`field-input${formErrors.qty ? ' error' : ''}`}
                    inputMode="decimal"
                    value={newItem.qty}
                    onChange={setNI('qty')}
                  />
                  <span className="input-unit">шт.</span>
                </div>
                {formErrors.qty && <span className="field-error">{formErrors.qty}</span>}
              </div>

              {/* Закупочная цена */}
              <div className="item-form-field">
                <label className="field-label">Закупочная цена</label>
                <div className="input-unit-wrap">
                  <input
                    className={`field-input${formErrors.purchase_price ? ' error' : ''}`}
                    inputMode="decimal"
                    value={newItem.purchase_price}
                    onChange={setNI('purchase_price')}
                    placeholder="0"
                  />
                  <span className="input-unit">₽</span>
                </div>
                {formErrors.purchase_price && <span className="field-error">{formErrors.purchase_price}</span>}
              </div>

              {/* Цена продажи */}
              <div className="item-form-field">
                <label className="field-label">Цена продажи</label>
                <div className="input-unit-wrap">
                  <input
                    className={`field-input${formErrors.price ? ' error' : ''}`}
                    inputMode="decimal"
                    value={newItem.price}
                    onChange={setNI('price')}
                    placeholder="0"
                  />
                  <span className="input-unit">₽</span>
                </div>
                {formErrors.price && <span className="field-error">{formErrors.price}</span>}
              </div>

              {/* Тип детали */}
              <div className="item-form-field">
                <label className="field-label">
                  Тип детали
                  <div className="tooltip-wrap">
                    <span className="field-label-hint">❓</span>
                    <div className="tooltip">Оригинал / аналог — для раздельной аналитики.Прибыль считается для обоих.</div>
                  </div>
                </label>
                <select
                  className="field-input"
                  value={newItem.is_analog ? 'analog' : 'original'}
                  onChange={e => setNewItem(p => ({ ...p, is_analog: e.target.value === 'analog' }))}
                >
                  <option value="original">✅ Оригинал</option>
                  <option value="analog">🔄 Аналог</option>
                </select>
              </div>
            </div>

            {/* Предварительный расчёт */}
            <div className="item-preview">
              <div className="item-preview-row">
                <span>Сумма позиции (price × qty)</span>
                <strong>{formatRub(preview.line_total)}</strong>
              </div>
              <div className="item-preview-row">
                <span>Маржа позиции</span>
                <strong style={{ color: marginColor(preview.margin_pct) }}>{formatRub(preview.line_margin)}</strong>
              </div>
              <div className="item-preview-row">
                <span>Маржинальность</span>
                <strong style={{ color: marginColor(preview.margin_pct) }}>
                  {preview.line_total > 0 ? `${preview.margin_pct.toFixed(1)}%` : '0%'}
                </strong>
              </div>
            </div>

            <div className="item-form-actions">
              <button className="btn btn-primary" onClick={handleAddItem} disabled={itemSaving}>
                {itemSaving ? 'Добавляю...' : 'Добавить позицию'}
              </button>
            </div>
          </div>
        )}

        {/* Таблица позиций */}
        {items.length === 0 && !showItemForm ? (
          <div className="empty-state">
            <div className="empty-state-icon">📦</div>
            <div className="empty-state-title">В заявке пока нет позиций</div>
            <div className="empty-state-desc">Добавьте первую деталь, чтобы рассчитать сумму и прибыль</div>
            <button className="btn btn-primary" onClick={() => setShowItemForm(true)}>+ Добавить первую позицию</button>
          </div>
        ) : items.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table items-table">
              <thead>
                <tr>
                  <th>Название</th><th>OEM</th><th>Бренд</th><th>Тип</th>
                  <th className="col-num">Кол-во</th>
                  <th className="col-num">Закуп</th>
                  <th className="col-num">Продажа</th>
                  <th className="col-num">Сумма</th>
                  <th className="col-num">Маржа</th>
                  <th className="col-num">Марж.%</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => {
                  const pct = lineMarginPct(item)
                  return (
                    <tr key={item.id}>
                      <td><b>{item.name}</b></td>
                      <td><code className="oem-code">{item.oem || '—'}</code></td>
                      <td>{item.brand || '—'}</td>
                      <td>
                        {item.is_analog
                          ? <span className="badge badge-analog">🔄 Аналог</span>
                          : <span className="badge badge-original">✅ Оригинал</span>}
                      </td>
                      <td className="col-num">{item.qty}&nbsp;шт.</td>
                      <td className="col-num">{formatRub(item.purchase_price)}</td>
                      <td className="col-num">{formatRub(item.price)}</td>
                      <td className="col-num">{formatRub(item.line_total)}</td>
                      <td className="col-num">
                        <span className={item.line_margin != null && item.line_margin >= 0 ? 'positive' : 'negative'}>
                          {formatRub(item.line_margin)}
                        </span>
                      </td>
                      <td className="col-num">
                        <span style={{ color: marginColor(pct) }}>{pct.toFixed(1)}%</span>
                      </td>
                      <td>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeleteItem(item.id)}>Удалить</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {/* Audit log расположен последним по запросу */}
      {isAdmin && (
        <section className="card detail-section-card">
          <div className="section-header"><h2 className="section-title">Audit log</h2></div>
          {extrasLoading ? <div className="muted">Загрузка…</div> : audit.length === 0 ? (
            <div className="empty-compact">Записей пока нет</div>
          ) : (
            <div className="audit-table-wrap">
              <table className="data-table audit-table">
                <thead><tr><th>Дата</th><th>Действие</th><th>Поле</th><th>Было</th><th>Стало</th><th>Пользователь</th></tr></thead>
                <tbody>
                  {[...audit].sort((a, b) => b.created_at.localeCompare(a.created_at)).map(entry => (
                    <tr key={entry.id}>
                      <td>{formatDateTime(entry.created_at)}</td>
                      <td>{auditAction(entry.action)}</td>
                      <td>{auditField(entry.field)}</td>
                      <td>{auditValue(entry.field, entry.old_value)}</td>
                      <td>{auditValue(entry.field, entry.new_value)}</td>
                      <td>{entry.actor_id != null ? users.find(item => item.id === entry.actor_id)?.full_name ?? `#${entry.actor_id}` : 'Система'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
