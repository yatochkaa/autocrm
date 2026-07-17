// src/components/KanbanColumn.tsx  — FULL REPLACEMENT (Phase 2).
// Принимает isOver / canDrop для визуальной обратной связи.
// CSS-классы: kcolumn--valid, kcolumn--invalid, kcolumn--can-drop, kcolumn--no-drop.
import React from 'react'
import { useDroppable } from '@dnd-kit/core'
import type { Lead, LeadStatus } from '../types'
import { STATUS_COLORS } from '../utils/constants'
import KanbanCard from './KanbanCard'
import './KanbanColumn.css'

interface Props {
  status: LeadStatus
  title: string
  leads: Lead[]
  isOver: boolean
  canDrop: boolean | null  // null — ничто не тащится
}

export default function KanbanColumn({ status, title, leads, isOver, canDrop }: Props) {
  const { setNodeRef } = useDroppable({ id: status })

  const dropClass = isOver
    ? canDrop ? 'kcolumn--can-drop' : 'kcolumn--no-drop'
    : canDrop === true ? 'kcolumn--valid' : canDrop === false ? 'kcolumn--invalid' : ''

  return (
    <div
      ref={setNodeRef}
      className={`kcolumn ${dropClass}`}
      style={{ borderTopColor: STATUS_COLORS[status] }}
    >
      <div className="kcolumn__header">
        <span className="kcolumn__title">{title}</span>
        <span className="kcolumn__count">{leads.length}</span>
      </div>
      <div className="kcolumn__body">
        {leads.map(lead => (
          <KanbanCard key={lead.id} lead={lead} />
        ))}
      </div>
    </div>
  )
}
