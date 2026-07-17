import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { Lead } from '../types'
import { STATUS_COLORS, SOURCE_ICONS, SOURCE_LABELS } from '../utils/constants'
import { formatRub, formatDate } from '../utils/format'
import './KanbanCard.css'

export function KanbanCard({ lead }: { lead: Lead }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: lead.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? .5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="kboard-card" {...attributes} {...listeners}>
      <div className="kcard-header">
        <span className="kcard-id">#{lead.id}</span>
        <span className="kcard-source">{SOURCE_ICONS[lead.source]}</span>
      </div>
      <div className="kcard-name">{lead.name}</div>
      {lead.car_info && <div className="kcard-car">{lead.car_info}</div>}
      {lead.phone && <div className="kcard-phone muted">{lead.phone}</div>}
      {lead.total_amount > 0 && (
        <div className="kcard-amount">{formatRub(lead.total_amount)}</div>
      )}
      {lead.total_margin != null && lead.total_margin !== 0 && (
        <div className={`kcard-margin ${lead.total_margin >= 0 ? 'positive' : 'negative'}`}>
          М: {formatRub(lead.total_margin)}
        </div>
      )}
      <div className="kcard-date muted">{formatDate(lead.created_at)}</div>
    </div>
  )
}
