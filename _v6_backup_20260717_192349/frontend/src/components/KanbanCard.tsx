// src/components/KanbanCard.tsx — Phase 2 HOTFIX.
// Оформленная карточка: имя, авто, телефон, источник, сумма, маржа, приоритет.
// Двойной клик или кнопка ↗ открывает заявку. Без полного email в узкой карточке.
import type { CSSProperties } from 'react'
import { useDraggable } from '@dnd-kit/core'
import type { Lead } from '../types'
import { STATUS_COLORS, SOURCE_LABELS, PRIORITY_LABELS, PRIORITY_COLORS } from '../utils/constants'
import { formatRub } from '../utils/format'
import { Icon, SourceIcon } from './Icon'
import './KanbanCard.css'

interface Props {
  lead: Lead
  onOpen?: (id: number) => void
  /** Копия в DragOverlay: без регистрации draggable-узла */
  isOverlay?: boolean
}

export function KanbanCard({ lead, onOpen, isOverlay }: Props) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: lead.id,
    disabled: isOverlay,
  })

  const style = {
    '--card-accent': STATUS_COLORS[lead.status],
    opacity: !isOverlay && isDragging ? 0.4 : undefined,
  } as CSSProperties

  return (
    <div
      ref={isOverlay ? undefined : setNodeRef}
      className={`kboard-card${isOverlay ? ' kboard-card--overlay' : ''}`}
      style={style}
      onDoubleClick={() => onOpen?.(lead.id)}
      {...attributes}
      {...listeners}
    >
      <div className="kcard-accent-bar" />
      <div className="kcard-head">
        <span className="kcard-name">{lead.name}</span>
        <button
          type="button"
          className="kcard-open-btn"
          title="Открыть заявку"
          onClick={e => { e.stopPropagation(); onOpen?.(lead.id) }}
          onPointerDown={e => e.stopPropagation()}
        >↗</button>
      </div>
      {lead.car_info && <div className="kcard-line kcard-car"><Icon name="car" size={13}/> {lead.car_info}</div>}
      {lead.phone && <div className="kcard-line kcard-phone"><Icon name="phone" size={13}/> {lead.phone}</div>}
      <div className="kcard-line kcard-source"><SourceIcon source={lead.source} size={13}/> {SOURCE_LABELS[lead.source]}</div>
      <div className="kcard-footer">
        <span className="kcard-amount">{formatRub(lead.total_amount)}</span>
        <span className="kcard-margin">маржа {formatRub(lead.total_margin)}</span>
        <span className="kcard-priority" style={{ background: PRIORITY_COLORS[lead.priority] }}>{PRIORITY_LABELS[lead.priority]}</span>
      </div>
    </div>
  )
}
