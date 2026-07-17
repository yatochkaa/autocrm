// src/pages/KanbanPage.tsx  — FULL REPLACEMENT (Phase 2).
// Использует data.items из PaginatedLeads.
import React, { useEffect, useState } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { getLeads, changeLeadStatus } from '../api/leads'
import type { Lead, LeadStatus } from '../types'
import { KANBAN_COLUMNS, STATUS_LABELS, canTransition } from '../utils/constants'
import KanbanColumn from '../components/KanbanColumn'
import KanbanCard from '../components/KanbanCard'

type ColumnsMap = Record<LeadStatus, Lead[]>

export default function KanbanPage() {
  const [columns, setColumns] = useState<ColumnsMap>(() =>
    Object.fromEntries(KANBAN_COLUMNS.map(s => [s, [] as Lead[]])) as unknown as ColumnsMap
  )
  const [activeId, setActiveId] = useState<number | null>(null)
  const [overId, setOverId]     = useState<LeadStatus | null>(null)
  const [loading, setLoading]   = useState(false)

  const sensors = useSensors(useSensor(PointerSensor, {
    activationConstraint: { distance: 4 },
  }))

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await getLeads({ limit: 200, include_completed: true })
        const leads: Lead[] = data.items  // PaginatedLeads.items
        const map = Object.fromEntries(KANBAN_COLUMNS.map(s => [s, [] as Lead[]])) as unknown as ColumnsMap
        for (const lead of leads) {
          if (map[lead.status]) map[lead.status].push(lead)
        }
        setColumns(map)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const activeLead = activeId
    ? Object.values(columns).flat().find(l => l.id === activeId) ?? null
    : null

  const handleDragStart = (e: DragStartEvent) => {
    setActiveId(e.active.id as number)
  }

  const handleDragOver = (e: DragOverEvent) => {
    setOverId((e.over?.id as LeadStatus) ?? null)
  }

  const handleDragEnd = async (e: DragEndEvent) => {
    const { active, over } = e
    setActiveId(null)
    setOverId(null)
    if (!over) return
    const leadId  = active.id as number
    const toStatus = over.id as LeadStatus
    const lead = Object.values(columns).flat().find(l => l.id === leadId)
    if (!lead || lead.status === toStatus) return
    if (!canTransition(lead.status, toStatus)) return

    // Оптимистичное обновление UI
    setColumns(prev => {
      const next = { ...prev } as ColumnsMap
      next[lead.status] = prev[lead.status].filter(l => l.id !== leadId)
      next[toStatus] = [...prev[toStatus], { ...lead, status: toStatus }]
      return next
    })

    try {
      await changeLeadStatus(leadId, toStatus)
    } catch {
      // Откатить UI при ошибке
      setColumns(prev => {
        const next = { ...prev } as ColumnsMap
        next[toStatus] = prev[toStatus].filter(l => l.id !== leadId)
        next[lead.status] = [...prev[lead.status], lead]
        return next
      })
    }
  }

  if (loading) return <div className="loading">Загрузка…</div>

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="kanban-board">
        {KANBAN_COLUMNS.map(status => (
          <KanbanColumn
            key={status}
            status={status}
            title={STATUS_LABELS[status]}
            leads={columns[status]}
            isOver={overId === status}
            canDrop={activeLead ? canTransition(activeLead.status, status) : null}
          />
        ))}
      </div>
      <DragOverlay>
        {activeLead ? <KanbanCard lead={activeLead} isDragging /> : null}
      </DragOverlay>
    </DndContext>
  )
}
