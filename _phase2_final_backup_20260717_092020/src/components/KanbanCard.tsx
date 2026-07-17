// src/components/KanbanCard.tsx  — FULL REPLACEMENT (Phase 2).
// isDragging проп, priority badge с PRIORITY_COLORS.
import React from 'react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import type { Lead } from '../types'
import { PRIORITY_COLORS, PRIORITY_LABELS } from '../utils/constants'
import './KanbanCard.css'

interface Props {
  lead: Lead
  isDragging?: boolean
}

export default function KanbanCard({ lead, isDragging = false }: Props) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: lead.id })

  const style: React.CSSProperties = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
  }

  const priorityColor = PRIORITY_COLORS[lead.priority] ?? '#64748b'

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`kcard ${isDragging ? 'kcard--dragging' : ''}`}
      {...attributes}
      {...listeners}
    >
      <div className="kcard__header">
        <span className="kcard__name">{lead.name}</span>
        <span
          className="kcard__priority"
          style={{ backgroundColor: priorityColor }}
          title={PRIORITY_LABELS[lead.priority]}
        >
          {lead.priority.toUpperCase()}
        </span>
      </div>
      {lead.car_info && <div className="kcard__car">{lead.car_info}</div>}
      <div className="kcard__footer">
        <span>{lead.total_amount.toLocaleString('ru-RU')} ₽</span>
        {lead.phone && <span>{lead.phone}</span>}
      </div>
    </div>
  )
}
