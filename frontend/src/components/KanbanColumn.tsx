import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import type { Lead, LeadStatus } from '../types'
import { STATUS_LABELS, STATUS_COLORS } from '../utils/constants'
import { KanbanCard } from './KanbanCard'
import './KanbanColumn.css'

export function KanbanColumn({ status, leads }: { status: LeadStatus; leads: Lead[] }) {
  const { setNodeRef, isOver } = useDroppable({ id: status })

  return (
    <div className={`kcolumn${isOver ? ' kcolumn--over' : ''}`}>
      <div className="kcolumn-header">
        <span className="kcolumn-dot" style={{ background: STATUS_COLORS[status] }} />
        <span className="kcolumn-title">{STATUS_LABELS[status]}</span>
        <span className="kcolumn-count">{leads.length}</span>
      </div>
      <div ref={setNodeRef} className="kcolumn-body">
        <SortableContext items={leads.map(l => l.id)} strategy={verticalListSortingStrategy}>
          {leads.map(lead => <KanbanCard key={lead.id} lead={lead} />)}
        </SortableContext>
        {leads.length === 0 && (
          <div className="kcolumn-empty">Пусто</div>
        )}
      </div>
    </div>
  )
}
