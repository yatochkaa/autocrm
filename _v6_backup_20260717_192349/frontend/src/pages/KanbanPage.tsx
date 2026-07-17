// src/pages/KanbanPage.tsx — Phase 2 HOTFIX.
// Горизонтальная доска. Завершённые колонки скрыты по умолчанию (animated toggle со счётчиками).
// DnD: статус определяется даже при drop на карточку; причина отказа для lost запрашивается
// ДО перехода (отмена = ничего); один toast на переход; PointerSensor с activationConstraint.
import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  DndContext, DragOverlay, PointerSensor, useSensor, useSensors,
} from '@dnd-kit/core'
import type { DragStartEvent, DragOverEvent, DragEndEvent } from '@dnd-kit/core'
import { getLeads, changeLeadStatus } from '../api/leads'
import { friendlyError } from '../api/client'
import type { Lead, LeadStatus } from '../types'
import { STATUS_LABELS, KANBAN_ACTIVE, KANBAN_COMPLETED, canTransition } from '../utils/constants'
import { KanbanColumn } from '../components/KanbanColumn'
import { KanbanCard } from '../components/KanbanCard'
import { useToast } from '../hooks/useToast'
import { useAuth } from '../hooks/useAuth'
import { ToastContainer } from '../components/Toast'
import './KanbanPage.css'

export default function KanbanPage() {
  const navigate = useNavigate()
  const { toasts, toast, removeToast } = useToast()
  const { isAdmin } = useAuth()
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [showCompleted, setShowCompleted] = useState(false)
  const [activeLead, setActiveLead] = useState<Lead | null>(null)
  const [overStatus, setOverStatus] = useState<LeadStatus | null>(null)
  const savingRef = useRef(false)

  // Клик не начинает drag
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }))

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const all: Lead[] = []
      let page = 1
      for (;;) {
        const res = await getLeads({ include_completed: true, page, limit: 200 })
        all.push(...res.items)
        if (page >= res.pages || page >= 25) break
        page += 1
      }
      setLeads(all)
    } catch (e) {
      toast.error(friendlyError(e, 'Не удалось загрузить заявки'))
    } finally { setLoading(false) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { load() }, [load])

  const visibleStatuses: LeadStatus[] = showCompleted ? [...KANBAN_ACTIVE, ...KANBAN_COMPLETED] : KANBAN_ACTIVE

  const columns = useMemo(() => {
    const map = new Map<LeadStatus, Lead[]>()
    for (const s of [...KANBAN_ACTIVE, ...KANBAN_COMPLETED]) map.set(s, [])
    for (const l of leads) map.get(l.status)?.push(l)
    return map
  }, [leads])

  const wonCount = columns.get('won')?.length ?? 0
  const lostCount = columns.get('lost')?.length ?? 0

  /** Статус колонки даже при drop на карточку — никогда не undefined */
  const resolveStatus = (overId: string | number | null | undefined): LeadStatus | null => {
    if (overId == null) return null
    const key = String(overId)
    if ((STATUS_LABELS as Record<string, string>)[key]) return key as LeadStatus
    const numId = Number(key)
    if (!Number.isNaN(numId)) {
      const target = leads.find(l => l.id === numId)
      if (target) return target.status
    }
    return null
  }

  const handleDragStart = (e: DragStartEvent) => {
    const lead = leads.find(l => l.id === Number(e.active.id)) ?? null
    setActiveLead(lead)
    setOverStatus(null)
  }
  const handleDragOver = (e: DragOverEvent) => setOverStatus(resolveStatus(e.over?.id))
  const handleDragCancel = () => { setActiveLead(null); setOverStatus(null) }

  const handleDragEnd = async (e: DragEndEvent) => {
    const lead = activeLead
    const to = resolveStatus(e.over?.id)
    setActiveLead(null); setOverStatus(null)
    if (!lead || !to || to === lead.status || savingRef.current) return
    if (!isAdmin && !canTransition(lead.status, to)) {
      toast.warning(`Нельзя перевести «${STATUS_LABELS[lead.status]}» → «${STATUS_LABELS[to]}»`)
      return
    }
    // Причина отказа — ДО оптимистичного обновления; отмена ввода = переход не выполняем
    let reason: string | undefined
    if (to === 'lost') {
      const input = window.prompt('Укажите причину отказа:')
      if (input == null || input.trim() === '') return
      reason = input.trim()
    }
    savingRef.current = true
    const prev = leads
    setLeads(ls => ls.map(l => (l.id === lead.id ? { ...l, status: to } : l)))
    try {
      const updated = await changeLeadStatus(lead.id, to, reason)
      setLeads(ls => ls.map(l => (l.id === lead.id ? updated : l)))
      toast.success(`Заявка #${lead.id}: «${STATUS_LABELS[to]}»`)
    } catch (err) {
      setLeads(prev)
      toast.error(friendlyError(err, 'Недопустимый переход статуса'))
    } finally { savingRef.current = false }
  }

  /** Подсветка зон: true — можно, false — нельзя, null — нейтрально */
  const dropState = (s: LeadStatus): boolean | null => {
    if (!activeLead || s === activeLead.status) return null
    return isAdmin || canTransition(activeLead.status, s)
  }

  return (
    <div className="kanban-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <div className="page-header">
        <h1 className="page-title">Канбан</h1>
        <div className="kanban-toolbar">
          <label className="switch">
            <input type="checkbox" checked={showCompleted} onChange={e => setShowCompleted(e.target.checked)} />
            <span className="switch-track" />
            <span className="switch-label-text">Показывать завершённые</span>
          </label>
          <span className="completed-counts">Продажа: {wonCount} · Отказ: {lostCount}</span>
        </div>
      </div>

      {loading ? (
        <div className="kanban-board">
          {KANBAN_ACTIVE.map(s => <div key={s} className="skeleton skeleton-block kcolumn-skeleton" style={{ flex: '1 0 280px' }} />)}
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragCancel={handleDragCancel}
          onDragEnd={handleDragEnd}
        >
          <div className={`kanban-board${showCompleted ? ' kanban-board--completed' : ''}`}>
            {visibleStatuses.map(s => (
              <KanbanColumn
                key={s}
                status={s}
                title={STATUS_LABELS[s]}
                leads={columns.get(s) ?? []}
                isOver={overStatus === s}
                canDrop={dropState(s)}
                onOpenLead={id => navigate(`/leads/${id}`)}
              />
            ))}
          </div>
          <DragOverlay>{activeLead ? <KanbanCard lead={activeLead} isOverlay /> : null}</DragOverlay>
        </DndContext>
      )}
    </div>
  )
}
