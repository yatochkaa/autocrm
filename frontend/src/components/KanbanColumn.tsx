// src/components/KanbanColumn.tsx — Phase 2 HOTFIX.
// Колонка горизонтальной доски: цветная линия, счётчик, подсветка валидных/запрещённых drop-зон.
import { useDroppable } from '@dnd-kit/core'
import type { Lead, LeadStatus } from '../types'
import { STATUS_COLORS } from '../utils/constants'
import { KanbanCard } from './KanbanCard'
import './KanbanColumn.css'

interface Props {
  status: LeadStatus
  title: string
  leads: Lead[]
  isOver: boolean
  /** true — разрешённая зона, false — запрещённая, null — нет активного перетаскивания */
  canDrop: boolean | null
  onOpenLead: (id: number) => void
}

export function KanbanColumn({ status, title, leads, isOver, canDrop, onOpenLead }: Props) {
  const { setNodeRef } = useDroppable({ id: status })
  const color = STATUS_COLORS[status]

  let stateClass = ''
  if (isOver && canDrop) stateClass = ' kcolumn--valid'
  else if (isOver && canDrop === false) stateClass = ' kcolumn--invalid'
  else if (canDrop === true) stateClass = ' kcolumn--can-drop'
  else if (canDrop === false) stateClass = ' kcolumn--no-drop'

  return (
    <div ref={setNodeRef} className={`kcolumn${stateClass}`}>
      <div className="kcolumn-accent" style={{ background: color }} />
      <div className="kcolumn-header">
        <span className="kcolumn-dot" style={{ background: color }} />
        <span className="kcolumn-title">{title}</span>
        <span className="kcolumn-count" style={{ background: `${color}22`, color }}>{leads.length}</span>
      </div>
      <div className="kcolumn-body">
        {leads.length === 0 && <div className="kcolumn-empty">Нет заявок</div>}
        {leads.map(l => <KanbanCard key={l.id} lead={l} onOpen={onOpenLead} />)}
      </div>
    </div>
  )
}
