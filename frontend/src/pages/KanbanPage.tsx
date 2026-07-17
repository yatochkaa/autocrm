import { useState, useEffect } from 'react'
import {
  DndContext, DragOverlay, closestCorners,
  type DragStartEvent, type DragEndEvent,
} from '@dnd-kit/core'
import { getLeads, updateLeadStatus } from '../api/leads'
import { friendlyError } from '../api/client'
import type { Lead, LeadStatus } from '../types'
import {
  KANBAN_ACTIVE, KANBAN_COMPLETED, STATUS_LABELS,
  canTransition,
} from '../utils/constants'
import { KanbanColumn } from '../components/KanbanColumn'
import { KanbanCard } from '../components/KanbanCard'
import { useToast } from '../hooks/useToast'
import { ToastContainer } from '../components/Toast'
import './KanbanPage.css'

export default function KanbanPage() {
  const { toasts, toast, removeToast } = useToast()
  const [leads, setLeads]             = useState<Lead[]>([])
  const [loading, setLoading]         = useState(true)
  const [showCompleted, setShowCompleted] = useState(false)
  const [activeId, setActiveId]       = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    getLeads()
      .then(setLeads)
      .catch(e => toast.error(friendlyError(e, 'Не удалось загрузить заявки')))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const visibleColumns: LeadStatus[] = showCompleted
    ? [...KANBAN_ACTIVE, ...KANBAN_COMPLETED]
    : KANBAN_ACTIVE

  const byStatus = (status: LeadStatus) => leads.filter(l => l.status === status)

  const activeLead = activeId != null ? leads.find(l => l.id === activeId) : null

  const handleDragStart = (e: DragStartEvent) => {
    setActiveId(Number(e.active.id))
  }

  const handleDragEnd = async (e: DragEndEvent) => {
    setActiveId(null)
    const { active, over } = e
    if (!over) return

    const leadId   = Number(active.id)
    const toStatus = over.id as LeadStatus
    const lead     = leads.find(l => l.id === leadId)
    if (!lead || lead.status === toStatus) return

    // Проверяем разрешённый переход до отправки запроса
    if (!canTransition(lead.status, toStatus)) {
      toast.error(
        `Нельзя перевести заявку из «${STATUS_LABELS[lead.status]}» в «${STATUS_LABELS[toStatus]}»`
      )
      return
    }

    // Оптимистично обновляем UI
    setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: toStatus } : l))

    try {
      const updated = await updateLeadStatus(leadId, toStatus)
      setLeads(prev => prev.map(l => l.id === leadId ? updated : l))
      toast.success(`${lead.name} → «${STATUS_LABELS[toStatus]}»`)
    } catch (err) {
      // Откатываем оригинальный статус
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: lead.status } : l))
      toast.error(friendlyError(err, `Нельзя перевести из «${STATUS_LABELS[lead.status]}» в «${STATUS_LABELS[toStatus]}»`))
    }
  }

  const totalByStatus = (s: LeadStatus) => leads.filter(l => l.status === s).length

  return (
    <div className="kanban-page">
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      <div className="page-header">
        <h1 className="page-title">Канбан</h1>
        <label className="completed-toggle">
          <input
            type="checkbox"
            checked={showCompleted}
            onChange={e => setShowCompleted(e.target.checked)}
          />
          <span>Показывать завершённые</span>
          <span className="completed-counts">
            Продажа: {totalByStatus('won')}, Отказ: {totalByStatus('lost')}
          </span>
        </label>
      </div>

      {loading ? (
        <div className="kanban-loading">
          {KANBAN_ACTIVE.map(s => (
            <div key={s} className="kcolumn">
              <div className="kcolumn-header">
                <div className="skeleton skeleton-text" style={{ width: '80%', height: 16 }} />
              </div>
              <div className="kcolumn-body">
                {[1,2].map(i => (
                  <div key={i} className="skeleton skeleton-block" style={{ height: 80 }} />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <DndContext
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="kanban-board">
            {visibleColumns.map(status => (
              <KanbanColumn
                key={status}
                status={status}
                leads={byStatus(status)}
              />
            ))}
          </div>
          <DragOverlay>
            {activeLead && <KanbanCard lead={activeLead} />}
          </DragOverlay>
        </DndContext>
      )}
    </div>
  )
}
